from django.urls import path

from .views import AsmaDetailView, AsmaListView, AsmaQuizCheckView, AsmaQuizView

app_name = "asma"

urlpatterns = [
    path("", AsmaListView.as_view(), name="list"),
    path("quiz/", AsmaQuizView.as_view(), name="quiz"),
    path("quiz/check/", AsmaQuizCheckView.as_view(), name="quiz_check"),
    path("<int:pk>/", AsmaDetailView.as_view(), name="detail"),
]
