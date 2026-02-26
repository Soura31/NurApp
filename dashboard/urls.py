from django.urls import path

from .views import (
    AdminPanelView,
    DashboardBookmarksView,
    DashboardFavoritesView,
    DashboardHomeView,
    DashboardInvoicesView,
    DashboardProfileView,
    DashboardSubscriptionView,
)

app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("subscription/", DashboardSubscriptionView.as_view(), name="subscription"),
    path("favorites/", DashboardFavoritesView.as_view(), name="favorites"),
    path("bookmarks/", DashboardBookmarksView.as_view(), name="bookmarks"),
    path("invoices/", DashboardInvoicesView.as_view(), name="invoices"),
    path("profile/", DashboardProfileView.as_view(), name="profile"),
    path("admin-panel/", AdminPanelView.as_view(), name="admin_panel"),
]
