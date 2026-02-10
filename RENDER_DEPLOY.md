# Render Deployment Guide - Kinyan CRM

## Architecture: Single Server

Everything runs on **ONE server** - no separate frontend/backend!
- FastAPI serves the API (`/api/*`)
- FastAPI also serves the React frontend (all other routes)
- Database: PostgreSQL on Render

## Quick Deploy (One-Click)

1. **Push to GitHub** - `git push origin main`
2. **Go to Render Dashboard** → https://dashboard.render.com
3. **New → Blueprint** ct your GitHub repo
4. **Render will auto-detect `render.yaml`** → Click "Apply"
5. **Done!** Everything deploys automatically

---

## What Gets Created

| Service | Type | URL |
|---------|------|-----|
| `kinyan-crm` | Web Service (Python) | `https://kinyan-crm.onrender.com` |
| `kinyan-crm-db` | PostgreSQL 16 | Internal connection |

---

## Manual Configuration Required

After deployment, set these **secrets** in the Render Dashboard:

### Google OAuth (for login)
- `GOOGLE_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - From Google Cloud Console  
- `GOOGLE_REDIRECT_URI` - `https://kinyan-crm.onrender.com/auth/google/callback`

### Email (SMTP)
- `SMTP_HOST` - e.g., `smtp.gmail.com`
- `SMTP_USER` - Your email
- `SMTP_PASSWORD` - App password (not regular password)
- `SMTP_FROM_EMAIL` - Sender email address

---

## Local Development

```powershell
# Single command to run everything:
.\start.ps1
```

This will:
1. Build the frontend (if needed)
2. Run database migrations
3. Start the server at http://localhost:8000

---

## Troubleshooting

### "Frontend not built" error
```powershell
cd frontend
npm install
npm run build
cd ..
```

### Database connection error
- Check that `DATABASE_URL` is set correctly
- The app auto-converts `postgres://` → `postgresql+asyncpg://`
