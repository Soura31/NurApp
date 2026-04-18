from .hijri import get_today_hijri
from .verse_of_day import get_daily_verse


def global_spiritual_context(request):
    return {
        "navbar_hijri_today": get_today_hijri(),
        "global_verse_of_day": get_daily_verse(),
        "assistant_history": request.session.get("assistant_history", []),
    }
