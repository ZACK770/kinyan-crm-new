# מערכת יומן פעילות (Audit Logs)

מערכת מקיפה לתיעוד כל הפעולות במערכת, כולל פעולות משתמשים ופעולות אוטומטיות.

## תכונות

- ✅ תיעוד כל הפעולות: יצירה, עדכון, מחיקה, צפייה, התחברות
- ✅ רישום משתמש, תאריך ושעה, כתובת IP
- ✅ תיעוד שינויים (before/after)
- ✅ ממשק משתמש מסונן ומנוהל
- ✅ גישה למנהלים בלבד (manager ומעלה)

## מיקום במערכת

הדף נמצא תחת **ניהול מערכת** בתפריט הצדדי, וזמין למשתמשים ברמת הרשאה **manager** ומעלה.

נתיב: `/admin/audit-logs`

## שימוש ב-API

### קריאת לוגים

```python
# בקובץ API שלך
from services import audit_logs
from fastapi import Request

# התחברות
await audit_logs.log_login(
    db=db,
    user=user,
    description=f"התחברות מוצלחת: {user.email}",
    request=request,
)

# יצירת רשומה
await audit_logs.log_create(
    db=db,
    user=user,
    entity_type="leads",
    entity_id=lead.id,
    description=f"נוצר ליד חדש: {lead.full_name}",
    request=request,
)

# עדכון רשומה
await audit_logs.log_update(
    db=db,
    user=user,
    entity_type="students",
    entity_id=student_id,
    description=f"עודכן תלמיד: {student.full_name}",
    changes={"status": {"old": "active", "new": "graduated"}},
    request=request,
)

# מחיקת רשומה
await audit_logs.log_delete(
    db=db,
    user=user,
    entity_type="expenses",
    entity_id=expense_id,
    description=f"נמחקה הוצאה: {expense.vendor}",
    request=request,
)

# צפייה
await audit_logs.log_view(
    db=db,
    user=user,
    entity_type="payments",
    description="צפייה ברשימת תשלומים",
    request=request,
)
```

### פעולות API/מערכת (ללא משתמש)

```python
# לפעולות אוטומטיות או webhooks
await audit_logs.log_api_action(
    db=db,
    action="webhook",
    description="התקבלה פניה מ-Elementor",
    entity_type="leads",
    entity_id=lead_id,
    request=request,
)
```

## API Endpoints

### קריאת לוגים (עם סינון)
```
GET /api/audit-logs?page=1&page_size=50&days=30
```

פרמטרים:
- `page` - מספר עמוד
- `page_size` - כמות רשומות בעמוד
- `user_id` - סינון לפי משתמש
- `entity_type` - סינון לפי סוג ישות (leads, students, וכו')
- `action` - סינון לפי פעולה (create, update, delete, view, login)
- `days` - הצגת לוגים מ-X ימים אחרונים

### לוגים לישות ספציפית
```
GET /api/audit-logs/entity/{entity_type}/{entity_id}
```

דוגמה: `/api/audit-logs/entity/students/123` - כל השינויים בתלמיד מספר 123

### פעילות משתמש ספציפי
```
GET /api/audit-logs/user/{user_id}?days=30
```

### הפעילות שלי
```
GET /api/audit-logs/my-activity?days=30
```

## מבנה הטבלה

```python
class AuditLog:
    id: int
    user_id: int | None  # null for system/API actions
    user_name: str | None  # שם המשתמש (cached)
    action: str  # create/update/delete/view/login/etc
    entity_type: str | None  # leads/students/courses/etc
    entity_id: int | None  # מזהה הרשומה המושפעת
    description: str | None  # תיאור קריא
    ip_address: str | None
    user_agent: str | None
    request_method: str | None  # GET/POST/PUT/DELETE
    request_path: str | None
    changes: str | None  # JSON של שינויים
    created_at: datetime
```

## דוגמאות שימוש

### הוספת לוג להתחברות (כבר מיושם ב-auth_api.py)

```python
@router.post("/login")
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, body.email)
    # ... validation ...
    
    await audit_logs.log_login(
        db=db,
        user=user,
        description=f"התחברות מוצלחת: {user.email}",
        request=request,
    )
    
    return create_token_response(user)
```

### הוספת לוג ליצירת ליד (כבר מיושם ב-leads_api.py)

```python
@router.post("/")
async def create_lead(
    data: LeadCreate,
    request: Request,
    user = Depends(require_entity_access("leads", "create")),
    db: AsyncSession = Depends(get_db)
):
    result = await lead_svc.process_incoming_lead(db, **data.model_dump())
    
    if result and "lead_id" in result:
        await audit_logs.log_create(
            db=db,
            user=user,
            entity_type="leads",
            entity_id=result["lead_id"],
            description=f"נוצר ליד חדש: {data.name} - {data.phone}",
            request=request,
        )
    
    return result
```

## המלצות

1. **תעדו פעולות קריטיות**: התחברות, יצירה, עדכון, מחיקה
2. **השתמשו בתיאורים ברורים**: כדי שיהיה קל להבין מה קרה
3. **תעדו שינויים**: השתמשו בפרמטר `changes` כדי לראות מה השתנה
4. **אל תתעדו הכל**: סינון יתר עלול להאט את המערכת

## הרשאות

- **viewer/editor** - אין גישה ליומן הפעילות
- **manager** - צפייה בכל הלוגים, כולל פעילות של כל המשתמשים
- **admin** - צפייה בכל הלוגים + ניהול מערכת מלא

## ביצועים

הטבלה משתמשת באינדקסים על:
- `user_id` - חיפוש לפי משתמש
- `entity_type, entity_id` - חיפוש לפי ישות
- `action` - חיפוש לפי סוג פעולה
- `created_at` - מיון לפי תאריך

## תחזוקה

מומלץ לנקות לוגים ישנים מדי פעם:

```sql
-- מחיקת לוגים מעל שנה
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '1 year';
```

או ליצור ארכיון:

```sql
-- העברה לטבלת ארכיון
CREATE TABLE audit_logs_archive AS 
SELECT * FROM audit_logs WHERE created_at < NOW() - INTERVAL '1 year';

DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '1 year';
```
