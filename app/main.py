from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.jobs import process_job
from app.models import Job, Recipient
from app.schemas import JobCreate, JobCreated, JobStatus, RecipientStatus

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bulk Certificate Generator")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs", response_model=JobCreated, status_code=202)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobCreated:
    job_id = str(uuid4())

    job = Job(
        id=job_id,
        course_name=payload.course_name.strip(),
        event_name=payload.event_name.strip() if payload.event_name else None,
        completion_date=payload.completion_date,
        status="pending",
        total_count=len(payload.recipients),
    )
    db.add(job)

    for item in payload.recipients:
        db.add(
            Recipient(
                id=str(uuid4()),
                job_id=job_id,
                name=item.name,
                email=str(item.email),
                status="pending",
            )
        )

    db.commit()
    background_tasks.add_task(process_job, job_id)

    return JobCreated(id=job.id, status=job.status, total_count=job.total_count)


@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobStatus:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")

    recipients = db.scalars(
        select(Recipient).where(Recipient.job_id == job_id)
    ).all()

    return JobStatus(
        id=job.id,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        recipients=[
            RecipientStatus(
                id=recipient.id,
                name=recipient.name,
                email=recipient.email,
                status=recipient.status,
                error=recipient.error,
                certificate_url=(
                    f"/jobs/{job.id}/certificates/{recipient.id}"
                    if recipient.status == "completed"
                    else None
                ),
            )
            for recipient in recipients
        ],
    )


@app.get("/jobs/{job_id}/certificates/{recipient_id}")
def get_certificate(
    job_id: str,
    recipient_id: str,
    db: Session = Depends(get_db),
):
    recipient = db.scalar(
        select(Recipient).where(
            Recipient.id == recipient_id,
            Recipient.job_id == job_id,
        )
    )

    if recipient is None:
        raise HTTPException(status_code=404, detail="recipient not found")

    if recipient.status != "completed" or not recipient.certificate_path:
        raise HTTPException(status_code=404, detail="certificate not available")

    path = Path(recipient.certificate_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="certificate file not found")

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=f"{recipient.name}-certificate.pdf",
    )
