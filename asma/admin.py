from django.contrib import admin

from .models import AsmaName


@admin.register(AsmaName)
class AsmaNameAdmin(admin.ModelAdmin):
    list_display = ("number", "transliteration", "meaning")
