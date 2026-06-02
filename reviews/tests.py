from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import ContractorProfile, User
from projects.models import Project, ProjectCategory

from .models import Review


class ReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat = ProjectCategory.objects.first()
        cls.client_user = User.objects.create_user("cli", password="pw", role=User.Role.CLIENT)
        cls.contractor = User.objects.create_user("ctr", password="pw", role=User.Role.CONTRACTOR)
        cls.profile = ContractorProfile.objects.create(
            user=cls.contractor, company_name="C", verification_status="VERIFIED"
        )

    def _project(self, status, confirmed):
        return Project.objects.create(
            client=self.client_user, category=self.cat, title="P", description="d",
            location="L", budget_min=1, budget_max=2, deadline="2026-12-31",
            awarded_contractor=self.contractor, status=status, completion_confirmed=confirmed,
        )

    def _review(self, project, rating="4"):
        self.client.login(username="cli", password="pw")
        return self.client.post(
            reverse("review_create", args=[project.pk]),
            {"rating": rating, "comment": "ok"},
        )

    def test_cannot_review_before_confirmation(self):
        project = self._project(Project.Status.IN_PROGRESS, False)
        self._review(project)
        self.assertFalse(Review.objects.filter(project=project).exists())

    def test_review_after_confirmation_updates_rating(self):
        project = self._project(Project.Status.COMPLETED, True)
        self._review(project, "4")
        self.assertTrue(Review.objects.filter(project=project).exists())
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.rating_average, Decimal("4.00"))

    def test_rating_average_is_mean_of_reviews(self):
        p1 = self._project(Project.Status.COMPLETED, True)
        self._review(p1, "4")
        p2 = self._project(Project.Status.COMPLETED, True)
        self._review(p2, "2")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.rating_average, Decimal("3.00"))

    def test_duplicate_review_prevented(self):
        project = self._project(Project.Status.COMPLETED, True)
        self._review(project, "4")
        self._review(project, "1")
        self.assertEqual(Review.objects.filter(project=project).count(), 1)

    def test_out_of_range_rating_rejected(self):
        project = self._project(Project.Status.COMPLETED, True)
        self._review(project, "9")
        self.assertFalse(Review.objects.filter(project=project).exists())
