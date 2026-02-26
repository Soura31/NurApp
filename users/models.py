from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("trialing", "Trialing"),
        ("canceled", "Canceled"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey("subscriptions.Plan", on_delete=models.SET_NULL, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    subscription_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="inactive")
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    preferred_language = models.CharField(max_length=10, default="fr")
    preferred_reciter = models.CharField(max_length=50, default="ar.alafasy")
    show_transliteration = models.BooleanField(default=True)
    streak_days = models.PositiveIntegerField(default=0)
    total_verses_read = models.PositiveIntegerField(default=0)
    total_tasbih = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Profil {self.user.email or self.user.username}"

    @property
    def is_premium(self) -> bool:
        return bool(self.plan and self.plan.slug != "free" and self.subscription_status in {"active", "trialing"})
