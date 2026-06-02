from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("project", "contractor", "client", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("project__title", "contractor__username", "client__username")
