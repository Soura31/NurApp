from django.urls import path

from .views import SaveTasbihView, TasbihView

app_name = "tasbih"

urlpatterns = [
    path("", TasbihView.as_view(), name="index"),
    path("save/", SaveTasbihView.as_view(), name="save_tasbih"),
]
