# ארכיטקטורת Kinyan CRM - מדריך לבניית מערכות Full-Stack

## סקירה כללית

מערכת **Single-Server Full-Stack** שמשלבת:
- **Backend**: FastAPI (Python) - API אסינכרוני
- **Frontend**: React + TypeScript + Vite
- **Database**: PostgreSQL (async)
- **Deployment**: Render.com (שרת אחד)

```
┌─────────────────────────────────────────────────────────────┐
│                    Single Server (Render)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                 FastAPI Application                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   /api/*    │  │  /webhooks  │  │  /* (Frontend)  │ │ │
│  │  │  API Routes │  │   Webhooks  │  │  Static Files   │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              PostgreSQL (Render Managed)                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## מבנה תיקיות

```
project-root/
├── app.py                 # Entry point - FastAPI app
├── requirements.txt       # Python dependencies
├── alembic.ini           # Database migrations config
├── render.yaml           # Render deployment blueprint
├── start.ps1             # Local dev startup script
├── .env                  # Environment variables (local)
├── .env.example          # Template for .env
│
├── db/                   # Database layer
│   ├── __init__.py       # Engine, Session, Settings
│   ├── models.py         # SQLAlchemy models
│   └── seed.py           # Seed data (optional)
│
├── api/                  # API layer (FastAPI routers)
│   ├── __init__.py
│   ├── dependencies.py   # Auth & permission dependencies
│   ├── auth_api.py       # Authentication endpoints
│   ├── users_api.py      # User management
│   ├── leads_api.py      # Business logic endpoints
│   └── ...               # More domain routers
│
├── services/             # Business logic layer
│   ├── __init__.py
│   ├── auth.py           # JWT, password hashing
│   ├── leads.py          # Lead CRUD operations
│   └── ...               # More services
│
├── utils/                # Shared utilities
│   ├── __init__.py
│   ├── dates.py          # Date helpers
│   └── phone.py          # Phone formatting
│
├── webhooks/             # External integrations
│   ├── __init__.py
│   └── elementor.py      # Webhook handlers
│
├── alembic/              # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/         # Migration files
│
└── frontend/             # React application
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx          # React entry point
        ├── App.tsx           # Routes definition
        ├── components/       # UI components
        │   ├── layout/       # AppLayout, Sidebar, Header
        │   ├── ui/           # DataTable, Modal, Toast
        │   └── ProtectedRoute.tsx
        ├── contexts/         # React contexts
        │   └── AuthContext.tsx
        ├── lib/              # Utilities
        │   └── api.ts        # API client
        ├── pages/            # Page components
        │   ├── auth/         # Login, Register
        │   ├── Dashboard.tsx
        │   └── ...
        ├── styles/           # CSS
        │   └── globals.css
        └── types/            # TypeScript types
            └── index.ts
```

---

## שכבות הארכיטקטורה

### 1. Database Layer (`db/`)

**`db/__init__.py`** - הגדרת חיבור וסשן:
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://localhost/mydb"
    SECRET_KEY: str = "dev-secret"
    JWT_SECRET_KEY: str = "jwt-secret"
    # ... more settings
    
    class Config:
        env_file = ".env"
    
    @property
    def async_database_url(self) -> str:
        """Convert Render's postgres:// to postgresql+asyncpg://"""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

settings = Settings()
engine = create_async_engine(settings.async_database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as session:
        yield session
```

**`db/models.py`** - SQLAlchemy models:
```python
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(300), unique=True)
    full_name: Mapped[str] = mapped_column(String(300))
    hashed_password: Mapped[str | None] = mapped_column(String(500))
    permission_level: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

---

### 2. API Layer (`api/`)

**`api/dependencies.py`** - Auth middleware:
```python
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from services.auth import verify_access_token
from db import get_db

security = HTTPBearer()

async def get_current_user(
    request: Request,
    token = Depends(security),
    db = Depends(get_db)
):
    payload = verify_access_token(token.credentials)
    if not payload:
        raise HTTPException(401, "טוקן לא תקין")
    # Get user from DB
    user = await get_user_by_id(db, payload["sub"])
    return user

def require_permission(min_level: int):
    async def checker(user = Depends(get_current_user)):
        if user.permission_level < min_level:
            raise HTTPException(403, "אין הרשאה")
        return user
    return checker
```

**`api/leads_api.py`** - Router example:
```python
from fastapi import APIRouter, Depends
from db import get_db
from services import leads as lead_svc
from .dependencies import require_permission

router = APIRouter(tags=["leads"])

@router.get("/")
async def list_leads(
    db = Depends(get_db),
    user = Depends(require_permission(10))  # Viewer+
):
    return await lead_svc.get_all_leads(db)

@router.post("/")
async def create_lead(
    data: LeadCreate,
    db = Depends(get_db),
    user = Depends(require_permission(20))  # Editor+
):
    return await lead_svc.create_lead(db, data, user.id)
```

---

### 3. Services Layer (`services/`)

**`services/auth.py`** - Business logic:
```python
from jose import jwt
from passlib.context import CryptContext
from db import settings

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def verify_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    except:
        return None
```

---

### 4. Frontend Architecture

**`frontend/src/lib/api.ts`** - API Client:
```typescript
const BASE = '/api'  // Same server - relative path!

class ApiClient {
  private authToken: string | null = null

  setAuthToken(token: string | null) {
    this.authToken = token
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
      },
      ...options,
    })
    if (!res.ok) throw await res.json()
    return res.json()
  }

  get = <T>(path: string) => this.request<T>(path)
  post = <T>(path: string, body: unknown) => 
    this.request<T>(path, { method: 'POST', body: JSON.stringify(body) })
}

export const api = new ApiClient()
```

**`frontend/src/contexts/AuthContext.tsx`** - Auth state:
```typescript
export function AuthProvider({ children }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      api.setAuthToken(token)
      refreshUser().finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (credentials) => {
    const { access_token, user } = await api.post('/auth/login', credentials)
    localStorage.setItem('auth_token', access_token)
    api.setAuthToken(access_token)
    setUser(user)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, ... }}>
      {children}
    </AuthContext.Provider>
  )
}
```

---

## 5. App Entry Point (`app.py`)

```python
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db import init_db
from api import leads_api, auth_api, users_api, ...

FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"

app = FastAPI(title="My CRM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
app.include_router(leads_api.router, prefix="/api/leads", tags=["leads"])
# ... more routers

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Serve Frontend (SPA)
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"))
    
    @app.get("/")
    @app.get("/login")
    @app.get("/dashboard")
    # ... all frontend routes
    async def serve_spa():
        return FileResponse(FRONTEND_DIR / "index.html")
```

---

## 6. Deployment (`render.yaml`)

```yaml
databases:
  - name: myapp-db
    databaseName: myapp
    plan: starter
    region: frankfurt

services:
  - type: web
    name: myapp
    runtime: python
    region: frankfurt
    
    buildCommand: |
      pip install -r requirements.txt
      cd frontend && npm install && npm run build && cd ..
      alembic upgrade head
    
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: myapp-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET_KEY
        generateValue: true
```

---

## 7. Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# Security (auto-generated in production)
SECRET_KEY=random-string
JWT_SECRET_KEY=jwt-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# OAuth (optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
```

---

## 8. Permission System

| Level | Role | Capabilities |
|-------|------|--------------|
| 0 | pending | רישום ממתין לאישור |
| 10 | viewer | צפייה בלבד |
| 20 | editor | יצירה ועריכה |
| 30 | manager | ניהול צוות |
| 40 | admin | הכל כולל ניהול משתמשים |

---

## 9. פקודות פיתוח

```powershell
# הרצה מקומית
.\start.ps1

# או ידנית
uvicorn app:app --reload --port 8000

# בניית frontend
cd frontend && npm run build

# מיגרציות
alembic upgrade head           # הרץ מיגרציות
alembic revision --autogenerate -m "description"  # צור מיגרציה
```

---

## 10. יתרונות הארכיטקטורה

| יתרון | הסבר |
|-------|------|
| **שרת אחד** | פשטות בפריסה ותחזוקה |
| **Async מלא** | ביצועים גבוהים עם asyncpg + FastAPI |
| **Type Safety** | Pydantic + TypeScript |
| **Auto API Docs** | Swagger ב-`/docs` |
| **Hot Reload** | פיתוח מהיר עם `--reload` |
| **Zero Config Deploy** | `render.yaml` מגדיר הכל |

---

## 11. החלפת רכיבים (Swappable)

| רכיב | ברירת מחדל | חלופות |
|------|------------|--------|
| Database | PostgreSQL | MySQL, SQLite (dev) |
| Auth | JWT | OAuth, Session |
| Frontend | React | Vue, Svelte, HTMX |
| Deploy | Render | Railway, Fly.io, Vercel |
| CSS | CSS Modules | Tailwind, Styled Components |

---

**נוצר עבור: Kinyan CRM**  
**תאריך: פברואר 2026**  
**גרסה: 1.0.0**
