from django.urls import path

from . import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("new/", views.project_create, name="project_create"),
    path("<int:pk>/", views.project_detail, name="project_detail"),
    path("<int:pk>/complete/", views.mark_completed, name="mark_completed"),
    path("<int:pk>/confirm/", views.confirm_completion, name="confirm_completion"),
]
