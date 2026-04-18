from django.urls import path

from .views import PrayerNotificationSettingsView, PrayerTimesView, QiblaView

app_name = "prayer"

urlpatterns = [
    path("", PrayerTimesView.as_view(), name="times"),
    path("qibla/", QiblaView.as_view(), name="qibla"),
    path("notifications/", PrayerNotificationSettingsView.as_view(), name="notifications"),
]
