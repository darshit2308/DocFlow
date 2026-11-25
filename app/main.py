"""DocFlow — AI-powered document workflow automation."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="DocFlow API",
    version="0.1.0",
    description="AI-powered document approval workflow for vendor invoices and purchase requests.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/healthz", tags=["health"])
async def healthz():
    return {"status": "ok", "service": "docflow"}
