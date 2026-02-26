from django.db import models


class DashboardMetric(models.Model):
    """Table optionnelle pour snapshots statistiques admin."""
    key = models.CharField(max_length=120)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
