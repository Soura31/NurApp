import random

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from community.models import ForumPost
from prayer.models import PrayerReminder
from prayer.views import PRAYER_NAMES, ensure_prayer_reminders
from subscriptions.models import Plan

from .assistant_service import ask_islamic_assistant
from .engagement import (
    HISTORY_TIMELINE,
    build_month_streak_calendar,
    can_create_goal,
    ensure_daily_reminders,
    ensure_initial_content,
    get_active_challenges,
    get_daily_dua,
    get_daily_name_of_allah,
    get_global_verse_counter,
    get_or_create_notification_preferences,
    get_or_create_ramadan_log,
    get_pending_notifications,
    get_profile_summary,
)
from .forms import UserGoalForm
from .hijri import get_adjacent_hijri_period, get_current_hijri_period, get_hijri_month_calendar, get_today_hijri
from .models import BadgeDefinition, FavoriteDua, NotificationPreference, ReadingGroup, ReadingGroupMembership, RamadanDayLog, UserFollow
from .verse_of_day import get_daily_verse

User = get_user_model()


class LandingPageView(TemplateView):
    template_name = "landing/index.html"

    def get_context_data(self, **kwargs):
        ensure_initial_content()
        context = super().get_context_data(**kwargs)
        today_hijri = get_today_hijri()
        context["plans"] = Plan.objects.all()
        context["features"] = [
            {"label": "Coran avec traductions multiplies", "url": "/quran/"},
            {"label": "Horaires de priere geolocalises", "url": "/prayer-times/"},
            {"label": "Dua du jour et favoris", "url": "/duas/"},
            {"label": "Badges et streaks spirituels", "url": "/badges/"},
            {"label": "Feed Ummah et groupes de lecture", "url": "/community/"},
            {"label": "Dashboard spirituel personnel", "url": "/dashboard/"},
        ]
        context["testimonials"] = [
            {"name": "Amina B.", "text": "NurCoran m'aide a rester reguliere dans mes rappels."},
            {"name": "Moussa D.", "text": "Le suivi des prieres est clair et motive toute la famille."},
            {"name": "Fatou K.", "text": "Les streaks et les badges me poussent a revenir chaque jour."},
        ]
        context["faqs"] = [
            ("Puis-je commencer gratuitement ?", "Oui, le plan Free est disponible sans carte bancaire."),
            ("Puis-je suivre ma progression ?", "Oui, streaks, objectifs, badges et calendrier mensuel sont disponibles."),
            ("Le feed communaute est-il modere ?", "Oui, chaque publication peut etre signalee."),
            ("Puis-je memoriser les noms d'Allah ?", "Oui, un tracker Asma ul Husna est disponible."),
        ]
        context["verse_of_day"] = get_daily_verse()
        context["daily_dua"] = get_daily_dua()
        context["daily_name"] = get_daily_name_of_allah()
        context["home_summary"] = get_profile_summary(self.request.user) if self.request.user.is_authenticated else None
        context["ramadan_banner"] = today_hijri and today_hijri.get("hijri_month_number") == 9
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


class BadgesView(LoginRequiredMixin, TemplateView):
    template_name = "users/badges.html"

    def get_context_data(self, **kwargs):
        ensure_initial_content()
        context = super().get_context_data(**kwargs)
        context["summary"] = get_profile_summary(self.request.user)
        context["all_badges"] = self.request.user.badges.select_related("badge")
        context["badge_catalog"] = BadgeDefinition.objects.all()
        context["unlocked_badge_ids"] = set(self.request.user.badges.values_list("badge_id", flat=True))
        return context


class NotificationSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "users/notification_settings.html"

    def get_context_data(self, **kwargs):
        ensure_initial_content()
        context = super().get_context_data(**kwargs)
        context["preferences"] = get_or_create_notification_preferences(self.request.user)
        context["prayer_reminders"] = ensure_prayer_reminders(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        preferences, _ = NotificationPreference.objects.get_or_create(user=request.user)
        for field in [
            "verse_of_day",
            "daily_reading",
            "streak_danger",
            "badge_unlocked",
            "group_activity",
            "post_replies",
            "morning_dua",
            "push_enabled",
            "high_contrast",
        ]:
            setattr(preferences, field, bool(request.POST.get(field)))
        preferences.reminder_hour = min(23, max(0, int(request.POST.get("reminder_hour", preferences.reminder_hour))))
        preferences.save()

        for prayer_name in PRAYER_NAMES:
            reminder, _ = PrayerReminder.objects.get_or_create(user=request.user, prayer_name=prayer_name)
            key = prayer_name.lower()
            reminder.enabled = bool(request.POST.get(f"enabled_{key}"))
            reminder.delay_minutes = min(30, max(0, int(request.POST.get(f"delay_{key}", reminder.delay_minutes or 0))))
            reminder.sound = request.POST.get(f"sound_{key}", reminder.sound or "adhan")
            reminder.save()

        messages.success(request, "Parametres de notifications enregistres.")
        return redirect("users:notification_settings")


class GoalCreateView(LoginRequiredMixin, View):
    def post(self, request):
        if not can_create_goal(request.user):
            messages.error(request, "Maximum 3 objectifs actifs.")
            return redirect("dashboard:home")
        form = UserGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, "Objectif ajoute au dashboard.")
        else:
            messages.error(request, "Impossible d'ajouter cet objectif.")
        return redirect("dashboard:home")


class DuasView(TemplateView):
    template_name = "users/duas.html"

    def get_context_data(self, **kwargs):
        from .models import Dua, DuaCategory

        ensure_initial_content()
        context = super().get_context_data(**kwargs)
        category_slug = self.request.GET.get("categorie")
        duas = Dua.objects.select_related("category").all()
        if category_slug:
            duas = duas.filter(category__slug=category_slug)
        context["daily_dua"] = get_daily_dua()
        context["categories"] = DuaCategory.objects.all()
        context["duas"] = duas
        context["selected_category"] = category_slug
        context["favorite_dua_ids"] = (
            set(FavoriteDua.objects.filter(user=self.request.user).values_list("dua_id", flat=True))
            if self.request.user.is_authenticated
            else set()
        )
        return context


class ToggleFavoriteDuaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from .models import Dua

        dua = get_object_or_404(Dua, pk=pk)
        favorite, created = FavoriteDua.objects.get_or_create(user=request.user, dua=dua)
        if created:
            messages.success(request, "Dua ajoutee aux favoris.")
        else:
            favorite.delete()
            messages.info(request, "Dua retiree des favoris.")
        return redirect(request.META.get("HTTP_REFERER") or "users:duas")


class RamadanTrackerView(LoginRequiredMixin, TemplateView):
    template_name = "users/ramadan.html"

    def get_context_data(self, **kwargs):
        ensure_initial_content()
        context = super().get_context_data(**kwargs)
        today_hijri = get_today_hijri() or {"hijri_month_number": 9, "hijri": {"year": 1447}}
        hijri_year = int(today_hijri.get("hijri", {}).get("year") or 1447)
        logs = get_or_create_ramadan_log(self.request.user, hijri_year)
        context["ramadan_logs"] = logs
        context["hijri_year"] = hijri_year
        context["daily_dua"] = get_daily_dua()
        context["recommended_surah"] = (today_hijri.get("hijri_day") or 1, ["Yasin", "Al-Mulk", "Ar-Rahman"][timezone.localdate().day % 3])
        context["iftar_time"] = "19:00"
        context["suhoor_time"] = "05:00"
        return context

    def post(self, request, *args, **kwargs):
        today_hijri = get_today_hijri() or {"hijri": {"year": 1447}}
        hijri_year = int(today_hijri.get("hijri", {}).get("year") or 1447)
        day_number = int(request.POST.get("day_number", 0))
        status = request.POST.get("status", "unknown")
        log = get_object_or_404(RamadanDayLog, user=request.user, hijri_year=hijri_year, day_number=day_number)
        log.status = status
        log.save(update_fields=["status", "updated_at"])
        messages.success(request, "Jour de Ramadan mis a jour.")
        return redirect("users:ramadan")


class HistoryView(TemplateView):
    template_name = "users/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        history_items = []
        for index, (section, title, description) in enumerate(HISTORY_TIMELINE, start=1):
            history_items.append({"index": index, "section": section, "title": title, "description": description})
        quiz_pool = [
            {"question": "Quel prophete est associe a la patience exemplaire ?", "answer": "Ayyub"},
            {"question": "Quel evenement marque le debut de la communaute a Madinah ?", "answer": "Hijra"},
            {"question": "Quel calife a supervise la compilation du Mushaf ?", "answer": "Uthman"},
        ]
        context["timeline"] = history_items
        context["quiz"] = random.choice(quiz_pool)
        return context


class GroupsView(LoginRequiredMixin, TemplateView):
    template_name = "users/groups.html"

    def get_context_data(self, **kwargs):
        ensure_initial_content()
        context = super().get_context_data(**kwargs)
        groups = ReadingGroup.objects.prefetch_related("memberships__user", "messages__author")
        context["groups"] = groups
        context["my_membership_ids"] = set(
            ReadingGroupMembership.objects.filter(user=self.request.user).values_list("group_id", flat=True)
        )
        return context

    def post(self, request, *args, **kwargs):
        name = (request.POST.get("name") or "").strip()
        if name:
            group = ReadingGroup.objects.create(
                name=name,
                slug=f"{name.lower().replace(' ', '-')}-{ReadingGroup.objects.count() + 1}",
                description=request.POST.get("description", ""),
                target_days=max(1, int(request.POST.get("target_days", 30))),
                creator=request.user,
            )
            ReadingGroupMembership.objects.create(group=group, user=request.user, role="leader", progress_percent=0)
            messages.success(request, "Groupe de lecture cree.")
        return redirect("users:groups")


class JoinGroupView(LoginRequiredMixin, View):
    def post(self, request, slug):
        group = get_object_or_404(ReadingGroup, slug=slug)
        membership, created = ReadingGroupMembership.objects.get_or_create(group=group, user=request.user)
        if created:
            membership.assigned_juz = group.memberships.count()
            membership.assigned_surahs = "A definir"
            membership.save()
            messages.success(request, "Vous avez rejoint le groupe.")
        else:
            messages.info(request, "Vous etes deja membre de ce groupe.")
        return redirect("users:groups")


class GroupMessageCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        from .models import GroupMessage

        group = get_object_or_404(ReadingGroup, slug=slug)
        if not group.memberships.filter(user=request.user).exists():
            messages.error(request, "Rejoignez le groupe avant d'envoyer un message.")
            return redirect("users:groups")
        content = (request.POST.get("content") or "").strip()
        if content:
            GroupMessage.objects.create(group=group, author=request.user, content=content)
            messages.success(request, "Message ajoute au chat du groupe.")
        return redirect("users:groups")


class ChallengesView(TemplateView):
    template_name = "users/challenges.html"

    def get_context_data(self, **kwargs):
        ensure_initial_content()
        context = super().get_context_data(**kwargs)
        context["challenges"] = [
            {
                "challenge": challenge,
                "leaders": challenge.participants.select_related("user")[:10],
            }
            for challenge in get_active_challenges()
        ]
        context["global_counter"] = get_global_verse_counter()
        return context


class PublicProfileView(TemplateView):
    template_name = "users/public_profile.html"

    def dispatch(self, request, *args, **kwargs):
        self.profile_user = get_object_or_404(User, username=kwargs["username"])
        if (
            hasattr(self.profile_user, "userprofile")
            and self.profile_user.userprofile.is_private
            and request.user != self.profile_user
        ):
            messages.error(request, "Ce profil est prive.")
            return redirect("community:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = self.profile_user
        context["summary"] = get_profile_summary(self.profile_user)
        context["recent_posts"] = ForumPost.objects.filter(author=self.profile_user).select_related("category")[:6]
        context["is_following"] = (
            self.request.user.is_authenticated
            and UserFollow.objects.filter(follower=self.request.user, following=self.profile_user).exists()
        )
        return context


class ToggleFollowView(LoginRequiredMixin, View):
    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            messages.error(request, "Vous ne pouvez pas vous suivre vous-meme.")
            return redirect("users:public_profile", username=username)
        follow, created = UserFollow.objects.get_or_create(follower=request.user, following=target)
        if created:
            messages.success(request, f"Vous suivez maintenant {target.username}.")
        else:
            follow.delete()
            messages.info(request, f"Vous ne suivez plus {target.username}.")
        return redirect("users:public_profile", username=username)
