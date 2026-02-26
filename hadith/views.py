from datetime import date

from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView, TemplateView

from users.mixins import PremiumRequiredMixin
from .models import Hadith


class HadithOfDayView(TemplateView):
    template_name = "hadith/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        hadith = Hadith.objects.filter(display_date=today).first()
        if not hadith:
            all_hadith = list(Hadith.objects.all())
            if all_hadith:
                hadith = all_hadith[today.toordinal() % len(all_hadith)]
            else:
                messages.warning(self.request, "Aucun hadith configure actuellement.")
        context["hadith"] = hadith
        return context


class HadithArchiveView(PremiumRequiredMixin, ListView):
    model = Hadith
    template_name = "hadith/archive.html"
    context_object_name = "hadiths"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(text_french__icontains=q) | Q(source__icontains=q) | Q(reference__icontains=q))
        return qs
