from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import jobs as jobs_module
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Job, Recipient


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_state(tmp_path, monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(jobs_module, "GENERATED_DIR", tmp_path / "generated")
    yield
    Base.metadata.drop_all(bind=engine)


def payload():
    return {
        "course_name": "Python Bootcamp",
        "event_name": "Backend Week",
        "completion_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ],
    }


def test_create_generation_job():
    response = client.post("/jobs", json=payload())

    assert response.status_code == 202
    body = response.json()
    assert body["total_count"] == 2
    assert body["id"]


def test_rejects_empty_recipients():
    data = payload()
    data["recipients"] = []

    response = client.post("/jobs", json=data)

    assert response.status_code == 422


def test_certificate_generation_creates_pdf():
    response = client.post("/jobs", json=payload())
    job_id = response.json()["id"]

    status = client.get(f"/jobs/{job_id}")
    assert status.status_code == 200

    completed = [
        item for item in status.json()["recipients"]
        if item["status"] == "completed"
    ]
    assert len(completed) == 2

    with SessionLocal() as db:
        recipient = db.get(Recipient, completed[0]["id"])
        assert recipient is not None
        assert recipient.certificate_path is not None
        pdf_path = Path(recipient.certificate_path)
        assert pdf_path.exists()
        assert pdf_path.read_bytes().startswith(b"%PDF")


def test_job_status_reports_progress_result():
    response = client.post("/jobs", json=payload())
    job_id = response.json()["id"]

    status = client.get(f"/jobs/{job_id}")

    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "completed"
    assert body["total_count"] == 2
    assert body["success_count"] == 2
    assert body["failed_count"] == 0


def test_individual_certificate_failure_does_not_stop_job(monkeypatch):
    original = jobs_module.generate_certificate_pdf

    def fail_for_bob(**kwargs):
        if kwargs["recipient_name"] == "Bob":
            raise RuntimeError("simulated generation failure")
        return original(**kwargs)

    monkeypatch.setattr(jobs_module, "generate_certificate_pdf", fail_for_bob)

    response = client.post("/jobs", json=payload())
    job_id = response.json()["id"]

    status = client.get(f"/jobs/{job_id}")
    body = status.json()

    assert body["status"] == "completed_with_errors"
    assert body["success_count"] == 1
    assert body["failed_count"] == 1

    recipients = {item["name"]: item for item in body["recipients"]}
    assert recipients["Alice"]["status"] == "completed"
    assert recipients["Bob"]["status"] == "failed"
    assert "simulated generation failure" in recipients["Bob"]["error"]


def test_retrieve_generated_certificate():
    response = client.post("/jobs", json=payload())
    job_id = response.json()["id"]

    status = client.get(f"/jobs/{job_id}").json()
    recipient = next(
        item for item in status["recipients"]
        if item["status"] == "completed"
    )

    certificate = client.get(recipient["certificate_url"])

    assert certificate.status_code == 200
    assert certificate.headers["content-type"] == "application/pdf"
    assert certificate.content.startswith(b"%PDF")
