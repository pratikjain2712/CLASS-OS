from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, publishers, templates, questions, papers, admin
from app.services.data_loader import DataLoaderFactory

app = FastAPI(
    title="ClassOS API",
    description="Question Paper Generator for Indian coaching institutes",
    version="1.0.0",
)

# Initialize data loader based on environment
try:
    DataLoaderFactory.initialize()
except Exception as e:
    print(f"Warning: Data loader initialization failed: {e}")

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
