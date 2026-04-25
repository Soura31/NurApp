from django.urls import path

from .views import (
    AssistantMessageView,
    AssistantPageView,
    BadgesView,
    ChallengesView,
    DuasView,
    GoalCreateView,
    GroupMessageCreateView,
    GroupsView,
    HijriCalendarView,
    HistoryView,
    JoinGroupView,
    LandingPageView,
    NotificationSettingsView,
    PublicProfileView,
    RamadanTrackerView,
    ToggleFavoriteDuaView,
    ToggleFollowView,
)

app_name = "users"

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("calendar/", HijriCalendarView.as_view(), name="calendar"),
    path("assistant/", AssistantPageView.as_view(), name="assistant"),
    path("assistant/message/", AssistantMessageView.as_view(), name="assistant_message"),
    path("badges/", BadgesView.as_view(), name="badges"),
    path("duas/", DuasView.as_view(), name="duas"),
    path("duas/favori/<int:pk>/", ToggleFavoriteDuaView.as_view(), name="toggle_favorite_dua"),
    path("parametres/notifications/", NotificationSettingsView.as_view(), name="notification_settings"),
    path("ramadan/", RamadanTrackerView.as_view(), name="ramadan"),
    path("histoire/", HistoryView.as_view(), name="history"),
    path("groupes/", GroupsView.as_view(), name="groups"),
    path("groupes/<slug:slug>/rejoindre/", JoinGroupView.as_view(), name="join_group"),
    path("groupes/<slug:slug>/message/", GroupMessageCreateView.as_view(), name="group_message"),
    path("defis/", ChallengesView.as_view(), name="challenges"),
    path("objectifs/ajouter/", GoalCreateView.as_view(), name="goal_create"),
    path("profil/<str:username>/", PublicProfileView.as_view(), name="public_profile"),
    path("profil/<str:username>/suivre/", ToggleFollowView.as_view(), name="toggle_follow"),
]
