# מדריך מערכת שיוך לידים חכמה

## סקירה כללית

מערכת שיוך לידים אוטומטית עם בקרת עומסים, מגבלות יומיות, והעדפות לאנשי מכירות.

**הבעיה שנפתרה:**
- לידים היו מתחלקים באופן פשוט מדי (round-robin)
- אין שליטה על כמות לידים לאיש מכירות
- אין אפשרות להעדיף איש מכירות מסוים
- אין בקרה על עומסים (כמה לידים פתוחים יש לאיש מכירות)
- לידים "יתומים" ללא אחראי

**הפתרון:**
מערכת כללים גמישה שמאפשרת:
- ✅ מגבלות יומיות לאיש מכירות
- ✅ משקלי העדפה (priority weights)
- ✅ בקרת עומסים (מקסימום לידים פתוחים)
- ✅ סינון לפי סטטוסים
- ✅ fallback אוטומטי אם אין זמינים

---

## ארכיטקטורה

### טבלה: `sales_assignment_rules`

```sql
CREATE TABLE sales_assignment_rules (
    id SERIAL PRIMARY KEY,
    salesperson_id INT UNIQUE REFERENCES salespeople(id) ON DELETE CASCADE,
    
    -- מגבלות יומיות
    daily_lead_limit INT,              -- NULL = ללא הגבלה
    daily_leads_assigned INT DEFAULT 0,
    last_reset_date DATE,
    
    -- משקל העדפה
    priority_weight INT DEFAULT 1,     -- 1-10 (גבוה יותר = יותר לידים)
    
    -- בקרת עומסים
    max_open_leads INT,                -- NULL = ללא הגבלה
    status_filters TEXT[],             -- סטטוסים לספירה
    
    -- הפעלה
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### אלגוריתם השיוך

```python
async def assign_salesperson(db, lead_id, phone):
    """
    1. שלוף אנשי מכירות פעילים + כללים
    2. סנן לפי זמינות:
       - לא הגיע למגבלה יומית
       - לא הגיע למקסימום לידים פתוחים
       - כללים פעילים
    3. בחר באופן משוקלל (weighted random) לפי priority_weight
    4. עדכן ספירות
    5. אם אין זמינים - fallback ל-round-robin פשוט
    """
```

---

## API Endpoints

### 1. קבלת כל הכללים
```http
GET /api/sales-assignment-rules/
GET /api/sales-assignment-rules/?include_stats=true
```

**תגובה:**
```json
[
  {
    "id": 1,
    "salesperson_id": 5,
    "salesperson_name": "משה כהן",
    "daily_lead_limit": 20,
    "daily_leads_assigned": 12,
    "last_reset_date": "2026-02-10",
    "priority_weight": 3,
    "max_open_leads": 50,
    "status_filters": ["ליד חדש", "במעקב", "מתעניין"],
    "is_active": true,
    "current_open_leads": 35
  }
]
```

### 2. סטטיסטיקות מפורטות
```http
GET /api/sales-assignment-rules/stats
```

**תגובה:**
```json
[
  {
    "salesperson_id": 5,
    "salesperson_name": "משה כהן",
    "total_leads": 250,
    "open_leads": 35,
    "daily_assigned": 12,
    "daily_limit": 20,
    "priority_weight": 3,
    "is_available": true,
    "availability_reason": null
  },
  {
    "salesperson_id": 6,
    "salesperson_name": "שרה לוי",
    "total_leads": 180,
    "open_leads": 52,
    "daily_assigned": 8,
    "daily_limit": 15,
    "priority_weight": 2,
    "is_available": false,
    "availability_reason": "הגיע למקסימום לידים פתוחים (50)"
  }
]
```

### 3. יצירת כללים
```http
POST /api/sales-assignment-rules/
Content-Type: application/json

{
  "salesperson_id": 5,
  "daily_lead_limit": 20,
  "priority_weight": 3,
  "max_open_leads": 50,
  "status_filters": ["ליד חדש", "במעקב", "מתעניין"],
  "is_active": true
}
```

### 4. עדכון כללים
```http
PATCH /api/sales-assignment-rules/{salesperson_id}
Content-Type: application/json

{
  "daily_lead_limit": 25,
  "priority_weight": 5,
  "max_open_leads": 60
}
```

### 5. איפוס ספירות יומיות
```http
POST /api/sales-assignment-rules/reset-daily-counts
```

### 6. מחיקת כללים
```http
DELETE /api/sales-assignment-rules/{salesperson_id}
```

---

## תרחישי שימוש

### תרחיש 1: הגדרת מגבלות בסיסיות
```json
{
  "salesperson_id": 5,
  "daily_lead_limit": 20,
  "priority_weight": 1,
  "is_active": true
}
```
**תוצאה:** איש מכירות יקבל עד 20 לידים ליום, ללא בקרת עומסים.

---

### תרחיש 2: העדפה לאיש מכירות מנוסה
```json
{
  "salesperson_id": 5,
  "daily_lead_limit": 30,
  "priority_weight": 5,
  "max_open_leads": 80,
  "is_active": true
}
```
**תוצאה:** איש מכירות זה יקבל פי 5 יותר לידים מאחרים (במשקל 1).

---

### תרחיש 3: בקרת עומסים קפדנית
```json
{
  "salesperson_id": 6,
  "daily_lead_limit": 15,
  "priority_weight": 2,
  "max_open_leads": 40,
  "status_filters": ["ליד חדש", "במעקב"],
  "is_active": true
}
```
**תוצאה:** 
- מקסימום 15 לידים ליום
- אם יש לו 40 לידים בסטטוס "ליד חדש" או "במעקב" - לא יקבל עוד
- משקל העדפה x2

---

### תרחיש 4: השבתה זמנית
```json
{
  "salesperson_id": 7,
  "is_active": false
}
```
**תוצאה:** איש מכירות לא יקבל לידים חדשים (חופשה/מחלה).

---

## זרימת עבודה

### 1. ליד חדש נכנס מוובהוק
```
Webhook (Elementor/Generic) 
  → process_incoming_lead()
    → assign_salesperson()
      → בדיקת כללים
      → בחירה משוקללת
      → עדכון ספירות
      → שיוך ללידים
```

### 2. איפוס יומי אוטומטי
```python
# בכל שיוך, המערכת בודקת:
if rules.last_reset_date != today:
    rules.daily_leads_assigned = 0
    rules.last_reset_date = today
```

### 3. fallback אם אין זמינים
```python
if not available:
    # חזרה ל-round-robin פשוט
    return await _assign_salesperson_simple(db, lead_id, phone, salespeople)
```

---

## דוגמאות קוד

### יצירת כללים לכל אנשי המכירות
```python
import httpx

salespeople = [
    {"id": 1, "name": "משה", "limit": 20, "weight": 3},
    {"id": 2, "name": "שרה", "limit": 15, "weight": 2},
    {"id": 3, "name": "דוד", "limit": 25, "weight": 5},
]

async with httpx.AsyncClient() as client:
    for sp in salespeople:
        await client.post(
            "http://localhost:8000/api/sales-assignment-rules/",
            json={
                "salesperson_id": sp["id"],
                "daily_lead_limit": sp["limit"],
                "priority_weight": sp["weight"],
                "max_open_leads": 50,
                "is_active": True
            }
        )
```

### בדיקת זמינות לפני שיוך ידני
```python
stats = await client.get("http://localhost:8000/api/sales-assignment-rules/stats")
available = [s for s in stats.json() if s["is_available"]]
print(f"זמינים כרגע: {len(available)} אנשי מכירות")
```

---

## ניטור ובקרה

### דשבורד מומלץ
1. **תצוגת זמינות** - מי זמין כרגע לקבל לידים
2. **ספירות יומיות** - כמה לידים קיבל כל אחד היום
3. **עומסים נוכחיים** - כמה לידים פתוחים יש לכל אחד
4. **התראות** - אזהרה כשכולם מלאים

### שאילתות שימושיות

**מי הכי עמוס?**
```sql
SELECT s.name, COUNT(l.id) as open_leads
FROM salespeople s
LEFT JOIN leads l ON l.salesperson_id = s.id
WHERE l.status IN ('ליד חדש', 'במעקב', 'מתעניין')
GROUP BY s.id, s.name
ORDER BY open_leads DESC;
```

**מי קיבל הכי הרבה לידים היום?**
```sql
SELECT s.name, sar.daily_leads_assigned
FROM salespeople s
JOIN sales_assignment_rules sar ON sar.salesperson_id = s.id
WHERE sar.last_reset_date = CURRENT_DATE
ORDER BY sar.daily_leads_assigned DESC;
```

---

## טיפים והמלצות

### 1. הגדרת משקלים
- **משקל 1** - איש מכירות רגיל
- **משקל 2-3** - איש מכירות מנוסה
- **משקל 5-10** - איש מכירות מוביל/מנהל

### 2. מגבלות יומיות
- התחל עם 15-20 לידים ליום
- התאם לפי ביצועים
- השאר NULL למנהלים (ללא הגבלה)

### 3. בקרת עומסים
- הגדר 40-60 לידים פתוחים מקסימום
- כלול רק סטטוסים רלוונטיים בספירה
- לידים "סגורים" לא נספרים

### 4. תחזוקה
- בדוק סטטיסטיקות פעם ביום
- אפס ידנית אם יש בעיה
- עדכן משקלים לפי ביצועים

---

## פתרון בעיות

### בעיה: כל הלידים הולכים לאיש מכירות אחד
**פתרון:** בדוק משקלי העדפה - אולי אחד מוגדר עם משקל גבוה מדי.

### בעיה: אף אחד לא מקבל לידים
**פתרון:** 
1. בדוק שיש אנשי מכירות עם `is_active=true`
2. בדוק שלא כולם הגיעו למגבלות
3. הרץ `/reset-daily-counts` אם צריך

### בעיה: לידים "יתומים" ללא שיוך
**פתרון:** המערכת תעבור ל-fallback אוטומטי. בדוק logs לראות למה אף אחד לא היה זמין.

---

## מיגרציה ממערכת ישנה

אם יש לך לידים קיימים עם שיוך ישן:

```sql
-- אין צורך לעשות כלום!
-- המערכת החדשה משתמשת באותו שדה salesperson_id
-- הכללים החדשים ישפיעו רק על לידים חדשים
```

---

## סיכום

המערכת מספקת:
- ✅ **שליטה מלאה** על חלוקת לידים
- ✅ **גמישות** - כל איש מכירות עם כללים משלו
- ✅ **אוטומציה** - איפוס יומי, fallback חכם
- ✅ **שקיפות** - API מלא לניטור וסטטיסטיקות
- ✅ **אמינות** - אין לידים יתומים

**התחל עכשיו:**
1. הרץ את המיגרציה: `alembic upgrade head`
2. צור כללים לאנשי המכירות: `POST /api/sales-assignment-rules/`
3. בדוק סטטיסטיקות: `GET /api/sales-assignment-rules/stats`
4. הלידים הבאים יתחלקו אוטומטית לפי הכללים החדשים! 🎉
