from django.contrib import admin

from .models import TasbihSession


@admin.register(TasbihSession)
class TasbihSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "dhikr_text", "count", "target", "created_at")
