from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from dashboard.views import AdminPanelView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("users.urls")),
    path("admin-panel/", AdminPanelView.as_view(), name="admin_panel_root"),
    path("subscriptions/", include("subscriptions.urls")),
    path("payments/", include("payments.urls")),
    path("quran/", include("quran.urls")),
    path("prayer-times/", include("prayer.urls")),
    path("azkar/", include("azkar.urls")),
    path("tasbih/", include("tasbih.urls")),
    path("asma-allah/", include("asma.urls")),
    path("hadith/", include("hadith.urls")),
    path("community/", include("community.urls")),
    path("dashboard/", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
