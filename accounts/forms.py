from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import ContractorProfile, User


class RegisterForm(UserCreationForm):
    """Sign-up form. Role is restricted to Client/Contractor on purpose --
    ADMIN must never be self-selectable; admins are made via createsuperuser.
    """

    ROLE_CHOICES = [
        (User.Role.CLIENT, "Client"),
        (User.Role.CONTRACTOR, "Contractor"),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role", "phone_number", "address")


class ContractorProfileForm(forms.ModelForm):
    """Contractor-only details collected at registration and editable later.

    `verification_status` and `rating_average` are intentionally excluded --
    only an admin sets verification, and rating is computed from reviews.
    """

    class Meta:
        model = ContractorProfile
        fields = (
            "company_name",
            "experience_years",
            "license_number",
            "license_document",
            "biography",
        )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "phone_number", "address", "profile_picture")
