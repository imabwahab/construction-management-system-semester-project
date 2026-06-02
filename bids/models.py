from django.conf import settings
from django.db import models

from projects.models import Project


class Bid(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="bids")
    contractor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bids"
    )
    bid_amount = models.DecimalField(max_digits=12, decimal_places=2)
    proposed_timeline_days = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["bid_amount"]
        # One bid per contractor per project.
        constraints = [
            models.UniqueConstraint(
                fields=["project", "contractor"], name="unique_bid_per_contractor"
            )
        ]

    def __str__(self):
        return f"{self.contractor} -> {self.project} ({self.bid_amount})"
