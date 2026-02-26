from django.contrib import admin

from .models import ForumCategory, ForumPost, ForumReply


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_premium")


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "is_pinned", "is_reported", "created_at")
    list_filter = ("category", "is_reported", "is_pinned")


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")
