from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    """Custom user with a role.

    NOTE: `role` is for application logic (who can post vs. bid) and is NOT the
    gate for the Django admin site -- admin access is controlled by
    `is_staff`/`is_superuser`. The ADMIN choice exists for labelling only;
    real admins are created via `createsuperuser`. Registration must never let
    a user self-select ADMIN (see accounts.forms.RegisterForm).
    """

    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        CONTRACTOR = "CONTRACTOR", "Contractor"
        ADMIN = "ADMIN", "Admin"

    # Users authenticate with `username` (AbstractUser default). Switching to
    # email login would require USERNAME_FIELD changes before the first migrate.
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_contractor(self):
        return self.role == self.Role.CONTRACTOR

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class ContractorProfile(models.Model):
    """One-to-one profile for contractors, holding verification + rating state."""

    class Verification(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="contractor_profile"
    )
    company_name = models.CharField(max_length=150)
    experience_years = models.PositiveIntegerField(default=0)
    license_number = models.CharField(max_length=100, blank=True)
    license_document = models.FileField(upload_to="license_documents/", blank=True, null=True)
    biography = models.TextField(blank=True)
    verification_status = models.CharField(
        max_length=20, choices=Verification.choices, default=Verification.PENDING
    )
    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    @property
    def is_verified(self):
        return self.verification_status == self.Verification.VERIFIED

    def recalculate_rating(self):
        """Recompute rating_average from this contractor's received reviews."""
        from django.db.models import Avg

        average = self.user.reviews_received.aggregate(value=Avg("rating"))["value"]
        self.rating_average = round(average, 2) if average is not None else 0
        self.save(update_fields=["rating_average"])

    def __str__(self):
        return f"{self.company_name} [{self.get_verification_status_display()}]"
