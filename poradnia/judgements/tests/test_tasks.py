"""
Tests for judgements Celery tasks.
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from poradnia.judgements.factories import CourtFactory
from poradnia.judgements.models import Court
from poradnia.judgements.settings import JUDGEMENT_BOT_USERNAME
from poradnia.judgements.tasks import _get_courts_queryset, run_court_session_parser


class RunCourtSessionParserTaskTestCase(TestCase):
    """Test the run_court_session_parser Celery task."""

    def setUp(self):
        """Set up test data."""
        self.court = CourtFactory(name="TestCourt", parser_key="WSA_Warszawa")
        # Mock the parser_status property to return True
        Court.parser_status = property(lambda self: True)

    @patch("poradnia.judgements.tasks.Manager")
    def test_task_execution_success(self, mock_manager_class):
        """Test successful task execution."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Execute task
        result = run_court_session_parser()

        # Assertions
        self.assertEqual(result["status"], "completed_success")
        self.assertEqual(result["courts_processed"], 1)
        self.assertEqual(result["courts_failed"], 0)

        # Verify manager was called
        mock_manager.handle_court.assert_called_once_with(self.court)

    @patch("poradnia.judgements.tasks.Manager")
    def test_task_execution_with_court_filter(self, mock_manager_class):
        """Test task execution with court ID filter."""
        # Create additional courts
        CourtFactory(name="OtherCourt")
        Court.parser_status = property(lambda self: True)

        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Execute task with court filter
        result = run_court_session_parser(court_ids=[self.court.id])

        # Should only process the filtered court
        self.assertEqual(result["courts_processed"], 1)
        mock_manager.handle_court.assert_called_once_with(self.court)

    @patch("poradnia.judgements.tasks.Manager")
    def test_task_execution_with_parser_filter(self, mock_manager_class):
        """Test task execution with parser key filter."""
        # Create court with different parser
        CourtFactory(name="OtherCourt", parser_key="WSA_Gliwice")
        Court.parser_status = property(lambda self: True)

        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Execute task with parser filter
        result = run_court_session_parser(parser_key="WSA_Warszawa")

        # Should only process courts with matching parser
        self.assertEqual(result["courts_processed"], 1)
        mock_manager.handle_court.assert_called_once_with(self.court)

    def test_task_execution_no_courts(self):
        """Test task execution when no courts match criteria."""
        # Delete the court or make it inactive
        self.court.delete()

        result = run_court_session_parser()

        self.assertEqual(result["status"], "completed_no_courts")
        self.assertEqual(result["courts_processed"], 0)

    @patch("poradnia.judgements.tasks.Manager")
    def test_task_execution_partial_failure(self, mock_manager_class):
        """Test task execution with some courts failing."""
        # Create multiple courts
        court2 = CourtFactory(name="Court2", parser_key="WSA_Warszawa")
        Court.parser_status = property(lambda self: True)

        # Setup mock to fail for one court
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        def side_effect(court):
            if court == court2:
                raise Exception("Parser error")

        mock_manager.handle_court.side_effect = side_effect

        # Execute task
        result = run_court_session_parser()

        # Should have partial success
        self.assertEqual(result["status"], "completed_partial")
        self.assertEqual(result["courts_processed"], 1)
        self.assertEqual(result["courts_failed"], 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["court_id"], court2.id)

    def test_invalid_parser_key(self):
        """Test task execution with invalid parser key."""
        # Should raise ValueError for invalid parser key
        with self.assertRaises(ValueError):
            run_court_session_parser(parser_key="invalid_parser")

    def test_judgement_bot_creation(self):
        """Test that judgement bot user is created if it doesn't exist."""
        # Ensure bot user doesn't exist
        User = get_user_model()
        User.objects.filter(username=JUDGEMENT_BOT_USERNAME).delete()

        with patch("poradnia.judgements.tasks.Manager"):
            run_court_session_parser()

        # Verify bot user was created
        bot_user = User.objects.get(username=JUDGEMENT_BOT_USERNAME)
        self.assertIsNotNone(bot_user)


class GetCourtsQuerysetTestCase(TestCase):
    """Test the _get_courts_queryset helper function."""

    def setUp(self):
        """Set up test data."""
        self.court1 = CourtFactory(name="Court1", parser_key="WSA_Warszawa")
        self.court2 = CourtFactory(name="Court2", parser_key="WSA_Gliwice")
        # Mock parser_status to return True
        Court.parser_status = property(lambda self: True)

    def test_no_filters(self):
        """Test getting all courts with no filters."""
        courts = list(_get_courts_queryset())
        self.assertEqual(len(courts), 2)
        self.assertIn(self.court1, courts)
        self.assertIn(self.court2, courts)

    def test_court_id_filter(self):
        """Test filtering by court IDs."""
        courts = list(_get_courts_queryset(court_ids=[self.court1.id]))
        self.assertEqual(len(courts), 1)
        self.assertEqual(courts[0], self.court1)

    def test_parser_key_filter(self):
        """Test filtering by parser key."""
        courts = list(_get_courts_queryset(parser_key="WSA_Warszawa"))
        self.assertEqual(len(courts), 1)
        self.assertEqual(courts[0], self.court1)

    def test_combined_filters(self):
        """Test combining court ID and parser key filters."""
        courts = list(
            _get_courts_queryset(court_ids=[self.court1.id], parser_key="WSA_Warszawa")
        )
        self.assertEqual(len(courts), 1)
        self.assertEqual(courts[0], self.court1)

        # Test with mismatched filters
        courts = list(
            _get_courts_queryset(court_ids=[self.court1.id], parser_key="WSA_Gliwice")
        )
        self.assertEqual(len(courts), 0)

    def test_inactive_parser_exclusion(self):
        """Test that courts with inactive parsers are excluded."""

        # Mock parser_status to return False for court2
        def parser_status_side_effect(court_instance):
            return court_instance.id == self.court1.id

        with patch.object(
            Court,
            "parser_status",
            new_callable=lambda: property(parser_status_side_effect),
        ):
            courts = list(_get_courts_queryset())
            self.assertEqual(len(courts), 1)
            self.assertEqual(courts[0], self.court1)
