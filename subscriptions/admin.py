from django.contrib import admin

from .models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "price_monthly", "price_yearly", "is_popular")
    search_fields = ("name", "slug")
