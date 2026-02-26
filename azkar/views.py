from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from .models import AzkarCategory, Zikr, ZikrCounter


class AzkarCategoryListView(ListView):
    model = AzkarCategory
    template_name = "azkar/list.html"
    context_object_name = "categories"

    def get_queryset(self):
        # Initialise des categories/azkar de base pour eviter une page vide.
        if not AzkarCategory.objects.exists():
            matin = AzkarCategory.objects.create(name="Matin", slug="matin")
            soir = AzkarCategory.objects.create(name="Soir", slug="soir")
            Zikr.objects.create(
                category=matin,
                text_arabic="أَصْـبَحْنا وَأَصْـبَحَ المـلكُ لله",
                transliteration="Asbahna wa asbahal-mulku lillah",
                translation="Nous entrons dans la matinee et la royaute appartient a Allah.",
                repetitions=1,
            )
            Zikr.objects.create(
                category=soir,
                text_arabic="أَمْسَيْنا وَأَمْسَى المـلكُ لله",
                transliteration="Amsayna wa amsal-mulku lillah",
                translation="Nous entrons dans la soiree et la royaute appartient a Allah.",
                repetitions=1,
            )
        return AzkarCategory.objects.all()


class AzkarListView(DetailView):
    model = AzkarCategory
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "azkar/list.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_premium = user.is_authenticated and hasattr(user, "userprofile") and user.userprofile.is_premium
        azkar = self.object.azkar.all()
        if not is_premium:
            azkar = azkar.exclude(is_premium_audio=True)
        context["azkar"] = azkar
        context["is_premium"] = is_premium
        return context


class ZikrCounterUpdateView(LoginRequiredMixin, View):
    def post(self, request, zikr_id):
        zikr = get_object_or_404(Zikr, id=zikr_id)
        obj, _ = ZikrCounter.objects.get_or_create(user=request.user, zikr=zikr)
        obj.count += int(request.POST.get("increment", 1))
        obj.save()
        messages.success(request, "Compteur mis a jour.")
        return redirect(request.META.get("HTTP_REFERER", "azkar:categories"))
