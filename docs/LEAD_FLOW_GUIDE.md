# מדריך פלואו לידים ואינטגרציית נדרים פלוס

## סקירה כללית

מערכת ה-CRM מספקת זרימה מלאה מליד ועד לתלמיד משלם עם אינטגרציה מלאה לנדרים פלוס לסליקה ותשלומים חוזרים.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Lead Sales Flow                                  │
│                                                                          │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │ ליד חדש │───▶│ בחירת   │───▶│ יצירת   │───▶│ סליקה מוצלחת    │   │
│  │         │    │ מוצר    │    │ לינק    │    │                  │   │
│  └─────────┘    │ (Lead   │    │ תשלום   │    │ ☑ first_payment  │   │
│                 │ Product)│    │ (נדרים) │    │ ☑ status=נסלק    │   │
│                 └──────────┘    └──────────┘    └────────┬─────────┘   │
│                                                          │             │
│                                                          ▼             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      המרה לתלמיד                                 │  │
│  │  Lead ──▶ Student + Enrollment + Commitment + Collection[]       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## שלב 1: ליד חדש

כאשר ליד נכנס למערכת (מאלמנטור, ימות, או ידנית):

```python
POST /api/leads/
{
    "full_name": "ישראל ישראלי",
    "phone": "0501234567",
    "source_type": "אלמנטור",
    "campaign_id": 5
}
```

- **סטטוס**: `ליד חדש`
- **שיוך אוטומטי**: איש מכירות מוקצה ב-round-robin

---

## שלב 2: בחירת מוצר

איש המכירות בוחר מוצר ותנאי תשלום:

```python
POST /api/leads/{lead_id}/select-product
{
    "product_id": 3,
    "price": 2500,
    "payments_count": 10,
    "monthly_payment": 250,
    "payment_day": 15,
    "payment_type": "הוראת קבע"
}
```

- נוצרת רשומת `LeadProduct` עם כל הפרטים
- השדה `selected_product_id` בליד מתעדכן

---

## שלב 3: יצירת לינק תשלום

איש המכירות יוצר לינק תשלום לסליקה:

```python
POST /api/leads/{lead_id}/create-payment-link
{
    "amount": 250,
    "currency": "ILS",
    "installments": 1,
    "payment_method": "credit_card"
}
```

**מה קורה מאחורי הקלעים:**
1. נוצר `Payer` בנדרים פלוס עם פרטי הליד
2. נוצרת רשומת `Payment` בסטטוס "ממתין"
3. נוצר לינק תשלום בנדרים פלוס
4. הלינק נשמר ב-`lead.nedarim_payment_link`

**תגובה:**
```json
{
    "payment_id": 123,
    "lead_id": 456,
    "nedarim_donation_id": "DON_abc123",
    "payment_link": "https://nedarim.co.il/pay/abc123",
    "status": "ממתין"
}
```

---

## שלב 4: סליקה מוצלחת

כאשר הלקוח משלם, נדרים פלוס שולח webhook:

```python
POST /api/webhooks/nedarim
{
    "event_type": "donation.completed",
    "donation_id": "DON_abc123",
    "amount": 250,
    "timestamp": "2026-02-10T12:00:00Z"
}
```

**מה מתעדכן:**
- `Payment.status` → "שולם"
- `Payment.payment_date` → התאריך
- `Lead.first_payment` → `true`
- `Lead.first_payment_id` → 123
- `Lead.status` → "נסלק"

---

## שלב 5: המרה לתלמיד

לאחר הסליקה, איש המכירות ממיר את הליד לתלמיד:

```python
POST /api/leads/{lead_id}/convert
{
    "course_id": 7
}
```

**מה נוצר:**
1. `Student` — משוכפל מפרטי הליד
2. `Enrollment` — הרשמה לקורס שנבחר
3. `Commitment` — הוראת קבע (אם נבחר תשלומים)
4. `Collection[]` — רשומות גביה לכל תשלום עתידי

---

## זרימת גביה חוזרת

כאשר נדרים פלוס גובה תשלום חוזר:

```python
POST /api/webhooks/nedarim
{
    "event_type": "subscription.charged",
    "subscription_id": "SUB_xyz789",
    "donation_id": "DON_def456",
    "amount": 250
}
```

**מה נוצר:**
1. `Payment` חדש (שולם)
2. `Collection` מעודכן ל-"נגבה"
3. `Student.total_paid` מתעדכן

---

## API Endpoints

### לידים
| Method | Endpoint | תיאור |
|--------|----------|--------|
| POST | `/api/leads/{id}/select-product` | בחירת מוצר לליד |
| POST | `/api/leads/{id}/create-payment-link` | יצירת לינק תשלום |
| GET | `/api/leads/{id}/payment-status` | סטטוס תשלומים |
| POST | `/api/leads/{id}/convert` | המרה לתלמיד |

### גביות
| Method | Endpoint | תיאור |
|--------|----------|--------|
| GET | `/api/collections/pending` | גביות ממתינות |
| GET | `/api/collections/overdue` | גביות באיחור |
| GET | `/api/collections/due-soon?days=7` | גביות בשבוע הקרוב |
| GET | `/api/collections/student/{id}` | גביות לתלמיד |
| GET | `/api/collections/summary` | סטטיסטיקות גביה |
| POST | `/api/collections/{id}/collected` | סימון כנגבה |
| POST | `/api/collections/{id}/failed` | סימון כנכשל |
| POST | `/api/collections/{id}/retry` | ניסיון חוזר |
| POST | `/api/collections/commitment/{id}/generate` | יצירת גביות מהתחייבות |

---

## דשבורד תלמיד

כאשר מביאים נתוני תלמיד, מתקבלים גם:

```python
GET /api/students/{id}
```

**תגובה כוללת:**
```json
{
    "id": 1,
    "full_name": "ישראל ישראלי",
    "total_price": 2500,
    "total_paid": 750,
    "payment_status": "בתשלומים",
    "enrollments": [...],
    "payments": [
        {"id": 1, "amount": 250, "status": "שולם", "payment_date": "2026-01-15"},
        {"id": 2, "amount": 250, "status": "שולם", "payment_date": "2026-02-15"},
        {"id": 3, "amount": 250, "status": "שולם", "payment_date": "2026-03-15"}
    ],
    "collections": [
        {"id": 1, "amount": 250, "status": "נגבה", "installment_number": 1},
        {"id": 2, "amount": 250, "status": "נגבה", "installment_number": 2},
        {"id": 3, "amount": 250, "status": "נגבה", "installment_number": 3},
        {"id": 4, "amount": 250, "status": "ממתין", "installment_number": 4, "due_date": "2026-04-15"},
        ...
    ],
    "commitments": [
        {"id": 1, "monthly_amount": 250, "installments": 10, "status": "פעיל"}
    ]
}
```

---

## סטטוסים

### סטטוס ליד
| סטטוס | תיאור |
|-------|--------|
| ליד חדש | נכנס למערכת |
| חיוג ראשון | בוצעה שיחה ראשונה |
| במעקב | מעוניין, דורש מעקב |
| מתעניין | מעוניין רציני |
| **נסלק** | בוצע תשלום ראשון ✓ |
| ליד סגור-לקוח | הומר לתלמיד |
| ליד סגור-לא רלוונטי | לא רלוונטי |

### סטטוס גביה
| סטטוס | תיאור |
|-------|--------|
| ממתין | טרם הגיע מועד/טרם נגבה |
| נגבה | גביה הצליחה ✓ |
| נכשל | גביה נכשלה ✗ |
| בוטל | בוטל ידנית |

### סטטוס התחייבות
| סטטוס | תיאור |
|-------|--------|
| פעיל | הוראת קבע פעילה |
| מושהה | מושהה זמנית |
| הסתיים | כל התשלומים בוצעו |
| בוטל | בוטל |
