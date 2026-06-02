from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Project, ProjectCategory


class ProjectPostingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ProjectCategory.objects.first()
        cls.client_user = User.objects.create_user("cli", password="pw", role=User.Role.CLIENT)
        cls.contractor = User.objects.create_user("ctr", password="pw", role=User.Role.CONTRACTOR)

    def _valid_payload(self, **overrides):
        data = {
            "title": "Build a wall",
            "category": self.category.id,
            "description": "Need a wall.",
            "location": "Lahore",
            "budget_min": "1000",
            "budget_max": "5000",
            "deadline": "2026-12-31",
        }
        data.update(overrides)
        return data

    def test_client_can_post_project(self):
        self.client.login(username="cli", password="pw")
        self.client.post(reverse("project_create"), self._valid_payload())
        project = Project.objects.get(title="Build a wall")
        self.assertEqual(project.status, Project.Status.OPEN)
        self.assertEqual(project.client, self.client_user)

    def test_contractor_cannot_post_project(self):
        self.client.login(username="ctr", password="pw")
        resp = self.client.post(reverse("project_create"), self._valid_payload())
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Project.objects.filter(title="Build a wall").exists())

    def test_budget_max_below_min_rejected(self):
        self.client.login(username="cli", password="pw")
        resp = self.client.post(
            reverse("project_create"),
            self._valid_payload(budget_min="5000", budget_max="1000"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Project.objects.exists())


class ProjectFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cat = ProjectCategory.objects.first()
        cli = User.objects.create_user("cli", password="pw", role=User.Role.CLIENT)
        Project.objects.create(client=cli, category=cat, title="Lahore job", description="d",
            location="Lahore", budget_min=1, budget_max=2, deadline="2026-12-31")
        Project.objects.create(client=cli, category=cat, title="Karachi job", description="d",
            location="Karachi", budget_min=1, budget_max=2, deadline="2026-12-31")

    def test_location_filter(self):
        resp = self.client.get(reverse("project_list"), {"location": "Lahore"})
        self.assertContains(resp, "Lahore job")
        self.assertNotContains(resp, "Karachi job")
