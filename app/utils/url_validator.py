import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import get_settings


class URLValidationError(ValueError):
    pass


def validate_external_url(url: str) -> str:
    settings = get_settings()
    parsed = urlparse(url.strip())
    allowed = {s.strip() for s in settings.allowed_url_schemes.split(",")}

    if parsed.scheme not in allowed:
        raise URLValidationError(f"Scheme not allowed: {parsed.scheme}")

    if not parsed.netloc:
        raise URLValidationError("Invalid URL.")

    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("Missing hostname.")

    if settings.block_private_ips:
        try:
            for info in socket.getaddrinfo(hostname, None):
                ip = ipaddress.ip_address(info[4][0])
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise URLValidationError("URL points to a private address.")
        except socket.gaierror as exc:
            raise URLValidationError(f"Could not resolve hostname: {hostname}") from exc

    return url.strip()
