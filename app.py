"""
Kinyan CRM - FastAPI Application Entry Point
Minimal app.py - all logic lives in services/
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from api import leads_api, students_api, courses_api, dashboard_api, webhooks_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables if needed."""
    await init_db()
    yield


app = FastAPI(
    title="Kinyan CRM",
    description="מערכת CRM לניהול שיווק ולמידה - קניין הוראה",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routes ---
app.include_router(leads_api.router, prefix="/api/leads", tags=["leads"])
app.include_router(students_api.router, prefix="/api/students", tags=["students"])
app.include_router(courses_api.router, prefix="/api/courses", tags=["courses"])
app.include_router(dashboard_api.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(webhooks_api.router, prefix="/webhooks", tags=["webhooks"])


@app.get("/")
async def root():
    return {"status": "ok", "app": "Kinyan CRM", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
