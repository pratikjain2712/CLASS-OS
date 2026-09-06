from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, publishers, templates, questions, papers, admin

app = FastAPI(
    title="ClassOS API",
    description="Question Paper Generator for Indian coaching institutes",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(publishers.router)
app.include_router(templates.router)
app.include_router(questions.router)
app.include_router(papers.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ClassOS API"}
