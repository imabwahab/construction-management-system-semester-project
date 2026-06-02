from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from projects.models import Project


class Review(models.Model):
    # One review per project.
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="review")
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_given"
    )
    contractor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_received"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}/5 for {self.contractor} on {self.project}"
