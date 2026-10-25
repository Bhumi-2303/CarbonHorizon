"""
Tests for trusted proxy handling and client IP derivation based on TRUSTED_PROXY_COUNT.

Verifies:
1. 1-hop proxy configuration:
   - Honors single proxy appending client IP.
   - Ignores attacker-spoofed IPs prepended to X-Forwarded-For.
2. 2-hop proxy configuration (Cloud Run Frontend Nginx -> Backend Run.app):
   - Correctly extracts client IP (2 hops from the right).
   - Ignores attacker-spoofed IPs on the left.
3. 0-hop (no trusted proxy):
   - Always returns raw socket peer.
4. Temporary debug logging:
   - Emits structured debug logs when DEBUG_CLIENT_IP=True.
5. End-to-end ASGI integration tests with TestClient:
   - Verifies rate limiter key is derived securely and prevents spoofing.
"""
import logging
from starlette.requests import Request
from app.core.config import settings
from app.core.client_ip import get_trusted_client_ip


def make_mock_request(client_host: str, headers: dict) -> Request:
    scope = {
        "type": "http",
        "client": (client_host, 50000),
        "headers": [
            (k.lower().encode("latin1"), v.encode("latin1"))
            for k, v in headers.items()
        ],
    }
    return Request(scope)


def test_one_hop_proxy_resolution(monkeypatch):
    """TRUSTED_PROXY_COUNT = 1: Single trusted proxy hop (e.g. direct Cloud Run GFE)."""
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 1)

    req = make_mock_request(
        client_host="169.254.8.1",
        headers={"x-forwarded-for": "203.0.113.19"},
    )
    assert get_trusted_client_ip(req) == "203.0.113.19"


def test_one_hop_proxy_with_spoofed_header(monkeypatch):
    """
    TRUSTED_PROXY_COUNT = 1: Attacker sends spoofed 'X-Forwarded-For: 198.51.100.99'.
    The single proxy appends the real socket peer '203.0.113.19'.
    System picks 1 hop from right -> '203.0.113.19'.
    """
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 1)

    req = make_mock_request(
        client_host="169.254.8.1",
        headers={"x-forwarded-for": "198.51.100.99, 203.0.113.19"},
    )
    assert get_trusted_client_ip(req) == "203.0.113.19"


def test_two_hop_proxy_resolution(monkeypatch):
    """
    TRUSTED_PROXY_COUNT = 2:
    Topology: Browser (203.0.113.19) -> Frontend Nginx (192.0.2.50) -> Backend GFE.
    X-Forwarded-For: '203.0.113.19, 192.0.2.50'
    System picks 2 hops from right -> '203.0.113.19'.
    """
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 2)

    req = make_mock_request(
        client_host="169.254.8.1",
        headers={"x-forwarded-for": "203.0.113.19, 192.0.2.50"},
    )
    assert get_trusted_client_ip(req) == "203.0.113.19"


def test_two_hop_proxy_with_spoofed_header(monkeypatch):
    """
    TRUSTED_PROXY_COUNT = 2:
    Attacker sends spoofed 'X-Forwarded-For: 1.1.1.1, 8.8.8.8'.
    Frontend Nginx appends real client IP '203.0.113.19'.
    Backend GFE appends Frontend Nginx egress IP '192.0.2.50'.
    Header: '1.1.1.1, 8.8.8.8, 203.0.113.19, 192.0.2.50'
    System picks 2 hops from right -> '203.0.113.19'.
    """
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 2)

    req = make_mock_request(
        client_host="169.254.8.1",
        headers={
            "x-forwarded-for": "1.1.1.1, 8.8.8.8, 203.0.113.19, 192.0.2.50"
        },
    )
    assert get_trusted_client_ip(req) == "203.0.113.19"


def test_zero_hop_ignores_forwarded_headers(monkeypatch):
    """TRUSTED_PROXY_COUNT = 0: No proxy is trusted; raw socket peer is returned."""
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 0)

    req = make_mock_request(
        client_host="198.51.100.5",
        headers={"x-forwarded-for": "203.0.113.19, 192.0.2.50"},
    )
    assert get_trusted_client_ip(req) == "198.51.100.5"


def test_fallback_to_x_real_ip_when_no_x_forwarded_for(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 1)

    req = make_mock_request(
        client_host="169.254.8.1",
        headers={"x-real-ip": "198.51.100.77"},
    )
    assert get_trusted_client_ip(req) == "198.51.100.77"


def test_debug_client_ip_logging(monkeypatch, caplog):
    """Temporary debug log can be toggled on staging to inspect the derived key."""
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 2)
    monkeypatch.setattr(settings, "DEBUG_CLIENT_IP", True)

    with caplog.at_level(logging.INFO, logger="app.security"):
        req = make_mock_request(
            client_host="169.254.8.1",
            headers={"x-forwarded-for": "203.0.113.19, 192.0.2.50"},
        )
        ip = get_trusted_client_ip(req)
        assert ip == "203.0.113.19"
        assert "[ClientIP Debug]" in caplog.text
        assert "derived_ip=203.0.113.19" in caplog.text
        assert "trusted_hops=2" in caplog.text


def test_debug_client_ip_disabled_by_default(monkeypatch, caplog):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 2)
    monkeypatch.setattr(settings, "DEBUG_CLIENT_IP", False)

    with caplog.at_level(logging.INFO, logger="app.security"):
        req = make_mock_request(
            client_host="169.254.8.1",
            headers={"x-forwarded-for": "203.0.113.19, 192.0.2.50"},
        )
        get_trusted_client_ip(req)
        assert "[ClientIP Debug]" not in caplog.text


def test_asgi_integration_limiter_key_with_two_hop_proxy(monkeypatch, db):
    """
    End-to-end integration test through actual ASGI app (TestClient).
    Configures TRUSTED_PROXY_COUNT = 2 (Cloud Run topology).
    Verifies that spoofed X-Forwarded-For headers cannot bypass rate limits.
    """
    from fastapi.testclient import TestClient
    from main import app
    from app.core.rate_limit import limiter
    from app.core.security import get_db

    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 2)
    app.dependency_overrides[get_db] = lambda: db

    gfe_peer = "169.254.8.1"
    nginx_egress = "192.0.2.50"
    client = TestClient(app, client=(gfe_peer, 54321))

    prev_enabled = limiter.enabled
    limiter.enabled = True
    limiter.reset()

    try:
        statuses = []
        for i in range(6):
            payload = {
                "email": f"attacker_{i}@example.com",
                "password": "Password123!",
                "full_name": f"Attacker {i}",
                "terms_accepted": True,
                "terms_version": "1.0",
                "turnstile_token": "test-mock-token",
            }
            # Attacker rotates a spoofed prefix: 'spoofed_ip, 203.0.113.88, egress'
            # With TRUSTED_PROXY_COUNT=2, limiter resolves to 203.0.113.88 every time
            spoofed_prefix = f"10.99.{i}.1"
            header_val = f"{spoofed_prefix}, 203.0.113.88, {nginx_egress}"

            resp = client.post(
                "/api/v1/auth/register",
                json=payload,
                headers={"X-Forwarded-For": header_val},
            )
            statuses.append(resp.status_code)

        # First 5 succeed, 6th is HTTP 429 Too Many Requests
        assert statuses[:5] == [201] * 5
        assert statuses[5] == 429
    finally:
        limiter.enabled = prev_enabled
        limiter.reset()
        app.dependency_overrides.pop(get_db, None)
