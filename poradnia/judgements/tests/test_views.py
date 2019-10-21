from atom.ext.guardian.tests import PermissionStatusMixin
from django.test import TestCase
from django.urls import reverse

from poradnia.cases.factories import CaseFactory
from poradnia.judgements.factories import CourtCaseFactory
from poradnia.users.factories import UserFactory


class CaseCourtCreateViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_add_record"]

    def setUp(self):
        super(CaseCourtCreateViewTestCase, self).setUp()
        self.user = UserFactory(username="john")
        self.case = CaseFactory()
        self.permission_object = self.case
        self.url = reverse("judgements:create", kwargs={"case_pk": str(self.case.pk)})


class CaseCourtUpdateViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_add_record"]

    def setUp(self):
        super(CaseCourtUpdateViewTestCase, self).setUp()
        self.user = UserFactory(username="john")
        self.court_case = CourtCaseFactory()
        self.permission_object = self.court_case.case
        self.url = reverse("judgements:update", kwargs={"pk": self.court_case.pk})


class CaseCourtDeleteViewTestCase(PermissionStatusMixin, TestCase):
    permission = ["cases.can_add_record"]

    def setUp(self):
        super(CaseCourtDeleteViewTestCase, self).setUp()
        self.user = UserFactory(username="john")
        self.court_case = CourtCaseFactory()
        self.permission_object = self.court_case.case
        self.url = reverse("judgements:delete", kwargs={"pk": self.court_case.pk})
