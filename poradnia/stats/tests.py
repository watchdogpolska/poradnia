from datetime import datetime
from unittest import skipUnless

from dateutil.rrule import MONTHLY, WEEKLY, DAILY
from django.core.urlresolvers import reverse
from django.db import connection
from django.http.response import HttpResponse
from django.test import TestCase

from cases.factories import CaseFactory
from cases.models import Case
from letters.factories import LetterFactory
from letters.models import Letter
from users.factories import UserFactory
from stats.utils import GapFiller, DATE_FORMAT_MONTHLY, DATE_FORMAT_WEEKLY

def polyfill_http_response_json():
    try:
        getattr(HttpResponse, 'json')
    except AttributeError:
        setattr(HttpResponse, 'json', lambda x: json.loads(x.content))


class StatsCaseCreatedPermissionTestCase(TestCase):
    def setUp(self):
        self.api_url = reverse('stats:case_created_api')
        self.render_url = reverse('stats:case_created_render')
        self.main_url = reverse('stats:case_created')

    def test_permission_forbidden(self):
        user = UserFactory(is_superuser=False)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    def test_permission_not_logged_in(self):
        user = UserFactory(is_superuser=False)
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)

    @skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
    def test_permission_superuser(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


class StatsCaseUnansweredPermissionTestCase(TestCase):
    def setUp(self):
        self.api_url = reverse('stats:case_unanswered_api')
        self.render_url = reverse('stats:case_unanswered_render')
        self.main_url = reverse('stats:case_unanswered')

    def test_permission_not_logged_in(self):
        user = UserFactory(is_superuser=False)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    def test_permission_not_logged_in(self):
        user = UserFactory(is_superuser=False)
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)

    @skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
    def test_permission_superuser(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


class StatsCaseReactionPermissionTestCase(TestCase):
    def setUp(self):
        self.api_url = reverse('stats:case_reaction_api')
        self.render_url = reverse('stats:case_reaction_render')
        self.main_url = reverse('stats:case_reaction')

    def test_permission_not_logged_in(self):
        user = UserFactory(is_superuser=False)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    def test_permission_not_logged_in(self):
        user = UserFactory(is_superuser=False)
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)

    def test_permission_superuser(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseCreatedApiTestCase(TestCase):
    def setUp(self):
        polyfill_http_response_json()
        self.url = reverse('stats:case_created_api')

    def _prepare_cases(self, db_data):
        for size, status, created_on in db_data:
            for obj in CaseFactory.create_batch(size=size, status=status):
                obj.created_on = created_on
                obj.save()

    def test_no_cases(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')

        result = self.client.get(self.url).json()
        expected = []
        self.assertEqual(result, expected)

    def test_basic(self):
        db_data = [
            (1, Case.STATUS.free, datetime(2015, 1, 2)),
            (2, Case.STATUS.assigned, datetime(2015, 1, 2)),
            (3, Case.STATUS.closed, datetime(2015, 1, 2)),
            (2, Case.STATUS.free, datetime(2015, 2, 2)),
            (1, Case.STATUS.assigned, datetime(2015, 2, 2))
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)
        result = self.client.get(self.url).json()
        expected = [
            {'date': "2015-01", 'open': 1, 'assigned': 2, 'closed': 3},
            {'date': "2015-02", 'open': 2, 'assigned': 1, 'closed': 0}
        ]
        self.assertEqual(result, expected)

    def test_gap_by_month(self):
        db_data = [
            (1, Case.STATUS.free, datetime(2015, 1, 2)),
            (2, Case.STATUS.assigned, datetime(2015, 1, 2)),
            (3, Case.STATUS.closed, datetime(2015, 1, 2)),
            (2, Case.STATUS.free, datetime(2015, 3, 2)),
            (1, Case.STATUS.assigned, datetime(2015, 3, 2))
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2015-01", 'open': 1, 'assigned': 2, 'closed': 3},
            {'date': "2015-02", 'open': 0, 'assigned': 0, 'closed': 0},
            {'date': "2015-03", 'open': 2, 'assigned': 1, 'closed': 0}
        ]
        self.assertEqual(result, expected)


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseReactionApiTestCase(TestCase):
    def setUp(self):
        polyfill_http_response_json()
        self.url = reverse('stats:case_reaction_api')
        self.staff_user = UserFactory(is_staff=True)
        self.non_staff_user = UserFactory(is_staff=False)

    def _prepare_cases(self, db_data):
        for created_on, letter_data in db_data:
            for obj in CaseFactory.create_batch(size=1):
                obj.letter_set = self._prepare_letters(letter_data, obj)
                obj.created_on = created_on
                obj.save()

    def _prepare_letters(self, letter_data, case):
        letters = []
        for accept, created_by, status in letter_data:
            obj = LetterFactory.create_batch(size=1, created_by=created_by, case=case, status=status)[0]
            obj.accept = accept
            obj.save()
            letters.append(obj)
        return letters

    def test_no_cases(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')

        result = self.client.get(self.url).json()
        expected = []
        self.assertEqual(result, expected)

    def test_basic(self):
        db_data = [
            (
                datetime(2015, 1, 2),
                [(datetime(2015, 4, 2), self.staff_user, Letter.STATUS.done)]
            ),
            (
                datetime(2015, 2, 3),
                [(datetime(2015, 4, 3), self.staff_user, Letter.STATUS.done)]
            ),
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2015-01", 'reaction_time': 89},
            {'date': "2015-02", 'reaction_time': 58}
        ]
        self.assertEqual(result, expected)

    def test_letter_from_non_staff(self):
        db_data = [
            (
                datetime(2015, 1, 2),
                [(datetime(2015, 4, 2), self.non_staff_user, Letter.STATUS.done)]
            )
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)

        result = self.client.get(self.url).json()
        expected = []
        self.assertEqual(result, expected)

    def test_many_letters(self):
        db_data = [
            (
                datetime(2015, 1, 2),
                [
                    (datetime(2015, 3, 2), self.staff_user, Letter.STATUS.done),
                    (datetime(2015, 4, 2), self.staff_user, Letter.STATUS.done)
                ]
            )
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2015-01", 'reaction_time': 59}
        ]
        self.assertEqual(result, expected)

    def test_not_done(self):
        db_data = [
            (
                datetime(2015, 1, 2),
                [(datetime(2015, 3, 2), self.staff_user, Letter.STATUS.staff)]
            )
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)

        result = self.client.get(self.url).json()
        expected = []
        self.assertEqual(result, expected)

    def test_gap_by_month(self):
        db_data = [
            (
                datetime(2015, 1, 2),
                [(datetime(2015, 4, 2), self.staff_user, Letter.STATUS.done)]
            ),
            (
                datetime(2015, 3, 3),
                [(datetime(2015, 3, 4), self.staff_user, Letter.STATUS.done)]
            )
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2015-01", 'reaction_time': 89},
            {'date': "2015-02", 'reaction_time': 0},
            {'date': "2015-03", 'reaction_time': 1}
        ]
        self.assertEqual(result, expected)


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseUnansweredApiTestCase(TestCase):
    def setUp(self):
        polyfill_http_response_json()
        self.url = reverse('stats:case_unanswered_api')

    def _prepare_cases(self, db_data):
        for size, sent, created_on in db_data:
            last_send = datetime(2015, 1, 2) if sent else None
            for obj in CaseFactory.create_batch(size=size, last_send=last_send):
                obj.created_on = created_on
                obj.save()

    def test_no_cases(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')

        result = self.client.get(self.url).json()
        expected = []
        self.assertEqual(result, expected)

    def test_basic(self):
        db_data = [
            (1, False, datetime(2015, 1, 2)),
            (1, True, datetime(2015, 1, 2)),
            (2, False, datetime(2015, 2, 2))
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2015-01", 'count': 1},
            {'date': "2015-02", 'count': 2}
        ]
        self.assertEqual(result, expected)

    def test_gap_by_month(self):
        db_data = [
            (1, False, datetime(2015, 1, 2)),
            (2, False, datetime(2015, 3, 2))
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_cases(db_data)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2015-01", 'count': 1},
            {'date': "2015-02", 'count': 0},
            {'date': "2015-03", 'count': 2}
        ]
        self.assertEqual(result, expected)


class GapFillerTestCase(TestCase):
    def setUp(self):
        self.date_key = 'date'

    def test_single_month_gap(self):
        qs = [
            {'date': "2015-01", 'param': 1},
            {'date': "2015-03", 'param': 3}
        ]

        gf = GapFiller(qs, MONTHLY, self.date_key, DATE_FORMAT_MONTHLY)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01", 'param': 1},
            {'date': "2015-02", 'param': 0},
            {'date': "2015-03", 'param': 3}
        ]
        self.assertEqual(result, expected)

    def test_single_week_gap(self):
        qs = [
            {'date': "2015-01", 'param': 1},
            {'date': "2015-03", 'param': 3}
        ]

        gf = GapFiller(qs, WEEKLY, self.date_key, DATE_FORMAT_WEEKLY)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01", 'param': 1},
            {'date': "2015-02", 'param': 0},
            {'date': "2015-03", 'param': 3}
        ]
        self.assertEqual(result, expected)

    def test_multiple_month_gaps(self):
        qs = [
            {'date': "2015-01", 'param': 1},
            {'date': "2015-03", 'param': 3},
            {'date': "2015-07", 'param': 7}
        ]

        gf = GapFiller(qs, MONTHLY, self.date_key, DATE_FORMAT_MONTHLY)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01", 'param': 1},
            {'date': "2015-02", 'param': 0},
            {'date': "2015-03", 'param': 3},
            {'date': "2015-04", 'param': 0},
            {'date': "2015-05", 'param': 0},
            {'date': "2015-06", 'param': 0},
            {'date': "2015-07", 'param': 7}
        ]
        self.assertEqual(result, expected)

    def test_no_gaps(self):
        qs = [
            {'date': "2015-01", 'param': 1},
            {'date': "2015-02", 'param': 0},
            {'date': "2015-03", 'param': 3}
        ]

        gf = GapFiller(qs, WEEKLY, self.date_key, DATE_FORMAT_WEEKLY)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01", 'param': 1},
            {'date': "2015-02", 'param': 0},
            {'date': "2015-03", 'param': 3}
        ]
        self.assertEqual(result, expected)

    def test_empty_qs(self):
        qs = []
        gf = GapFiller(qs, WEEKLY, self.date_key, DATE_FORMAT_WEEKLY)

        result = gf.fill_gaps()
        expected = []
        self.assertEqual(result, expected)

    def test_multiple_params(self):
        qs = [
            {'date': "2015-01", 'a': 1, 'b': 1},
            {'date': "2015-03", 'a': 3, 'b': 4}
        ]

        gf = GapFiller(qs, MONTHLY, self.date_key, DATE_FORMAT_MONTHLY)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01", 'a': 1, 'b': 1},
            {'date': "2015-02", 'a': 0, 'b': 0},
            {'date': "2015-03", 'a': 3, 'b': 4}
        ]
        self.assertEqual(result, expected)

    def test_one_element(self):
        qs = [
            {'date': "2015-01", 'param': 1}
        ]

        gf = GapFiller(qs, MONTHLY, self.date_key, DATE_FORMAT_MONTHLY)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01", 'param': 1}
        ]
        self.assertEqual(result, expected)
