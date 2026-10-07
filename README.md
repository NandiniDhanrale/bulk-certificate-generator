# Bulk Certificate Generator

Backend API for creating many participant certificates in one request.

## Current build plan
- FastAPI
- SQLAlchemy
- SQLite for local development
- ReportLab PDF generation
- FastAPI BackgroundTasks
- Pytest

The API creates one generation job, validates recipients, processes recipients independently, tracks progress, and serves generated PDF certificates.

Implementation work is being developed on a feature branch before merging to `main`.
