from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from .models import TasbihSession


class TasbihView(TemplateView):
    template_name = "tasbih/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["history"] = TasbihSession.objects.filter(user=self.request.user)[:20]
        else:
            context["history"] = []
        context["presets"] = [
            ("SubhanAllah", 33),
            ("Alhamdulillah", 33),
            ("AllahuAkbar", 33),
        ]
        return context


class SaveTasbihSessionView(LoginRequiredMixin, View):
    def post(self, request):
        dhikr_text = request.POST.get("dhikr_text", "SubhanAllah")
        count = int(request.POST.get("count", 0))
        target = int(request.POST.get("target", 33))
        TasbihSession.objects.create(user=request.user, dhikr_text=dhikr_text, count=count, target=target)
        messages.success(request, "Session Tasbih enregistree.")
        return redirect("tasbih:index")
