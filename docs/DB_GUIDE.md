# Kinyan CRM — Database Guide

> **כלל ברזל: המערכת עובדת אך ורק מול PostgreSQL.**
> לא SQLite, לא MySQL, לא שום דבר אחר — בכל סביבה, בכל deployment.

---

## פרטי חיבור — Render PostgreSQL (Production)

| פרמטר | ערך |
|--------|-----|
| **Hostname (internal)** | `dpg-d65jjr56ubrc7396u8r0-a` |
| **Hostname (external)** | `dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com` |
| **Port** | `5432` |
| **Database** | `crm_new` |
| **Username** | `crm_new_user` |
| **Password** | `45RsFRWnUuvPQFAttG37PxisVlC79HZv` |

### Connection URLs

**Internal** (שירותי Render בלבד):
```
postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a/crm_new
```

**External** (חיבור ממחשב מקומי / CI / Make):
```
postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new
```

**Async (Python — asyncpg):**
```
postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new
```

### PSQL Command (חיבור מהטרמינל)
```bash
PGPASSWORD=45RsFRWnUuvPQFAttG37PxisVlC79HZv psql -h dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com -U crm_new_user crm_new
```

---

## קובץ `.env`

קובץ `.env` בשורש הפרויקט מכיל את ה-URL האמיתי. דוגמה:

```dotenv
DATABASE_URL=postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new
SECRET_KEY=<random-secret>
API_KEY=<webhook-key>
```

- **מקומי / CI / Make**: תמיד External hostname (עם `.frankfurt-postgres.render.com`)
- **Render service**: Internal hostname (בלי `.frankfurt-postgres...`)
- הפורמט **חייב** לפתוח ב- `postgresql+asyncpg://` — המערכת משתמשת ב-asyncpg

---

## ארכיטקטורת DB

### Driver & ORM
- **SQLAlchemy 2.0** (async mode) עם `asyncpg`
- **Alembic** למיגרציות
- **אין fallback** ל-SQLite — אין תמיכה, אין בדיקות עם SQLite

### קובצי הגדרות

| קובץ | תפקיד |
|-------|--------|
| `db/__init__.py` | Engine, session factory, `Base`, הגדרות |
| `db/models.py` | כל המודלים (17 ישויות + טבלאות ילד) |
| `db/seed.py` | נתוני בסיס (קורסים, אנשי מכירות, מוצרים) |
| `alembic.ini` | הגדרות Alembic (URL נדרס מ-`.env`) |
| `alembic/env.py` | Alembic async runner |
| `alembic/versions/` | קבצי מיגרציה |

### זרימת חיבור

```
.env  →  db/__init__.py (Settings)  →  create_async_engine()
                                    →  Alembic env.py (overrides alembic.ini)
```

`alembic.ini` מכיל URL ברירת מחדל, אבל `alembic/env.py` **דורס** אותו עם `settings.DATABASE_URL` מה-`.env`.

---

## מיגרציות (Alembic)

### יצירת מיגרציה חדשה (אחרי שינוי models.py)
```bash
alembic revision --autogenerate -m "describe change"
```

### הרצת מיגרציות
```bash
alembic upgrade head
```

### חזרה לגרסה קודמת
```bash
alembic downgrade -1
```

### בדיקת סטטוס
```bash
alembic current
alembic history
```

> **חשוב:** תמיד לבדוק את קובץ המיגרציה שנוצר לפני `upgrade`. Alembic לפעמים יוצר פקודות לא מדויקות.

---

## טבלאות

ראו [ENTITIES_SPEC.md](ENTITIES_SPEC.md) לאפיון מלא של כל 17 הישויות.

### רשימת טבלאות
```
salespeople                   — entity 4:  אנשי מכירות
campaigns                     — entity 3:  קמפיינים
campaign_salesperson_links    — child:     לינקים לאנשי מכירות בקמפיין
campaign_landing_links        — child:     לינקים לדפי נחיתה
products                      — helper:    מוצרים
courses                       — entity 8:  קורסים
course_modules                — entity 9:  שיעורים/מודולים
lecturers                     — entity 10: מרצים
coupons                       — entity 15: קופונים
leads                         — entity 1:  לידים
lead_interactions             — helper:    תקשורת + IVR + אתר
lead_products                 — helper:    מוצרי ליד
students                      — entity 2:  תלמידים
enrollments                   — helper:    הרשמות לקורסים
payments                      — entity 13: תשלומים
exams                         — entity 11: מבחנים
exam_submissions              — child:     הגשות מבחנים
sales_tasks                   — entity 5:  משימות מכירות
task_reports                  — child:     דיווחי ביצוע
lead_messages                 — entity 6:  הודעות לידים
inquiries                     — entity 7:  פניות נכנסות
inquiry_responses             — child:     שרשור תגובות
attendance                    — entity 12: נוכחות ומטלות
commitments                   — entity 14: התחייבויות
collections                   — entity 16: גביה
expenses                      — entity 17: הוצאות
```

---

## כלים שימושיים

### חיבור מ-Python (בדיקה מהירה)
```python
import asyncio, asyncpg

async def test():
    conn = await asyncpg.connect(
        "postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
    )
    version = await conn.fetchval("SELECT version()")
    print(version)
    await conn.close()

asyncio.run(test())
```

### רשימת טבלאות קיימות
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' ORDER BY table_name;
```

### ספירת רשומות בכל הטבלאות
```sql
SELECT schemaname, relname, n_live_tup
FROM pg_stat_user_tables ORDER BY n_live_tup DESC;
```

---

## הנחיות לפיתוח

1. **לעולם** לא לכתוב `sqlite://` בשום קונפיגורציה — המערכת PostgreSQL only.
2. **לעולם** לא לעקוף את Alembic ולשנות את ה-DB ידנית — כל שינוי דרך מיגרציה.
3. **לעולם** לשמור על `.env` מעודכן — זה מקור האמת לחיבור.
4. הקוד ב- `db/__init__.py` קורא את `DATABASE_URL` מ-`.env` → מעביר ל-engine → מעביר ל-Alembic.
5. כל שינוי במבנה טבלאות → עדכון `models.py` → `alembic revision --autogenerate` → בדיקה → `alembic upgrade head`.
