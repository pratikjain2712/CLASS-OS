"""PDF ingestion pipeline — placeholder for Phase 2."""
from app.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.ingest_pdf")
def ingest_pdf(self, job_id: str):
    # Phase 2: pdfplumber → chapter chunks → embeddings
    pass
