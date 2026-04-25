from datetime import date

from django.conf import settings
from django.db import models
from django.urls import reverse


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
    bio = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return f"Profil {self.user.email or self.user.username}"

    @property
    def is_premium(self) -> bool:
        return bool(self.plan and self.plan.slug != "free" and self.subscription_status in {"active", "trialing"})

    def get_public_url(self):
        return reverse("users:public_profile", kwargs={"username": self.user.username})


class DailyReadingLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_reading_logs")
    log_date = models.DateField(default=date.today)
    verses_read = models.PositiveIntegerField(default=0)
    surahs_completed = models.JSONField(default=list, blank=True)
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-log_date"]
        unique_together = ("user", "log_date")

    def __str__(self):
        return f"{self.user} - {self.log_date}"


class UserGoal(models.Model):
    GOAL_TYPES = [
        ("verses_day", "X versets/jour"),
        ("finish_quran", "Finir le Coran en X mois"),
        ("memorize_surahs", "Memoriser X sourates"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    goal_type = models.CharField(max_length=30, choices=GOAL_TYPES)
    title = models.CharField(max_length=160, blank=True)
    target_value = models.PositiveIntegerField(default=1)
    current_value = models.PositiveIntegerField(default=0)
    target_months = models.PositiveIntegerField(default=3)
    reminder_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "-updated_at"]

    def __str__(self):
        return self.title or self.get_goal_type_display()

    @property
    def progress_percent(self):
        if not self.target_value:
            return 0
        return min(100, round((self.current_value / self.target_value) * 100))


class BadgeDefinition(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField()
    icon = models.CharField(max_length=80, default="fa-solid fa-star-and-crescent")
    category = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(BadgeDefinition, on_delete=models.CASCADE, related_name="holders")
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-unlocked_at"]
        unique_together = ("user", "badge")

    def __str__(self):
        return f"{self.user} - {self.badge.name}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences")
    verse_of_day = models.BooleanField(default=True)
    daily_reading = models.BooleanField(default=True)
    streak_danger = models.BooleanField(default=True)
    badge_unlocked = models.BooleanField(default=True)
    group_activity = models.BooleanField(default=True)
    post_replies = models.BooleanField(default=True)
    morning_dua = models.BooleanField(default=False)
    quiet_hours_start = models.PositiveSmallIntegerField(default=0)
    quiet_hours_end = models.PositiveSmallIntegerField(default=6)
    reminder_hour = models.PositiveSmallIntegerField(default=20)
    push_enabled = models.BooleanField(default=False)
    high_contrast = models.BooleanField(default=False)

    def __str__(self):
        return f"Notifications {self.user}"


class AppNotification(models.Model):
    TYPES = [
        ("streak", "Streak"),
        ("badge", "Badge"),
        ("reading", "Lecture"),
        ("community", "Communaute"),
        ("group", "Groupe"),
        ("dua", "Dua"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="app_notifications")
    notification_type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=180)
    body = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.title}"


class RamadanDayLog(models.Model):
    STATUS_CHOICES = [
        ("unknown", "Non renseigne"),
        ("fasted", "Jeune"),
        ("missed", "Non jeune"),
        ("makeup", "Rattrape"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ramadan_logs")
    hijri_year = models.PositiveIntegerField()
    day_number = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unknown")
    notes = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["day_number"]
        unique_together = ("user", "hijri_year", "day_number")

    def __str__(self):
        return f"Ramadan {self.hijri_year} - {self.user} - {self.day_number}"


class DuaCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Dua(models.Model):
    category = models.ForeignKey(DuaCategory, on_delete=models.CASCADE, related_name="duas")
    title = models.CharField(max_length=180)
    arabic_text = models.TextField()
    transliteration = models.TextField(blank=True)
    translation = models.TextField()
    audio_url = models.URLField(blank=True)
    source = models.CharField(max_length=120, blank=True)
    share_text = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["category__order", "id"]

    def __str__(self):
        return self.title


class FavoriteDua(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_duas")
    dua = models.ForeignKey(Dua, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "dua")

    def __str__(self):
        return f"{self.user} - {self.dua.title}"


class UserFollow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_links")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("follower", "following")

    def __str__(self):
        return f"{self.follower} -> {self.following}"


class ReadingGroup(models.Model):
    name = models.CharField(max_length=140)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    target_days = models.PositiveIntegerField(default=30)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_reading_groups")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through="ReadingGroupMembership", related_name="reading_groups")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ReadingGroupMembership(models.Model):
    ROLE_CHOICES = [
        ("leader", "Leader"),
        ("member", "Membre"),
    ]

    group = models.ForeignKey(ReadingGroup, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    assigned_juz = models.PositiveSmallIntegerField(null=True, blank=True)
    assigned_surahs = models.CharField(max_length=200, blank=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-progress_percent", "joined_at"]
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user} in {self.group}"


class GroupMessage(models.Model):
    group = models.ForeignKey(ReadingGroup, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_messages")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} - {self.group}"


class CollectiveChallenge(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    target_value = models.PositiveIntegerField(default=6236)
    current_value = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    season = models.CharField(max_length=80, blank=True)
    badge_slug = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["end_date", "title"]

    def __str__(self):
        return self.title

    @property
    def progress_percent(self):
        if not self.target_value:
            return 0
        return min(100, round((self.current_value / self.target_value) * 100))


class ChallengeParticipant(models.Model):
    challenge = models.ForeignKey(CollectiveChallenge, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenge_entries")
    contribution = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-contribution", "user__username"]
        unique_together = ("challenge", "user")

    def __str__(self):
        return f"{self.user} - {self.challenge}"
