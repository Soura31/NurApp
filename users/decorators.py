from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def premium_required(view_func):
    @login_required
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, "userprofile", None)
        if not profile or not profile.is_premium:
            messages.warning(request, "Cette fonctionnalite est reservee aux membres Premium.")
            return redirect("subscriptions:plans")
        return view_func(request, *args, **kwargs)

    return _wrapped
