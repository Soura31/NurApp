from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect


class PremiumRequiredMixin(LoginRequiredMixin):
    """Mixin pour proteger les vues Premium."""

    def dispatch(self, request, *args, **kwargs):
        profile = getattr(request.user, "userprofile", None)
        if not profile or not profile.is_premium:
            messages.warning(request, "Abonnement Premium requis pour cette section.")
            return redirect("subscriptions:plans")
        return super().dispatch(request, *args, **kwargs)
