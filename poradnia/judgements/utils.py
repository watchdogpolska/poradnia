import logging
import sys

from django.utils.encoding import force_str
from pytz import timezone

from poradnia.events.models import Event
from poradnia.judgements.models import CourtCase, CourtSession

logger = logging.getLogger(__name__)


class Manager:
    def __init__(self, bot, stdout=sys.stdout, stderr=sys.stderr):
        self.bot = bot
        self.stdout = stdout
        self.stderr = stderr

    def handle_court(self, court, parser=None):
        logger.info("=" * 6 + force_str(court))
        self.stdout.write("=" * 6 + force_str(court))
        signatures = {
            x.signature: x
            for x in CourtCase.objects.filter(court=court).with_events().all()
        }
        parser = parser or court.get_parser()
        for session_row in parser.get_session_rows():
            if session_row.signature not in signatures:
                continue
            self.handle_session_row(
                court, session_row, signatures[session_row.signature]
            )

    def handle_session_row(self, court, session_row, courtcase):
        dates = {
            courtsession.event.time.astimezone(timezone("UTC")).date(): courtsession
            for courtsession in courtcase.courtsession_set.all()
        }
        courtsession = dates.get(
            session_row.datetime.astimezone(timezone("UTC")).date(), None
        )

        if courtsession:
            self.handle_update_courtsession(courtsession, session_row)
        else:
            self.handle_new_courtsession(court, courtcase, session_row)

    def _cmp_event_sessionrow(self, event, session_row):
        event_time = event.time.astimezone(timezone("UTC"))
        session_row_time = session_row.datetime.astimezone(timezone("UTC"))
        return (
            event_time.hour == session_row_time.hour
            and event_time.minute == session_row_time.minute
            and event.text == session_row.description
        )

    def handle_update_courtsession(self, courtsession, session_row):
        if self._cmp_event_sessionrow(courtsession.event, session_row):
            logger.info(
                "Skip update court session {} to {}".format(
                    courtsession, session_row.datetime
                )
            )
            self.stdout.write(
                "Skip update court session {} to {}".format(
                    courtsession, session_row.datetime
                )
            )
            return

        logger.info(
            "Update court session {} to {} from {}".format(
                courtsession, session_row.datetime, courtsession.event.time
            )
        )
        self.stdout.write(
            "Update court session {} to {} from {}".format(
                courtsession, session_row.datetime, courtsession.event.time
            )
        )
        event = courtsession.event
        event.text = session_row.description
        event.time = session_row.datetime
        event.modified_by = self.bot
        event.save(update_fields=["text", "time", "modified_by"])
        event.send_notification(
            actor=self.bot,
            user_qs=event.case.get_users_with_perms().filter(is_staff=True),
            verb="created",
        )

    def handle_new_courtsession(self, court, courtcase, session_row):
        event = Event.objects.create(
            deadline=False,
            case=courtcase.case,
            time=session_row.datetime,
            created_by=self.bot,
            text=session_row.description,
        )
        event.send_notification(
            actor=self.bot,
            user_qs=event.case.get_users_with_perms().filter(is_staff=True),
            verb="created",
        )
        CourtSession.objects.create(
            courtcase=courtcase, parser_key=court.parser_key, event=event
        )
        logger.info(
            "Registered court session for {} at {}".format(
                session_row.signature, session_row.datetime
            )
        )
        self.stdout.write(
            "Registered court session for {} at {}".format(
                session_row.signature, session_row.datetime
            )
        )
