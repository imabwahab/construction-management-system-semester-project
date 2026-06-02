from django.urls import path

from . import views

urlpatterns = [
    path("projects/<int:project_pk>/review/", views.review_create, name="review_create"),
]
