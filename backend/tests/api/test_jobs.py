"""API tests: job creation + retrieval (spec §20)."""


def _create_job(client, headers):
    return client.post("/api/jobs", headers=headers, json={
        "title": "Backend Engineer",
        "description": "We need Python, FastAPI, PostgreSQL and REST APIs.",
        "requirements": [
            {"kind": "skill", "priority": "required", "value": "Python"},
            {"kind": "skill", "priority": "required", "value": "FastAPI"},
            {"kind": "skill", "priority": "preferred", "value": "Docker"},
            {"kind": "experience", "priority": "required", "value": "experience", "min_years": 3},
        ],
        "weights": {"skill": 0.35, "experience": 0.20, "semantic": 0.15, "education": 0.10,
                    "project": 0.10, "certification": 0.05, "preferred": 0.05},
        "hard_gate": False,
        "parse_with_llm": False,
    })


def test_create_and_get_job(client, auth_headers):
    r = _create_job(client, auth_headers)
    assert r.status_code == 201, r.text
    job = r.json()
    assert job["title"] == "Backend Engineer"
    assert len(job["requirements"]) == 4

    got = client.get(f"/api/jobs/{job['id']}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["id"] == job["id"]


def test_list_jobs(client, auth_headers):
    _create_job(client, auth_headers)
    r = client.get("/api/jobs", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert "candidate_count" in r.json()[0]


def test_update_job_weights(client, auth_headers):
    job_id = _create_job(client, auth_headers).json()["id"]
    r = client.put(f"/api/jobs/{job_id}", headers=auth_headers, json={
        "weights": {"skill": 1, "experience": 1}, "hard_gate": True})
    assert r.status_code == 200
    assert r.json()["hard_gate"] is True
    # weights are normalized to sum to 1
    assert abs(sum(r.json()["weights"].values()) - 1.0) < 1e-4


def test_delete_job(client, auth_headers):
    job_id = _create_job(client, auth_headers).json()["id"]
    assert client.delete(f"/api/jobs/{job_id}", headers=auth_headers).status_code == 200
    assert client.get(f"/api/jobs/{job_id}", headers=auth_headers).status_code == 404


def test_job_not_found(client, auth_headers):
    assert client.get("/api/jobs/999999", headers=auth_headers).status_code == 404
