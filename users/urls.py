from django.urls import path

from .views import AssistantMessageView, AssistantPageView, HijriCalendarView, LandingPageView

app_name = "users"

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("calendar/", HijriCalendarView.as_view(), name="calendar"),
    path("assistant/", AssistantPageView.as_view(), name="assistant"),
    path("assistant/message/", AssistantMessageView.as_view(), name="assistant_message"),
]
