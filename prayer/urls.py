from django.urls import path

from .views import PrayerNotificationSettingsView, PrayerTimesView

app_name = "prayer"

urlpatterns = [
    path("", PrayerTimesView.as_view(), name="times"),
    path("notifications/", PrayerNotificationSettingsView.as_view(), name="notifications"),
]
