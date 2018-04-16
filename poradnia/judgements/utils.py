import sys

from django.utils.encoding import force_text

from poradnia.events.models import Event
from poradnia.judgements.models import CourtCase, CourtSession


class Manager(object):
    def __init__(self, bot, stdout=sys.stdout, stderr=sys.stderr):
        self.bot = bot
        self.stdout = stdout
        self.stderr = stderr

    def handle_court(self, court, parser):
        self.stdout.write("=" * 6 + force_text(court))
        signatures = {x.signature: x for x in CourtCase.objects.filter(court=court).with_events().all()}
        parser = parser or court.get_parser()
        for session_row in parser.get_session_rows():
            if session_row.signature not in signatures:
                continue
            self.handle_session_row(court, session_row, signatures[session_row.signature])

    def handle_session_row(self, court, session_row, courtcase):
        dates = {courtsession.event.time.date(): courtsession
                 for courtsession in courtcase.courtsession_set.all()}
        courtsession = dates.get(session_row.datetime.date(), None)

        if courtsession:
            self.handle_update_courtsession(courtsession, session_row)
        else:
            self.handle_new_courtsession(court, courtcase, session_row)

    def _cmp_event_sessionrow(self, event, session_row):
        return event.time.hour == session_row.datetime.hour and \
               event.time.minute == session_row.datetime.minute and \
               event.text == session_row.description

    def handle_update_courtsession(self, courtsession, session_row):
        if self._cmp_event_sessionrow(courtsession.event, session_row):
            self.stdout.write("Skip update court session {} to {}".format(courtsession, session_row.datetime))
            return
        self.stdout.write("Update court session {} to {} from {}".format(courtsession,
                                                                         session_row.datetime,
                                                                         courtsession.event.time))
        event = courtsession.event
        event.text = session_row.description
        event.time = session_row.datetime
        event.modified_by = self.bot
        event.save(update_fields=['text', 'time', 'modified_by'])

    def handle_new_courtsession(self, court, courtcase, session_row):
        event = Event.objects.create(deadline=False,
                                     case=courtcase.case,
                                     time=session_row.datetime,
                                     created_by=self.bot,
                                     text=session_row.description)
        CourtSession.objects.create(courtcase=courtcase,
                                    parser_key=court.parser_key,
                                    event=event)
        self.stdout.write("Registered court session for {} at {}".format(session_row.signature, session_row.datetime))
