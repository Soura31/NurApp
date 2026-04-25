from django.conf import settings
from django.db import models


class AsmaName(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    name_arabic = models.CharField(max_length=100)
    transliteration = models.CharField(max_length=100)
    meaning = models.CharField(max_length=255)
    explanation = models.TextField(blank=True)
    hadith_reference = models.CharField(max_length=255, blank=True, default="Invoquez Allah par Ses plus beaux Noms.")
    audio_url = models.URLField(blank=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. {self.transliteration}"


class LearnedName(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learned_names")
    name = models.ForeignKey(AsmaName, on_delete=models.CASCADE, related_name="learners")
    memorized_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-memorized_at"]
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.user} - {self.name}"
