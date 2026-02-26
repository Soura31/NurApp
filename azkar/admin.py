from django.contrib import admin

from .models import AzkarCategory, Zikr, ZikrCounter


@admin.register(AzkarCategory)
class AzkarCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


@admin.register(Zikr)
class ZikrAdmin(admin.ModelAdmin):
    list_display = ("category", "repetitions", "is_premium_audio")


@admin.register(ZikrCounter)
class ZikrCounterAdmin(admin.ModelAdmin):
    list_display = ("user", "zikr", "count", "updated_at")
