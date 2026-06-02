from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect

from accounts.decorators import role_required
from accounts.models import User
from projects.models import Project

from .forms import BidForm
from .models import Bid


@role_required(User.Role.CONTRACTOR)
def bid_create(request, project_pk):
    """A verified contractor submits one bid on an open project."""
    project = get_object_or_404(Project, pk=project_pk)
    profile = getattr(request.user, "contractor_profile", None)

    if profile is None or not profile.is_verified:
        messages.error(request, "Only verified contractors can submit bids.")
        return redirect("project_detail", pk=project.pk)

    if not project.is_open:
        messages.error(request, "This project is no longer open for bids.")
        return redirect("project_detail", pk=project.pk)

    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.project = project
            bid.contractor = request.user
            try:
                # Savepoint so a unique-constraint violation doesn't poison the
                # surrounding transaction (matters on Postgres and in tests).
                with transaction.atomic():
                    bid.save()
                messages.success(request, "Your bid has been submitted.")
            except IntegrityError:
                # Hits the unique_bid_per_contractor constraint.
                messages.error(request, "You have already bid on this project.")
        else:
            messages.error(request, "Please correct the errors in your bid.")
    return redirect("project_detail", pk=project.pk)


@role_required(User.Role.CLIENT)
def award_bid(request, bid_pk):
    """The project's client awards the project to one bid."""
    bid = get_object_or_404(Bid.objects.select_related("project"), pk=bid_pk)
    project = bid.project

    if project.client_id != request.user.id:
        messages.error(request, "You can only award your own projects.")
        return redirect("project_detail", pk=project.pk)

    if not project.is_open:
        messages.error(request, "This project is no longer open.")
        return redirect("project_detail", pk=project.pk)

    if request.method == "POST":
        with transaction.atomic():
            project.bids.exclude(pk=bid.pk).update(status=Bid.Status.REJECTED)
            bid.status = Bid.Status.ACCEPTED
            bid.save(update_fields=["status"])
            project.awarded_contractor = bid.contractor
            project.status = Project.Status.IN_PROGRESS
            project.save(update_fields=["awarded_contractor", "status"])
        messages.success(request, f"Project awarded to {bid.contractor.username}.")
    return redirect("project_detail", pk=project.pk)
