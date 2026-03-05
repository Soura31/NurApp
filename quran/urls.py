from django.urls import path

from .views import (
    BookmarkVerseView,
    FavoriteVerseView,
    QuranLanguagesView,
    QuranListView,
    QuranPageView,
    QuranRecitersView,
    SurahDetailView,
)

app_name = "quran"

urlpatterns = [
    path("", QuranListView.as_view(), name="list"),
    path("", QuranListView.as_view(), name="surah_list"),
    path("reciters/", QuranRecitersView.as_view(), name="reciters"),
    path("languages/", QuranLanguagesView.as_view(), name="languages"),
    path("pages/<int:page>/", QuranPageView.as_view(), name="page"),
    path("favorites/add/", FavoriteVerseView.as_view(), name="favorite_add"),
    path("bookmarks/add/", BookmarkVerseView.as_view(), name="bookmark_add"),
    path("<int:surah_number>/", SurahDetailView.as_view(), name="surah_detail"),
    path("<int:surah_number>/", SurahDetailView.as_view(), name="detail"),
]
