"""AI question generation via Claude API — placeholder for Phase 2."""
from app.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.generate_ai_questions")
def generate_ai_questions(self, job_id: str):
    # Phase 2: RAG retrieval → Claude API → save to question bank
    pass
