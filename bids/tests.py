from django.test import TestCase
from django.urls import reverse

from accounts.models import ContractorProfile, User
from projects.models import Project, ProjectCategory

from .models import Bid


class BiddingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cat = ProjectCategory.objects.first()
        cls.client_user = User.objects.create_user("cli", password="pw", role=User.Role.CLIENT)
        cls.verified = User.objects.create_user("ver", password="pw", role=User.Role.CONTRACTOR)
        cls.unverified = User.objects.create_user("unv", password="pw", role=User.Role.CONTRACTOR)
        ContractorProfile.objects.create(user=cls.verified, company_name="V", verification_status="VERIFIED")
        ContractorProfile.objects.create(user=cls.unverified, company_name="U", verification_status="PENDING")
        cls.project = Project.objects.create(client=cls.client_user, category=cat, title="P",
            description="d", location="L", budget_min=1, budget_max=2, deadline="2026-12-31")

    def _bid(self, user, amount="150"):
        self.client.login(username=user.username, password="pw")
        return self.client.post(
            reverse("bid_create", args=[self.project.pk]),
            {"bid_amount": amount, "proposed_timeline_days": "10"},
        )

    def test_verified_contractor_can_bid(self):
        self._bid(self.verified)
        self.assertTrue(Bid.objects.filter(contractor=self.verified, project=self.project).exists())

    def test_unverified_contractor_cannot_bid(self):
        self._bid(self.unverified)
        self.assertFalse(Bid.objects.filter(contractor=self.unverified).exists())

    def test_duplicate_bid_prevented(self):
        self._bid(self.verified, "150")
        self._bid(self.verified, "160")
        self.assertEqual(Bid.objects.filter(contractor=self.verified, project=self.project).count(), 1)


class AwardingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cat = ProjectCategory.objects.first()
        cls.client_user = User.objects.create_user("cli", password="pw", role=User.Role.CLIENT)
        cls.c1 = User.objects.create_user("c1", password="pw", role=User.Role.CONTRACTOR)
        cls.c2 = User.objects.create_user("c2", password="pw", role=User.Role.CONTRACTOR)
        cls.project = Project.objects.create(client=cls.client_user, category=cat, title="P",
            description="d", location="L", budget_min=1, budget_max=2, deadline="2026-12-31")
        cls.bid1 = Bid.objects.create(project=cls.project, contractor=cls.c1, bid_amount=100, proposed_timeline_days=5)
        cls.bid2 = Bid.objects.create(project=cls.project, contractor=cls.c2, bid_amount=200, proposed_timeline_days=8)

    def test_award_accepts_one_rejects_rest(self):
        self.client.login(username="cli", password="pw")
        self.client.post(reverse("award_bid", args=[self.bid1.pk]))
        self.project.refresh_from_db()
        self.bid1.refresh_from_db()
        self.bid2.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.IN_PROGRESS)
        self.assertEqual(self.project.awarded_contractor, self.c1)
        self.assertEqual(self.bid1.status, Bid.Status.ACCEPTED)
        self.assertEqual(self.bid2.status, Bid.Status.REJECTED)

    def test_non_owner_cannot_award(self):
        other = User.objects.create_user("other", password="pw", role=User.Role.CLIENT)
        self.client.login(username="other", password="pw")
        self.client.post(reverse("award_bid", args=[self.bid1.pk]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.OPEN)
