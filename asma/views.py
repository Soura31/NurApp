import random

from django.contrib import messages
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from users.mixins import PremiumRequiredMixin
from .models import AsmaName


class AsmaListView(ListView):
    model = AsmaName
    template_name = "asma/list.html"
    context_object_name = "names"


class AsmaDetailView(DetailView):
    model = AsmaName
    template_name = "asma/detail.html"
    context_object_name = "asma"


class AsmaQuizView(PremiumRequiredMixin, TemplateView):
    template_name = "asma/quiz.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
            return self.get_redirect()
        if answer in {asma.transliteration.lower(), asma.meaning.lower()}:
            messages.success(request, "Bonne reponse.")
        else:
            messages.warning(request, f"Reponse attendue: {asma.transliteration} - {asma.meaning}")
        return self.get_redirect()

    def get_redirect(self):
        from django.shortcuts import redirect

        return redirect("asma:quiz")
