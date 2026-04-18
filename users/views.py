from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from subscriptions.models import Plan

from .assistant_service import ask_islamic_assistant
from .hijri import get_adjacent_hijri_period, get_current_hijri_period, get_hijri_month_calendar
from .verse_of_day import get_daily_verse


class LandingPageView(TemplateView):
    template_name = "landing/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = Plan.objects.all()
        context["features"] = [
            {"label": "Coran avec traductions multiplies", "url": "/quran/"},
            {"label": "Horaires de priere geolocalises", "url": "/prayer-times/"},
            {"label": "Audio recitateurs premium", "url": "/subscriptions/plans/"},
            {"label": "Azkar avec compteur intelligent", "url": "/azkar/"},
            {"label": "Forum communaute modere", "url": "/community/"},
            {"label": "Dashboard spirituel personnel", "url": "/dashboard/"},
        ]
        context["testimonials"] = [
            {"name": "Amina B.", "text": "NurCoran m'aide a rester reguliere dans mes rappels."},
            {"name": "Moussa D.", "text": "Le suivi des prieres est clair et motive toute la famille."},
            {"name": "Fatou K.", "text": "Les recitations audio ont transforme mon apprentissage."},
        ]
        context["faqs"] = [
            ("Puis-je commencer gratuitement ?", "Oui, le plan Free est disponible sans carte bancaire."),
            ("La devise est-elle en FCFA ?", "Oui, tous les montants sont affiches en FCFA."),
            ("Comment annuler un abonnement ?", "Via le portail client Stripe accessible dans le dashboard."),
            ("Les contenus premium sont-ils immediats ?", "Oui, activation automatique apres paiement valide."),
            ("Puis-je utiliser NurCoran sur mobile ?", "Oui, toute l'interface est responsive mobile-first."),
        ]
        context["verse_of_day"] = get_daily_verse()
        return context


class HijriCalendarView(TemplateView):
    template_name = "calendar/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requested_month = self.request.GET.get("month")
        requested_year = self.request.GET.get("year")
        month = None
        year = None

        if requested_month and requested_year:
            try:
                month = int(requested_month)
                year = int(requested_year)
            except (TypeError, ValueError):
                month = None
                year = None

        if month is None or year is None:
            current = get_current_hijri_period() or {"month": 9, "year": 1447}
            month = current["month"]
            year = current["year"]

        calendar_days = get_hijri_month_calendar(month, year)
        prev_month, prev_year = get_adjacent_hijri_period(month, year, -1)
        next_month, next_year = get_adjacent_hijri_period(month, year, 1)

        context.update(
            {
                "calendar_days": calendar_days,
                "calendar_month": month,
                "calendar_year": year,
                "calendar_label": f"{calendar_days[0]['hijri_month_name']} {year}" if calendar_days else f"{month}/{year}",
                "prev_month": prev_month,
                "prev_year": prev_year,
                "next_month": next_month,
                "next_year": next_year,
                "important_days": [
                    "1 Ramadan",
                    "27 Ramadan",
                    "1 Chawwal",
                    "10 Dhou al-Hijja",
                    "12 Rabi al-Awwal",
                    "10 Mouharram",
                ],
            }
        )
        return context


class AssistantPageView(TemplateView):
    template_name = "assistant/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assistant_history"] = self.request.session.get("assistant_history", [])
        return context


class AssistantMessageView(View):
    def post(self, request):
        message = (request.POST.get("message") or "").strip()
        if not message:
            return JsonResponse({"error": "message manquant"}, status=400)

        history = request.session.get("assistant_history", [])
        history.append({"role": "user", "content": message})
        history = history[-10:]

        result = ask_islamic_assistant(history)
        assistant_text = result["text"]
        history.append({"role": "assistant", "content": assistant_text})
        request.session["assistant_history"] = history[-12:]
        request.session.modified = True
        return JsonResponse({"reply": assistant_text, "ok": result["ok"]})
