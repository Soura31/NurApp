from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum
from django.views.generic import ListView, TemplateView, UpdateView
from django.urls import reverse_lazy

from community.models import ForumPost
from payments.models import Payment
from quran.models import Bookmark, Favorite
from subscriptions.models import Plan
from tasbih.models import TasbihSession
from users.forms import ProfileForm
from hadith.models import Hadith


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["stats"] = {
            "versets_lus": Favorite.objects.filter(user=user).count(),
            "prieres_suivies": 0,
            "tasbih_total": TasbihSession.objects.filter(user=user).aggregate(total=Sum("count")).get("total") or 0,
        }
        return context


class DashboardSubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/subscription.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.request.user.userprofile
        context["plans"] = Plan.objects.all()
        return context


class DashboardFavoritesView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = "dashboard/favorites.html"
    context_object_name = "favorites"

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)


class DashboardBookmarksView(LoginRequiredMixin, ListView):
    model = Bookmark
    template_name = "dashboard/bookmarks.html"
    context_object_name = "bookmarks"

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


class DashboardInvoicesView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = "dashboard/invoices.html"
    context_object_name = "invoices"

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class DashboardProfileView(LoginRequiredMixin, UpdateView):
    template_name = "dashboard/profile.html"
    form_class = ProfileForm
    success_url = reverse_lazy("dashboard:profile")

    def get_object(self, queryset=None):
        return self.request.user.userprofile


class AdminPanelView(UserPassesTestMixin, TemplateView):
    template_name = "dashboard/admin_panel.html"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        revenue = Payment.objects.filter(status="succeeded").aggregate(total=Sum("amount")).get("total") or 0
        context["mrr"] = revenue
        context["subscribers_by_plan"] = (
            Plan.objects.annotate(total=Count("userprofile")).values("name", "total").order_by("price_monthly")
        )
        context["active_users"] = ForumPost.objects.values("author").distinct().count()
        context["reported_posts"] = ForumPost.objects.filter(is_reported=True)[:20]
        context["hadith_count"] = Hadith.objects.count()
        return context
