# Render Deployment Guide - Kinyan CRM

## Quick Deploy (One-Click)

1. **Push to GitHub** - Make sure your repo is on GitHub
2. **Go to Render Dashboard** → https://dashboard.render.com
3. **New → Blueprint** → Connect your GitHub repo
4. **Render will auto-detect `render.yaml`** → Click "Apply"
5. **Done!** All services will be created automatically

---

## What Gets Created

| Service | Type | URL |
|---------|------|-----|
| `kinyan-crm-api` | Web Service (Python) | `https://kinyan-crm-api.onrender.com` |
| `kinyan-crm-frontend` | Static Site (React) | `https://kinyan-crm-frontend.onrender.com` |
| `kinyan-crm-db` | PostgreSQL 16 | Internal connection |

---

## Manual Configuration Required

After deployment, set these **secrets** in the Render Dashboard:

### Google OAuth (for login)
- `GOOGLE_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - From Google Cloud Console  
- `GOOGLE_REDIRECT_URI` - `https://kinyan-crm-frontend.onrender.com/auth/google/callback`

### Email (SMTP)
- `SMTP_HOST` - e.g., `smtp.gmail.com`
- `SMTP_USER` - Your email
- `SMTP_PASSWORD` - App password (not regular password)
- `SMTP_FROM_EMAIL` - Sender email address

---

## Auto-Generated Secrets

These are generated automatically by Render:
- `SECRET_KEY` - App secret
- `JWT_SECRET_KEY` - JWT signing key  
- `API_KEY` - Webhook authentication

---

## Environment Variables Reference

| Variable | Source | Description |
|----------|--------|-------------|
| `DATABASE_URL` | Auto-linked to DB | PostgreSQL connection string |
| `FRONTEND_URL` | Auto-linked | Frontend host for CORS/emails |
| `VITE_API_URL` | Auto-linked | Backend URL for frontend |
| `PYTHON_VERSION` | `3.11` | Python runtime |
| `NODE_VERSION` | `20` | Node.js runtime |

---

## Database Migrations

Migrations run automatically during each deploy (`alembic upgrade head`).

To run manually:
```bash
# SSH into your Render service, or run locally with Render DB URL
alembic upgrade head
```

---

## Upgrade to Production

Edit `render.yaml` and change `plan: starter` to `plan: standard` for:
- Better performance
- More memory
- Higher database limits

---

## Troubleshooting

### Build fails with database error
- Check that PostgreSQL is fully created before API builds
- Render should handle this automatically with blueprint

### Frontend can't connect to API
- Verify `VITE_API_URL` is set correctly
- Check CORS settings in `app.py` allow the frontend origin

### "Invalid database driver" error
- The app auto-converts `postgres://` → `postgresql+asyncpg://`
- This is handled in `db/__init__.py` → `async_database_url` property

---

## Local Development

```bash
# Backend
pip install -r requirements.txt
uvicorn app:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

Create `.env` file based on `.env.example` for local settings.
