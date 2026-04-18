from datetime import date

from django.conf import settings
from django.core.cache import cache
import requests

HIJRI_MONTHS_FR = {
    1: "Mouharram",
    2: "Safar",
    3: "Rabi al-Awwal",
    4: "Rabi ath-Thani",
    5: "Joumada al-Oula",
    6: "Joumada ath-Thania",
    7: "Rajab",
    8: "Chaabane",
    9: "Ramadan",
    10: "Chawwal",
    11: "Dhou al-Qi`da",
    12: "Dhou al-Hijja",
}

GREGORIAN_MONTHS_FR = {
    1: "Janvier",
    2: "Fevrier",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Aout",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Decembre",
}

IMPORTANT_HIJRI_DATES = {
    (1, 1): {"label": "Nouvel an hijri", "accent": "emerald"},
    (1, 10): {"label": "10 Mouharram - Achoura", "accent": "gold"},
    (3, 12): {"label": "Mawlid", "accent": "gold"},
    (7, 27): {"label": "Isra et Mi'raj", "accent": "emerald"},
    (8, 15): {"label": "Nuit du milieu de Chaabane", "accent": "emerald"},
    (9, 1): {"label": "Debut du Ramadan", "accent": "gold"},
    (9, 27): {"label": "Laylat al-Qadr", "accent": "gold"},
    (10, 1): {"label": "Aid el-Fitr", "accent": "gold"},
    (12, 9): {"label": "Jour de Arafat", "accent": "emerald"},
    (12, 10): {"label": "Aid el-Adha", "accent": "gold"},
}


def _request_calendar(endpoint: str):
    response = requests.get(endpoint, timeout=12)
    response.raise_for_status()
    return response.json().get("data", [])


def _normalize_days(days):
    normalized = []
    for item in days:
        hijri = item.get("hijri", {})
        gregorian = item.get("gregorian", {})
        hijri_month = int(hijri.get("month", {}).get("number") or 0)
        hijri_day = int(hijri.get("day") or 0)
        gregorian_month = int(gregorian.get("month", {}).get("number") or 0)
        gregorian_day = int(gregorian.get("day") or 0)

        normalized.append(
            {
                "gregorian": gregorian,
                "hijri": hijri,
                "gregorian_day": gregorian_day,
                "gregorian_month_name": GREGORIAN_MONTHS_FR.get(
                    gregorian_month, gregorian.get("month", {}).get("en", "")
                ),
                "hijri_day": hijri_day,
                "hijri_month_number": hijri_month,
                "hijri_month_name": HIJRI_MONTHS_FR.get(hijri_month, hijri.get("month", {}).get("en", "")),
                "special": IMPORTANT_HIJRI_DATES.get((hijri_month, hijri_day)),
                "is_today": False,
            }
        )
    return normalized


def get_hijri_month_calendar(month: int, year: int):
    cache_key = f"hijri_calendar_{month}_{year}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        days = _request_calendar(f"{settings.ALADHAN_API_BASE}/hToGCalendar/{month}/{year}")
    except Exception:
        return []

    normalized = _normalize_days(days)
    cache.set(cache_key, normalized, 43200)
    return normalized


def get_today_hijri():
    today = date.today()
    cache_key = f"hijri_today_{today.isoformat()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        days = _normalize_days(
            _request_calendar(f"{settings.ALADHAN_API_BASE}/gToHCalendar/{today.month}/{today.year}")
        )
    except Exception:
        return None

    match = None
    today_str = today.strftime("%d-%m-%Y")
    for item in days:
        if item.get("gregorian", {}).get("date") == today_str:
            match = item
            break
    if not match and days:
        match = days[0]
    if not match:
        return None

    match["is_today"] = True
    match["label"] = f"{match['hijri_day']} {match['hijri_month_name']} {match['hijri'].get('year', '')}".strip()
    cache.set(cache_key, match, 43200)
    return match


def get_current_hijri_period():
    today = get_today_hijri()
    if not today:
        return None
    return {
        "month": today.get("hijri_month_number"),
        "year": int(today.get("hijri", {}).get("year") or 0),
        "label": f"{today.get('hijri_month_name', '')} {today.get('hijri', {}).get('year', '')}".strip(),
    }


def get_adjacent_hijri_period(month: int, year: int, step: int):
    next_month = month + step
    next_year = year
    if next_month < 1:
        next_month = 12
        next_year -= 1
    elif next_month > 12:
        next_month = 1
        next_year += 1
    return next_month, next_year
