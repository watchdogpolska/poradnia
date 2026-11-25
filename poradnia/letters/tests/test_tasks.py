from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from poradnia.letters.factories import AttachmentFactory, LetterFactory
from poradnia.letters.models import Attachment
from poradnia.letters.tasks import (
    enqueue_attachment_text_content_updates,
    update_attachment_text_content_task,
    update_letter_attachments_text_content_task,
)

# close_old_connections() would drop the connection TestCase keeps inside
# its wrapping transaction, so it is stubbed out in every test here.
patch_models_conn = patch("poradnia.letters.models.close_old_connections")
patch_tasks_conn = patch("poradnia.letters.tasks.close_old_connections")


def _api_response(status_code=200, payload=None, text=""):
    response = MagicMock(status_code=status_code, text=text)
    response.json.return_value = payload or {}
    return response


@patch_models_conn
@patch("poradnia.letters.models.requests.post")
class AttachmentUpdateTextContentTestCase(TestCase):
    def setUp(self):
        self.attachment = AttachmentFactory()

    def test_success_stores_text_and_message(self, post, _conn):
        post.return_value = _api_response(
            payload={"text": "extracted text", "message": "Processed"}
        )
        self.assertTrue(self.attachment.update_text_content())
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.text_content, "extracted text")
        self.assertEqual(self.attachment.text_content_update_result, "Processed")

    @override_settings(FILE_TO_TEXT_URL="http://f2t.test/", FILE_TO_TEXT_TOKEN="tok")
    def test_sends_file_with_jwt_header(self, post, _conn):
        post.return_value = _api_response(payload={"text": "", "message": ""})
        self.attachment.update_text_content()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "http://f2t.test/")
        self.assertEqual(kwargs["headers"], {"Authorization": "JWT tok"})
        filename, content = kwargs["files"]["file"]
        self.assertEqual(filename, self.attachment.filename)
        self.assertTrue(content)

    def test_non_200_response_stores_error_and_returns_false(self, post, _conn):
        post.return_value = _api_response(status_code=500, text="boom")
        self.assertFalse(self.attachment.update_text_content())
        self.attachment.refresh_from_db()
        self.assertIsNone(self.attachment.text_content)
        self.assertEqual(
            self.attachment.text_content_update_result,
            "File to text API response: 500, content: boom",
        )

    def test_exception_stores_message_and_returns_false(self, post, _conn):
        post.side_effect = ConnectionError("unreachable")
        self.assertFalse(self.attachment.update_text_content())
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.text_content_update_result, "unreachable")


@patch_models_conn
class LetterUpdateAttachmentsTextContentTestCase(TestCase):
    def test_summary_counts_updated_and_failed(self, _conn):
        letter = LetterFactory()
        ok = AttachmentFactory(letter=letter)
        bad = AttachmentFactory(letter=letter)

        def fake_update(attachment):
            return attachment.pk == ok.pk

        with patch.object(
            Attachment, "update_text_content", autospec=True, side_effect=fake_update
        ):
            result = letter.update_attachments_text_content()

        self.assertEqual(result["letter_pk"], letter.pk)
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["attachments_total"], 2)
        self.assertEqual(result["attachments_updated"], 1)
        self.assertEqual(result["attachments_failed"], 1)
        self.assertEqual(result["updated_attachment_pks"], [ok.pk])
        self.assertEqual(result["failed_attachment_pks"], [bad.pk])

    def test_no_attachments(self, _conn):
        result = LetterFactory().update_attachments_text_content()
        self.assertEqual(result["attachments_total"], 0)
        self.assertEqual(result["attachments_updated"], 0)
        self.assertEqual(result["attachments_failed"], 0)

    def test_enqueue_runs_task_after_commit(self, _conn):
        letter = LetterFactory()
        with patch(
            "poradnia.letters.tasks.update_letter_attachments_text_content_task.delay"
        ) as delay:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                letter.enqueue_attachments_text_content_update()
            delay.assert_not_called()
            for callback in callbacks:
                callback()
        delay.assert_called_once_with(letter.pk)


@patch_tasks_conn
class UpdateLetterAttachmentsTextContentTaskTestCase(TestCase):
    def test_missing_letter_returns_not_found(self, _conn):
        result = update_letter_attachments_text_content_task(0)
        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["letter_pk"], 0)
        self.assertEqual(result["attachments_total"], 0)

    def test_delegates_to_letter(self, _conn):
        letter = LetterFactory()
        with patch(
            "poradnia.letters.models.Letter.update_attachments_text_content",
            return_value={"status": "done"},
        ) as update:
            result = update_letter_attachments_text_content_task(letter.pk)
        update.assert_called_once_with()
        self.assertEqual(result, {"status": "done"})


@patch_tasks_conn
class UpdateAttachmentTextContentTaskTestCase(TestCase):
    def test_missing_attachment_returns_not_found(self, _conn):
        result = update_attachment_text_content_task(0)
        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["attachment_pk"], 0)

    def _run(self, ok):
        attachment = AttachmentFactory()
        with patch(
            "poradnia.letters.models.Attachment.update_text_content", return_value=ok
        ):
            result = update_attachment_text_content_task(attachment.pk)
        return attachment, result

    def test_success(self, _conn):
        attachment, result = self._run(ok=True)
        self.assertEqual(
            result,
            {
                "attachment_pk": attachment.pk,
                "letter_pk": attachment.letter_id,
                "status": "ok",
            },
        )

    def test_failure(self, _conn):
        _, result = self._run(ok=False)
        self.assertEqual(result["status"], "failed")


LOCK_KEY = "enqueue_attachment_text_content_updates_lock"


@override_settings(
    CELERY_MONITOR_VHOST="/",
    CELERY_ATTACHMENT_TEXT_CONTENT_QUEUE="text_queue",
    CELERY_QUEUE_READY_WARN=3,
)
@patch("poradnia.letters.tasks.update_attachment_text_content_task.apply_async")
@patch("poradnia.celery_monitor.tasks.rabbit_api")
class EnqueueAttachmentTextContentUpdatesTestCase(TestCase):
    def setUp(self):
        cache.delete(LOCK_KEY)

    def tearDown(self):
        cache.delete(LOCK_KEY)

    def _queue(self, messages_ready=0, name="text_queue"):
        return [{"name": name, "messages_ready": messages_ready}]

    def test_locked_returns_early(self, rabbit_api, apply_async):
        cache.add(LOCK_KEY, "1")
        result = enqueue_attachment_text_content_updates()
        self.assertEqual(result["status"], "locked")
        rabbit_api.assert_not_called()
        apply_async.assert_not_called()
        # The lock belongs to the other run, so it must be left in place.
        self.assertEqual(cache.get(LOCK_KEY), "1")

    def test_queue_not_found(self, rabbit_api, apply_async):
        rabbit_api.return_value = self._queue(name="other")
        result = enqueue_attachment_text_content_updates()
        self.assertEqual(result["status"], "queue_not_found")
        self.assertEqual(result["queue"], "text_queue")
        rabbit_api.assert_called_once_with("api/queues//")
        apply_async.assert_not_called()
        self.assertIsNone(cache.get(LOCK_KEY))

    def test_queue_full_enough(self, rabbit_api, apply_async):
        AttachmentFactory()
        rabbit_api.return_value = self._queue(messages_ready=3)
        result = enqueue_attachment_text_content_updates()
        self.assertEqual(result["status"], "queue_full_enough")
        self.assertEqual(result["max_batch_size"], 3)
        apply_async.assert_not_called()

    def test_nothing_to_enqueue(self, rabbit_api, apply_async):
        AttachmentFactory(text_content_update_result="Processed")
        AttachmentFactory(text_content_update_result="File type not supported")
        rabbit_api.return_value = self._queue()
        result = enqueue_attachment_text_content_updates()
        self.assertEqual(result["status"], "nothing_to_enqueue")
        apply_async.assert_not_called()

    def test_enqueues_pending_newest_first_up_to_free_slots(
        self, rabbit_api, apply_async
    ):
        AttachmentFactory(text_content_update_result="Processed")
        oldest = AttachmentFactory(text_content_update_result=None)
        middle = AttachmentFactory(text_content_update_result="")
        newest = AttachmentFactory(text_content_update_result="API error")
        rabbit_api.return_value = self._queue(messages_ready=1)

        result = enqueue_attachment_text_content_updates()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["free_slots"], 2)
        self.assertEqual(result["attachment_ids"], [newest.pk, middle.pk])
        self.assertNotIn(oldest.pk, result["attachment_ids"])
        self.assertEqual(apply_async.call_count, 2)
        _, kwargs = apply_async.call_args
        self.assertEqual(kwargs["queue"], "text_queue")
        self.assertEqual(kwargs["kwargs"]["queue_name"], "text_queue")
        self.assertIn("enqueued_at_iso", kwargs["kwargs"])
        self.assertIsNone(cache.get(LOCK_KEY))

    def test_explicit_max_batch_size_overrides_setting(self, rabbit_api, apply_async):
        AttachmentFactory()
        rabbit_api.return_value = self._queue(messages_ready=5)
        result = enqueue_attachment_text_content_updates(max_batch_size=10)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["free_slots"], 5)

    def test_error_is_reraised_and_lock_released(self, rabbit_api, apply_async):
        rabbit_api.side_effect = RuntimeError("rabbit down")
        with self.assertRaises(RuntimeError):
            enqueue_attachment_text_content_updates()
        self.assertIsNone(cache.get(LOCK_KEY))
