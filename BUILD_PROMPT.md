# Build Prompt — Bulk Certificate Generator

Build a complete backend API for bulk certificate generation.

## Goal
A client submits one request containing certificate information and many recipients. The API creates a generation job, processes each recipient independently, tracks progress, and allows generated PDF certificates to be downloaded.

## Required stack
- Python 3.12+
- FastAPI
- SQLAlchemy
- SQLite for local development
- ReportLab for PDF generation
- Pytest

Do not add authentication, Redis, Celery, Docker, cloud storage, multiple templates, or a frontend unless the core assignment is complete first.

## Required behavior

### 1. Create a bulk generation job
Endpoint:
POST /jobs

Example request:
{
  "course_name": "Python Bootcamp",
  "event_name": "Backend Engineering Week",
  "completion_date": "2026-10-07",
  "recipients": [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
  ]
}

Behavior:
- Validate the request.
- Reject an empty recipient list.
- Create one Job row.
- Create one Recipient row per recipient.
- Return the job ID quickly.
- Run certificate generation in a FastAPI background task.

### 2. Generate certificates independently
For every recipient:
- mark recipient as processing;
- generate one PDF using the predefined template;
- save it under generated/<job_id>/<recipient_id>.pdf;
- mark success and store the path;
- if generation fails, mark only that recipient as failed and store the error;
- continue processing remaining recipients.

### 3. Track job progress
Endpoint:
GET /jobs/{job_id}

Return:
- job ID;
- overall status: pending, processing, completed, completed_with_errors;
- total count;
- successful count;
- failed count;
- each recipient's ID, name, email, status, error, and certificate download URL when successful.

### 4. Retrieve certificates
Endpoint:
GET /jobs/{job_id}/certificates/{recipient_id}

Behavior:
- verify the recipient belongs to the job;
- return 404 if job/recipient/file does not exist;
- return the generated PDF with application/pdf.

### 5. Health endpoint
GET /health
Return {"status":"ok"}.

## Data model

Job:
- id: UUID string primary key
- course_name
- event_name nullable
- completion_date
- status
- total_count
- success_count
- failed_count
- created_at
- updated_at

Recipient:
- id: UUID string primary key
- job_id foreign key
- name
- email
- status
- certificate_path nullable
- error nullable
- created_at
- updated_at

## Processing decision
Use FastAPI BackgroundTasks for this assignment because it keeps the implementation small and allows POST /jobs to return before all PDFs are generated.

Document the limitation:
- background tasks run in the API process;
- they are not durable if the process crashes;
- for a production workload, a durable queue such as Celery/RQ/Arq plus Redis/RabbitMQ would be appropriate.

Do not introduce that complexity in V1.

## Tests
At minimum test:
1. creating a generation job;
2. validation of invalid/empty input;
3. certificate PDF generation;
4. job status/progress;
5. one recipient failing without preventing another from succeeding;
6. retrieving a generated certificate.

## Quality constraints
- Keep modules small.
- No speculative abstractions.
- No authentication unless explicitly required.
- Do not hide exceptions globally; store per-recipient generation errors.
- All important behavior must be explainable in an interview.
