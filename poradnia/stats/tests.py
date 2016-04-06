from unittest import skip

from django.test import TestCase
from django.core.urlresolvers import reverse
from users.factories import UserFactory

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
