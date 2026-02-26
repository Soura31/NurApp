from django.urls import path

from .views import LandingPageView

app_name = "users"

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
]
