from django.urls import path

from .views import HadithArchiveView, HadithOfDayView

app_name = "hadith"

urlpatterns = [
    path("", HadithArchiveView.as_view(), name="list"),
    path("day/", HadithOfDayView.as_view(), name="day"),
    path("archive/", HadithArchiveView.as_view(), name="archive"),
]
