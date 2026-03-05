from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView
import requests
from pathlib import Path
import re

from users.mixins import PremiumRequiredMixin
from .models import Bookmark, Favorite
from .reciters_catalog import RECITERS_CATALOG

FREE_TRANSLATIONS = {
    "fr": "20",  # Francais
    "en": "131",  # English
    "ar": "203",  # Arabe simplifie
}
FREE_RECITERS = {"7": "Al-Afasy", "1": "Husary"}
ARABIC_DIGITS_TRANS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def to_arabic_digits(value):
    if value is None:
        return ""
    return str(value).translate(ARABIC_DIGITS_TRANS)


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
                chapter["id_ar"] = to_arabic_digits(chapter.get("id", ""))
                chapter["verses_count_ar"] = to_arabic_digits(chapter.get("verses_count", ""))
                filtered.append(chapter)

        context.update({"chapters": filtered, "q": q, "revelation_place": place})
        return context


class QuranRecitersView(TemplateView):
    template_name = "quran/reciters.html"

    @staticmethod
    def _slugify(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        avatars_dir = Path(settings.BASE_DIR) / "static" / "images" / "reciters"
        reciters = []
        for item in RECITERS_CATALOG:
            slug = self._slugify(item["name"])
            local_avatar = None
            for ext in ("jpg", "jpeg", "png", "webp"):
                candidate = avatars_dir / f"{slug}.{ext}"
                if candidate.exists():
                    local_avatar = f"/static/images/reciters/{slug}.{ext}"
                    break
            if not local_avatar:
                local_avatar = "/static/images/reciters/placeholder.svg"
            reciters.append(
                {
                    "name": item["name"],
                    "country": item["country"],
                    "avatar": local_avatar,
                }
            )
        context["reciters"] = reciters
        return context


class QuranLanguagesView(TemplateView):
    template_name = "quran/languages.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["languages"] = [
            "Arabe",
            "Francais",
            "Anglais",
            "Espagnol",
            "Allemand",
            "Italien",
            "Portugais",
            "Turc",
            "Ourdou",
            "Persan",
            "Malais",
            "Indonesien",
            "Bengali",
            "Hindi",
            "Russe",
            "Swahili",
            "Hausa",
            "Tamoul",
            "Chinois",
            "Japonais",
        ]
        return context


class SurahDetailView(View):
    template_name = "quran/detail.html"

    def get(self, request, surah_number: int):
        surah_cache_key = f"surah_{surah_number}"
        surah_data = cache.get(surah_cache_key)
        if not surah_data:
            try:
                response = requests.get(f"{settings.QURAN_API_BASE}/chapters/{surah_number}", timeout=10)
                response.raise_for_status()
                surah_data = response.json().get("chapter", {})
                cache.set(surah_cache_key, surah_data, 86400)
            except Exception:
                surah_data = {}

        verses_cache_key = f"verses_{surah_number}_v2"
        verses = cache.get(verses_cache_key)
        if not verses:
            try:
                response = requests.get(
                    f"{settings.QURAN_API_BASE}/verses/by_chapter/{surah_number}",
                    params={
                        "per_page": "300",
                        "fields": "text_uthmani,verse_number,verse_key,juz_number,hizb_number,page_number",
                        "translations": "136",
                        "audio": "7",
                    },
                    timeout=15,
                )
                response.raise_for_status()
                verses = response.json().get("verses", [])
                if verses:
                    cache.set(verses_cache_key, verses, 21600)
            except Exception:
                verses = []

        if surah_number != 9 and verses:
            first_text = (verses[0].get("text_uthmani") or "").strip()
            if "بِسْمِ" in first_text:
                verses = verses[1:]

        first_verse = verses[0] if verses else {}
        hizb = first_verse.get("hizb_number", "-")
        juz = first_verse.get("juz_number", "-")
        page_number = first_verse.get("page_number", "-")
        for index, verse in enumerate(verses, start=1):
            verse["verse_number_ar"] = to_arabic_digits(verse.get("verse_number", ""))
            verse["display_number"] = index
            verse["display_number_ar"] = to_arabic_digits(index)

        return render(
            request,
            self.template_name,
            {
                "surah": surah_data,
                "chapter": surah_data,
                "verses": verses,
                "surah_number": surah_number,
                "hizb": hizb,
                "hizb_ar": to_arabic_digits(hizb),
                "juz": juz,
                "juz_ar": to_arabic_digits(juz),
                "page_number": page_number,
                "page_number_ar": to_arabic_digits(page_number),
                "prev_surah": surah_number - 1 if surah_number > 1 else None,
                "next_surah": surah_number + 1 if surah_number < 114 else None,
            },
        )


class QuranPageView(TemplateView):
    template_name = "quran/page.html"

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

    def _get_page_verses(self, page_number: int, selected_reciter: str):
        cache_key = f"quran_page_arabic_{page_number}_{selected_reciter}"
        verses = cache.get(cache_key)
        if verses:
            return verses
        response = requests.get(
            f"{settings.QURAN_API_BASE}/verses/by_page/{page_number}",
            params={"audio": selected_reciter, "per_page": 50},
            timeout=12,
        )
        response.raise_for_status()
        verses = response.json().get("verses", [])
        for verse in verses:
            verse_key = verse.get("verse_key", "")
            if verse_key and ":" in verse_key and not verse.get("chapter_id"):
                try:
                    verse["chapter_id"] = int(verse_key.split(":")[0])
                except Exception:
                    verse["chapter_id"] = None
        cache.set(cache_key, verses, 21600)
        return verses

    def _get_chapters_map(self):
        cache_key = "quran_chapters_map"
        chapter_map = cache.get(cache_key)
        if chapter_map:
            return chapter_map
        response = requests.get(f"{settings.QURAN_API_BASE}/chapters", timeout=10)
        response.raise_for_status()
        chapters = response.json().get("chapters", [])
        chapter_map = {c.get("id"): c.get("name_arabic", "") for c in chapters}
        cache.set(cache_key, chapter_map, 86400)
        return chapter_map

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_number = int(self.kwargs["page"])
        if page_number < 1 or page_number > 604:
            raise Http404

        user = self.request.user
        is_premium = user.is_authenticated and hasattr(user, "userprofile") and user.userprofile.is_premium
        reciters = self._get_reciters(is_premium)
        selected_reciter = self.request.GET.get("reciter", "7")
        if not is_premium and selected_reciter not in FREE_RECITERS:
            selected_reciter = "7"

        verses = []
        chapter_map = {}
        try:
            verses = self._get_page_verses(page_number, selected_reciter)
            chapter_map = self._get_chapters_map()
            for verse in verses:
                chapter_id = verse.get("chapter_id")
                verse["chapter_name_arabic"] = chapter_map.get(chapter_id, "")
        except Exception:
            messages.error(self.request, "Erreur lors du chargement de la page du Coran.")

        context.update(
            {
                "page_number": page_number,
                "verses": verses,
                "reciters": reciters,
                "selected_reciter": selected_reciter,
                "prev_page": page_number - 1 if page_number > 1 else None,
                "next_page": page_number + 1 if page_number < 604 else None,
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
