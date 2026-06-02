from django.test import TestCase
from django.urls import reverse

from .models import ContractorProfile, User


class RegistrationTests(TestCase):
    def test_client_registration_creates_client(self):
        resp = self.client.post(
            reverse("register"),
            {
                "username": "alice",
                "email": "alice@example.com",
                "role": "CLIENT",
                "password1": "Buildbid!2026",
                "password2": "Buildbid!2026",
            },
        )
        self.assertRedirects(resp, reverse("dashboard"))
        user = User.objects.get(username="alice")
        self.assertEqual(user.role, User.Role.CLIENT)

    def test_contractor_registration_creates_pending_profile(self):
        self.client.post(
            reverse("register"),
            {
                "username": "bob",
                "email": "bob@example.com",
                "role": "CONTRACTOR",
                "company_name": "Bob Builders",
                "experience_years": "5",
                "password1": "Buildbid!2026",
                "password2": "Buildbid!2026",
            },
        )
        user = User.objects.get(username="bob")
        self.assertEqual(user.role, User.Role.CONTRACTOR)
        profile = ContractorProfile.objects.get(user=user)
        self.assertEqual(profile.verification_status, ContractorProfile.Verification.PENDING)

    def test_admin_role_cannot_be_self_selected(self):
        resp = self.client.post(
            reverse("register"),
            {
                "username": "evil",
                "email": "evil@example.com",
                "role": "ADMIN",
                "password1": "Buildbid!2026",
                "password2": "Buildbid!2026",
            },
        )
        self.assertEqual(resp.status_code, 200)  # re-rendered with error
        self.assertFalse(User.objects.filter(username="evil").exists())


class DashboardRoutingTests(TestCase):
    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)

    def test_client_sees_client_dashboard(self):
        User.objects.create_user("cli", password="pw", role=User.Role.CLIENT)
        self.client.login(username="cli", password="pw")
        resp = self.client.get(reverse("dashboard"))
        self.assertTemplateUsed(resp, "accounts/dashboard_client.html")
