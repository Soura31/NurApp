from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
import requests

from users.mixins import PremiumRequiredMixin
from .models import Bookmark, Favorite

FREE_TRANSLATIONS = {
    "fr": "20",  # Francais
    "en": "131",  # English
    "ar": "203",  # Arabe simplifie
}
FREE_RECITERS = {"7": "Al-Afasy", "1": "Husary"}


class QuranListView(TemplateView):
    template_name = "quran/list.html"

    def _fetch_chapters(self):
        cache_key = "quran_chapters"
        data = cache.get(cache_key)
        if data:
            return data
        try:
            response = requests.get(f"{settings.QURAN_API_BASE}/chapters", timeout=10)
            response.raise_for_status()
            data = response.json().get("chapters", [])
            cache.set(cache_key, data, 86400)  # 24h
            return data
        except Exception:
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chapters = self._fetch_chapters()
        q = self.request.GET.get("q", "").strip().lower()
        place = self.request.GET.get("revelation_place", "").strip().lower()

        filtered = []
        for chapter in chapters:
            name_ar = chapter.get("name_arabic", "")
            name_fr = chapter.get("translated_name", {}).get("name", "")
            match_q = not q or q in str(chapter.get("id", "")).lower() or q in name_ar.lower() or q in name_fr.lower()
            match_place = not place or chapter.get("revelation_place", "").lower() == place
            if match_q and match_place:
                filtered.append(chapter)

        context.update({"chapters": filtered, "q": q, "revelation_place": place})
        return context


class SurahDetailView(TemplateView):
    template_name = "quran/detail.html"

    def _get_translations(self, is_premium: bool):
        if not is_premium:
            return [{"id": v, "name": k.upper()} for k, v in FREE_TRANSLATIONS.items()]
        cache_key = "quran_translations"
        translations = cache.get(cache_key)
        if translations:
            return translations
        try:
            response = requests.get(f"{settings.QURAN_API_BASE}/resources/translations", timeout=10)
            response.raise_for_status()
            translations = response.json().get("translations", [])
            cache.set(cache_key, translations, 86400)
            return translations
        except Exception:
            return [{"id": v, "name": k.upper()} for k, v in FREE_TRANSLATIONS.items()]

    def _get_reciters(self, is_premium: bool):
        if not is_premium:
            return [{"id": k, "reciter_name": v} for k, v in FREE_RECITERS.items()]
        cache_key = "quran_reciters"
        reciters = cache.get(cache_key)
        if reciters:
            return reciters
        try:
            response = requests.get(f"{settings.QURAN_API_BASE}/resources/recitations", timeout=10)
            response.raise_for_status()
            reciters = response.json().get("recitations", [])
            cache.set(cache_key, reciters, 86400)
            return reciters
        except Exception:
            return [{"id": k, "reciter_name": v} for k, v in FREE_RECITERS.items()]

    def _get_chapter(self, surah_number: int):
        cache_key = f"quran_chapter_{surah_number}"
        chapter = cache.get(cache_key)
        if chapter:
            return chapter
        response = requests.get(f"{settings.QURAN_API_BASE}/chapters/{surah_number}", timeout=10)
        response.raise_for_status()
        chapter = response.json().get("chapter", {})
        cache.set(cache_key, chapter, 86400)
        return chapter

    def _get_verses(self, surah_number: int, selected_translation: str, selected_reciter: str):
        cache_key = f"quran_verses_{surah_number}_{selected_translation}_{selected_reciter}"
        verses = cache.get(cache_key)
        if verses:
            return verses
        response = requests.get(
            f"{settings.QURAN_API_BASE}/verses/by_chapter/{surah_number}",
            params={
                "language": "fr",
                "words": "true",
                "translations": selected_translation,
                "audio": selected_reciter,
                "per_page": 300,
            },
            timeout=12,
        )
        response.raise_for_status()
        verses = response.json().get("verses", [])
        cache.set(cache_key, verses, 21600)  # 6h
        return verses

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        surah_number = int(self.kwargs["number"])
        user = self.request.user
        is_premium = user.is_authenticated and hasattr(user, "userprofile") and user.userprofile.is_premium

        translations = self._get_translations(is_premium)
        reciters = self._get_reciters(is_premium)

        selected_translation = self.request.GET.get("translation", FREE_TRANSLATIONS["fr"])
        selected_reciter = self.request.GET.get("reciter", "7")
        show_translit = self.request.GET.get("translit", "1") == "1"

        if not is_premium and selected_translation not in FREE_TRANSLATIONS.values():
            selected_translation = FREE_TRANSLATIONS["fr"]
        if not is_premium and selected_reciter not in FREE_RECITERS:
            selected_reciter = "7"

        chapter = {}
        verses = []
        try:
            chapter = self._get_chapter(surah_number)
            verses = self._get_verses(surah_number, selected_translation, selected_reciter)
        except Exception:
            messages.error(self.request, "Erreur lors du chargement de la sourate.")

        context.update(
            {
                "chapter": chapter,
                "verses": verses,
                "translations": translations,
                "reciters": reciters,
                "selected_translation": selected_translation,
                "selected_reciter": selected_reciter,
                "show_translit": show_translit,
                "is_premium": is_premium,
            }
        )
        return context


class FavoriteVerseView(PremiumRequiredMixin, View):
    def post(self, request):
        surah = int(request.POST.get("surah_number", 0))
        ayah = int(request.POST.get("ayah_number", 0))
        note = request.POST.get("note", "")
        if not surah or not ayah:
            raise Http404
        Favorite.objects.get_or_create(
            user=request.user,
            surah_number=surah,
            ayah_number=ayah,
            defaults={"note": note},
        )
        messages.success(request, "Verset ajoute aux favoris.")
        return redirect(request.META.get("HTTP_REFERER", "quran:list"))


class BookmarkVerseView(PremiumRequiredMixin, View):
    def post(self, request):
        surah = int(request.POST.get("surah_number", 0))
        ayah = int(request.POST.get("ayah_number", 0))
        if not surah or not ayah:
            raise Http404
        Bookmark.objects.update_or_create(
            user=request.user,
            surah_number=surah,
            ayah_number=ayah,
            defaults={},
        )
        messages.success(request, "Position de lecture enregistree.")
        return redirect(request.META.get("HTTP_REFERER", "quran:list"))
