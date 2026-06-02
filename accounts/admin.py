from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ContractorProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & contact", {"fields": ("role", "phone_number", "address", "profile_picture")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role & contact", {"fields": ("role", "phone_number", "address")}),
    )


@admin.register(ContractorProfile)
class ContractorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "user",
        "verification_status",
        "rating_average",
        "experience_years",
    )
    list_filter = ("verification_status",)
    search_fields = ("company_name", "user__username", "license_number")
    readonly_fields = ("rating_average",)
    actions = ("verify_contractors", "reject_contractors")

    @admin.action(description="Verify selected contractors")
    def verify_contractors(self, request, queryset):
        updated = queryset.update(verification_status=ContractorProfile.Verification.VERIFIED)
        self.message_user(request, f"{updated} contractor(s) verified.")

    @admin.action(description="Reject selected contractors")
    def reject_contractors(self, request, queryset):
        updated = queryset.update(verification_status=ContractorProfile.Verification.REJECTED)
        self.message_user(request, f"{updated} contractor(s) rejected.")
