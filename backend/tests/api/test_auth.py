"""API tests: authentication (spec §20, §22)."""


def test_register_and_login(client):
    r = client.post("/api/auth/register", json={
        "email": "a@b.com", "full_name": "A B", "password": "password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["user"]["email"] == "a@b.com"

    r2 = client.post("/api/auth/login", json={"email": "a@b.com", "password": "password123"})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


def test_duplicate_email_rejected(client):
    payload = {"email": "dup@b.com", "full_name": "Dup", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 422


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "email": "w@b.com", "full_name": "W", "password": "password123"})
    r = client.post("/api/auth/login", json={"email": "w@b.com", "password": "wrongwrong"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    # no protected "me" endpoint, but protected jobs must 401 without token
    assert client.get("/api/jobs").status_code == 401
