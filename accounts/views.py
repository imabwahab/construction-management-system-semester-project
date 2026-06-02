from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContractorProfileForm, RegisterForm, UserProfileForm
from .models import ContractorProfile, User


def home(request):
    return render(request, "home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        profile_form = ContractorProfileForm(request.POST, request.FILES)
        is_contractor = request.POST.get("role") == User.Role.CONTRACTOR

        # Only validate the contractor profile when registering as a contractor.
        valid = form.is_valid()
        if is_contractor:
            valid = profile_form.is_valid() and valid

        if valid:
            user = form.save(commit=False)
            user.role = form.cleaned_data["role"]
            user.save()
            if is_contractor:
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            login(request, user)
            messages.success(request, "Account created. Welcome to BuildBid!")
            return redirect("dashboard")
    else:
        form = RegisterForm()
        profile_form = ContractorProfileForm()

    return render(
        request,
        "registration/register.html",
        {"form": form, "profile_form": profile_form},
    )


@login_required
def dashboard(request):
    """Route each user to their role-specific dashboard."""
    from django.db.models import Count

    from bids.models import Bid
    from projects.models import Project

    user = request.user
    if user.is_contractor:
        my_bids = (
            Bid.objects.filter(contractor=user)
            .select_related("project")
            .order_by("-submitted_at")
        )
        awarded = Project.objects.filter(awarded_contractor=user).exclude(
            status=Project.Status.OPEN
        )
        return render(
            request,
            "accounts/dashboard_contractor.html",
            {
                "my_bids": my_bids,
                "awarded": awarded,
                "profile": getattr(user, "contractor_profile", None),
            },
        )
    if user.is_client:
        my_projects = (
            Project.objects.filter(client=user)
            .annotate(bid_count=Count("bids"))
            .select_related("category")
        )
        return render(
            request, "accounts/dashboard_client.html", {"my_projects": my_projects}
        )
    # Admins use the Django admin site.
    return redirect("/admin/")


def contractor_detail(request, pk):
    """Public contractor profile: company info, verification, rating, reviews."""
    contractor = get_object_or_404(User, pk=pk, role=User.Role.CONTRACTOR)
    profile = getattr(contractor, "contractor_profile", None)
    # `reviews_received` is added with the Review model (reviews app); guard so
    # this page works before that app exists.
    reviews_manager = getattr(contractor, "reviews_received", None)
    reviews = (
        reviews_manager.select_related("project", "client").all()
        if reviews_manager is not None
        else []
    )
    return render(
        request,
        "accounts/contractor_detail.html",
        {"contractor": contractor, "profile": profile, "reviews": reviews},
    )


@login_required
def profile_edit(request):
    """Edit own account details; contractors also edit their contractor profile."""
    user = request.user
    is_contractor = user.is_contractor
    contractor_profile = None
    if is_contractor:
        contractor_profile, _ = ContractorProfile.objects.get_or_create(
            user=user, defaults={"company_name": user.username}
        )

    if request.method == "POST":
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        profile_form = (
            ContractorProfileForm(request.POST, request.FILES, instance=contractor_profile)
            if is_contractor
            else None
        )
        valid = user_form.is_valid()
        if is_contractor:
            valid = profile_form.is_valid() and valid
        if valid:
            user_form.save()
            if is_contractor:
                profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile_edit")
    else:
        user_form = UserProfileForm(instance=user)
        profile_form = (
            ContractorProfileForm(instance=contractor_profile) if is_contractor else None
        )

    return render(
        request,
        "accounts/profile_edit.html",
        {"user_form": user_form, "profile_form": profile_form},
    )
