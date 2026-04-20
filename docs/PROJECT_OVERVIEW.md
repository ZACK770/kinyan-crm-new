# Kinyan CRM — סקירת פרויקט מקיפה

> **עדכון אחרון:** אפריל 2026  
> **גרסה:** 2.x (פרודקשן פעיל)

---

## 1. מטרת הפרויקט

### 1.1 מי הלקוח

**קניין הוראה** — מוסד לימודי תורני (כולל / בית מדרש) המציע קורסי הלכה פרקטיים לציבור הרחב. הקורסים מכסים נושאים כגון: שבת, איסור והיתר, טהרה, ממונות, נזיקין, וסמיכה להוראה.

### 1.2 הבעיה שפותרת המערכת

מוסד לימודי הפועל בקנה מידה מסחרי חייב לנהל בו-זמנית:
- **מאות לידים** שמגיעים ממקורות שונים (אתר, טלפון IVR, ידני)
- **תהליך מכירות** עם מספר אנשי מכירות ומשימות מעקב
- **סליקה ותשלומים** — חד-פעמי, תשלומים, הוראות קבע
- **ניהול תלמידים** — רישום לקורסים, נוכחות, מבחנים, התקדמות
- **ניהול קורסים** — מודולים, מרצים, לוחות זמנים, הקלטות

לפני המערכת, כל אלה נוהלו בגיליונות אקסל נפרדים ללא חיבור ביניהם — מה שגרם לכפילויות, שגיאות ועיוורון מידע.

### 1.3 המטרה המרכזית

**מערכת CRM אחת** שמנהלת את מחזור החיים המלא:

```
ליד חדש → שיחת מכירות → בחירת מוצר → סליקה → תלמיד רשום → קורס → בוגר
```

כולל:
- אוטומציה של הגעת לידים (webhooks)
- חלוקה אוטומטית לאנשי מכירות (round-robin)
- קישור ישיר לשע"מ הישראלי (נדרים פלוס) לסליקה
- מעקב מלא אחר כל נקודת מגע עם הלקוח
- דשבורד ניהולי עם מדדי ביצוע

---

## 2. ערימת הטכנולוגיות (Tech Stack)

### 2.1 Backend

| רכיב | טכנולוגיה | תפקיד |
|------|-----------|--------|
| Framework | **FastAPI** (Python 3.11) | API אסינכרוני, Swagger מובנה |
| ORM | **SQLAlchemy 2.x** (async) | מיפוי DB, Mapped types |
| Database | **PostgreSQL** (asyncpg driver) | אחסון כל הנתונים |
| Migrations | **Alembic** | ניהול גרסאות DB |
| Auth | **JWT** (python-jose) + bcrypt | אימות משתמשים |
| Validation | **Pydantic v2** | סכמות קלט/פלט |
| HTTP Client | **httpx** (async) | קריאות ל-API חיצוני (נדרים) |
| Env | **python-dotenv** + pydantic-settings | קריאת משתני סביבה |

### 2.2 Frontend

| רכיב | טכנולוגיה | תפקיד |
|------|-----------|--------|
| Framework | **React 18** + TypeScript | UI אינטראקטיבי |
| Build | **Vite** | בנייה מהירה, HMR |
| Styling | **TailwindCSS** | עיצוב utility-first |
| Routing | **React Router v6** | ניהול נתיבים (SPA) |
| State | React Context + useState/useEffect | מצב גלובלי (Auth) |
| API Client | Fetch API (wrapper מותאם) | תקשורת עם Backend |
| Icons | Lucide React | אייקונים |

### 2.3 אינטגרציות חיצוניות

| שירות | תפקיד | פרוטוקול |
|-------|--------|-----------|
| **נדרים פלוס** | שע"מ ישראלי — סליקת אשראי + הוראות קבע | HTTP API (DebitCard.aspx, DebitKeva.aspx) + Webhooks |
| **אלמנטור** | טפסי הרשמה מהאתר | Webhook (POST JSON) |
| **ימות המשיח** | מרכזיית IVR — פניות טלפוניות | Webhook (POST JSON/form-data) |
| **Google OAuth** | כניסה עם חשבון גוגל | OAuth 2.0 |
| **Make.com** | סינכרון מיילים נכנסים | Webhook |
| **Cloudinary / Storage** | העלאת קבצים | HTTP API |

### 2.4 תשתית ופריסה

| רכיב | טכנולוגיה |
|------|-----------|
| Hosting | **Render.com** (single web service) |
| DB Hosting | **Render Managed PostgreSQL** (Frankfurt) |
| Branch | `fitchers` (auto-deploy לכל push) |
| URL פרודקשן | https://kinyan-crm-new-1.onrender.com/ |
| Process Manager | **uvicorn** (`--host 0.0.0.0 --port $PORT`) |
| Python venv | `.venv311` (Python 3.11) |

---

## 3. ארכיטקטורת המערכת

### 3.1 מבנה Single-Server

```
┌─────────────────────────────────────────────┐
│              Render Web Service              │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  /api/*  │  │/webhooks │  │  /* (SPA) │ │
│  │  FastAPI │  │ Handlers │  │  React    │ │
│  └──────────┘  └──────────┘  └───────────┘ │
│                     │                       │
│  ┌──────────────────────────────────────┐   │
│  │      PostgreSQL (Render Managed)     │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

הפרונטאנד בנוי ל-`frontend/dist/` ומוגש ישירות מ-FastAPI כ-Static Files. אין שרת נפרד לפרונטאנד.

### 3.2 שכבות הקוד

```
app.py              → Entry point, router registration, CORS, SPA fallback
├── api/            → FastAPI routers (endpoint handlers + validation)
├── services/       → Business logic (pure Python, no HTTP awareness)
├── db/
│   ├── models.py   → SQLAlchemy ORM models
│   └── __init__.py → Engine, Session, Settings
├── webhooks/       → Webhook handlers (Elementor, Yemot, Nedarim)
└── utils/          → Phone normalization, date helpers
```

### 3.3 מערכת הרשאות

| רמה | תפקיד | יכולות |
|-----|--------|--------|
| 0 | pending | ממתין לאישור |
| 10 | viewer | צפייה בלבד |
| 20 | editor | יצירה ועריכה |
| 30 | manager | ניהול צוות ומשימות |
| 40 | admin | גישה מלאה + ניהול משתמשים |

---

## 4. הישויות המרכזיות (Domain Model)

המערכת בנויה סביב **21 ישויות** מרכזיות המכסות את מחזור החיים המלא:

### 4.1 מסלול המכירה

```
Campaign (קמפיין) → Lead (ליד) → LeadProduct (מוצר נבחר)
     ↓                  ↓               ↓
Salesperson        SalesTask       Payment (תשלום ראשון)
(איש מכירות)      (משימת מעקב)         ↓
                        ↓          Student (תלמיד)
                  LeadInteraction
                  (תיעוד כל פנייה)
```

### 4.2 מסלול הלמידה

```
Course (קורס) → Topic (נושא) → Lesson (מפגש)
     ↓               ↓
Enrollment       Attendance (נוכחות)
(הרשמה)         Assignment (מטלה)
     ↓
  Exam (מבחן) → ExamSubmission (ציון)
```

### 4.3 מסלול הכספים

```
LeadProduct → Payment (תשלום חד-פעמי/תשלומים)
                   ↓
            Commitment (הוראת קבע) → Collection (גביה חודשית)
```

### 4.4 סטטוסי ליד (Life Cycle)

```
ליד חדש → חיוג ראשון → במעקב → מתעניין → נסלק → ליד סגור-לקוח
                                              ↘ ליד סגור-לא רלוונטי
```

---

## 5. יכולות המערכת (Feature Map)

### 5.1 ניהול לידים ✅

- קבלת לידים אוטומטית מ-3 מקורות: אלמנטור, ימות המשיח, גנרי
- מניעת כפילויות לפי מספר טלפון
- שיוך אוטומטי לאיש מכירות (round-robin)
- תיעוד כל פנייה (`LeadInteraction`) — שיחה יוצאת/נכנסת, טופס אתר, IVR
- מעקב מלא: מקור הגעה, קמפיין, הודעת ליד, תאריך שיחה הבאה
- ייבוא לידים מאקסל (`/api/import`)
- סינון, חיפוש, מיון, ייצוא לאקסל

### 5.2 ניהול מכירות ✅

- דשבורד אנשי מכירות עם מדדי ביצוע
- משימות מכירות עם עדיפות, תאריך יעד, דיווח ביצוע
- מנגנון שיוך חכם (Sales Assignment) עם העדפות קמפיין
- סימולטור מכירות לבדיקת כללי שיוך
- היסטוריית כל הלידים לפי איש מכירות

### 5.3 תהליך תשלום ✅

שילוב מלא עם **נדרים פלוס**:

| סוג | API | שימוש |
|-----|-----|--------|
| סליקה רגילה + תשלומים | `DebitCard.aspx` | ליד משלם בכרטיס, מפוצל לתשלומים |
| הוראת קבע | `DebitKeva.aspx` | חיוב חודשי קבוע, יוצר `KevaId` |
| Callback סליקה | `POST /webhooks/nedarim-debitcard` | עדכון תשלום + ליד לאחר סליקה |
| Callback הו"ק | `POST /webhooks/nedarim-keva` | עדכון גביה חודשית + יצירת Collection |

תהליך מלא:
1. בחירת מוצר + מחיר + הנחה + מספר תשלומים
2. יצירת לינק תשלום בנדרים פלוס
3. שליחת לינק ללקוח (SMS/מייל/וואטסאפ)
4. קבלת webhook + עדכון אוטומטי של Payment/Lead/Student

### 5.4 ניהול תלמידים ✅

- המרת ליד לתלמיד עם שמירת היסטוריה
- פרטים אישיים: שם, ת"ז, טלפון, מייל, כתובת
- מעקב פיננסי: `total_price`, `total_paid`, יתרה, סטטוס תשלום
- הרשמות לקורסים עם מחיר הרשמה
- מעקב נוכחות ומטלות
- מבחנים וציונים
- אישור תקנון

### 5.5 ניהול קורסים ✅

- קורסים עם שיעורים/מודולים, לוחות זמנים, זום, הקלטות
- **מערכת נושאים (Topics)** — לופ אינסופי, נקודות כניסה דינמיות
- מרצים ושיוך למודולים
- מבחנים לפי קורס עם הגשות וציונים
- נוכחות אוטומטית לפי מפגש

### 5.6 דשבורד ומדדים ✅

- סטטיסטיקות לידים: כמות, המרה, מקורות
- מדדי מכירות לפי איש מכירות
- מדדי כספים: הכנסות, גביה, חובות
- גרפים ותרשימים

### 5.7 כלים נוספים ✅

| כלי | תיאור |
|-----|--------|
| Import API | ייבוא לידים ותלמידים מאקסל עם ולידציה |
| Export API | ייצוא כל טבלה לאקסל/CSV |
| Audit Logs | לוג מלא של כל שינוי בכל ישות |
| Webhook Queue | תור לעיבוד webhooks עם retry |
| File Upload | העלאת קבצים (חשבוניות, תמונות) |
| Templates | תבניות הודעות לשימוש חוזר |
| Popup System | חלונות קופצים להתראות ועדכונים |
| Chat | מערכת צ'אט פנימית |
| Inbound Emails | קליטת מיילים נכנסים (Make.com) |
| Table Preferences | הגדרות טבלה לפי משתמש |
| Public Exams API | API פומבי למועמדים לבחינות סמיכה |

---

## 6. תהליכי ליבה (Core Workflows)

### 6.1 ליד חדש מאלמנטור

```
טופס אתר → POST /webhooks/elementor
              ↓ חיפוש לפי טלפון
         קיים? → הוסף LeadInteraction
         חדש? → צור Lead + שיוך Salesperson + צור LeadInteraction
              ↓
         הצג ב-CRM לאיש המכירות
```

### 6.2 ליד מ-IVR ימות המשיח

```
שיחה נכנסת → POST /webhooks/yemot
              ↓ זיהוי שלוחה → מיפוי לקורס
         שמור LeadInteraction עם:
         - משך שיחה, זמן המתנה, סטטוס מענה
         - קורס שמתעניין בו (לפי שלוחה)
```

### 6.3 תהליך תשלום מלא

```
איש מכירות → בחר מוצר → הגדר הנחה → צור לינק נדרים
                                            ↓
                               לקוח משלם בדף נדרים
                                            ↓
                               Webhook → עדכן Payment + Lead
                                            ↓
                            (אם הו"ק) → יצור Commitment → גביה חודשית
```

### 6.4 המרת ליד לתלמיד

```
Lead.status = "ליד סגור-לקוח"
    ↓
POST /api/leads/{id}/convert
    ↓
צור Student ← קישור Lead.student_id
    ↓
צור Enrollment ← קורס שנבחר
    ↓
עדכן Student.total_price ← LeadProduct.final_price
```

---

## 7. יכולות שנדרשות להמשך פיתוח

### 7.1 ישויות חסרות (מתוך ENTITIES_SPEC)

| ישות | טבלה | עדיפות |
|------|------|--------|
| הודעות לידים | `lead_messages` | גבוהה |
| פניות נכנסות | `inquiries` | גבוהה |
| נוכחות ומטלות | `attendance` | גבוהה |
| מרצים | `lecturers` | בינונית |
| התחייבויות | `commitments` | גבוהה |
| גביה | `collections` | גבוהה |
| הוצאות | `expenses` | בינונית |

### 7.2 יכולות חסרות בתהליך המכירה

| יכולת | תיאור | עדיפות |
|-------|--------|--------|
| רישום תגובת ליד | שדה dropdown לסוג תגובה בשיחה | גבוהה |
| שליחת חומרים ללידים | SMS / מייל אוטומטי לאחר שיחה ראשונה | בינונית |
| מעקב ניסיונות חיוג | כמה פעמים ניסינו לחייג לליד | גבוהה |
| אישור תקנון דיגיטלי | חתימה דיגיטלית + מעקב | בינונית |

### 7.3 יכולות טכניות לשיפור

| יכולת | תיאור |
|-------|--------|
| Multi-tenant | הפרדת נתונים לפי ארגון (Nexus CRM) |
| Notification System | התראות real-time |
| Mobile-responsive UI | שיפור חוויה על מובייל |
| Background tasks | Celery/ARQ לסליקה אוטומטית |
| Rate limiting | הגנה על Webhooks מ-spam |

---

## 8. משתני סביבה נדרשים

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# Security
SECRET_KEY=...
JWT_SECRET_KEY=...
JWT_EXPIRATION_MINUTES=1440

# Nedarim Plus
NEDARIM_MOSAD_ID=...
NEDARIM_API_KEY=...
NEDARIM_WEBHOOK_SECRET=...

# Google OAuth (אופציונלי)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Email (אופציונלי)
SMTP_HOST=...
SMTP_USER=...
SMTP_PASSWORD=...

# Dev
DEV_SKIP_AUTH=true
```

---

## 9. סביבת פיתוח

### הרצה מקומית

```powershell
# הרצה עם skip-auth
.\dev.ps1

# או ידנית
.venv311\Scripts\uvicorn app:app --reload --port 8000
```

### בנייה ופריסה

```powershell
# בנה פרונטאנד
cd frontend && npm run build && cd ..

# Push לבראנץ fitchers (auto-deploy)
git add -A
git commit -m "תיאור"
git push origin fitchers
```

### תיעוד API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 10. ניווט בקוד — נקודות כניסה מרכזיות

| נושא | קובץ |
|------|------|
| ניהול לידים | `api/leads_api.py`, `services/leads.py` |
| תהליך מכירה | `api/lead_conversion_api.py`, `services/lead_conversion.py` |
| תשלומים + נדרים | `webhooks/nedarim_debitcard.py`, `webhooks/nedarim_keva.py` |
| הגעת לידים | `webhooks/elementor.py`, `webhooks/yemot.py` |
| שיוך אנשי מכירות | `api/sales_assignment_api.py`, `services/sales_assignment.py` |
| ניהול קורסים | `api/courses_api.py`, `api/topics_api.py` |
| דשבורד | `api/dashboard_api.py` |
| מודלים | `db/models.py` |
| הרשאות | `api/dependencies.py` |

---

**מסמך זה מיועד לתיאור מלא ועדכני של המערכת לצורך onboarding, תכנון פיתוח, ועבודה עם AI.**
