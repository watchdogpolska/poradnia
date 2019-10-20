import re
from datetime import datetime
from unittest import skipUnless

from dateutil.rrule import MONTHLY, WEEKLY
from django.core.management import call_command
from django.db import connection
from django.http.response import HttpResponse
from django.test import TestCase
from django.utils.module_loading import import_string
from io import StringIO
from django.utils.timezone import make_aware

from poradnia.cases.factories import CaseFactory
from poradnia.cases.models import Case
from poradnia.letters.factories import LetterFactory
from poradnia.letters.models import Letter
from poradnia.stats.factories import ItemFactory, ValueFactory
from poradnia.stats.mixins import PermissionStatusMixin
from poradnia.stats.utils import (DATE_FORMAT_MONTHLY, DATE_FORMAT_WEEKLY,
                                  GapFiller)
from poradnia.users.factories import UserFactory
from poradnia.users.models import User
from poradnia.stats.settings import STAT_METRICS

from django.urls import reverse


def polyfill_http_response_json():
    try:
        getattr(HttpResponse, 'json')
    except AttributeError:
        import json
        setattr(HttpResponse, 'json', lambda x: json.loads(x.content))


def purge_users(func):
    def func_wrapper(*args, **kwargs):
        User.objects.all().delete()
        func(*args, **kwargs)

    return func_wrapper


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseCreatedPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_created')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseCreatedRenderPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_created_render')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseCreatedApiPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_created_api')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseUnansweredPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_unanswered')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseUnansweredRenderPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_unanswered_render')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseUnansweredApiPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_unanswered_api')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseReactionPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_reaction')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseReactionRenderPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_reaction_render')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseReactionApiPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:case_reaction_api')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsLetterCreatedPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:letter_created')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsLetterCreatedRenderPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:letter_created_render')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsLetterCreatedApiPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:letter_created_api')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsUserRegisteredPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:user_registered')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsUserRegisteredRenderPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:user_registered_render')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsUserRegisteredApiPermissionTestCase(PermissionStatusMixin, TestCase):
    url = reverse('stats:user_registered_api')
    permissions = ["superuser"]


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsCaseCreatedApiTestCase(TestCase):
    def setUp(self):
        polyfill_http_response_json()
        self.url = reverse('stats:case_created_api')

    def _prepare_cases(self, db_data):
        for size, status, created_on in db_data:
            for obj in CaseFactory.create_batch(size=size, status=status):
                obj.created_on = make_aware(created_on)
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
                obj.letter_set.set(self._prepare_letters(letter_data, obj))
                obj.created_on = make_aware(created_on)
                obj.save()

    def _prepare_letters(self, letter_data, case):
        letters = []
        for accept, created_by, status in letter_data:
            obj = LetterFactory(created_by=created_by,
                                case=case,
                                status=status)
            obj.accept = make_aware(accept)
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
            last_send = make_aware(datetime(2015, 1, 2)) if sent else None
            for obj in CaseFactory.create_batch(size=size, last_send=last_send):
                obj.created_on = make_aware(created_on)
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


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsLetterCreatedApiTestCase(TestCase):
    def setUp(self):
        polyfill_http_response_json()
        self.url = reverse('stats:letter_created_api')
        self.staff_user = UserFactory(is_staff=True)
        self.non_staff_user = UserFactory(is_staff=False)

    def _prepare_letters(self, letter_data):
        letters = []
        for created_on, created_by in letter_data:
            obj = LetterFactory(created_by=created_by)
            obj.created_on = make_aware(created_on)
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
                self.non_staff_user
            ),
            (
                datetime(2015, 1, 2),
                self.staff_user
            ),
            (
                datetime(2015, 2, 3),
                self.non_staff_user
            ),
        ]

        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        self._prepare_letters(db_data)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2015-01", 'staff': 1, 'client': 1},
            {'date': "2015-02", 'staff': 0, 'client': 1},
        ]
        self.assertEqual(result, expected)


@skipUnless(connection.vendor == 'mysql', "MySQL specific tests")
class StatsUserRegisteredApiTestCase(TestCase):
    def setUp(self):
        polyfill_http_response_json()
        self.url = reverse('stats:user_registered_api')

    def _prepare_users(self, db_data):
        admin = None
        for created_on in db_data:
            if admin is None:
                obj = UserFactory(is_superuser=True)
                admin = obj
            else:
                obj = UserFactory()
            obj.created_on = make_aware(created_on) if created_on is not None else None
            obj.save()
        return admin

    @purge_users
    def test_basic(self):
        db_data = [
            datetime(2016, 11, 2),
            datetime(2016, 11, 2),
            datetime(2016, 11, 3),
            datetime(2016, 12, 2),
        ]

        user = self._prepare_users(db_data)
        self.client.force_login(user)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2016-11", 'count': 3},
            {'date': "2016-12", 'count': 4}
        ]
        self.assertEqual(result, expected)

    @purge_users
    def test_gap_after_init_date(self):
        db_data = [
            datetime(2017, 1, 2),
            datetime(2017, 3, 2)
        ]

        user = self._prepare_users(db_data)
        self.client.force_login(user)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2016-11", 'count': 0},
            {'date': "2016-12", 'count': 0},
            {'date': "2017-01", 'count': 1},
            {'date': "2017-02", 'count': 1},
            {'date': "2017-03", 'count': 2},
        ]
        self.assertEqual(result, expected)

    @purge_users
    def test_before_start_date(self):
        db_data = [
            datetime(2016, 1, 2),
        ]

        user = self._prepare_users(db_data)
        self.client.force_login(user)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2016-11", 'count': 1},
        ]
        self.assertEqual(result, expected)

    @purge_users
    def test_created_on_none(self):
        db_data = [
            None
        ]

        user = self._prepare_users(db_data)
        self.client.force_login(user)

        result = self.client.get(self.url).json()
        expected = [
            {'date': "2016-11", 'count': 1},
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


class ValueBrowseListViewTestCase(TestCase):
    def setUp(self):
        self.obj = ItemFactory()
        self.values = ValueFactory.create_batch(size=10, item=self.obj)
        self.url = reverse('stats:item_detail', kwargs={'key': self.obj.key,
                                                        'month': str(self.values[0].time.month),
                                                        'year': str(self.values[0].time.year),
                                                        })
        self.user = UserFactory(is_staff=True)
        self.client.login(username=self.user.username, password="pass")

    def test_valid_status_code_for_detail_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, "Invalid status code on '{}'".format(self.url))

    def test_output_contains_values(self):
        response = self.client.get(self.url)
        self.assertContains(response, self.values[0].value)

    def test_output_contains_description(self):
        response = self.client.get(self.url)
        self.assertContains(response, self.obj.description)


class CSVValueListViewTestCase(TestCase):
    def setUp(self):
        self.obj = ItemFactory()
        self.values = ValueFactory.create_batch(size=10, item=self.obj)
        self.url = reverse('stats:item_detail_csv', kwargs={'key': self.obj.key,
                                                            'month': self.values[0].time.month,
                                                            'year': self.values[0].time.year,
                                                            })
        self.user = UserFactory(is_staff=True)
        self.client.login(username=self.user.username, password="pass")

    def test_valid_status_code_for_detail_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, "Invalid status code on '{}'".format(self.url))

    def test_output_contains_values(self):
        response = self.client.get(self.url)
        self.assertContains(response, str(self.values[0].value))

    def test_output_contains_item_name(self):
        response = self.client.get(self.url)
        self.assertContains(response, self.obj.name)


class JSONValueListViewTestCase(TestCase):
    def setUp(self):
        self.obj = ItemFactory()
        self.values = ValueFactory.create_batch(size=10, item=self.obj)
        self.url = reverse('stats:item_detail_json', kwargs={'key': self.obj.key,
                                                             'month': self.values[0].time.month,
                                                             'year': self.values[0].time.year,
                                                             })
        self.user = UserFactory(is_staff=True)
        self.client.login(username=self.user.username, password="pass")

    def test_valid_status_code_for_detail_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, "Invalid status code on '{}'".format(self.url))

    def test_output_contains_values(self):
        response = self.client.get(self.url).json()
        self.assertTrue(any(entry['value'] == self.values[0].value for entry in response['values']))

    def test_output_contains_item_name(self):
        response = self.client.get(self.url).json()
        self.assertEqual(response['item']['name'], self.obj.name)


class TestManagementCommand(TestCase):
    def setUp(self):
        self.stdout = StringIO()

    def test_command_no_raises_exception(self):
        call_command('update_stats', stdout=self.stdout)

    def test_command_outputs(self):
        call_command('update_stats', stdout=self.stdout)
        output = self.stdout.getvalue()
        self.assertTrue(re.search("Registered .* new items", output))
        self.assertTrue(re.search("Registered .* values.", output))

    def test_metric_result_is_not_null(self):
        for key, import_path in STAT_METRICS.items():
            f = import_string(import_path)
            self.assertNotEqual(f(), None, "Metric '{}' result of '{}' cannot be null.".format(key, import_path))
