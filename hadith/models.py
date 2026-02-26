from django.db import models


class Hadith(models.Model):
    text_arabic = models.TextField()
    text_french = models.TextField()
    narrator = models.CharField(max_length=120)
    source = models.CharField(max_length=120)
    reference = models.CharField(max_length=120)
    display_date = models.DateField(unique=True)

    class Meta:
        ordering = ["-display_date"]

    def __str__(self):
        return f"{self.source} - {self.reference}"
