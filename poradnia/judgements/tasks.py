"""
Celery tasks for judgements app.

This module contains Celery tasks for background processing of court-related data,
migrated from management commands to provide better error handling, retry logic,
and monitoring capabilities.
"""

from typing import Any, Dict

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model

from poradnia.judgements.models import Court, CourtSession
from poradnia.judgements.registry import get_parser_keys
from poradnia.judgements.settings import JUDGEMENT_BOT_USERNAME
from poradnia.judgements.utils import Manager

logger = get_task_logger(__name__)


class LoggerWrapper:
    """Simple wrapper to redirect stdout/stderr to logger."""

    def __init__(self, logger_func):
        self.logger_func = logger_func

    def write(self, message):
        if message and message.strip():
            self.logger_func(message.strip())

    def flush(self):
        pass


@shared_task
def run_court_session_parser(
    court_ids: list = None, parser_key: str = None
) -> Dict[str, Any]:
    """
    Parse court session data from various Polish courts.

    This task processes court session data, creating events and updating
    court sessions based on data scraped from various Polish court websites.

    Args:
        court_ids: Optional list of Court IDs to process. If None, processes all.
        parser_key: Optional parser key to filter courts. Must be from registry.

    Returns:
        Dict containing task execution results including success/failure counts.
    """
    logger.info("Starting court session parser task")

    # Initialize task result structure
    result = _initialize_task_result()

    # Validate inputs and prepare processing environment
    judgement_bot = _prepare_task_environment(parser_key)

    # Get courts to process
    courts_list = _get_courts_to_process(court_ids, parser_key)
    if not courts_list:
        return _complete_task_no_courts(result)

    logger.info(f"Processing {len(courts_list)} courts")

    # Process all courts
    _process_all_courts(courts_list, judgement_bot, result)

    # Finalize and return result
    return _finalize_task_result(result)


def _initialize_task_result() -> Dict[str, Any]:
    """Initialize the task result structure."""
    return {
        "status": "started",
        "courts_processed": 0,
        "courts_failed": 0,
        "total_sessions_created": 0,
        "total_sessions_updated": 0,
        "errors": [],
    }


def _prepare_task_environment(parser_key: str):
    """Validate inputs and prepare the processing environment."""
    # Validate parser_key if provided
    if parser_key and parser_key not in get_parser_keys():
        raise ValueError(f"Invalid parser key: {parser_key}")

    # Get or create the judgement bot user
    User = get_user_model()
    judgement_bot, created = User.objects.get_or_create(username=JUDGEMENT_BOT_USERNAME)
    if created:
        logger.info(f"Created new judgement bot user: {JUDGEMENT_BOT_USERNAME}")

    return judgement_bot


def _get_courts_to_process(court_ids: list, parser_key: str) -> list:
    """Get the list of courts to process based on filters."""
    courts = _get_courts_queryset(court_ids, parser_key)
    return list(courts)


def _complete_task_no_courts(result: Dict[str, Any]) -> Dict[str, Any]:
    """Complete task when no courts are found."""
    logger.warning("No courts found matching the criteria")
    result.update(
        {
            "status": "completed_no_courts",
            "message": "No courts found matching the specified criteria",
        }
    )
    return result


def _process_all_courts(courts_list: list, judgement_bot, result: Dict[str, Any]):
    """Process all courts in the list."""
    # Initialize the manager with logger-based output
    manager = Manager(
        bot=judgement_bot,
        stdout=LoggerWrapper(logger.info),
        stderr=LoggerWrapper(logger.error),
    )

    # Process each court
    for court in courts_list:
        _process_single_court(court, manager, result)


def _process_single_court(court, manager, result: Dict[str, Any]):
    """Process a single court and update results."""
    try:
        logger.info(f"Processing court: {court} (ID: {court.id})")

        # Count sessions before processing (using correct relationship)
        sessions_before = _count_court_sessions(court)
        manager.handle_court(court)
        sessions_after = _count_court_sessions(court)

        sessions_processed = sessions_after - sessions_before
        result["courts_processed"] += 1
        if sessions_processed > 0:
            result["total_sessions_created"] += sessions_processed

        logger.info(
            f"Successfully processed court {court}: "
            f"{sessions_processed} new sessions"
        )

    except Exception as exc:
        result["courts_failed"] += 1
        error_msg = f"Failed to process court {court} (ID: {court.id}): {exc}"
        logger.error(error_msg, exc_info=True)
        result["errors"].append(
            {"court_id": court.id, "court_name": str(court), "error": str(exc)}
        )


def _count_court_sessions(court) -> int:
    """Count court sessions for a given court (through CourtCase relationship)."""
    return CourtSession.objects.filter(courtcase__court=court).count()


def _finalize_task_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize the task result and set final status."""
    if result["courts_failed"] == 0:
        result["status"] = "completed_success"
        logger.info(
            f"Task completed successfully: {result['courts_processed']} courts "
            f"processed, {result['total_sessions_created']} sessions created"
        )
    elif result["courts_processed"] > 0:
        result["status"] = "completed_partial"
        logger.warning(
            f"Task completed with errors: {result['courts_processed']} courts "
            f"succeeded, {result['courts_failed']} courts failed"
        )
    else:
        result["status"] = "failed_all_courts"
        error_msg = f"All {result['courts_failed']} courts failed to process"
        logger.error(error_msg)

    logger.info(f"Court session parser task finished with status: {result['status']}")
    return result


def _get_courts_queryset(court_ids: list = None, parser_key: str = None):
    """
    Get queryset of courts to process based on provided filters.

    Args:
        court_ids: Optional list of Court IDs to filter by
        parser_key: Optional parser key to filter by

    Returns:
        Generator of Court objects that have active parsers
    """
    qs = Court.objects

    if court_ids:
        qs = qs.filter(id__in=court_ids)
    if parser_key:
        qs = qs.filter(parser_key=parser_key)

    # Only return courts that have active parsers (same logic as command)
    return (court for court in qs.all() if court.parser_status)
