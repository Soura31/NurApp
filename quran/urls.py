from django.urls import path

from .views import BookmarkVerseView, FavoriteVerseView, QuranListView, QuranPageView, SurahDetailView

app_name = "quran"

urlpatterns = [
    path("", QuranListView.as_view(), name="list"),
    path("pages/<int:page>/", QuranPageView.as_view(), name="page"),
    path("favorites/add/", FavoriteVerseView.as_view(), name="favorite_add"),
    path("bookmarks/add/", BookmarkVerseView.as_view(), name="bookmark_add"),
    path("<int:number>/", SurahDetailView.as_view(), name="detail"),
]
