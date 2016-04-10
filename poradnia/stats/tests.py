from unittest import skip
from datetime import datetime

from dateutil.rrule import MONTHLY, WEEKLY, DAILY
from django.test import TestCase
from django.core.urlresolvers import reverse
from users.factories import UserFactory
from stats.utils import GapFiller, DATE_FORMAT

class StatsCaseCreatedTestCase(TestCase):
    def setUp(self):
        self.api_url = reverse('stats:case_created_api')
        self.render_url = reverse('stats:case_created_render')
        self.main_url = reverse('stats:case_created')

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

    @skip("SQLite Error")
    def test_permission_superuser(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


class StatsCaseUnansweredTestCase(TestCase):
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

    @skip("SQLite Error")
    def test_permission_superuser(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


class StatsCaseReactionTestCase(TestCase):
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

    # @skip("SQLite Error")
    def test_permission_superuser(self):
        user = UserFactory(is_superuser=True)
        self.client.login(username=user.username, password='pass')
        for url in[self.api_url, self.render_url, self.main_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


class FillGapsTestCase(TestCase):
    def setUp(self):
        self.date_key = 'date'
        self.date_format = DATE_FORMAT

    def test_single_month_gap(self):
        qs = [
            {'date': datetime(2015, 1, 1), 'param': 1},
            {'date': datetime(2015, 3, 1), 'param': 3}
        ]

        gf = GapFiller(qs, MONTHLY, self.date_key, self.date_format)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01-01", 'param': 1},
            {'date': "2015-02-01", 'param': 0},
            {'date': "2015-03-01", 'param': 3}
        ]
        self.assertEqual(result, expected)

    def test_single_week_gap(self):
        qs = [
            {'date': datetime(2015, 1, 5), 'param': 1},
            {'date': datetime(2015, 1, 19), 'param': 3}
        ]

        gf = GapFiller(qs, WEEKLY, self.date_key, self.date_format)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01-05", 'param': 1},
            {'date': "2015-01-12", 'param': 0},
            {'date': "2015-01-19", 'param': 3}
        ]
        self.assertEqual(result, expected)

    def test_single_day_gap(self):
        qs = [
            {'date': datetime(2015, 1, 1), 'param': 1},
            {'date': datetime(2015, 1, 3), 'param': 3}
        ]

        gf = GapFiller(qs, DAILY, self.date_key, self.date_format)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01-01", 'param': 1},
            {'date': "2015-01-02", 'param': 0},
            {'date': "2015-01-03", 'param': 3}
        ]
        self.assertEqual(result, expected)

    def test_multiple_month_gaps(self):
        qs = [
            {'date': datetime(2015, 1, 1), 'param': 1},
            {'date': datetime(2015, 3, 1), 'param': 3},
            {'date': datetime(2015, 7, 1), 'param': 7}
        ]

        gf = GapFiller(qs, MONTHLY, self.date_key, self.date_format)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01-01", 'param': 1},
            {'date': "2015-02-01", 'param': 0},
            {'date': "2015-03-01", 'param': 3},
            {'date': "2015-04-01", 'param': 0},
            {'date': "2015-05-01", 'param': 0},
            {'date': "2015-06-01", 'param': 0},
            {'date': "2015-07-01", 'param': 7}
        ]
        self.assertEqual(result, expected)

    def test_no_gaps(self):
        qs = [
            {'date': datetime(2015, 1, 1), 'param': 1},
            {'date': datetime(2015, 1, 2), 'param': 0},
            {'date': datetime(2015, 1, 3), 'param': 3}
        ]

        gf = GapFiller(qs, WEEKLY, self.date_key, self.date_format)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01-01", 'param': 1},
            {'date': "2015-01-02", 'param': 0},
            {'date': "2015-01-03", 'param': 3}
        ]
        self.assertEqual(result, expected)

    def test_empty_qs(self):
        qs = []
        gf = GapFiller(qs, WEEKLY, self.date_key, self.date_format)

        result = gf.fill_gaps()
        expected = []
        self.assertEqual(result, expected)

    def test_multiple_params(self):
        qs = [
            {'date': datetime(2015, 1, 1), 'a': 1, 'b': 1},
            {'date': datetime(2015, 3, 1), 'a': 3, 'b': 4}
        ]

        gf = GapFiller(qs, MONTHLY, self.date_key, self.date_format)

        result = gf.fill_gaps()
        expected = [
            {'date': "2015-01-01", 'a': 1, 'b': 1},
            {'date': "2015-02-01", 'a': 0, 'b': 0},
            {'date': "2015-03-01", 'a': 3, 'b': 4}
        ]
        self.assertEqual(result, expected)
