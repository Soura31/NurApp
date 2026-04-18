from __future__ import annotations

from datetime import date, timedelta
from difflib import SequenceMatcher
import re

from django.conf import settings
from django.core.cache import cache
from django.utils.html import escape
import requests

from .models import QuranReadingProgress, ReadSurah

ARABIC_DIACRITICS_PATTERN = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
TAJWEED_TAG_PATTERN = re.compile(r"<tajweed class=([^>]+)>")

TAJWEED_CLASS_MAP = {
    "ghunnah": "tajweed-ghunna",
    "ikhfa_shafawi": "tajweed-ikhfaa-shafawi",
    "ikhfa": "tajweed-ikhfaa",
    "idgham": "tajweed-idgham",
    "qalqalah": "tajweed-qalqalah",
    "madda": "tajweed-madd",
}


def fetch_chapters():
    cache_key = "quran_chapters"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        response = requests.get(f"{settings.QURAN_API_BASE}/chapters", timeout=10)
        response.raise_for_status()
        chapters = response.json().get("chapters", [])
    except Exception:
        chapters = []
    cache.set(cache_key, chapters, 86400)
    return chapters


def fetch_chapter_map():
    return {chapter.get("id"): chapter for chapter in fetch_chapters()}


def get_or_create_reading_progress(user):
    if not user.is_authenticated:
        return None
    progress, _ = QuranReadingProgress.objects.get_or_create(user=user)
    return progress


def get_read_surah_ids(user):
    progress = get_or_create_reading_progress(user)
    if not progress:
        return []
    return list(progress.read_surahs.values_list("surah_number", flat=True))


def get_progress_snapshot(user):
    progress = get_or_create_reading_progress(user)
    chapters = fetch_chapters()
    total_surahs = len(chapters) or 114
    total_verses = sum(chapter.get("verses_count", 0) for chapter in chapters) or 6236
    read_surahs = list(progress.read_surahs.all()) if progress else []
    read_count = len(read_surahs)
    verses_read = sum(item.verses_count for item in read_surahs)
    target_date = date.today() + timedelta(days=(progress.goal_days or 30)) if progress else None
    is_completed = read_count >= total_surahs and total_surahs > 0
    if progress and is_completed and not progress.completed_at:
        progress.completed_at = date.today()
        progress.save(update_fields=["completed_at"])

    return {
        "progress": progress,
        "chapters": chapters,
        "read_surahs": read_surahs,
        "read_surah_ids": [item.surah_number for item in read_surahs],
        "read_surah_count": read_count,
        "total_surahs": total_surahs,
        "read_verses": verses_read,
        "total_verses": total_verses,
        "surah_percent": round((read_count / total_surahs) * 100, 1) if total_surahs else 0,
        "verse_percent": round((verses_read / total_verses) * 100, 1) if total_verses else 0,
        "is_completed": is_completed,
        "target_date": target_date,
    }


def mark_surah_read(user, surah_number: int, surah_name: str, surah_name_ar: str, verses_count: int):
    progress = get_or_create_reading_progress(user)
    if not progress:
        return None
    return ReadSurah.objects.get_or_create(
        progress=progress,
        surah_number=surah_number,
        defaults={
            "surah_name": surah_name,
            "surah_name_ar": surah_name_ar,
            "verses_count": verses_count,
        },
    )


def unmark_surah_read(user, surah_number: int):
    progress = get_or_create_reading_progress(user)
    if not progress:
        return
    progress.read_surahs.filter(surah_number=surah_number).delete()


def strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


def normalize_arabic_text(value: str) -> str:
    normalized = ARABIC_DIACRITICS_PATTERN.sub("", value or "")
    normalized = re.sub(r"[^\u0600-\u06FF0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def render_tajweed_html(value: str) -> str:
    if not value:
        return ""

    def repl(match):
        raw_class = match.group(1).strip().strip('"').strip("'")
        mapped_class = "tajweed-default"
        for key, css_class in TAJWEED_CLASS_MAP.items():
            if key in raw_class:
                mapped_class = css_class
                break
        return f'<span class="tajweed-word {mapped_class}" data-rule="{escape(raw_class)}">'

    html = TAJWEED_TAG_PATTERN.sub(repl, value)
    html = html.replace("</tajweed>", "</span>")
    html = html.replace("<span class=end>", '<span class="tajweed-end">')
    return html


def compute_recitation_feedback(reference_text: str, transcript_text: str):
    reference_words = normalize_arabic_text(reference_text).split()
    transcript_words = normalize_arabic_text(transcript_text).split()
    matcher = SequenceMatcher(None, reference_words, transcript_words)
    ratio = matcher.ratio()
    score = int(round(ratio * 100))

    word_states = []
    mistakes = []
    for index, word in enumerate(reference_words):
        transcript_word = transcript_words[index] if index < len(transcript_words) else ""
        correct = transcript_word == word
        word_states.append({"word": word, "correct": correct})
        if not correct:
            mistakes.append(
                {
                    "expected": word,
                    "heard": transcript_word,
                    "position": index + 1,
                }
            )

    feedback = "Bonne recitation globale."
    if mistakes:
        feedback = "Travaillez les mots signales en rouge et repetez lentement avec ecoute attentive."
    if score >= 95:
        feedback = "Excellent. Votre recitation est tres proche du texte attendu."

    return {
        "score": score,
        "mistakes": mistakes[:10],
        "word_states": word_states,
        "feedback": feedback,
    }
