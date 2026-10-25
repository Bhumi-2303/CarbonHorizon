"""
Trusted proxy and client IP resolution.

Behind Cloud Run and reverse proxies (e.g. Nginx), the raw socket peer is the
local infrastructure proxy/Google Front End (GFE).

Topology for Cloud Run with Frontend Nginx Reverse Proxy:
  Browser (client_ip)
    │  (sends request, potentially with spoofed X-Forwarded-For: attacker_ip)
    ▼
  Frontend Cloud Run (Google Front End + Nginx Container)
    │  GFE sets/appends client_ip.
    │  Nginx appends $remote_addr via proxy_set_header X-Forwarded-For.
    │  Nginx connects via outbound HTTPS to backend Cloud Run.
    ▼
  Backend Cloud Run (Google Front End + Uvicorn Container)
    │  Backend GFE receives request from frontend_egress_ip.
    │  Backend GFE appends frontend_egress_ip to X-Forwarded-For.
    ▼
  Uvicorn Container:
    - Socket peer (request.client.host): 169.254.8.1 (local GFE/container proxy)
    - X-Forwarded-For header received:
        "<spoofed_ip>, <client_ip>, <frontend_egress_ip>"

With TRUSTED_PROXY_COUNT = 2:
  The two rightmost hops are trusted infrastructure hops:
    - Index -1: frontend_egress_ip (appended by Backend GFE)
    - Index -2: client_ip (appended by Frontend Nginx)
  The client IP is therefore ips[-2] (or ips[-TRUSTED_PROXY_COUNT]).
  Any spoofed_ip prepended by an attacker on the left is ignored.

When TRUSTED_PROXY_COUNT = 1 (direct connection to Cloud Run or single proxy):
  Header is "<spoofed_ip>, <client_ip>"
  The rightmost hop (index -1) was appended by trusted proxy -> ips[-1] is client_ip.

When TRUSTED_PROXY_COUNT <= 0:
  Forwarded headers are ignored; raw socket peer is returned.
"""
import logging
from starlette.requests import Request
from app.core.config import settings

logger = logging.getLogger("app.security")


def get_trusted_client_ip(request: Request) -> str:
    """
    Safely resolve client IP based on configurable TRUSTED_PROXY_COUNT hops.
    """
    direct_peer = request.client.host if request.client else "127.0.0.1"
    trusted_hops = getattr(settings, "TRUSTED_PROXY_COUNT", 1)

    if trusted_hops <= 0:
        derived_ip = direct_peer
    else:
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # Parse CSV list of IPs
            ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
            if len(ips) >= trusted_hops:
                derived_ip = ips[-trusted_hops]
            elif ips:
                derived_ip = ips[0]
            else:
                derived_ip = direct_peer
        else:
            x_real_ip = request.headers.get("x-real-ip")
            if x_real_ip and x_real_ip.strip():
                derived_ip = x_real_ip.strip()
            else:
                derived_ip = direct_peer

    if getattr(settings, "DEBUG_CLIENT_IP", False):
        logger.info(
            "[ClientIP Debug] derived_ip=%s direct_peer=%s x_forwarded_for=%s "
            "trusted_hops=%d",
            derived_ip,
            direct_peer,
            request.headers.get("x-forwarded-for"),
            trusted_hops,
        )

    return derived_ip
