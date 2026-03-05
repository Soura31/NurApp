import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from .models import TasbihSession


class TasbihView(View):
    template_name = "tasbih/index.html"

    DHIKR_LIST = [
        {"name": "SubhanAllah", "arabic": "سُبْحَانَ اللَّهِ", "target": 33},
        {"name": "Alhamdulillah", "arabic": "الْحَمْدُ لِلَّهِ", "target": 33},
        {"name": "AllahuAkbar", "arabic": "اللَّهُ أَكْبَرُ", "target": 33},
    ]

    def get(self, request):
        sessions = []
        if request.user.is_authenticated:
            sessions = TasbihSession.objects.filter(user=request.user).order_by("-created_at")[:5]

        return render(
            request,
            self.template_name,
            {
                "dhikr_list": self.DHIKR_LIST,
                "sessions": sessions,
            },
        )


class SaveTasbihView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body or "{}")
            TasbihSession.objects.create(
                user=request.user,
                dhikr_text=data.get("dhikr", ""),
                count=int(data.get("count", 0)),
                target=int(data.get("target", 33)),
            )
            return JsonResponse({"status": "ok"})
        except Exception as exc:
            return JsonResponse({"status": "error", "message": str(exc)}, status=400)
