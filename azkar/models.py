from django.conf import settings
from django.db import models


class AzkarCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Zikr(models.Model):
    category = models.ForeignKey(AzkarCategory, on_delete=models.CASCADE, related_name="azkar")
    text_arabic = models.TextField()
    transliteration = models.TextField(blank=True)
    translation = models.TextField(blank=True)
    repetitions = models.PositiveIntegerField(default=1)
    audio_url = models.URLField(blank=True)
    is_premium_audio = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category} - {self.id}"


class ZikrCounter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    zikr = models.ForeignKey(Zikr, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "zikr")
