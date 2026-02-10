"""
Kinyan CRM - FastAPI Application Entry Point
Minimal app.py - all logic lives in services/
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from api import leads_api, students_api, courses_api, dashboard_api, webhooks_api
from api import inquiries_api, exams_api, payments_api, expenses_api, attendance_api, collections_api
from api import auth_api, users_api


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
app.include_router(exams_api.router, prefix="/api/exams", tags=["exams"])
app.include_router(attendance_api.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(payments_api.router, prefix="/api/finance", tags=["finance"])
app.include_router(collections_api.router, prefix="/api/collections", tags=["collections"])
app.include_router(expenses_api.router, prefix="/api/expenses", tags=["expenses"])
app.include_router(inquiries_api.router, prefix="/api/inquiries", tags=["inquiries"])
app.include_router(dashboard_api.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(webhooks_api.router, prefix="/webhooks", tags=["webhooks"])

# --- Auth & User Management ---
app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
app.include_router(users_api.router, prefix="/api/users", tags=["users"])


@app.get("/")
async def root():
    return {"status": "ok", "app": "Kinyan CRM", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
