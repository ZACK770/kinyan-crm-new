"""
Kinyan CRM - FastAPI Application Entry Point
Minimal app.py - all logic lives in services/
Serves both API and Frontend from a single server!
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db import init_db
from api import leads_api, students_api, courses_api, dashboard_api, webhooks_api
from api import inquiries_api, exams_api, payments_api, expenses_api, attendance_api, collections_api
from api import auth_api, users_api, audit_logs_api

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

# --- System Management ---
app.include_router(audit_logs_api.router, prefix="/api/audit-logs", tags=["audit-logs"])


# Health check endpoint (for Render and monitoring)
@app.get("/health")
async def health():
    return {"status": "healthy"}


# API status endpoint
@app.get("/api/status")
async def api_status():
    return {"status": "ok", "app": "Kinyan CRM", "version": "1.0.0"}


# --- Serve Frontend (SPA) ---
# Mount static assets if frontend is built
if FRONTEND_DIR.exists():
    # Serve static assets (JS, CSS, images)
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    
    # Root route - serve frontend
    @app.get("/")
    async def serve_root():
        """Serve the React SPA at root."""
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"detail": "Frontend not built. Run: cd frontend && npm run build"}
    
    # Catch-all route for SPA - must be LAST
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA for all non-API routes."""
        # Don't serve frontend for API/webhooks routes
        if full_path.startswith(("api/", "webhooks/", "docs", "openapi.json", "redoc", "health")):
            return {"detail": "Not Found"}
        
        # Serve index.html for all other routes (SPA handles routing)
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"detail": "Frontend not built. Run: cd frontend && npm run build"}
else:
    # No frontend built - show API status at root
    @app.get("/")
    async def root():
        return {"status": "ok", "app": "Kinyan CRM", "version": "1.0.0", "frontend": "not built"}
