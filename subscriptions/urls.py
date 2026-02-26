from django.urls import path

from .views import CreateCheckoutSessionView, CustomerPortalView, PlanListView

app_name = "subscriptions"

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plans"),
    path("checkout/<slug:slug>/", CreateCheckoutSessionView.as_view(), name="checkout"),
    path("portal/", CustomerPortalView.as_view(), name="portal"),
]
