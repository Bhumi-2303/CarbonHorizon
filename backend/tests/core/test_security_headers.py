import re
from pathlib import Path
import pytest
from fastapi import Response
from fastapi.testclient import TestClient

from app.core.security import set_secure_cookie
from main import app

client = TestClient(app)


def parse_csp(csp_str: str) -> dict[str, set[str]]:
    directives = {}
    for part in csp_str.split(";"):
        tokens = part.strip().split()
        if not tokens:
            continue
        directives[tokens[0]] = set(tokens[1:])
    return directives


def test_https_redirect_when_forwarded_proto_is_http():
    """Verify HTTP requests are redirected to HTTPS via X-Forwarded-Proto."""
    resp = client.get(
        "/health",
        headers={"X-Forwarded-Proto": "http"},
        follow_redirects=False,
    )
    assert resp.status_code == 308
    assert resp.headers["location"].startswith("https://")


def test_no_redirect_when_forwarded_proto_is_https():
    """Verify HTTPS requests proceed normally without redirect."""
    resp = client.get(
        "/health",
        headers={"X-Forwarded-Proto": "https"},
        follow_redirects=False,
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_no_redirect_for_local_requests_without_proto_header():
    """Verify local development requests without header are not redirected."""
    resp = client.get("/health", follow_redirects=False)
    assert resp.status_code == 200


def test_security_headers_present():
    """Verify standard security headers are attached to API responses."""
    resp = client.get("/health")
    assert resp.status_code == 200

    h = resp.headers
    assert h.get("Strict-Transport-Security") == (
        "max-age=31536000; includeSubDomains"
    )
    assert h.get("X-Content-Type-Options") == "nosniff"
    assert h.get("X-Frame-Options") == "DENY"
    assert h.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in h.get("Permissions-Policy", "")
    assert "frame-ancestors 'none'" in h.get("Content-Security-Policy", "")


def test_csp_header_allows_turnstile_plausible_fonts_and_no_wildcards():
    """
    Verify CSP allows Cloudflare Turnstile, Plausible, Google Fonts,
    and no wildcard schemes like 'https:' or '*' in script/connect/frame.
    """
    resp = client.get("/health")
    csp_header = resp.headers.get("Content-Security-Policy", "")
    assert csp_header, "CSP header missing from response"

    directives = parse_csp(csp_header)

    # 1. script-src (Strict: no 'unsafe-inline', no wildcards, no cdn)
    script_src = directives.get("script-src", set())
    assert "https://challenges.cloudflare.com" in script_src
    assert "https://plausible.io" in script_src
    assert "'unsafe-inline'" not in script_src
    assert "https://cdn.jsdelivr.net" not in script_src
    assert "https:" not in script_src
    assert "*" not in script_src

    # 2. frame-src
    frame_src = directives.get("frame-src", set())
    assert "https://challenges.cloudflare.com" in frame_src
    assert "https:" not in frame_src
    assert "*" not in frame_src

    # 3. connect-src
    connect_src = directives.get("connect-src", set())
    assert "https://challenges.cloudflare.com" in connect_src
    assert "https://plausible.io" in connect_src
    assert "https:" not in connect_src
    assert "wss:" not in connect_src
    assert "*" not in connect_src

    # 4. Google Fonts
    style_src = directives.get("style-src", set())
    assert "https://fonts.googleapis.com" in style_src
    assert "'unsafe-inline'" in style_src  # Allowed for Tailwind / styles
    assert "https://cdn.jsdelivr.net" not in style_src
    font_src = directives.get("font-src", set())
    assert "https://fonts.gstatic.com" in font_src
    assert "https://cdn.jsdelivr.net" not in font_src

    # 5. Core restrictions: object-src, base-uri, frame-ancestors
    assert directives.get("object-src") == {"'none'"}
    assert directives.get("base-uri") == {"'self'"}
    assert directives.get("frame-ancestors") == {"'none'"}


def test_nginx_csp_configuration_matches_spec():
    """Verify nginx.conf.template enforces the exact same restricted CSP."""
    root_dir = Path(__file__).resolve().parents[3]
    nginx_path = root_dir / "nginx.conf.template"
    if not nginx_path.exists():
        pytest.skip("nginx.conf.template not found in root")

    content = nginx_path.read_text()
    match = re.search(
        r'add_header\s+Content-Security-Policy\s+"([^"]+)"', content
    )
    assert match, (
        "Could not find Content-Security-Policy directive in nginx.conf"
    )

    nginx_csp = parse_csp(match.group(1))

    # Turnstile & Plausible
    assert "https://challenges.cloudflare.com" in nginx_csp.get(
        "script-src", set()
    )
    assert "https://challenges.cloudflare.com" in nginx_csp.get(
        "frame-src", set()
    )
    assert "https://challenges.cloudflare.com" in nginx_csp.get(
        "connect-src", set()
    )
    assert "https://plausible.io" in nginx_csp.get("script-src", set())
    assert "https://plausible.io" in nginx_csp.get("connect-src", set())

    # Script-src: No unsafe-inline
    assert "'unsafe-inline'" not in nginx_csp.get("script-src", set())

    # Google Fonts
    assert "https://fonts.googleapis.com" in nginx_csp.get("style-src", set())
    assert "https://fonts.gstatic.com" in nginx_csp.get("font-src", set())

    # No wildcards or jsdelivr
    assert "https:" not in nginx_csp.get("script-src", set())
    assert "https:" not in nginx_csp.get("connect-src", set())
    assert "wss:" not in nginx_csp.get("connect-src", set())
    assert "https://cdn.jsdelivr.net" not in nginx_csp.get("script-src", set())

    # Strict directives
    assert nginx_csp.get("object-src") == {"'none'"}
    assert nginx_csp.get("base-uri") == {"'self'"}
    assert nginx_csp.get("frame-ancestors") == {"'none'"}


def test_set_secure_cookie_attributes():
    """Verify set_secure_cookie helper sets Secure, HttpOnly, and SameSite."""
    res = Response()
    set_secure_cookie(
        response=res,
        key="session_token",
        value="test_value",
        max_age=3600,
    )
    cookie_header = res.headers.get("set-cookie", "")
    assert "session_token=test_value" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "Secure" in cookie_header
    assert "SameSite=lax" in cookie_header or "samesite=lax" in cookie_header


def test_docs_and_openapi_disabled_in_production(monkeypatch):
    """Verify Swagger, ReDoc, and OpenAPI endpoints return 404 in production."""
    from fastapi import FastAPI
    prod_app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    prod_client = TestClient(prod_app)
    assert prod_client.get("/api/docs").status_code == 404
    assert prod_client.get("/api/redoc").status_code == 404
    assert prod_client.get("/api/openapi.json").status_code == 404


def test_csp_identical_across_fastapi_nginx_and_vercel():
    """Assert CSP directives are identical across FastAPI, Nginx, and Vercel."""
    import json
    root_dir = Path(__file__).resolve().parents[3]

    # 1. FastAPI CSP
    resp = client.get("/health")
    fastapi_csp_str = resp.headers.get("Content-Security-Policy", "")
    fastapi_directives = parse_csp(fastapi_csp_str)

    # 2. Nginx CSP
    nginx_path = root_dir / "nginx.conf.template"
    assert nginx_path.exists(), "nginx.conf.template must exist"
    nginx_content = nginx_path.read_text()
    nginx_match = re.search(
        r'add_header\s+Content-Security-Policy\s+"([^"]+)"', nginx_content
    )
    assert nginx_match, "Nginx CSP not found"
    nginx_directives = parse_csp(nginx_match.group(1))

    # 3. Vercel CSP
    vercel_path = root_dir / "frontend" / "vercel.json"
    assert vercel_path.exists(), "frontend/vercel.json must exist"
    vercel_data = json.loads(vercel_path.read_text())
    vercel_csp_str = ""
    for route in vercel_data.get("headers", []):
        for h in route.get("headers", []):
            if h.get("key") == "Content-Security-Policy":
                vercel_csp_str = h.get("value")
                break
    assert vercel_csp_str, "Vercel CSP header not found"
    vercel_directives = parse_csp(vercel_csp_str)

    # Assert exact directive parity
    assert fastapi_directives == nginx_directives, (
        "FastAPI and Nginx CSP must be identical"
    )
    assert nginx_directives == vercel_directives, (
        "Nginx and Vercel CSP must be identical"
    )
