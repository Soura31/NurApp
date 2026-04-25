from django.conf import settings
from django.db import models


class ForumCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_premium = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ForumPost(models.Model):
    POST_TYPES = [
        ("verse", "Verset + reflexion"),
        ("dua", "Dua"),
        ("hadith", "Hadith"),
        ("question", "Question"),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default="verse")
    title = models.CharField(max_length=200)
    content = models.TextField()
    verse_reference = models.CharField(max_length=50, blank=True)
    is_pinned = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    liked_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="liked_forum_posts")
    is_reported = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class ForumReply(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    likes_count = models.PositiveIntegerField(default=0)
    is_reported = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reponse de {self.author}"
