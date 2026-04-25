from datetime import date, timedelta
from pathlib import Path
import re
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView
import requests

from users.mixins import PremiumRequiredMixin

from .models import Bookmark, Favorite, HifzAssignment, HifzPlan, RecitationAttempt
from .reciters_catalog import RECITERS_CATALOG
from .services import (
    compute_recitation_feedback,
    fetch_chapter_map,
    fetch_chapters,
    get_or_create_reading_progress,
    get_progress_snapshot,
    get_read_surah_ids,
    mark_surah_read,
    render_tajweed_html,
    strip_html,
    unmark_surah_read,
)

FREE_RECITERS = {"7": "Al-Afasy", "1": "Husary"}
ARABIC_DIGITS_TRANS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
ALQURAN_API_BASE = "https://api.alquran.cloud/v1"
FRENCH_SEARCH_EDITION = "fr.hamidullah"
TRANSLITERATION_SEARCH_EDITION = "en.transliteration"
ARABIC_EDITION = "quran-uthmani"
TAFSIR_EDITIONS = {
    "ibn-kathir": {"label": "Ibn Kathir", "edition": "en.ibn-kathir"},
    "jalalayn": {"label": "Jalalayn", "edition": "en.jalalayn"},
}


def build_simple_explanation(translation_text: str, tafsir_text: str) -> str:
    translation = strip_html(translation_text)
    tafsir = strip_html(tafsir_text)
    if tafsir:
        summary = tafsir.split(". ")[0].strip()
        if summary and len(summary) > 220:
            summary = summary[:217].rstrip() + "..."
        if summary:
            return f"En termes simples : {translation}\n\nPoint cle : {summary}"
    if translation:
        return f"En termes simples : {translation}"
    return "Aucune explication simple n'est disponible pour ce verset."


def to_arabic_digits(value):
    if value is None:
        return ""
    return str(value).translate(ARABIC_DIGITS_TRANS)


class QuranListView(TemplateView):
    template_name = "quran/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chapters = fetch_chapters()
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

        context.update(
            {
                "chapters": filtered,
                "q": q,
                "revelation_place": place,
                "read_surah_ids": get_read_surah_ids(self.request.user),
            }
        )
        return context


class QuranSearchApiView(View):
    @staticmethod
    def _is_arabic_query(query: str) -> bool:
        return bool(re.search(r"[\u0600-\u06FF]", query))

    def _fetch_ayah_details(self, reference: str):
        cache_key = f"alquran_search_ayah_{reference}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            response = requests.get(
                f"{ALQURAN_API_BASE}/ayah/{reference}/editions/quran-uthmani,{TRANSLITERATION_SEARCH_EDITION},{FRENCH_SEARCH_EDITION}",
                timeout=12,
            )
            response.raise_for_status()
            editions = response.json().get("data", [])
        except Exception:
            return None

        arabic = next((item for item in editions if item.get("edition", {}).get("identifier") == "quran-uthmani"), {})
        transliteration = next(
            (item for item in editions if item.get("edition", {}).get("identifier") == TRANSLITERATION_SEARCH_EDITION),
            {},
        )
        french = next((item for item in editions if item.get("edition", {}).get("identifier") == FRENCH_SEARCH_EDITION), {})
        if not arabic:
            return None

        result = {
            "surah_number": arabic.get("surah", {}).get("number"),
            "surah_name": arabic.get("surah", {}).get("englishName"),
            "surah_name_ar": arabic.get("surah", {}).get("name"),
            "ayah_number": arabic.get("numberInSurah"),
            "verse_key": f"{arabic.get('surah', {}).get('number')}:{arabic.get('numberInSurah')}",
            "arabic_text": strip_html(arabic.get("text", "")),
            "transliteration": strip_html(transliteration.get("text", "")),
            "translation_fr": strip_html(french.get("text", "")),
            "url": f"/quran/{arabic.get('surah', {}).get('number')}/#ayah-{arabic.get('numberInSurah')}",
        }
        cache.set(cache_key, result, 43200)
        return result

    def _search_keyword(self, query: str):
        edition = "quran-uthmani" if self._is_arabic_query(query) else "fr"
        cache_key = f"alquran_search_keyword_{edition}_{query.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = requests.get(f"{ALQURAN_API_BASE}/search/{quote(query)}/all/{edition}", timeout=12)
            response.raise_for_status()
            matches = response.json().get("data", {}).get("matches", [])
        except Exception:
            return []

        references = []
        for match in matches:
            surah_number = match.get("surah", {}).get("number")
            ayah_number = match.get("numberInSurah")
            if surah_number and ayah_number:
                ref = f"{surah_number}:{ayah_number}"
                if ref not in references:
                    references.append(ref)
            if len(references) >= 8:
                break
        results = [self._fetch_ayah_details(ref) for ref in references]
        results = [item for item in results if item]
        cache.set(cache_key, results, 1800)
        return results

    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            return JsonResponse({"results": []})

        reference_match = re.fullmatch(r"(?P<surah>\d{1,3})(?::(?P<ayah>\d{1,3}))?", query)
        if reference_match:
            surah_number = int(reference_match.group("surah"))
            ayah_number = reference_match.group("ayah")
            if 1 <= surah_number <= 114:
                reference = f"{surah_number}:{ayah_number or 1}"
                result = self._fetch_ayah_details(reference)
                return JsonResponse({"results": [result] if result else []})
            return JsonResponse({"results": []})

        return JsonResponse({"results": self._search_keyword(query)})


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
            reciters.append({"name": item["name"], "country": item["country"], "avatar": local_avatar})
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

    def _fetch_surah_meta(self, surah_number: int):
        surah_cache_key = f"surah_{surah_number}"
        surah_data = cache.get(surah_cache_key)
        if surah_data:
            return surah_data
        try:
            response = requests.get(f"{settings.QURAN_API_BASE}/chapters/{surah_number}", timeout=10)
            response.raise_for_status()
            surah_data = response.json().get("chapter", {})
        except Exception:
            surah_data = fetch_chapter_map().get(surah_number, {})
        cache.set(surah_cache_key, surah_data, 86400)
        return surah_data

    def _fetch_surah_verses(self, surah_number: int):
        verses_cache_key = f"verses_{surah_number}_v3"
        verses = cache.get(verses_cache_key)
        if verses:
            return verses
        try:
            response = requests.get(
                f"{settings.QURAN_API_BASE}/verses/by_chapter/{surah_number}",
                params={
                    "per_page": "300",
                    "fields": "text_uthmani,text_uthmani_tajweed,verse_number,verse_key,juz_number,hizb_number,page_number",
                    "translations": "136",
                    "audio": "7",
                },
                timeout=15,
            )
            response.raise_for_status()
            verses = response.json().get("verses", [])
        except Exception:
            verses = []
        if verses:
            cache.set(verses_cache_key, verses, 21600)
        return verses

    def _fetch_surah_support_editions(self, surah_number: int):
        cache_key = f"surah_support_editions_{surah_number}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            response = requests.get(
                f"{ALQURAN_API_BASE}/surah/{surah_number}/editions/{TRANSLITERATION_SEARCH_EDITION},{FRENCH_SEARCH_EDITION}",
                timeout=12,
            )
            response.raise_for_status()
            data = response.json().get("data", [])
        except Exception:
            return {}

        transliteration_map = {}
        translation_map = {}
        for edition in data:
            identifier = edition.get("edition", {}).get("identifier")
            for ayah in edition.get("ayahs", []):
                number_in_surah = ayah.get("numberInSurah")
                if identifier == TRANSLITERATION_SEARCH_EDITION:
                    transliteration_map[number_in_surah] = strip_html(ayah.get("text", ""))
                elif identifier == FRENCH_SEARCH_EDITION:
                    translation_map[number_in_surah] = strip_html(ayah.get("text", ""))

        payload = {
            "transliteration_map": transliteration_map,
            "translation_map": translation_map,
        }
        cache.set(cache_key, payload, 21600)
        return payload

    def get(self, request, surah_number: int):
        surah_data = self._fetch_surah_meta(surah_number)
        verses = self._fetch_surah_verses(surah_number)
        support_editions = self._fetch_surah_support_editions(surah_number)
        transliteration_map = support_editions.get("transliteration_map", {})
        translation_map = support_editions.get("translation_map", {})

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
            translations = verse.get("translations") or []
            verse_number = verse.get("verse_number")
            verse["translation_fr"] = (
                strip_html(translations[0].get("text", "")) if translations else translation_map.get(verse_number, "")
            )
            verse["transliteration"] = transliteration_map.get(verse_number, "")
            verse["tajweed_html"] = render_tajweed_html(verse.get("text_uthmani_tajweed", ""))

        progress_snapshot = get_progress_snapshot(request.user)
        context = {
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
            "tafisir_options": TAFSIR_EDITIONS,
            "read_surah_ids": progress_snapshot["read_surah_ids"],
            "is_read_surah": surah_number in progress_snapshot["read_surah_ids"],
        }
        return render(request, self.template_name, context)


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
        except Exception:
            reciters = [{"id": k, "reciter_name": v} for k, v in FREE_RECITERS.items()]
        cache.set(cache_key, reciters, 86400)
        return reciters

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
            chapter_map = {chapter_id: chapter.get("name_arabic", "") for chapter_id, chapter in fetch_chapter_map().items()}
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


class ToggleReadSurahView(LoginRequiredMixin, View):
    def post(self, request):
        surah_number = int(request.POST.get("surah_number", 0))
        surah_name = request.POST.get("surah_name", "")
        surah_name_ar = request.POST.get("surah_name_ar", "")
        verses_count = int(request.POST.get("verses_count", 0))
        action = request.POST.get("action", "toggle")
        if not surah_number:
            raise Http404

        progress = get_or_create_reading_progress(request.user)
        existing = progress.read_surahs.filter(surah_number=surah_number).first()
        if existing and action != "mark":
            unmark_surah_read(request.user, surah_number)
            marked = False
        else:
            mark_surah_read(request.user, surah_number, surah_name, surah_name_ar, verses_count)
            marked = True

        snapshot = get_progress_snapshot(request.user)
        return JsonResponse(
            {
                "marked": marked,
                "read_surah_count": snapshot["read_surah_count"],
                "surah_percent": snapshot["surah_percent"],
                "read_verses": snapshot["read_verses"],
                "verse_percent": snapshot["verse_percent"],
                "is_completed": snapshot["is_completed"],
            }
        )


class ResetKhatamTrackerView(LoginRequiredMixin, View):
    def post(self, request):
        progress = get_or_create_reading_progress(request.user)
        progress.read_surahs.all().delete()
        progress.completed_at = None
        progress.reset_count += 1
        progress.started_at = date.today()
        progress.save(update_fields=["completed_at", "reset_count", "started_at"])
        messages.success(request, "La progression Coran a ete reinitialisee.")
        return redirect("dashboard:home")


class UpdateKhatamGoalView(LoginRequiredMixin, View):
    def post(self, request):
        progress = get_or_create_reading_progress(request.user)
        progress.goal_days = max(1, int(request.POST.get("goal_days", 30)))
        progress.reminder_enabled = bool(request.POST.get("reminder_enabled"))
        progress.save(update_fields=["goal_days", "reminder_enabled"])
        messages.success(request, "Objectif Khatam mis a jour.")
        return redirect("dashboard:home")


class TafsirApiView(View):
    def get(self, request):
        reference = request.GET.get("reference", "").strip()
        tafsir_key = request.GET.get("edition", "ibn-kathir").strip()
        config = TAFSIR_EDITIONS.get(tafsir_key, TAFSIR_EDITIONS["ibn-kathir"])
        if not reference:
            return JsonResponse({"error": "reference manquante"}, status=400)

        cache_key = f"tafsir_{reference}_{config['edition']}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        try:
            response = requests.get(
                f"{ALQURAN_API_BASE}/ayah/{reference}/editions/{ARABIC_EDITION},{config['edition']},{FRENCH_SEARCH_EDITION}",
                timeout=12,
            )
            response.raise_for_status()
            data = response.json().get("data", [])
        except Exception:
            return JsonResponse({"error": "tafsir indisponible"}, status=502)

        arabic = next((item for item in data if item.get("edition", {}).get("identifier") == ARABIC_EDITION), {})
        tafsir = next((item for item in data if item.get("edition", {}).get("identifier") == config["edition"]), {})
        french = next((item for item in data if item.get("edition", {}).get("identifier") == FRENCH_SEARCH_EDITION), {})
        translation_text = strip_html(french.get("text", ""))
        tafsir_text = strip_html(tafsir.get("text", ""))
        payload = {
            "reference": reference,
            "label": config["label"],
            "arabic_text": strip_html(arabic.get("text", "")),
            "translation_fr": translation_text,
            "tafsir_text": tafsir_text,
            "simple_text": build_simple_explanation(translation_text, tafsir_text),
        }
        cache.set(cache_key, payload, 43200)
        return JsonResponse(payload)


class WordByWordApiView(View):
    def get(self, request):
        reference = request.GET.get("reference", "").strip()
        if not re.fullmatch(r"\d{1,3}:\d{1,3}", reference):
            return JsonResponse({"error": "reference invalide"}, status=400)

        cache_key = f"word_by_word_{reference}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        try:
            response = requests.get(
                f"{settings.QURAN_API_BASE}/verses/by_key/{reference}",
                params={
                    "words": "true",
                    "language": "fr",
                    "word_fields": "text_uthmani,location,audio_url,char_type_name",
                    "translation_fields": "text,language_name",
                },
                timeout=15,
            )
            response.raise_for_status()
            verse = response.json().get("verse", {})
        except Exception:
            return JsonResponse({"error": "mot-a-mot indisponible"}, status=502)

        words = []
        for item in verse.get("words", []):
            if item.get("char_type_name") != "word":
                continue
            translation = item.get("translation") or {}
            transliteration = item.get("transliteration") or {}
            words.append(
                {
                    "position": item.get("position") or item.get("location"),
                    "text": item.get("text_uthmani", ""),
                    "translation": translation.get("text", ""),
                    "transliteration": transliteration.get("text", ""),
                    "audio_url": item.get("audio_url", ""),
                    "root": item.get("root", "") or "Racine indisponible",
                }
            )

        payload = {"reference": reference, "words": words}
        cache.set(cache_key, payload, 21600)
        return JsonResponse(payload)


class RecitationAnalyzeView(LoginRequiredMixin, View):
    def post(self, request):
        if not settings.OPENAI_API_KEY:
            return JsonResponse({"error": "OPENAI_API_KEY manquant"}, status=503)

        audio = request.FILES.get("audio")
        verse_key = request.POST.get("verse_key", "")
        surah_number = int(request.POST.get("surah_number", 0))
        ayah_number = int(request.POST.get("ayah_number", 0))
        reference_text = request.POST.get("reference_text", "")
        if not audio or not verse_key or not reference_text:
            return JsonResponse({"error": "donnees manquantes"}, status=400)

        try:
            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                data={
                    "model": settings.OPENAI_TRANSCRIBE_MODEL,
                    "language": "ar",
                    "response_format": "json",
                },
                files={"file": (audio.name, audio.read(), audio.content_type or "audio/webm")},
                timeout=90,
            )
            response.raise_for_status()
            transcript = response.json().get("text", "")
        except Exception:
            return JsonResponse({"error": "transcription indisponible"}, status=502)

        result = compute_recitation_feedback(reference_text, transcript)
        RecitationAttempt.objects.create(
            user=request.user,
            surah_number=surah_number,
            ayah_number=ayah_number,
            verse_key=verse_key,
            transcript=transcript,
            score=result["score"],
            mistakes=result["mistakes"],
            feedback=result["feedback"],
        )
        return JsonResponse({"transcript": transcript, **result})


class HifzView(LoginRequiredMixin, TemplateView):
    template_name = "quran/hifz.html"

    def _fetch_hifz_verses(self, surah_number: int, start_ayah: int, end_ayah: int):
        try:
            response = requests.get(
                f"{settings.QURAN_API_BASE}/verses/by_chapter/{surah_number}",
                params={"per_page": "300", "fields": "text_uthmani,verse_number,verse_key", "audio": "7"},
                timeout=15,
            )
            response.raise_for_status()
            verses = response.json().get("verses", [])
        except Exception:
            return []
        return [verse for verse in verses if start_ayah <= int(verse.get("verse_number", 0)) <= end_ayah]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chapters = fetch_chapters()
        plan, _ = HifzPlan.objects.get_or_create(user=self.request.user)
        assignments = list(HifzAssignment.objects.filter(user=self.request.user)[:12])

        selected_surah = int(self.request.GET.get("surah", assignments[0].surah_number if assignments else 1))
        selected_start = int(self.request.GET.get("start", assignments[0].start_ayah if assignments else 1))
        selected_end = int(self.request.GET.get("end", assignments[0].end_ayah if assignments else 7))
        selected_end = max(selected_start, selected_end)
        verses = self._fetch_hifz_verses(selected_surah, selected_start, selected_end)

        context.update(
            {
                "chapters": chapters,
                "plan": plan,
                "assignments": assignments,
                "selected_surah": selected_surah,
                "selected_start": selected_start,
                "selected_end": selected_end,
                "selected_verses": verses,
            }
        )
        return context


class HifzCreateAssignmentView(LoginRequiredMixin, View):
    def post(self, request):
        surah_number = int(request.POST.get("surah_number", 0))
        start_ayah = int(request.POST.get("start_ayah", 1))
        end_ayah = int(request.POST.get("end_ayah", start_ayah))
        repetition_target = int(request.POST.get("repetition_target", 5))
        verses_per_day = int(request.POST.get("verses_per_day", 3))
        if not surah_number:
            raise Http404

        chapter = fetch_chapter_map().get(surah_number, {})
        HifzAssignment.objects.create(
            user=request.user,
            surah_number=surah_number,
            surah_name=chapter.get("name_simple") or chapter.get("translated_name", {}).get("name", ""),
            start_ayah=start_ayah,
            end_ayah=end_ayah,
            repetition_target=repetition_target,
            next_review_at=date.today(),
        )
        plan, _ = HifzPlan.objects.get_or_create(user=request.user)
        plan.verses_per_day = verses_per_day
        plan.repetition_target = repetition_target
        plan.save(update_fields=["verses_per_day", "repetition_target", "updated_at"])
        messages.success(request, "Plan Hifz ajoute.")
        return redirect(f"/hifz/?surah={surah_number}&start={start_ayah}&end={end_ayah}")


class HifzUpdateAssignmentView(LoginRequiredMixin, View):
    def post(self, request):
        assignment = HifzAssignment.objects.filter(user=request.user, id=request.POST.get("assignment_id")).first()
        if not assignment:
            raise Http404
        action = request.POST.get("action", "repeat")
        if action == "repeat":
            assignment.repetition_done = min(assignment.repetition_target, assignment.repetition_done + 1)
            if assignment.repetition_done >= assignment.repetition_target:
                assignment.is_mastered = True
                assignment.next_review_at = date.today() + timedelta(days=max(1, assignment.difficulty * 2))
        elif action == "difficult":
            assignment.difficulty = min(5, assignment.difficulty + 1)
            assignment.next_review_at = date.today() + timedelta(days=1)
        elif action == "reset":
            assignment.repetition_done = 0
            assignment.is_mastered = False
            assignment.next_review_at = date.today()
        assignment.save()
        return JsonResponse(
            {
                "repetition_done": assignment.repetition_done,
                "repetition_target": assignment.repetition_target,
                "is_mastered": assignment.is_mastered,
                "difficulty": assignment.difficulty,
            }
        )


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
