"""Strict copyright safety and SSRF defense for Trend Intelligence reference inputs."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


class TrendSafetyError(ValueError):
    """Raised when a reference URL violates SSRF, scheme, or privacy/scraping boundaries."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata",
}


def validate_safe_reference_url(raw_url: str) -> tuple[str, dict[str, str]]:
    """Validate reference URL without downloading streams or scraping private endpoints."""
    cleaned = raw_url.strip()
    parsed = urlparse(cleaned)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise TrendSafetyError(
            f"Unsupported URL scheme '{parsed.scheme or 'none'}'. Only public http/https URLs are permitted.",
            status_code=400,
        )

    if parsed.username or parsed.password:
        raise TrendSafetyError("Embedded URL credentials are forbidden for privacy and safety.", status_code=400)

    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise TrendSafetyError("Reference URL must include a valid hostname.", status_code=400)

    if host in _BLOCKED_HOSTNAMES or host.endswith(".local") or host.endswith(".internal"):
        raise TrendSafetyError(f"Blocked internal or local hostname '{host}' (SSRF policy).", status_code=422)

    try:
        ip_obj = ipaddress.ip_address(host)
    except ValueError:
        # Host is a DNS domain name rather than a literal IP
        ip_obj = None

    if ip_obj is not None and (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    ):
        raise TrendSafetyError(
            f"Blocked private, loopback, or link-local IP address '{host}' (SSRF policy).",
            status_code=422,
        )

    lower_path = f"{host}{parsed.path}".lower()
    hints = {
        "domain": host,
        "format_hint": "vertical_short" if any(k in lower_path for k in ("/shorts", "/reel", "/reels", "tiktok.com")) else "standard",
    }
    return cleaned, hints
