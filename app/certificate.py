from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


def generate_certificate_pdf(
    *,
    output_path: Path,
    recipient_name: str,
    course_name: str,
    event_name: str | None,
    completion_date: date,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = landscape(A4)
    pdf = canvas.Canvas(str(output_path), pagesize=(width, height))

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 120, "CERTIFICATE OF COMPLETION")

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width / 2, height - 190, "This certifies that")

    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 245, recipient_name)

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(
        width / 2,
        height - 300,
        f"successfully completed {course_name}",
    )

    if event_name:
        pdf.drawCentredString(width / 2, height - 335, f"at {event_name}")

    pdf.drawCentredString(
        width / 2,
        height - 385,
        completion_date.isoformat(),
    )

    pdf.save()
