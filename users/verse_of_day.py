from datetime import date

from django.core.cache import cache
import requests

TOTAL_QURAN_VERSES = 6236
FRENCH_TRANSLATION = "fr.hamidullah"
ARABIC_EDITION = "quran-uthmani"
TRANSLITERATION_EDITION = "en.transliteration"
ALQURAN_API_BASE = "https://api.alquran.cloud/v1"


def get_daily_verse_reference(day=None):
    current_day = day or date.today()
    ordinal = current_day.toordinal()
    return (ordinal % TOTAL_QURAN_VERSES) + 1


def get_daily_verse():
    today = date.today()
    cache_key = f"verse_of_day_{today.isoformat()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    reference = get_daily_verse_reference(today)

    try:
        response = requests.get(
            f"{ALQURAN_API_BASE}/ayah/{reference}/editions/{ARABIC_EDITION},{TRANSLITERATION_EDITION},{FRENCH_TRANSLATION}",
            timeout=12,
        )
        response.raise_for_status()
        editions = response.json().get("data", [])
    except Exception:
        return None

    arabic = next((item for item in editions if item.get("edition", {}).get("identifier") == ARABIC_EDITION), {})
    transliteration = next(
        (item for item in editions if item.get("edition", {}).get("identifier") == TRANSLITERATION_EDITION),
        {},
    )
    french = next((item for item in editions if item.get("edition", {}).get("identifier") == FRENCH_TRANSLATION), {})

    verse = {
        "reference": arabic.get("numberInSurah"),
        "surah_number": arabic.get("surah", {}).get("number"),
        "surah_name": arabic.get("surah", {}).get("englishName"),
        "surah_name_ar": arabic.get("surah", {}).get("name"),
        "ayah_number": arabic.get("numberInSurah"),
        "verse_key": f"{arabic.get('surah', {}).get('number')}:{arabic.get('numberInSurah')}",
        "arabic_text": arabic.get("text", ""),
        "transliteration": transliteration.get("text", ""),
        "translation_fr": french.get("text", ""),
        "edition_fr": french.get("edition", {}).get("englishName", "Francais"),
    }
    cache.set(cache_key, verse, 43200)
    return verse
