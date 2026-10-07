# Bulk Certificate Generator

A FastAPI backend that accepts one bulk certificate-generation request, processes recipients independently, tracks progress, and serves generated PDF certificates.

## Stack
- Python 3.12+
- FastAPI
- SQLAlchemy
- SQLite
- ReportLab
- Pytest

## Why this design

The assignment is a bulk-processing API, so the client submits one job containing many recipients instead of sending one request per certificate.

FastAPI `BackgroundTasks` keeps the first version simple: `POST /jobs` can return a job ID while certificate generation continues outside the request handler. Each recipient is processed in its own `try/except`, so one failed PDF does not stop the rest of the job.

This is intentionally not a durable distributed worker system. If the API process crashes, an in-process background task can be lost. For a production workload that requires durable retries or multiple workers, the next step would be a queue such as Celery/RQ/Arq backed by Redis or RabbitMQ.

Authentication, multiple templates, a frontend, and cloud storage are not added because they are outside the required scope.

## Setup

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Create a generation job

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "course_name": "Python Bootcamp",
    "event_name": "Backend Engineering Week",
    "completion_date": "2026-10-07",
    "recipients": [
      {"name": "Alice", "email": "alice@example.com"},
      {"name": "Bob", "email": "bob@example.com"}
    ]
  }'
```

Example response:

```json
{
  "id": "<job-id>",
  "status": "pending",
  "total_count": 2
}
```

## Check job status

```bash
curl http://127.0.0.1:8000/jobs/<job-id>
```

The response contains the overall job status, totals, per-recipient status, any failure reason, and a certificate URL for each successful recipient.

## Retrieve a certificate

```bash
curl -o certificate.pdf \
  http://127.0.0.1:8000/jobs/<job-id>/certificates/<recipient-id>
```

Generated PDFs are stored under:

```text
generated/<job-id>/<recipient-id>.pdf
```

## State transitions

```text
Job:       pending -> processing -> completed
                              \-> completed_with_errors

Recipient: pending -> processing -> completed
                                    \-> failed
```

## Run tests

```bash
pytest -q
```

Tests cover:
1. creating a generation job;
2. request validation;
3. PDF certificate generation;
4. job status/progress;
5. isolation of an individual certificate failure;
6. retrieval of generated certificates.

## API summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/jobs` | Create bulk generation job |
| GET | `/jobs/{job_id}` | Read progress/results |
| GET | `/jobs/{job_id}/certificates/{recipient_id}` | Download PDF |

## Important implementation decisions

### One job, many recipients
The API models the operation as a parent `Job` with many `Recipient` rows. This makes progress and partial failure explicit.

### Failure isolation
Certificate generation is wrapped per recipient. A failure updates only that recipient to `failed`; processing then continues.

### Database versus generated files
Job metadata, recipient status, file paths, and errors live in the relational database. PDF bytes live on disk.

### BackgroundTasks instead of Celery
The assignment does not require distributed processing. Adding Redis and Celery would increase setup and code surface before solving a demonstrated need. The limitation of in-process background work is documented above.

## Project structure

```text
app/
  main.py          API routes
  database.py      SQLAlchemy engine/session
  models.py        relational models
  schemas.py       request/response validation
  jobs.py          bulk processing workflow
  certificate.py   PDF generation
tests/
  test_api.py
generated/         runtime output, ignored by git
```

See `BUILD_PROMPT.md` for the complete implementation contract.
