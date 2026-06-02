from django.contrib import admin

from .models import Bid


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("project", "contractor", "bid_amount", "proposed_timeline_days", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("project__title", "contractor__username")
