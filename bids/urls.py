from django.urls import path

from . import views

urlpatterns = [
    path("projects/<int:project_pk>/bid/", views.bid_create, name="bid_create"),
    path("bids/<int:bid_pk>/award/", views.award_bid, name="award_bid"),
]
