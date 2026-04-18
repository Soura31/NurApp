from django.conf import settings
import requests

ISLAMIC_SYSTEM_PROMPT = (
    "Tu es un assistant islamique bienveillant et savant. "
    "Tu reponds uniquement aux questions liees a l'islam, au Coran, aux hadiths, "
    "a la spiritualite et a la vie du musulman. Tu cites toujours tes sources "
    "(sourate, verset, hadith). Tu es respectueux, humble et precis."
)


def ask_islamic_assistant(history):
    if not settings.ANTHROPIC_API_KEY:
        return {
            "ok": False,
            "text": "La cle API Anthropic n'est pas configuree sur le serveur.",
        }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": 900,
                "system": ISLAMIC_SYSTEM_PROMPT,
                "messages": history,
            },
            timeout=90,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("content", [])
        text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        return {"ok": True, "text": "\n\n".join(part for part in text_parts if part).strip()}
    except Exception:
        return {
            "ok": False,
            "text": "L'assistant IA est temporairement indisponible. Reessayez plus tard.",
        }
