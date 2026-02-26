from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "subscription_status", "city")
    list_filter = ("subscription_status",)
    search_fields = ("user__email", "user__username")
