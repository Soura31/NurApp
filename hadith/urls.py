from django.urls import path

from .views import HadithArchiveView, HadithOfDayView

app_name = "hadith"

urlpatterns = [
    path("", HadithOfDayView.as_view(), name="day"),
    path("archive/", HadithArchiveView.as_view(), name="archive"),
]
