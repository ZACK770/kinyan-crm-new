"""
Kinyan CRM - FastAPI Application Entry Point
Minimal app.py - all logic lives in services/
Serves both API and Frontend from a single server!
"""
# Load .env FIRST, before any other imports that use environment variables
from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from db import init_db
from api import (
    leads_api, students_api, courses_api, dashboard_api, webhooks_api
    , inquiries_api, exams_api, payments_api, expenses_api, attendance_api, collections_api
    , auth_api, users_api, audit_logs_api, campaigns_api, files_api, sales_assignment_api
    , course_tracks_api, lecturers_api, messages_api, templates_api, lead_conversion_api
    , import_api, import_generic_api, webhook_logs_api, webhook_queue_api, export_api, topics_api
    , inbound_emails_api, sales_simulator_api, popup_api, table_prefs_api, chat_api
)
from api import tasks_api
from api import salespeople_api
from webhooks import inbound_email as inbound_email_webhook
from webhooks import regulation_approval

# Frontend build directory
FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"


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
app.include_router(lead_conversion_api.router)  # Lead conversion endpoints (uses /api/leads prefix)
app.include_router(students_api.router, prefix="/api/students", tags=["students"])
app.include_router(courses_api.router, prefix="/api/courses", tags=["courses"])
app.include_router(course_tracks_api.router)
app.include_router(lecturers_api.router, prefix="/api/lecturers", tags=["lecturers"])
app.include_router(exams_api.router, prefix="/api/exams", tags=["exams"])
app.include_router(attendance_api.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(payments_api.router, prefix="/api/finance", tags=["finance"])
app.include_router(collections_api.router, prefix="/api/collections", tags=["collections"])
app.include_router(expenses_api.router, prefix="/api/expenses", tags=["expenses"])
app.include_router(inquiries_api.router, prefix="/api/inquiries", tags=["inquiries"])
app.include_router(dashboard_api.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(campaigns_api.router, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(tasks_api.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(webhooks_api.router, prefix="/webhooks", tags=["webhooks"])

# --- Auth & User Management ---
app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
app.include_router(users_api.router, prefix="/api/users", tags=["users"])
app.include_router(table_prefs_api.router, prefix="/api/table-prefs", tags=["table-prefs"])

# --- System Management ---
app.include_router(audit_logs_api.router, prefix="/api/audit-logs", tags=["audit-logs"])
app.include_router(files_api.router, prefix="/api/files", tags=["files"])
app.include_router(sales_assignment_api.router, prefix="/api/sales-assignment-rules", tags=["sales-assignment"])
app.include_router(salespeople_api.router, prefix="/api/salespeople", tags=["salespeople"])
app.include_router(webhook_logs_api.router, prefix="/api/webhook-logs", tags=["webhook-logs"])
app.include_router(webhook_queue_api.router, tags=["webhook-queue"])
app.include_router(messages_api.router, prefix="/api/messages", tags=["messages"])
app.include_router(templates_api.router, prefix="/api/templates", tags=["templates"])
app.include_router(import_api.router, prefix="/api/admin", tags=["import"])
app.include_router(import_generic_api.router, prefix="/api/admin/import", tags=["import-generic"])
app.include_router(export_api.router, prefix="/api/export", tags=["export"])
app.include_router(topics_api.router, prefix="/api/topics", tags=["topics"])
app.include_router(inbound_emails_api.router, prefix="/api/inbound-emails", tags=["inbound-emails"])
app.include_router(inbound_email_webhook.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(regulation_approval.router, prefix="/webhooks", tags=["webhooks"])

# --- Chat ---
app.include_router(chat_api.router, prefix="/api/chat", tags=["chat"])

# --- Sales Simulator (AI Training) ---
app.include_router(sales_simulator_api.router, prefix="/api/sales-simulator", tags=["sales-simulator"])

# --- Popup Announcements ---
app.include_router(popup_api.router, prefix="/api/popups", tags=["popups"])


# Health check endpoint (for Render and monitoring)
@app.get("/health")
async def health():
    return {"status": "healthy"}


# API status endpoint
@app.get("/api/status")
async def api_status():
    return {"status": "ok", "app": "Kinyan CRM", "version": "1.0.0"}




# --- Unified Server: API + Frontend SPA ---
# Instead of a catch-all route (which conflicts with API routers),
# we use a 404 exception handler. This way:
#   - All API/webhook routes work normally via their routers
#   - Only REAL 404s on non-API paths get redirected to React SPA
if FRONTEND_DIR.exists():
    # Mount static assets (JS/CSS/Images generated by Vite)
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    # Root route - serve React app
    @app.get("/", include_in_schema=False)
    async def serve_root():
        return FileResponse(FRONTEND_DIR / "index.html")

    # SPA fallback: catch 404s and serve index.html for frontend routes
    @app.exception_handler(404)
    async def spa_fallback(request: Request, exc: StarletteHTTPException):
        path = request.url.path
        # API and webhook 404s stay as real 404s
        if path.startswith("/api/") or path.startswith("/webhooks/"):
            return JSONResponse(status_code=404, content={"detail": str(exc.detail)})
        # Check if a physical file exists (favicon.ico, manifest.json, etc.)
        file_path = FRONTEND_DIR / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Everything else: let React Router handle it
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "status": "warning",
            "message": "Frontend not built. Run: cd frontend && npm run build",
            "api_status": "online"
        }

