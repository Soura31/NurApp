from django.db import models


class AsmaName(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    name_arabic = models.CharField(max_length=100)
    transliteration = models.CharField(max_length=100)
    meaning = models.CharField(max_length=255)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. {self.transliteration}"
