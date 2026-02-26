from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
import requests

from .models import PrayerNotificationSetting


class PrayerTimesView(TemplateView):
    template_name = "prayer/times.html"

    def _timings(self, city: str, country: str):
        key = f"prayer_timings_{city}_{country}"
        data = cache.get(key)
        if data:
            return data
        try:
            response = requests.get(
                f"{settings.ALADHAN_API_BASE}/timingsByCity",
                params={"city": city, "country": country, "method": 2},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            cache.set(key, data, 3600)  # 1h
            return data
        except Exception:
            return {}

    def _monthly(self, city: str, country: str):
        now = datetime.now()
        key = f"prayer_calendar_{city}_{country}_{now.year}_{now.month}"
        data = cache.get(key)
        if data:
            return data
        try:
            response = requests.get(
                f"{settings.ALADHAN_API_BASE}/calendarByCity",
                params={"city": city, "country": country, "method": 2, "month": now.month, "year": now.year},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            cache.set(key, data, 3600)
            return data
        except Exception:
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city = self.request.GET.get("city")
        country = self.request.GET.get("country", "SN")

        if self.request.user.is_authenticated and hasattr(self.request.user, "userprofile") and not city:
            city = self.request.user.userprofile.city or "Dakar"
        city = city or "Dakar"

        timings_data = self._timings(city, country)
        timings = timings_data.get("timings", {})

        context.update(
            {
                "city": city,
                "country": country,
                "timings": {k: timings.get(k) for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]},
                "monthly_calendar": self._monthly(city, country),
            }
        )
        return context


class PrayerNotificationSettingsView(LoginRequiredMixin, View):
    def post(self, request):
        obj, _ = PrayerNotificationSetting.objects.get_or_create(user=request.user)
        obj.fajr = bool(request.POST.get("fajr"))
        obj.dhuhr = bool(request.POST.get("dhuhr"))
        obj.asr = bool(request.POST.get("asr"))
        obj.maghrib = bool(request.POST.get("maghrib"))
        obj.isha = bool(request.POST.get("isha"))
        obj.city = request.POST.get("city", obj.city)
        obj.country = request.POST.get("country", obj.country)
        obj.save()
        messages.success(request, "Preferences de notification mises a jour.")
        return redirect("prayer:times")
