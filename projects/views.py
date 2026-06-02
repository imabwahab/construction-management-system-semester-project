from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from bids.forms import BidForm

from .forms import ProjectForm
from .models import Project, ProjectCategory


def project_list(request):
    """Browse open projects with category / location / budget filters + pagination."""
    projects = Project.objects.filter(status=Project.Status.OPEN).select_related(
        "category", "client"
    )

    category_id = request.GET.get("category")
    location = request.GET.get("location", "").strip()
    min_budget = request.GET.get("min_budget")
    max_budget = request.GET.get("max_budget")

    if category_id:
        projects = projects.filter(category_id=category_id)
    if location:
        projects = projects.filter(location__icontains=location)
    # Overlap filtering against the project's [budget_min, budget_max] range.
    if min_budget:
        projects = projects.filter(budget_max__gte=min_budget)
    if max_budget:
        projects = projects.filter(budget_min__lte=max_budget)

    paginator = Paginator(projects, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Preserve active filters across pagination links.
    querystring = request.GET.copy()
    querystring.pop("page", None)

    return render(
        request,
        "projects/project_list.html",
        {
            "page_obj": page_obj,
            "categories": ProjectCategory.objects.all(),
            "filters": {
                "category": category_id or "",
                "location": location,
                "min_budget": min_budget or "",
                "max_budget": max_budget or "",
            },
            "querystring": querystring.urlencode(),
        },
    )


def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related("category", "client", "awarded_contractor"), pk=pk
    )

    # `bids` is the Bid related_name (bids app); guard until that app exists.
    bids_manager = getattr(project, "bids", None)
    if bids_manager is not None:
        bids = bids_manager.select_related(
            "contractor", "contractor__contractor_profile"
        ).all()
        # Has the current contractor already bid on this project?
        user_bid = (
            bids.filter(contractor=request.user).first()
            if request.user.is_authenticated and request.user.is_contractor
            else None
        )
    else:
        bids = []
        user_bid = None

    user = request.user
    is_owner = user.is_authenticated and project.client_id == user.id
    is_awarded_contractor = (
        user.is_authenticated and project.awarded_contractor_id == user.id
    )

    can_bid = (
        user.is_authenticated
        and user.is_contractor
        and project.is_open
        and user_bid is None
        and getattr(getattr(user, "contractor_profile", None), "is_verified", False)
    )

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "bids": bids,
            "user_bid": user_bid,
            "is_owner": is_owner,
            "is_awarded_contractor": is_awarded_contractor,
            "can_bid": can_bid,
            "bid_form": BidForm() if can_bid else None,
        },
    )


@role_required(User.Role.CONTRACTOR)
def mark_completed(request, pk):
    """The awarded contractor marks an in-progress project as completed."""
    project = get_object_or_404(Project, pk=pk)
    if project.awarded_contractor_id != request.user.id:
        messages.error(request, "Only the awarded contractor can complete this project.")
        return redirect("project_detail", pk=project.pk)
    if request.method == "POST" and project.status == Project.Status.IN_PROGRESS:
        project.status = Project.Status.COMPLETED
        project.save(update_fields=["status"])
        messages.success(request, "Project marked as completed. Awaiting client confirmation.")
    return redirect("project_detail", pk=project.pk)


@role_required(User.Role.CLIENT)
def confirm_completion(request, pk):
    """The client confirms a completed project, which unlocks reviewing."""
    project = get_object_or_404(Project, pk=pk)
    if project.client_id != request.user.id:
        messages.error(request, "You can only confirm your own projects.")
        return redirect("project_detail", pk=project.pk)
    if request.method == "POST" and project.status == Project.Status.COMPLETED:
        project.completion_confirmed = True
        project.save(update_fields=["completion_confirmed"])
        messages.success(request, "Completion confirmed. You can now leave a review.")
    return redirect("project_detail", pk=project.pk)


@role_required(User.Role.CLIENT)
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.client = request.user
            project.save()
            messages.success(request, "Project posted.")
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, "projects/project_form.html", {"form": form})
