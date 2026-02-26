from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
import stripe

from .models import Plan

stripe.api_key = settings.STRIPE_SECRET_KEY


class PlanListView(TemplateView):
    template_name = "subscriptions/plans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = Plan.objects.all()
        return context


class CreateCheckoutSessionView(LoginRequiredMixin, View):
    def post(self, request, slug):
        plan = get_object_or_404(Plan, slug=slug)
        cycle = request.POST.get("billing_cycle", "monthly")
        price_id = plan.stripe_price_id_monthly if cycle == "monthly" else plan.stripe_price_id_yearly

        if not price_id:
            messages.error(request, "Prix Stripe non configure pour ce plan.")
            return redirect("subscriptions:plans")

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="subscription",
                customer_email=request.user.email,
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=request.build_absolute_uri(reverse("payments:success")),
                cancel_url=request.build_absolute_uri(reverse("payments:cancel")),
                metadata={"user_id": request.user.id, "plan_slug": plan.slug, "billing_cycle": cycle},
            )
            return redirect(session.url, code=303)
        except Exception:
            messages.error(request, "Impossible de demarrer le paiement pour le moment.")
            return redirect("subscriptions:plans")


class CustomerPortalView(LoginRequiredMixin, View):
    def post(self, request):
        profile = getattr(request.user, "userprofile", None)
        if not profile or not profile.stripe_customer_id:
            messages.error(request, "Aucun client Stripe associe a ce compte.")
            return redirect("dashboard:subscription")

        try:
            session = stripe.billing_portal.Session.create(
                customer=profile.stripe_customer_id,
                return_url=request.build_absolute_uri(reverse("dashboard:subscription")),
            )
            return redirect(session.url, code=303)
        except Exception:
            messages.error(request, "Portail client indisponible.")
            return redirect("dashboard:subscription")
