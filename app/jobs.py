from pathlib import Path

from sqlalchemy import select

from app.certificate import generate_certificate_pdf
from app.database import SessionLocal
from app.models import Job, Recipient

GENERATED_DIR = Path("generated")


def process_job(job_id: str) -> None:
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if job is None:
            return

        job.status = "processing"
        db.commit()

        recipients = db.scalars(
            select(Recipient).where(Recipient.job_id == job_id)
        ).all()

        success_count = 0
        failed_count = 0

        for recipient in recipients:
            recipient.status = "processing"
            recipient.error = None
            db.commit()

            try:
                output_path = GENERATED_DIR / job.id / f"{recipient.id}.pdf"
                generate_certificate_pdf(
                    output_path=output_path,
                    recipient_name=recipient.name,
                    course_name=job.course_name,
                    event_name=job.event_name,
                    completion_date=job.completion_date,
                )
                recipient.status = "completed"
                recipient.certificate_path = str(output_path)
                success_count += 1
            except Exception as exc:
                recipient.status = "failed"
                recipient.error = str(exc)
                recipient.certificate_path = None
                failed_count += 1

            job.success_count = success_count
            job.failed_count = failed_count
            db.commit()

        job.status = "completed" if failed_count == 0 else "completed_with_errors"
        db.commit()
