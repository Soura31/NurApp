from django.conf import settings
from django.db import models


class TasbihSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dhikr_text = models.CharField(max_length=150)
    dhikr_arabic = models.CharField(max_length=255, blank=True)
    count = models.PositiveIntegerField(default=0)
    target = models.PositiveIntegerField(default=33)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.dhikr_text} ({self.count}/{self.target})"
