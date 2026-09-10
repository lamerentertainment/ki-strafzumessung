"""
Einfaches IP-basiertes Rate-Limiting für öffentlich erreichbare, kostenpflichtige
API-Endpoints (aktuell: Präjudizensuche). Nutzt das Django-Cache-Framework
(DatabaseCache, siehe CACHES in settings) statt einer neuen Infrastruktur.
"""
import time

from django.conf import settings
from django.core.cache import cache


class RateLimitExceeded(Exception):
    """Wird geworfen, wenn eine IP das Stunden-Limit überschritten hat."""


def client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def check_and_increment_rate_limit(request) -> None:
    """Erhöht den Stunden-Zähler für die anfragende IP und wirft RateLimitExceeded,
    falls das konfigurierte Limit überschritten ist. Muss vor jedem kostenpflichtigen
    API-Call aufgerufen werden."""
    limit = getattr(settings, "PRAEJUDIZENSUCHE_RATE_LIMIT_PER_HOUR", 20)
    window_start = int(time.time() // 3600) * 3600
    key = f"praejudizensuche_rl:{client_ip(request)}:{window_start}"

    cache.add(key, 0, timeout=3600)
    try:
        current = cache.incr(key)
    except ValueError:
        # Key ist zwischen add() und incr() abgelaufen (Race) - neu setzen.
        cache.set(key, 1, timeout=3600)
        current = 1

    if current > limit:
        raise RateLimitExceeded(
            "Zu viele Anfragen. Bitte versuchen Sie es in einer Stunde erneut."
        )
