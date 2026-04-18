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


class QuranReadingProgress(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    goal_days = models.PositiveIntegerField(default=30)
    reminder_enabled = models.BooleanField(default=False)
    started_at = models.DateField(auto_now_add=True)
    completed_at = models.DateField(null=True, blank=True)
    reset_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Progression Coran {self.user}"


class ReadSurah(models.Model):
    progress = models.ForeignKey(QuranReadingProgress, on_delete=models.CASCADE, related_name="read_surahs")
    surah_number = models.PositiveSmallIntegerField()
    surah_name = models.CharField(max_length=150, blank=True)
    surah_name_ar = models.CharField(max_length=150, blank=True)
    verses_count = models.PositiveIntegerField(default=0)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("progress", "surah_number")
        ordering = ["surah_number"]

    def __str__(self):
        return f"{self.progress.user} - sourate {self.surah_number}"


class RecitationAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recitation_attempts")
    surah_number = models.PositiveSmallIntegerField()
    ayah_number = models.PositiveIntegerField()
    verse_key = models.CharField(max_length=20)
    transcript = models.TextField(blank=True)
    score = models.PositiveSmallIntegerField(default=0)
    mistakes = models.JSONField(default=list, blank=True)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.verse_key} ({self.score}%)"


class HifzPlan(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hifz_plan")
    verses_per_day = models.PositiveIntegerField(default=3)
    repetition_target = models.PositiveIntegerField(default=5)
    streak_days = models.PositiveIntegerField(default=0)
    reminder_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Plan Hifz {self.user}"


class HifzAssignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hifz_assignments")
    surah_number = models.PositiveSmallIntegerField()
    surah_name = models.CharField(max_length=150, blank=True)
    start_ayah = models.PositiveIntegerField(default=1)
    end_ayah = models.PositiveIntegerField(default=1)
    repetition_target = models.PositiveIntegerField(default=5)
    repetition_done = models.PositiveIntegerField(default=0)
    next_review_at = models.DateField(null=True, blank=True)
    difficulty = models.PositiveSmallIntegerField(default=1)
    is_mastered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["is_mastered", "surah_number", "start_ayah"]

    def __str__(self):
        return f"{self.user} - {self.surah_number}:{self.start_ayah}-{self.end_ayah}"
