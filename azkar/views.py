from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from .models import AzkarCategory, Zikr, ZikrCounter


DEFAULT_AZKAR = {
    "matin": {
        "name": "Matin",
        "items": [
            ("أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ", "Asbahna wa asbahal-mulku lillah", "Nous entrons dans la matinee et la royaute appartient a Allah.", 1),
            ("اللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا", "Allahumma bika asbahna wa bika amsayna", "O Allah, c'est par Toi que nous vivons matin et soir.", 1),
            ("رَضِيتُ بِاللَّهِ رَبًّا وَبِالإِسْلاَمِ دِينًا", "Raditu billahi rabban wa bil-islami dina", "Je suis satisfait d'Allah comme Seigneur et de l'Islam comme religion.", 3),
            ("سُبْحَانَ اللَّهِ وَبِحَمْدِهِ", "Subhanallahi wa bihamdihi", "Gloire et louange a Allah.", 100),
        ],
    },
    "soir": {
        "name": "Soir",
        "items": [
            ("أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ", "Amsayna wa amsal-mulku lillah", "Nous entrons dans la soiree et la royaute appartient a Allah.", 1),
            ("اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا", "Allahumma bika amsayna wa bika asbahna", "O Allah, c'est par Toi que nous vivons soir et matin.", 1),
            ("أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ", "A'udhu bi kalimatillahi at-tammati", "Je cherche refuge dans les paroles parfaites d'Allah.", 3),
            ("حَسْبِيَ اللَّهُ لاَ إِلَهَ إِلاَّ هُوَ", "Hasbiyallahu la ilaha illa Huwa", "Allah me suffit, nul dieu en dehors de Lui.", 7),
        ],
    },
    "apres-priere": {
        "name": "Après prière",
        "items": [
            ("أَسْتَغْفِرُ اللَّهَ", "Astaghfirullah", "Je demande pardon a Allah.", 3),
            ("اللَّهُمَّ أَنْتَ السَّلاَمُ وَمِنْكَ السَّلاَمُ", "Allahumma anta as-salam wa minka as-salam", "O Allah, Tu es la Paix et la paix vient de Toi.", 1),
            ("سُبْحَانَ اللَّهِ", "Subhanallah", "Gloire a Allah.", 33),
            ("الْحَمْدُ لِلَّهِ", "Alhamdulillah", "Louange a Allah.", 33),
            ("اللَّهُ أَكْبَرُ", "Allahu Akbar", "Allah est le Plus Grand.", 34),
        ],
    },
    "sommeil": {
        "name": "Avant de dormir",
        "items": [
            ("بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا", "Bismika Allahumma amutu wa ahya", "En Ton nom, O Allah, je meurs et je vis.", 1),
            ("اللَّهُمَّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ", "Allahumma qini 'adhabaka yawma tab'athu 'ibadak", "O Allah, protege-moi de Ton chatiment.", 1),
            ("سُبْحَانَ اللَّهِ", "Subhanallah", "Gloire a Allah.", 33),
            ("الْحَمْدُ لِلَّهِ", "Alhamdulillah", "Louange a Allah.", 33),
            ("اللَّهُ أَكْبَرُ", "Allahu Akbar", "Allah est le Plus Grand.", 34),
        ],
    },
    "reveil": {
        "name": "Réveil",
        "items": [
            ("الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا", "Alhamdulillahil-ladhi ahyana ba'da ma amatana", "Louange a Allah qui nous a redonne la vie.", 1),
            ("لاَ إِلَهَ إِلاَّ اللَّهُ وَحْدَهُ لاَ شَرِيكَ لَهُ", "La ilaha illa Allah wahdahu la sharika lah", "Nul dieu en dehors d'Allah, seul sans associe.", 1),
        ],
    },
    "voyage": {
        "name": "Voyage",
        "items": [
            ("سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا", "Subhanalladhi sakhkhara lana hadha", "Gloire a Celui qui a mis ceci a notre service.", 1),
            ("اللَّهُمَّ إِنَّا نَسْأَلُكَ فِي سَفَرِنَا هَذَا", "Allahumma inna nas'aluka fi safarina hadha", "O Allah, nous Te demandons la piete durant ce voyage.", 1),
        ],
    },
    "pluie": {
        "name": "Pluie",
        "items": [
            ("اللَّهُمَّ صَيِّبًا نَافِعًا", "Allahumma sayyiban nafi'an", "O Allah, une pluie benefique.", 1),
            ("مُطِرْنَا بِفَضْلِ اللَّهِ وَرَحْمَتِهِ", "Mutirna bifadlillahi wa rahmatih", "Nous avons recu la pluie par la grace d'Allah.", 1),
        ],
    },
    "detresse": {
        "name": "Détresse",
        "items": [
            ("لاَ إِلَهَ إِلاَّ أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ", "La ilaha illa anta subhanaka inni kuntu minaz-zalimin", "Nul dieu en dehors de Toi, j'etais parmi les injustes.", 1),
            ("حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ", "Hasbunallahu wa ni'mal wakil", "Allah nous suffit, quel excellent Protecteur.", 7),
            ("اللَّهُمَّ رَحْمَتَكَ أَرْجُو", "Allahumma rahmataka arju", "O Allah, j'espere Ta misericorde.", 1),
        ],
    },
}


def ensure_default_azkar():
    if AzkarCategory.objects.count() >= 8 and Zikr.objects.count() >= 20:
        return

    for slug, payload in DEFAULT_AZKAR.items():
        category, _ = AzkarCategory.objects.get_or_create(slug=slug, defaults={"name": payload["name"]})
        if category.name != payload["name"]:
            category.name = payload["name"]
            category.save(update_fields=["name"])

        for text_arabic, transliteration, translation, repetitions in payload["items"]:
            Zikr.objects.get_or_create(
                category=category,
                text_arabic=text_arabic,
                defaults={
                    "transliteration": transliteration,
                    "translation": translation,
                    "repetitions": repetitions,
                },
            )


class AzkarCategoryListView(ListView):
    model = AzkarCategory
    template_name = "azkar/list.html"
    context_object_name = "categories"

    def get_queryset(self):
        ensure_default_azkar()
        return AzkarCategory.objects.all()


class AzkarListView(DetailView):
    model = AzkarCategory
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "azkar/list.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ensure_default_azkar()
        user = self.request.user
        is_premium = user.is_authenticated and hasattr(user, "userprofile") and user.userprofile.is_premium
        azkar = self.object.azkar.all()
        if not is_premium:
            azkar = azkar.exclude(is_premium_audio=True)
        context["categories"] = AzkarCategory.objects.all()
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
