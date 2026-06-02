from django.contrib import admin

from .models import Project, ProjectCategory


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "category", "status", "deadline", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "location", "client__username")
    date_hierarchy = "created_at"
