from django.urls import path

from .views import (
    BookmarkVerseView,
    FavoriteVerseView,
    HifzCreateAssignmentView,
    HifzUpdateAssignmentView,
    QuranLanguagesView,
    QuranListView,
    QuranPageView,
    QuranRecitersView,
    QuranSearchApiView,
    RecitationAnalyzeView,
    ResetKhatamTrackerView,
    SurahDetailView,
    TafsirApiView,
    ToggleReadSurahView,
    UpdateKhatamGoalView,
    WordByWordApiView,
)

app_name = "quran"

urlpatterns = [
    path("", QuranListView.as_view(), name="list"),
    path("", QuranListView.as_view(), name="surah_list"),
    path("search/", QuranSearchApiView.as_view(), name="search"),
    path("tafsir/", TafsirApiView.as_view(), name="tafsir"),
    path("words/", WordByWordApiView.as_view(), name="words"),
    path("read/toggle/", ToggleReadSurahView.as_view(), name="read_toggle"),
    path("progress/reset/", ResetKhatamTrackerView.as_view(), name="progress_reset"),
    path("progress/goal/", UpdateKhatamGoalView.as_view(), name="progress_goal"),
    path("recitation/analyze/", RecitationAnalyzeView.as_view(), name="recitation_analyze"),
    path("hifz/create/", HifzCreateAssignmentView.as_view(), name="hifz_create"),
    path("hifz/update/", HifzUpdateAssignmentView.as_view(), name="hifz_update"),
    path("reciters/", QuranRecitersView.as_view(), name="reciters"),
    path("languages/", QuranLanguagesView.as_view(), name="languages"),
    path("pages/<int:page>/", QuranPageView.as_view(), name="page"),
    path("favorites/add/", FavoriteVerseView.as_view(), name="favorite_add"),
    path("bookmarks/add/", BookmarkVerseView.as_view(), name="bookmark_add"),
    path("<int:surah_number>/", SurahDetailView.as_view(), name="surah_detail"),
    path("<int:surah_number>/", SurahDetailView.as_view(), name="detail"),
]
