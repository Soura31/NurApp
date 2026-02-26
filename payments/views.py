import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import stripe

from .models import Payment
from subscriptions.models import Plan

stripe.api_key = settings.STRIPE_SECRET_KEY


def _find_plan_by_price(price_id: str):
    return Plan.objects.filter(stripe_price_id_monthly=price_id).first() or Plan.objects.filter(
        stripe_price_id_yearly=price_id
    ).first()


class PaymentSuccessView(View):
    def get(self, request):
        messages.success(request, "Paiement confirme. Bienvenue dans l'experience premium.")
        return redirect("dashboard:home")


class PaymentCancelView(View):
    def get(self, request):
        messages.warning(request, "Paiement annule.")
        return redirect("subscriptions:plans")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
        except Exception:
            return HttpResponse(status=400)

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        # Mise a jour des abonnements selon les evenements Stripe.
        if event_type == "checkout.session.completed":
            user_id = data.get("metadata", {}).get("user_id")
            customer = data.get("customer")
            subscription_id = data.get("subscription")
            User = get_user_model()
            user = User.objects.filter(id=user_id).first()
            if user and hasattr(user, "userprofile"):
                profile = user.userprofile
                profile.stripe_customer_id = customer or ""
                profile.subscription_status = "active"
                if subscription_id:
                    try:
                        sub = stripe.Subscription.retrieve(subscription_id)
                        items = sub.get("items", {}).get("data", [])
                        if items:
                            price_id = items[0].get("price", {}).get("id")
                            plan = _find_plan_by_price(price_id)
                            if plan:
                                profile.plan = plan
                    except Exception:
                        pass
                profile.save()

        elif event_type == "customer.subscription.updated":
            customer = data.get("customer")
            status = data.get("status", "inactive")
            profile = get_user_model().objects.filter(userprofile__stripe_customer_id=customer).first()
            if profile and hasattr(profile, "userprofile"):
                profile = profile.userprofile
                profile.subscription_status = status if status in {"active", "trialing", "canceled"} else "inactive"
                items = data.get("items", {}).get("data", [])
                if items:
                    price_id = items[0].get("price", {}).get("id")
                    plan = _find_plan_by_price(price_id)
                    if plan:
                        profile.plan = plan
                profile.save()

        elif event_type == "customer.subscription.deleted":
            customer = data.get("customer")
            user = get_user_model().objects.filter(userprofile__stripe_customer_id=customer).first()
            if user and hasattr(user, "userprofile"):
                user.userprofile.subscription_status = "canceled"
                user.userprofile.save()

        elif event_type == "invoice.payment_failed":
            customer = data.get("customer")
            user = get_user_model().objects.filter(userprofile__stripe_customer_id=customer).first()
            if user:
                Payment.objects.create(
                    user=user,
                    amount=data.get("amount_due", 0),  # XOF zero-decimal.
                    currency=data.get("currency", "xof"),
                    stripe_payment_id=data.get("id", ""),
                    status="failed",
                )

        elif event_type == "invoice.paid":
            customer = data.get("customer")
            user = get_user_model().objects.filter(userprofile__stripe_customer_id=customer).first()
            if user:
                Payment.objects.create(
                    user=user,
                    amount=data.get("amount_paid", 0),  # Pas de *100 pour XOF.
                    currency=data.get("currency", "xof"),
                    stripe_payment_id=data.get("id", ""),
                    status="succeeded",
                )

        return JsonResponse({"status": "ok"})
