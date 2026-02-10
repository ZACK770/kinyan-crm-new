# ✅ נוהל בדיקה אחרי עדכוני AI

## תזכורת מהירה - הרץ אחרי כל עדכון:

### 🎨 עדכונים בפרונטאנד
```powershell
cd frontend
npm run build
cd ..
```
**ואז רענן דפדפן** (`F5`)

---

### ⚙️ עדכונים בבקאנד
- אם השרת רץ עם reload → **אוטומטי** ✅
- אם לא → `.\start.ps1`

---

### 🗄️ שינויים במודלים (DB)
```powershell
$env:DATABASE_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
& ".venv311\Scripts\python.exe" -m alembic revision --autogenerate -m "תיאור"
& ".venv311\Scripts\python.exe" -m alembic upgrade head
```

---

### 🔍 בדיקה מהירה
1. פתח `http://localhost:8001`
2. בדוק Console (F12) - אין שגיאות
3. נסה את הפיצ'ר החדש
4. וודא שלא שברת דברים אחרים

---

**💡 טיפ:** אם משהו לא עובד - העתק את השגיאה מה-Console ושלח ל-AI
