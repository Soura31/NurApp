from django.contrib import admin

from .models import PrayerNotificationSetting


@admin.register(PrayerNotificationSetting)
class PrayerNotificationSettingAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "country", "updated_at")
