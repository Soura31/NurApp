from django.db import models


class Plan(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=0)
    stripe_price_id_monthly = models.CharField(max_length=255, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=255, blank=True)
    features = models.JSONField(default=list)
    is_popular = models.BooleanField(default=False)
    max_family_members = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["price_monthly"]

    def __str__(self):
        return self.name
