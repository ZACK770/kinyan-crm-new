# תהליך מכירה מלא - מליד ועד תלמיד משלם

> **מסמך תיעוד מקיף** - מפרט את תהליך המכירה המלא כולל פערים קיימים ופתרונות מוצעים
> 
> **עדכון אחרון**: 2026-02-10

---

## 📋 סקירת התהליך המלא

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    תהליך מכירה מלא - 10 שלבים                               │
│                                                                              │
│  1️⃣ קבלת ליד מוובהוק        ✅ קיים                                         │
│  2️⃣ חיוג ראשון + רישום תגובה  ⚠️ חלקי (חסר רישום תגובות)                  │
│  3️⃣ שליחת חומרים במייל        ❌ חסר                                        │
│  4️⃣ מעקב אחרי יום-יומיים      ⚠️ חלקי (חסר מערכת משימות אוטומטית)          │
│  5️⃣ בחירת מוצר מדויק          ✅ קיים                                        │
│  6️⃣ הגדרת הנחה וחישוב סכום    ⚠️ חלקי (חסר חישוב אוטומטי)                 │
│  7️⃣ הזנת פרטי אשראי           ✅ קיים (דרך נדרים פלוס)                      │
│  8️⃣ הגדרת תאריך חיוב חודשי    ⚠️ חלקי (לא מועבר לנדרים)                   │
│  9️⃣ אישור תקנון               ⚠️ חלקי (חסר מעקב ואימות)                    │
│  🔟 המרה לתלמיד                ✅ קיים                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 תהליך שלב אחר שלב

### שלב 1: קבלת ליד מוובהוק ✅

**סטטוס**: עובד מלא

**מה קורה**:
- ליד מגיע מאלמנטור/ימות/גנרי
- נוצר אוטומטית ב-DB
- משויך לאיש מכירות (round-robin)
- נוצרת אינטראקציה ראשונית

**API**:
```http
POST /api/webhooks/elementor
POST /api/webhooks/yemot
POST /api/webhooks/generic
```

**סטטוס ליד**: `ליד חדש`

---

### שלב 2: חיוג ראשון + רישום תגובה ⚠️

**סטטוס**: חלקי - חסר רישום תגובות מפורט

**מה צריך לקרות**:
1. איש המכירות מחייג לליד
2. רושם את תגובת הליד (מעוניין/לא מעוניין/צריך לחשוב/וכו')
3. מעדכן סטטוס
4. קובע מועד למעקב הבא

**מה קיים**:
```http
POST /api/leads/{id}/interactions
{
  "interaction_type": "outbound_call",
  "description": "שיחה ראשונה - מעוניין",
  "user_name": "שם איש המכירות",
  "next_call_date": "2026-02-12T10:00:00Z"
}
```

**מה חסר**:
- ❌ שדה ייעודי לתגובת הליד (`lead_response`)
- ❌ רשימת תגובות סטנדרטיות (dropdown)
- ❌ מעקב אחר מספר ניסיונות חיוג

**פתרון מוצע**:
```python
# הוספה למודל Lead:
lead_response: Mapped[Optional[str]] = mapped_column(String(100))
# אפשרויות: "מעוניין", "צריך לחשוב", "לא זמין", "לא מעוניין", "אחר"

follow_up_count: Mapped[int] = mapped_column(Integer, default=0)
last_contact_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
```

**API חדש נדרש**:
```http
PATCH /api/leads/{id}/record-call
{
  "response": "מעוניין",
  "notes": "מעוניין בקורס גמרא, מבקש חומרים",
  "next_call_date": "2026-02-12T10:00:00Z"
}
```

**סטטוס ליד**: `חיוג ראשון`

---

### שלב 3: שליחת חומרים במייל ❌

**סטטוס**: חסר לחלוטין

**מה צריך לקרות**:
- איש המכירות שולח מייל עם חומרים (סילבוס, מחירון, המלצות)
- המערכת שומרת שהמייל נשלח
- מעדכנת סטטוס

**מה קיים**:
- ✅ `email_service.py` - שירות שליחת מיילים
- ❌ אין תבנית מייל לחומרים
- ❌ אין API לשליחת חומרים

**פתרון מוצע**:

**1. תבנית מייל חדשה** (`services/email_service.py`):
```python
async def send_course_materials_email(
    to_email: str,
    lead_name: str,
    course_name: str,
    salesperson_name: str,
    materials_links: dict
) -> bool:
    """שליחת מייל חומרים ללקוח"""
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif;">
        <h2>שלום {lead_name},</h2>
        <p>תודה על ההתעניינות בקורס {course_name}!</p>
        <p>להלן החומרים שביקשת:</p>
        <ul>
            <li><a href="{materials_links.get('syllabus')}">סילבוס הקורס</a></li>
            <li><a href="{materials_links.get('pricing')}">מחירון</a></li>
            <li><a href="{materials_links.get('testimonials')}">המלצות תלמידים</a></li>
        </ul>
        <p>נשמח לענות על כל שאלה!</p>
        <p>בברכה,<br>{salesperson_name}</p>
    </div>
    """
    return await send_email(to_email, f"חומרים - {course_name}", html_body)
```

**2. API חדש**:
```http
POST /api/leads/{id}/send-materials
{
  "course_id": 5,
  "include_syllabus": true,
  "include_pricing": true,
  "include_testimonials": true,
  "custom_message": "הערה אישית..."
}
```

**3. עדכון LeadInteraction**:
```python
# רישום שהמייל נשלח
interaction = LeadInteraction(
    lead_id=lead_id,
    interaction_type="email_sent",
    description="נשלחו חומרים על קורס גמרא",
    user_name=salesperson_name
)
```

**סטטוס ליד**: `חומרים נשלחו`

---

### שלב 4: מעקב אחרי יום-יומיים ⚠️

**סטטוס**: חלקי - יש `next_call_date` אבל אין מערכת משימות

**מה צריך לקרות**:
- המערכת יוצרת משימת מעקב אוטומטית
- איש המכירות מקבל התראה
- חוזר ללקוח ומתעניין

**מה קיים**:
- ✅ `SalesTask` - מודל משימות
- ✅ `next_call_date` ב-`LeadInteraction`
- ❌ אין יצירה אוטומטית של משימות
- ❌ אין התראות

**פתרון מוצע**:

**1. יצירה אוטומטית של משימת מעקב**:
```python
# בעת שליחת חומרים או רישום שיחה
async def create_follow_up_task(
    db: AsyncSession,
    lead_id: int,
    salesperson_id: int,
    due_date: datetime,
    title: str = "מעקב אחר ליד"
):
    task = SalesTask(
        lead_id=lead_id,
        salesperson_id=salesperson_id,
        title=title,
        description=f"לחזור ללקוח ולבדוק אם קיבל החלטה",
        due_date=due_date,
        status="חדש",
        priority=2
    )
    db.add(task)
    await db.flush()
    return task
```

**2. API למשימות**:
```http
GET /api/sales-tasks/my-tasks?status=חדש&overdue=true
GET /api/sales-tasks/due-today
```

**3. התראות** (עתידי):
- מייל יומי עם משימות היום
- התראות בממשק

**סטטוס ליד**: `במעקב`

---

### שלב 5: בחירת מוצר מדויק ✅

**סטטוס**: עובד מלא

**מה קורה**:
- איש המכירות בוחר מוצר ספציפי
- מגדיר מספר תשלומים
- נוצרת רשומת `LeadProduct`

**API**:
```http
POST /api/leads/{id}/select-product
{
  "product_id": 3,
  "price": 2500,
  "payments_count": 10,
  "monthly_payment": 250,
  "payment_day": 15,
  "payment_type": "הוראת קבע"
}
```

**סטטוס ליד**: `מוצר נבחר`

---

### שלב 6: הגדרת הנחה וחישוב סכום ⚠️

**סטטוס**: חלקי - יש מודל `Coupon` אבל לא מיושם

**מה צריך לקרות**:
1. איש המכירות מחליט על הנחה
2. בוחר קופון או מגדיר הנחה מותאמת אישית
3. המערכת מחשבת את המחיר הסופי
4. שומרת את ההנחה ב-`LeadProduct`

**מה קיים**:
- ✅ `Coupon` - מודל קופונים
- ✅ שדות הנחה ב-`LeadProduct` (`discount_type`, `discount_amount`, `final_price`)
- ❌ אין חישוב אוטומטי של `final_price`
- ❌ אין API להחלת קופון

**פתרון מוצע**:

**1. פונקציית חישוב**:
```python
def calculate_discount(
    original_price: float,
    discount_type: str,
    discount_value: float
) -> tuple[float, float]:
    """
    מחשב הנחה ומחזיר (סכום_הנחה, מחיר_סופי)
    """
    if discount_type == "אחוז":
        discount_amount = original_price * (discount_value / 100)
    else:  # סכום קבוע
        discount_amount = discount_value
    
    final_price = max(0, original_price - discount_amount)
    return discount_amount, final_price
```

**2. API להחלת הנחה**:
```http
POST /api/leads/{id}/apply-discount
{
  "coupon_code": "SUMMER2026",  # או null
  "custom_discount_type": "אחוז",  # אם אין קופון
  "custom_discount_value": 10,
  "discount_notes": "הנחה מיוחדת ללקוח חוזר"
}
```

**3. עדכון `select-product`**:
```python
# בעת בחירת מוצר, לחשב אוטומטית final_price
if data.coupon_id:
    coupon = await get_coupon(db, data.coupon_id)
    discount_amount, final_price = calculate_discount(
        price, coupon.discount_type, coupon.discount_value
    )
else:
    final_price = price

lead_product.final_price = final_price
```

**שדות נוספים נדרשים ב-Lead**:
```python
discount_notes: Mapped[Optional[str]] = mapped_column(Text)
```

**סטטוס ליד**: `מוצר נבחר` (ללא שינוי)

---

### שלב 7: הזנת פרטי אשראי ✅

**סטטוס**: עובד מלא דרך נדרים פלוס

**מה קורה**:
1. נוצר לינק תשלום בנדרים פלוס
2. הלינק נשלח ללקוח (SMS/מייל/וואטסאפ)
3. הלקוח מזין פרטי אשראי בדף מאובטח
4. נדרים פלוס שולח webhook כשהתשלום מתבצע

**API**:
```http
POST /api/leads/{id}/create-payment-link
{
  "amount": 250,
  "currency": "ILS",
  "installments": 1,
  "payment_method": "credit_card"
}
```

**תגובה**:
```json
{
  "payment_id": 123,
  "payment_link": "https://nedarim.co.il/pay/abc123",
  "nedarim_donation_id": "DON_abc123"
}
```

**שיפור נדרש**:
- ⚠️ העברת `payment_day` לנדרים פלוס (לתשלומים חוזרים)
- ⚠️ מעקב אם הלקוח הזין פרטים (webhook מנדרים)

**סטטוס ליד**: `ממתין לתשלום`

---

### שלב 8: הגדרת תאריך ייעודי בחודש ⚠️

**סטטוס**: חלקי - יש שדה אבל לא מועבר לנדרים

**מה צריך לקרות**:
- איש המכירות מגדיר יום בחודש לחיוב (למשל 15)
- זה מועבר לנדרים פלוס בעת יצירת הוראת קבע
- נדרים פלוס יחייב בתאריך זה כל חודש

**מה קיים**:
- ✅ `payment_day` ב-`LeadProduct`
- ❌ לא מועבר ל-`nedarim_plus.create_lead_payment_link()`

**פתרון מוצע**:

**עדכון `services/nedarim_plus.py`**:
```python
async def create_lead_payment_link(
    db: AsyncSession,
    lead_id: int,
    amount: float,
    payment_day: int | None = None,  # ← הוספה
    **kwargs
):
    # ...
    
    # אם יש תשלומים חוזרים, להעביר את payment_day
    if installments > 1 and payment_day:
        nedarim_data["recurring_day"] = payment_day
    
    # שליחה לנדרים פלוס...
```

**עדכון API call**:
```python
# בעת יצירת לינק תשלום
selected_product = await get_selected_product(db, lead_id)
payment_day = selected_product.payment_day if selected_product else None

result = await nedarim_plus.create_lead_payment_link(
    db=db,
    lead_id=lead_id,
    amount=data.amount,
    payment_day=payment_day,  # ← הוספה
    ...
)
```

---

### שלב 9: אישור תקנון ⚠️

**סטטוס**: חלקי - יש שדה אבל אין מעקב

**מה צריך לקרות**:
1. איש המכירות מוודא שהלקוח מאשר תקנון
2. רושם איך אושר (טלפון/מייל/חתימה)
3. מעדכן את השדה `approved_terms`

**מה קיים**:
- ✅ `approved_terms` (Boolean) ב-`Lead` וב-`Student`
- ❌ אין שדה לשיטת אישור
- ❌ אין API לעדכון

**פתרון מוצע**:

**1. שדות נוספים ב-Lead**:
```python
approval_method: Mapped[Optional[str]] = mapped_column(String(50))
# אפשרויות: "טלפון", "מייל", "חתימה דיגיטלית", "SMS"

approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
```

**2. API לאישור תקנון**:
```http
POST /api/leads/{id}/approve-terms
{
  "method": "טלפון",
  "notes": "אישר בטלפון בתאריך 10/2/2026"
}
```

**3. שליחת מייל תקנון**:
```python
async def send_terms_approval_email(
    to_email: str,
    lead_name: str,
    approval_link: str
) -> bool:
    """שליחת מייל עם קישור לאישור תקנון"""
    html_body = f"""
    <div dir="rtl">
        <h2>שלום {lead_name},</h2>
        <p>לאישור התקנון והתחלת הקורס, אנא לחץ על הקישור:</p>
        <a href="{approval_link}">אישור תקנון</a>
    </div>
    """
    return await send_email(to_email, "אישור תקנון - קניין הוראה", html_body)
```

**4. דף אישור תקנון** (Frontend):
```
/approve-terms/{token}
```

**סטטוס ליד**: `ממתין לאישור תקנון` → `תקנון אושר`

---

### שלב 10: המרה לתלמיד ✅

**סטטוס**: עובד מלא

**מה קורה**:
1. נוצר `Student` מפרטי הליד
2. נוצר `Enrollment` לקורס
3. נוצר `Commitment` (הוראת קבע)
4. נוצרות רשומות `Collection` לכל תשלום עתידי
5. הליד מסומן כ-`converted`

**API**:
```http
POST /api/leads/{id}/convert
{
  "course_id": 7
}
```

**סטטוס ליד**: `ליד סגור-לקוח`

---

## 📊 סטטוסי ליד - מערכת מורחבת

### סטטוסים נוכחיים (קיימים):
1. `ליד חדש` - נכנס למערכת
2. `חיוג ראשון` - בוצעה שיחה ראשונה
3. `במעקב` - מעוניין, דורש מעקב
4. `מתעניין` - מעוניין רציני
5. `נסלק` - בוצע תשלום ראשון
6. `ליד סגור-לקוח` - הומר לתלמיד
7. `ליד סגור-לא רלוונטי` - לא רלוונטי

### סטטוסים מוצעים להוספה:
8. `חומרים נשלחו` - נשלח מייל חומרים
9. `ממתין להחלטה` - מחכים לתשובה אחרי שליחת חומרים
10. `מוצר נבחר` - בחר מוצר ספציפי
11. `ממתין לתשלום` - נוצר לינק תשלום
12. `ממתין לאישור תקנון` - צריך לאשר תקנון
13. `תקנון אושר` - אישר תקנון, מוכן להמרה

---

## 🔧 פערים טכניים ופתרונות

### 1. שדות חסרים במודל Lead

**להוסיף ל-`db/models.py`**:
```python
class Lead(Base):
    # ... שדות קיימים ...
    
    # תגובות ומעקב
    lead_response: Mapped[Optional[str]] = mapped_column(String(100))
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0)
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # הנחות
    discount_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # אישור תקנון
    approval_method: Mapped[Optional[str]] = mapped_column(String(50))
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
```

### 2. API Endpoints חסרים

**להוסיף ל-`api/leads_api.py`**:
```python
@router.patch("/{lead_id}/record-call")
async def record_call_response(...)
    """רישום תגובת ליד אחרי שיחה"""

@router.post("/{lead_id}/send-materials")
async def send_course_materials(...)
    """שליחת מייל חומרים"""

@router.post("/{lead_id}/apply-discount")
async def apply_discount(...)
    """החלת הנחה/קופון"""

@router.post("/{lead_id}/approve-terms")
async def approve_terms(...)
    """אישור תקנון"""

@router.post("/{lead_id}/create-follow-up-task")
async def create_follow_up_task(...)
    """יצירת משימת מעקב"""
```

### 3. שירותים חסרים

**להוסיף ל-`services/email_service.py`**:
```python
async def send_course_materials_email(...)
async def send_terms_approval_email(...)
async def send_follow_up_reminder_email(...)
```

**להוסיף ל-`services/leads.py`**:
```python
async def record_call_response(...)
async def apply_discount_to_lead(...)
async def approve_lead_terms(...)
```

**להוסיף ל-`services/sales.py`**:
```python
async def create_auto_follow_up_task(...)
async def get_overdue_tasks(...)
async def get_tasks_due_today(...)
```

### 4. שיפורים באינטגרציית נדרים פלוס

**עדכון `services/nedarim_plus.py`**:
```python
async def create_lead_payment_link(
    # ... פרמטרים קיימים ...
    payment_day: int | None = None,  # ← הוספה
    recurring: bool = False,  # ← הוספה
):
    # העברת payment_day לנדרים פלוס
    if recurring and payment_day:
        nedarim_data["recurring_day"] = payment_day
```

---

## 🎯 סדר עדיפויות ליישום

### עדיפות גבוהה (חובה):
1. ✅ **רישום תגובות ליד** - שדה `lead_response` + API
2. ✅ **שליחת מייל חומרים** - תבנית + API
3. ✅ **אישור תקנון** - שדות + API + מייל
4. ✅ **חישוב הנחות** - פונקציה + API

### עדיפות בינונית (חשוב):
5. ⚠️ **משימות מעקב אוטומטיות** - יצירה אוטומטית
6. ⚠️ **העברת payment_day לנדרים** - שיפור אינטגרציה
7. ⚠️ **סטטוסים מורחבים** - הוספת סטטוסים חדשים

### עדיפות נמוכה (נחמד):
8. 📧 **התראות מייל יומיות** - משימות היום
9. 📊 **דשבורד מכירות** - סטטיסטיקות
10. 🔔 **התראות בזמן אמת** - WebSocket

---

## 📝 דוגמת תהליך מלא

```
1. ליד נכנס מאלמנטור
   ↓ סטטוס: "ליד חדש"
   
2. איש מכירות מחייג
   POST /api/leads/123/record-call
   {
     "response": "מעוניין",
     "notes": "מעוניין בקורס גמרא"
   }
   ↓ סטטוס: "חיוג ראשון"
   
3. שולח חומרים
   POST /api/leads/123/send-materials
   {
     "course_id": 5,
     "include_syllabus": true
   }
   ↓ סטטוס: "חומרים נשלחו"
   ↓ נוצרת משימת מעקב ליומיים
   
4. מעקב אחרי יומיים
   POST /api/leads/123/record-call
   {
     "response": "מוכן לרכוש"
   }
   ↓ סטטוס: "מתעניין"
   
5. בחירת מוצר
   POST /api/leads/123/select-product
   {
     "product_id": 3,
     "price": 2500,
     "payments_count": 10,
     "payment_day": 15
   }
   ↓ סטטוס: "מוצר נבחר"
   
6. החלת הנחה
   POST /api/leads/123/apply-discount
   {
     "custom_discount_type": "אחוז",
     "custom_discount_value": 10
   }
   ↓ מחיר סופי: 2250 ש"ח
   
7. יצירת לינק תשלום
   POST /api/leads/123/create-payment-link
   {
     "amount": 225,
     "installments": 10
   }
   ↓ סטטוס: "ממתין לתשלום"
   ↓ לינק נשלח ללקוח
   
8. לקוח משלם (webhook מנדרים)
   POST /api/webhooks/nedarim
   ↓ Lead.first_payment = true
   ↓ סטטוס: "נסלק"
   
9. אישור תקנון
   POST /api/leads/123/approve-terms
   {
     "method": "טלפון"
   }
   ↓ סטטוס: "תקנון אושר"
   
10. המרה לתלמיד
    POST /api/leads/123/convert
    {
      "course_id": 5
    }
    ↓ סטטוס: "ליד סגור-לקוח"
    ↓ נוצר Student + Enrollment + Commitment + Collections
```

---

## 🚀 צעדים הבאים

### שלב א' - תשתית בסיסית (שבוע 1)
- [ ] הוספת שדות חסרים למודל Lead
- [ ] יצירת migration
- [ ] API לרישום תגובות
- [ ] API לשליחת חומרים
- [ ] תבניות מייל

### שלב ב' - הנחות ותשלומים (שבוע 2)
- [ ] פונקציית חישוב הנחות
- [ ] API להחלת הנחה
- [ ] שיפור אינטגרציית נדרים (payment_day)
- [ ] API לאישור תקנון

### שלב ג' - משימות ומעקב (שבוע 3)
- [ ] יצירה אוטומטית של משימות
- [ ] API למשימות
- [ ] התראות בסיסיות

### שלב ד' - ממשק משתמש (שבוע 4)
- [ ] עדכון LeadWorkspace
- [ ] טפסים לכל השלבים
- [ ] תצוגת סטטוסים מורחבת

---

## 📚 קבצים רלוונטיים

### Backend:
- `db/models.py` - מודלים (Lead, LeadProduct, Payment, etc.)
- `api/leads_api.py` - API endpoints
- `services/leads.py` - לוגיקה עסקית
- `services/email_service.py` - שליחת מיילים
- `services/nedarim_plus.py` - אינטגרציה לנדרים פלוס
- `services/sales.py` - משימות מכירות

### Frontend:
- `frontend/src/components/leads/LeadWorkspace.tsx`
- `frontend/src/components/leads/LeadPaymentTab.tsx`

### תיעוד:
- `LEAD_FLOW_GUIDE.md` - מדריך פלואו קיים
- `ENTITIES_SPEC.md` - אפיון ישויות
- `LEAD_SALES_WORKFLOW.md` - **מסמך זה**

---

**סיכום**: המערכת הקיימת מכסה את התשתית הבסיסית, אבל חסרים רכיבים קריטיים לתהליך מכירה מלא. יישום הפתרונות המוצעים ייצור תהליך מכירה מלא וחלק ללא כפילויות.
