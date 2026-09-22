"""API tests: resume upload validation + screening (spec §4, §21, §22, §23)."""
import io


def _job(client, headers):
    return client.post("/api/jobs", headers=headers, json={
        "title": "ML Engineer",
        "description": "Python, SQL, Machine Learning. 2+ years.",
        "requirements": [
            {"kind": "skill", "priority": "required", "value": "Python"},
            {"kind": "skill", "priority": "required", "value": "Machine Learning"},
            {"kind": "experience", "priority": "required", "value": "experience", "min_years": 2},
        ],
        "parse_with_llm": False,
    }).json()["id"]


def test_reject_unsupported_file_type(client, auth_headers):
    job_id = _job(client, auth_headers)
    files = {"files": ("resume.txt", io.BytesIO(b"hello"), "text/plain")}
    r = client.post(f"/api/jobs/{job_id}/resumes", headers=auth_headers, files=files)
    assert r.status_code == 201
    body = r.json()
    assert body["accepted"] == []
    assert body["rejected"][0]["reason"].startswith("unsupported")


def test_reject_oversized_file(client, auth_headers, monkeypatch):
    from app.utils import files as files_mod

    monkeypatch.setattr(files_mod.settings, "MAX_UPLOAD_MB", 0)
    job_id = _job(client, auth_headers)
    big = io.BytesIO(b"x" * 2048)
    r = client.post(f"/api/jobs/{job_id}/resumes", headers=auth_headers,
                    files={"files": ("r.pdf", big, "application/pdf")})
    assert r.status_code == 201
    assert r.json()["rejected"]


def test_empty_candidates_list(client, auth_headers):
    job_id = _job(client, auth_headers)
    r = client.get(f"/api/jobs/{job_id}/candidates", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_screen_empty_job_is_safe(client, auth_headers):
    job_id = _job(client, auth_headers)
    r = client.post(f"/api/jobs/{job_id}/screen", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["screened"] == 0
    assert client.get(f"/api/jobs/{job_id}/results", headers=auth_headers).json() == []


def test_export_csv(client, auth_headers):
    job_id = _job(client, auth_headers)
    r = client.get(f"/api/jobs/{job_id}/export?fmt=csv", headers=auth_headers)
    assert r.status_code == 200
    assert "Candidate" in r.text
