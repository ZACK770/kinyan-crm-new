# הוראות הפעלה - מערכת שיוך לידים חכמה

## סיכום מה נבנה

### ✅ מה כבר היה קיים
1. **ישות Lead** - עם שדה `salesperson_id` לשיוך
2. **מודול Webhooks** - Elementor, Generic, Nedarim
3. **שירות Leads** - `process_incoming_lead()` שמטפל בלידים חדשים
4. **שיוך בסיסי** - Round-robin פשוט על בסיס hash של טלפון

### ✅ מה נוסף עכשיו
1. **טבלה חדשה**: `sales_assignment_rules` - ניהול כללי שיוך
2. **לוגיקה חכמה**: `assign_salesperson()` משופר עם:
   - מגבלות יומיות
   - משקלי העדפה (priority weights)
   - בקרת עומסים (max open leads)
   - סינון לפי סטטוסים
   - Fallback אוטומטי
3. **API מלא**: `/api/sales-assignment-rules/` - 7 endpoints
4. **דוקומנטציה**: `SALES_ASSIGNMENT_GUIDE.md`

---

## שלבי הפעלה

### שלב 1: הרצת המיגרציה

```powershell
# ודא שאתה בתיקיית הפרויקט
cd c:\Users\admin\kinyan-crm-new

# הפעל את המיגרציה
alembic upgrade head
```

**אם יש שגיאה עם asyncpg:**
```powershell
pip install asyncpg
```

**בדיקה שהטבלה נוצרה:**
```sql
-- התחבר ל-PostgreSQL
SELECT * FROM sales_assignment_rules;
```

---

### שלב 2: יצירת כללים לאנשי מכירות

#### אופציה 1: דרך API (מומלץ)

```powershell
# קבל רשימת אנשי מכירות
curl http://localhost:8000/api/leads/salespersons

# צור כללים לכל אחד
curl -X POST http://localhost:8000/api/sales-assignment-rules/ `
  -H "Content-Type: application/json" `
  -d '{
    "salesperson_id": 1,
    "daily_lead_limit": 20,
    "priority_weight": 3,
    "max_open_leads": 50,
    "status_filters": ["ליד חדש", "במעקב", "מתעניין"],
    "is_active": true
  }'
```

#### אופציה 2: דרך SQL

```sql
-- דוגמה: צור כללים לאיש מכירות #1
INSERT INTO sales_assignment_rules (
    salesperson_id,
    daily_lead_limit,
    priority_weight,
    max_open_leads,
    status_filters,
    is_active,
    last_reset_date
) VALUES (
    1,
    20,
    3,
    50,
    ARRAY['ליד חדש', 'במעקב', 'מתעניין'],
    true,
    CURRENT_DATE
);
```

---

### שלב 3: בדיקת התקנה

```powershell
# בדוק שה-API עובד
curl http://localhost:8000/api/sales-assignment-rules/

# בדוק סטטיסטיקות
curl http://localhost:8000/api/sales-assignment-rules/stats
```

**תגובה מצופה:**
```json
[
  {
    "salesperson_id": 1,
    "salesperson_name": "משה כהן",
    "total_leads": 0,
    "open_leads": 0,
    "daily_assigned": 0,
    "daily_limit": 20,
    "priority_weight": 3,
    "is_available": true,
    "availability_reason": null
  }
]
```

---

### שלב 4: בדיקת שיוך אוטומטי

#### שלח ליד דרך webhook:

```powershell
curl -X POST http://localhost:8000/webhooks/elementor `
  -H "Content-Type: application/json" `
  -d '{
    "fields": {
      "name": {"value": "ישראל ישראלי"},
      "phone": {"value": "0501234567"},
      "email": {"value": "test@example.com"}
    }
  }'
```

#### בדוק שהליד שויך:

```powershell
curl http://localhost:8000/api/leads/search?phone=0501234567
```

**תגובה מצופה:**
```json
{
  "id": 123,
  "full_name": "ישראל ישראלי",
  "phone": "0501234567",
  "status": "ליד חדש",
  "salesperson_id": 1
}
```

---

## תצורות מומלצות

### תצורה 1: צוות קטן (2-3 אנשי מכירות)

```json
[
  {
    "salesperson_id": 1,
    "daily_lead_limit": 25,
    "priority_weight": 1,
    "max_open_leads": null,
    "is_active": true
  },
  {
    "salesperson_id": 2,
    "daily_lead_limit": 25,
    "priority_weight": 1,
    "max_open_leads": null,
    "is_active": true
  }
]
```

### תצורה 2: צוות גדול עם היררכיה

```json
[
  {
    "salesperson_id": 1,
    "daily_lead_limit": 30,
    "priority_weight": 5,
    "max_open_leads": 80,
    "is_active": true,
    "comment": "מנהל מכירות - מקבל הכי הרבה"
  },
  {
    "salesperson_id": 2,
    "daily_lead_limit": 20,
    "priority_weight": 3,
    "max_open_leads": 60,
    "is_active": true,
    "comment": "איש מכירות בכיר"
  },
  {
    "salesperson_id": 3,
    "daily_lead_limit": 15,
    "priority_weight": 2,
    "max_open_leads": 40,
    "is_active": true,
    "comment": "איש מכירות זוטר"
  }
]
```

### תצורה 3: עם בקרת עומסים קפדנית

```json
{
  "salesperson_id": 1,
  "daily_lead_limit": 20,
  "priority_weight": 3,
  "max_open_leads": 50,
  "status_filters": ["ליד חדש", "במעקב"],
  "is_active": true
}
```

---

## ניהול שוטף

### בוקר - בדיקת זמינות
```powershell
curl http://localhost:8000/api/sales-assignment-rules/stats
```

### צהריים - בדיקת התקדמות
```powershell
curl "http://localhost:8000/api/sales-assignment-rules/?include_stats=true"
```

### ערב - איפוס ידני (אם צריך)
```powershell
curl -X POST http://localhost:8000/api/sales-assignment-rules/reset-daily-counts
```

### עדכון כללים
```powershell
curl -X PATCH http://localhost:8000/api/sales-assignment-rules/1 `
  -H "Content-Type: application/json" `
  -d '{
    "daily_lead_limit": 25,
    "priority_weight": 4
  }'
```

---

## פתרון בעיות נפוצות

### בעיה: המיגרציה נכשלת
```powershell
# בדוק את גרסת alembic הנוכחית
alembic current

# אם יש בעיה, הרץ:
alembic stamp head
alembic upgrade head
```

### בעיה: אין שיוך אוטומטי
1. בדוק שיש אנשי מכירות פעילים:
```sql
SELECT * FROM salespeople WHERE is_active = true;
```

2. בדוק שיש כללים:
```sql
SELECT * FROM sales_assignment_rules WHERE is_active = true;
```

3. בדוק logs של השרת

### בעיה: כל הלידים הולכים לאותו אדם
```powershell
# בדוק משקלי העדפה
curl http://localhost:8000/api/sales-assignment-rules/

# אפס אם צריך
curl -X PATCH http://localhost:8000/api/sales-assignment-rules/1 `
  -d '{"priority_weight": 1}'
```

---

## אינטגרציה עם הממשק הקיים

המערכת משתלבת אוטומטית עם:
- ✅ Webhooks (Elementor, Generic, Nedarim)
- ✅ API ליצירת לידים ידנית
- ✅ מערכת ה-CRM הקיימת
- ✅ דשבורד הלידים

**אין צורך לשנות קוד קיים!**

---

## מעקב וניטור

### שאילתות שימושיות

**כמה לידים שויכו היום?**
```sql
SELECT 
    s.name,
    sar.daily_leads_assigned,
    sar.daily_lead_limit,
    sar.priority_weight
FROM salespeople s
JOIN sales_assignment_rules sar ON sar.salesperson_id = s.id
WHERE sar.last_reset_date = CURRENT_DATE
ORDER BY sar.daily_leads_assigned DESC;
```

**מי הכי עמוס?**
```sql
SELECT 
    s.name,
    COUNT(l.id) as open_leads,
    sar.max_open_leads
FROM salespeople s
LEFT JOIN leads l ON l.salesperson_id = s.id
LEFT JOIN sales_assignment_rules sar ON sar.salesperson_id = s.id
WHERE l.status IN ('ליד חדש', 'במעקב', 'מתעניין')
GROUP BY s.id, s.name, sar.max_open_leads
ORDER BY open_leads DESC;
```

**לידים ללא שיוך (יתומים)?**
```sql
SELECT COUNT(*) 
FROM leads 
WHERE salesperson_id IS NULL 
AND created_at > NOW() - INTERVAL '7 days';
```

---

## שדרוג עתידי

רעיונות להרחבה:
- [ ] שיוך לפי מיומנויות (קורס מסוים → איש מכירות מסוים)
- [ ] שיוך לפי גיאוגרפיה (עיר → איש מכירות מקומי)
- [ ] שיוך לפי קמפיין (קמפיין מסוים → צוות ייעודי)
- [ ] התראות אוטומטיות (SMS/Email כשמתקרבים למגבלה)
- [ ] דשבורד ויזואלי בממשק

---

## סיכום

### מה עובד עכשיו:
✅ שיוך אוטומטי חכם לכל ליד חדש  
✅ בקרת מגבלות יומיות  
✅ בקרת עומסים  
✅ משקלי העדפה  
✅ API מלא לניהול  
✅ Fallback אוטומטי  
✅ תיעוד מלא  

### מה צריך לעשות:
1. הרץ מיגרציה: `alembic upgrade head`
2. צור כללים לאנשי מכירות
3. בדוק שהשיוך עובד
4. התחל לעבוד! 🎉

**שאלות? בעיות?** ראה `SALES_ASSIGNMENT_GUIDE.md` למידע מפורט.
