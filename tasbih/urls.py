from django.urls import path

from .views import SaveTasbihSessionView, TasbihView

app_name = "tasbih"

urlpatterns = [
    path("", TasbihView.as_view(), name="index"),
    path("save/", SaveTasbihSessionView.as_view(), name="save"),
]
