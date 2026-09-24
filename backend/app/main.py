from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, patients, assistant, escalations

app = FastAPI(title="ChungaMama API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(patients.router, prefix=settings.API_V1_STR + "/patients", tags=["patients"])
app.include_router(assistant.router, prefix=settings.API_V1_STR + "/assistant", tags=["assistant"])
app.include_router(escalations.router, prefix=settings.API_V1_STR + "/escalations", tags=["escalations"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "ChungaMama API"}
