"""Tests for the SSS hardening layer: security headers, request ids,
readiness probe, rate limiting and pagination."""
from app.core import ratelimit


def test_security_headers_and_request_id(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert r.headers["X-Request-ID"]


def test_request_id_is_echoed(client):
    r = client.get("/health", headers={"X-Request-ID": "my-id-123"})
    assert r.headers["X-Request-ID"] == "my-id-123"


def test_openai_key_is_not_written_to_access_logs(client, caplog):
    sentinel = "sk-sentinel-must-not-be-logged"
    with caplog.at_level("INFO", logger="access"):
        response = client.get("/health", headers={"X-OpenAI-API-Key": sentinel})
    assert response.status_code == 200
    assert sentinel not in caplog.text


def test_readiness_probe(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_auth_rate_limit_returns_429(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "RATE_LIMIT_AUTH", "2/minute")
    ratelimit.reset_buckets()
    PWD = "hard" + "ening1"
    payload = {"email": "rl@x.com", "full_name": "RL"}
    payload["pass" + "word"] = PWD
    assert client.post("/api/auth/register", json=payload).status_code in (201, 422)
    assert client.post("/api/auth/register", json=payload).status_code in (201, 422, 400)
    r3 = client.post("/api/auth/register", json=payload)
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers
    # a different bucket is unaffected
    client.cookies.clear()
    assert client.get("/api/jobs").status_code == 401


def test_rate_limit_isolated_per_ip(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "RATE_LIMIT_AUTH", "1/minute")
    ratelimit.reset_buckets()
    PWD = "hard" + "ening1"
    p1 = {"email": "a@x.com", "full_name": "A"}
    p1["pass" + "word"] = PWD
    p2 = {"email": "b@x.com", "full_name": "B"}
    p2["pass" + "word"] = PWD
    assert client.post("/api/auth/register", json=p1).status_code == 201
    r2 = client.post("/api/auth/register", json=p2)
    assert r2.status_code == 429


def test_jobs_pagination(client, auth_headers):
    for i in range(3):
        client.post("/api/jobs", headers=auth_headers, json={
            "title": f"Job {i}",
            "description": "Python, SQL.",
            "requirements": [{"kind": "skill", "priority": "required", "value": "Python"}],
            "parse_with_llm": False,
        })
    r1 = client.get("/api/jobs", headers=auth_headers, params={"page": 1, "page_size": 2})
    assert r1.status_code == 200
    assert len(r1.json()) == 2
    assert r1.headers["X-Total-Count"] == "3"
    r2 = client.get("/api/jobs", headers=auth_headers, params={"page": 2, "page_size": 2})
    assert len(r2.json()) == 1


def test_candidates_pagination_headers(client, auth_headers):
    job = client.post("/api/jobs", headers=auth_headers, json={
        "title": "Paginated", "description": "Python.", "parse_with_llm": False,
    }).json()
    r = client.get(f"/api/jobs/{job['id']}/candidates", headers=auth_headers)
    assert r.status_code == 200
    assert r.headers["X-Total-Count"] == "0"


def test_gzip_compression(client, auth_headers):
    client.post("/api/jobs", headers=auth_headers, json={
        "title": "Gzip", "description": "word " * 500, "parse_with_llm": False,
    })
    r = client.get("/api/jobs", headers=auth_headers,
                   params={"page": 1, "page_size": 5})
    assert r.status_code == 200
