from django.urls import path

from .views import AzkarCategoryListView, AzkarListView, ZikrCounterUpdateView

app_name = "azkar"

urlpatterns = [
    path("", AzkarCategoryListView.as_view(), name="categories"),
    path("<slug:slug>/", AzkarListView.as_view(), name="list"),
    path("counter/<int:zikr_id>/", ZikrCounterUpdateView.as_view(), name="counter"),
]
