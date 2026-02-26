from django.contrib import admin

from .models import Hadith


@admin.register(Hadith)
class HadithAdmin(admin.ModelAdmin):
    list_display = ("source", "reference", "display_date")
    list_filter = ("source",)
