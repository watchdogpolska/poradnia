"""
Celery tasks for judgements app.

This module contains Celery tasks for background processing of court-related data,
migrated from management commands to provide better error handling, retry logic,
and monitoring capabilities.
"""

from typing import Any, Dict, List, Optional, Sequence

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model

from poradnia.judgements.models import Court, CourtSession
from poradnia.judgements.registry import get_parser_keys
from poradnia.judgements.settings import (
    JUDGEMENT_BOT_EMAIL,
    JUDGEMENT_BOT_USERNAME,
)
from poradnia.judgements.utils import Manager

logger = get_task_logger(__name__)


class LoggerWrapper:
    """Redirect file-like stdout/stderr writes to a logger function."""

    def __init__(self, logger_func):
        self.logger_func = logger_func

    def write(self, message: str) -> None:
        if message and message.strip():
            self.logger_func(message.strip())

    def flush(self) -> None:
        """Provided for file-like compatibility."""
        return None


@shared_task(
    bind=True,
    ignore_result=False,
)
def run_court_session_parser(
    self,
    court_ids: Optional[Sequence[int]] = None,
    parser_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Parse court session data from various Polish courts.

    This task processes court session data, creating court sessions and updating
    related records based on data scraped from Polish court websites.

    Args:
        court_ids: Optional sequence of Court IDs to process. If None, process all.
        parser_key: Optional parser key to filter courts. Must exist in registry.

    Returns:
        A dict containing execution summary and any per-court errors.
    """
    task_id = self.request.id
    normalized_court_ids = _normalize_court_ids(court_ids)

    logger.info(
        "Starting court session parser task id=%s parser_key=%s court_ids=%s",
        task_id,
        parser_key,
        normalized_court_ids,
    )

    result = _initialize_task_result(
        task_id=task_id,
        parser_key=parser_key,
        requested_court_ids=normalized_court_ids,
    )

    judgement_bot = _prepare_task_environment(parser_key)

    courts_list = _get_courts_to_process(
        court_ids=normalized_court_ids,
        parser_key=parser_key,
    )
    result["courts_total"] = len(courts_list)

    if not courts_list:
        return _complete_task_no_courts(result)

    logger.info(
        "Court session parser task id=%s will process %s court(s)",
        task_id,
        len(courts_list),
    )

    _process_all_courts(
        courts_list=courts_list, judgement_bot=judgement_bot, result=result
    )

    return _finalize_task_result(result)


def _normalize_court_ids(
    court_ids: Optional[Sequence[int]],
) -> Optional[List[int]]:
    """Normalize incoming court IDs to a plain list of ints or None."""
    if court_ids is None:
        return None
    return [int(court_id) for court_id in court_ids]


def _initialize_task_result(
    *,
    task_id: str,
    parser_key: Optional[str],
    requested_court_ids: Optional[List[int]],
) -> Dict[str, Any]:
    """Initialize the task result payload."""
    return {
        "status": "started",
        "task_id": task_id,
        "parser_key": parser_key,
        "requested_court_ids": requested_court_ids,
        "courts_total": 0,
        "courts_succeeded": 0,
        "courts_failed": 0,
        "total_sessions_created": 0,
        "errors": [],
    }


def _prepare_task_environment(parser_key: Optional[str]):
    """Validate inputs and prepare shared task resources."""
    if parser_key and parser_key not in get_parser_keys():
        raise ValueError(f"Invalid parser key: {parser_key}")

    User = get_user_model()
    judgement_bot, created = User.objects.get_or_create(
        username=JUDGEMENT_BOT_USERNAME,
        defaults={"email": JUDGEMENT_BOT_EMAIL},
    )

    if created:
        logger.info(
            "Created judgement bot user username=%s",
            JUDGEMENT_BOT_USERNAME,
        )

    return judgement_bot


def _get_courts_to_process(
    court_ids: Optional[Sequence[int]] = None,
    parser_key: Optional[str] = None,
) -> List[Court]:
    """
    Return the concrete list of courts to process.

    Courts are filtered by optional IDs and parser key, then restricted to those
    with an active parser according to `court.parser_status`.
    """
    qs = Court.objects.all()

    if court_ids:
        qs = qs.filter(id__in=court_ids)

    if parser_key:
        qs = qs.filter(parser_key=parser_key)

    return [court for court in qs if court.parser_status]


def _complete_task_no_courts(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return a completed result when no courts match the selection criteria."""
    logger.warning(
        "No courts found matching parser_key=%s court_ids=%s",
        result["parser_key"],
        result["requested_court_ids"],
    )
    result.update(
        {
            "status": "completed_no_courts",
            "message": "No courts found matching the specified criteria",
        }
    )
    return result


def _process_all_courts(
    *,
    courts_list: Sequence[Court],
    judgement_bot,
    result: Dict[str, Any],
) -> None:
    """Process all selected courts and accumulate summary metrics."""
    manager = Manager(
        bot=judgement_bot,
        stdout=LoggerWrapper(logger.info),
        stderr=LoggerWrapper(logger.error),
    )

    for court in courts_list:
        _process_single_court(court=court, manager=manager, result=result)


def _process_single_court(
    *,
    court: Court,
    manager: Manager,
    result: Dict[str, Any],
) -> None:
    """Process one court, updating success/failure counters and error details."""
    try:
        logger.info("Processing court id=%s name=%s", court.id, str(court))

        sessions_before = _count_court_sessions(court)
        manager.handle_court(court)
        sessions_after = _count_court_sessions(court)

        sessions_created = max(0, sessions_after - sessions_before)

        result["courts_succeeded"] += 1
        result["total_sessions_created"] += sessions_created

        logger.info(
            "Processed court id=%s name=%s sessions_created=%s",
            court.id,
            str(court),
            sessions_created,
        )

    except Exception as exc:
        result["courts_failed"] += 1

        error_msg = f"Failed to process court id={court.id} name={court}: {exc}"
        logger.exception(error_msg)

        result["errors"].append(
            {
                "court_id": court.id,
                "court_name": str(court),
                "error": str(exc),
            }
        )


def _count_court_sessions(court: Court) -> int:
    """Count court sessions linked to the given court."""
    return CourtSession.objects.filter(courtcase__court=court).count()


def _finalize_task_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize the task result status and log the final summary."""
    if result["courts_failed"] == 0:
        result["status"] = "completed_success"
        logger.info(
            "Court session parser completed successfully "
            "task_id=%s courts_total=%s courts_succeeded=%s "
            "sessions_created=%s",
            result["task_id"],
            result["courts_total"],
            result["courts_succeeded"],
            result["total_sessions_created"],
        )
    elif result["courts_succeeded"] > 0:
        result["status"] = "completed_partial"
        logger.warning(
            "Court session parser completed partially "
            "task_id=%s courts_total=%s courts_succeeded=%s courts_failed=%s",
            result["task_id"],
            result["courts_total"],
            result["courts_succeeded"],
            result["courts_failed"],
        )
    else:
        result["status"] = "failed_all_courts"
        logger.error(
            "Court session parser failed for all courts "
            "task_id=%s courts_total=%s courts_failed=%s",
            result["task_id"],
            result["courts_total"],
            result["courts_failed"],
        )

    return result
