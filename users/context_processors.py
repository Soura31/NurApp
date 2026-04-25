from .engagement import (
    build_month_streak_calendar,
    ensure_daily_reminders,
    ensure_initial_content,
    get_daily_dua,
    get_daily_name_of_allah,
    get_pending_notifications,
    get_profile_summary,
)
from .hijri import get_today_hijri
from .verse_of_day import get_daily_verse


def global_spiritual_context(request):
    ensure_initial_content()
    pending = []
    summary = {}
    streak_calendar = []
    if request.user.is_authenticated:
        ensure_daily_reminders(request.user)
        pending = get_pending_notifications(request.user)
        summary = get_profile_summary(request.user)
        streak_calendar = build_month_streak_calendar(request.user)

    return {
        "navbar_hijri_today": get_today_hijri(),
        "global_verse_of_day": get_daily_verse(),
        "assistant_history": request.session.get("assistant_history", []),
        "daily_dua": get_daily_dua(),
        "daily_name_of_allah": get_daily_name_of_allah(),
        "pending_notifications": pending,
        "global_profile_summary": summary,
        "global_streak_calendar": streak_calendar,
    }
