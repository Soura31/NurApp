import random

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from users.engagement import ensure_asma_catalog, get_daily_name_of_allah
from users.mixins import PremiumRequiredMixin

from .models import AsmaName, LearnedName


class AsmaListView(ListView):
    model = AsmaName
    template_name = "asma/list.html"
    context_object_name = "names"

    def get_queryset(self):
        ensure_asma_catalog()
        return AsmaName.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["daily_name"] = get_daily_name_of_allah()
        context["learned_ids"] = (
            set(LearnedName.objects.filter(user=self.request.user).values_list("name_id", flat=True))
            if self.request.user.is_authenticated
            else set()
        )
        return context


class AsmaDetailView(DetailView):
    model = AsmaName
    template_name = "asma/detail.html"
    context_object_name = "asma"


class AsmaQuizView(PremiumRequiredMixin, TemplateView):
    template_name = "asma/quiz.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ensure_asma_catalog()
        names = list(AsmaName.objects.all())
        context["question"] = random.choice(names) if names else None
        return context


class AsmaQuizCheckView(PremiumRequiredMixin, View):
    def post(self, request):
        asma_id = int(request.POST.get("asma_id", 0))
        answer = request.POST.get("answer", "").strip().lower()
        asma = AsmaName.objects.filter(id=asma_id).first()
        if not asma:
            messages.error(request, "Question invalide.")
            return redirect("asma:quiz")
        if answer in {asma.transliteration.lower(), asma.meaning.lower()}:
            messages.success(request, "Bonne reponse.")
        else:
            messages.warning(request, f"Reponse attendue: {asma.transliteration} - {asma.meaning}")
        return redirect("asma:quiz")


class ToggleLearnedNameView(LoginRequiredMixin, View):
    def post(self, request, pk):
        name = AsmaName.objects.filter(pk=pk).first()
        if not name:
            messages.error(request, "Nom introuvable.")
            return redirect("asma:list")
        learned, created = LearnedName.objects.get_or_create(user=request.user, name=name)
        if created:
            messages.success(request, f"{name.transliteration} ajoute a votre tracker de memorisation.")
        else:
            learned.delete()
            messages.info(request, f"{name.transliteration} retire de votre tracker.")
        return redirect("asma:list")
