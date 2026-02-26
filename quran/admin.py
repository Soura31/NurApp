from django.contrib import admin

from .models import Favorite, Bookmark


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "surah_number", "ayah_number", "created_at")


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "surah_number", "ayah_number", "updated_at")
