---
description: נוהל בדיקה אחרי עדכונים במערכת
---

# נוהל בדיקה אחרי עדכונים

כשה-AI מסיים לעדכן קוד (פרונטאנד או בקאנד), הרץ את הפקודות הבאות:

## 1️⃣ בדיקת שינויים בפרונטאנד

אם היו שינויים ב-`frontend/src`:

```powershell
cd frontend
npm run build
cd ..
```

**או** אם השרת כבר רץ - פשוט **רענן את הדפדפן** (`F5`)

---

## 2️⃣ בדיקת שינויים בבקאנד

אם היו שינויים ב-`api/`, `services/`, `db/models.py`:

### אם השרת רץ:
- **Uvicorn עם reload** יטען מחדש אוטומטית ✅
- רק תבדוק בטרמינל שאין שגיאות

### אם השרת לא רץ:
```powershell
.\start.ps1
```

---

## 3️⃣ שינויים במודלים (Database)

אם היו שינויים ב-`db/models.py`:

```powershell
# יצירת migration חדש
$env:DATABASE_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
& ".venv311\Scripts\python.exe" -m alembic revision --autogenerate -m "תיאור השינוי"

# הרצת migrations
& ".venv311\Scripts\python.exe" -m alembic upgrade head
```

---

## 4️⃣ בדיקה מהירה

לאחר כל עדכון:

1. ✅ **פתח את הדפדפן**: `http://localhost:8001`
2. ✅ **בדוק Console** (F12) - אין שגיאות אדומות
3. ✅ **נסה את הפיצ'ר החדש** - וודא שהוא עובד
4. ✅ **בדוק שלא שברת דברים אחרים** - ניווט מהיר בין דפים

---

## 🚨 אם יש שגיאות

1. **שגיאות בדפדפן** → העתק את השגיאה ושלח ל-AI
2. **שגיאות בשרת** → בדוק טרמינל של uvicorn
3. **422/500 errors** → בדוק את ה-Network tab (F12)

---

## 📝 טיפ מהיר

אם אתה רוצה לוודא שהכל עדכני:

```powershell
# עצור את השרת (Ctrl+C)
cd frontend
npm run build
cd ..
.\start.ps1
```

זה יבנה הכל מחדש ויפעיל את השרת עם הקוד העדכני ביותר.
