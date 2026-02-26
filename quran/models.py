from django.conf import settings
from django.db import models


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    surah_number = models.PositiveSmallIntegerField()
    ayah_number = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "surah_number", "ayah_number")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.surah_number}:{self.ayah_number}"


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    surah_number = models.PositiveSmallIntegerField()
    ayah_number = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "surah_number", "ayah_number")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Signet {self.user} - {self.surah_number}:{self.ayah_number}"
