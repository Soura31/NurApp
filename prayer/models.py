from django.conf import settings
from django.db import models


class PrayerNotificationSetting(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fajr = models.BooleanField(default=True)
    dhuhr = models.BooleanField(default=True)
    asr = models.BooleanField(default=True)
    maghrib = models.BooleanField(default=True)
    isha = models.BooleanField(default=True)
    city = models.CharField(max_length=120, default="Dakar")
    country = models.CharField(max_length=120, default="Senegal")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notifications prieres {self.user}"


class PrayerLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prayer_name = models.CharField(max_length=20)
    prayer_time = models.TimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
