from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from projects.models import Project

from .forms import ReviewForm


@role_required(User.Role.CLIENT)
def review_create(request, project_pk):
    """The client reviews a confirmed-complete project, once."""
    project = get_object_or_404(Project, pk=project_pk)

    if project.client_id != request.user.id:
        messages.error(request, "You can only review your own projects.")
        return redirect("project_detail", pk=project.pk)

    if project.status != Project.Status.COMPLETED or not project.completion_confirmed:
        messages.error(request, "You can review only after confirming completion.")
        return redirect("project_detail", pk=project.pk)

    if hasattr(project, "review"):
        messages.error(request, "You have already reviewed this project.")
        return redirect("project_detail", pk=project.pk)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.project = project
            review.client = request.user
            review.contractor = project.awarded_contractor
            review.save()
            # Refresh the contractor's average rating.
            profile = getattr(project.awarded_contractor, "contractor_profile", None)
            if profile is not None:
                profile.recalculate_rating()
            messages.success(request, "Thanks for your review.")
            return redirect("contractor_detail", pk=project.awarded_contractor.pk)
    else:
        form = ReviewForm()

    return render(request, "reviews/review_form.html", {"form": form, "project": project})
