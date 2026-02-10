# תהליך תשלום מלא לליד - מדריך מפורט

> **עדכון אחרון**: 2026-02-10
> **סטטוס**: ✅ מיושם ופעיל

---

## 📋 סקירה כללית

מסמך זה מתאר את התהליך המלא של ניהול תשלומים ללידים במערכת, כולל:
- בחירת מוצר ומחיר
- הגדרת הנחות
- חישוב מחיר סופי ותשלומים
- יצירת לינק תשלום בנדרים פלוס
- מעקב אחר סטטוס תשלום
- חיבור לישות Collection לתשלומים חוזרים

---

## 🔄 תהליך שלב אחר שלב

### שלב 1: בחירת מוצר לליד

איש המכירות בוחר מוצר ספציפי עבור הליד:

```http
POST /api/leads/{lead_id}/select-product
Content-Type: application/json

{
  "product_id": 3,
  "price": 10000,
  "payments_count": 10,
  "payment_day": 15,
  "payment_type": "הוראת קבע"
}
```

**מה קורה:**
- נוצרת רשומת `LeadProduct` עם פרטי המוצר
- `Lead.selected_product_id` מתעדכן
- המחיר והתשלומים נלקחים מהמוצר (ברירת מחדל)

**תגובה:**
```json
{
  "lead_id": 123,
  "lead_product_id": 456,
  "product_name": "קורס גמרא",
  "price": 10000,
  "payments_count": 10,
  "monthly_payment": 1000
}
```

---

### שלב 2: הגדרת הנחה (אופציונלי)

איש המכירות יכול להגדיר הנחה:

```http
PATCH /api/leads/{lead_id}/update-discount
Content-Type: application/json

{
  "discount_amount": 500,
  "installments_override": 12
}
```

**מה קורה:**
- המערכת מחשבת אוטומטית: `final_price = price - discount_amount`
- מחשבת מחדש: `monthly_payment = final_price / payments_count`
- שומרת את ההנחה ב-`LeadProduct`

**תגובה:**
```json
{
  "original_price": 10000,
  "discount_amount": 500,
  "final_price": 9500,
  "payments_count": 12,
  "monthly_payment": 791.67
}
```

---

### שלב 3: חישוב מקדים (לתצוגה בזמן אמת)

לפני שמירה, ניתן לחשב את המחיר הסופי:

```http
POST /api/leads/{lead_id}/calculate-pricing
Content-Type: application/json

{
  "product_id": 3,
  "discount_amount": 500
}
```

**שימוש:** תצוגה בזמן אמת בממשק כשמשנים את ההנחה

**תגובה:**
```json
{
  "product_id": 3,
  "product_name": "קורס גמרא",
  "original_price": 10000,
  "discount_amount": 500,
  "final_price": 9500,
  "payments_count": 10,
  "monthly_payment": 950
}
```

---

### שלב 4: יצירת לינק תשלום בנדרים פלוס

איש המכירות יוצר לינק תשלום:

```http
POST /api/leads/{lead_id}/create-payment-link
Content-Type: application/json

{
  "amount": 950,
  "installments": 10,
  "payment_method": "credit_card"
}
```

**אם לא מספקים פרמטרים**, המערכת לוקחת אוטומטית מ-`LeadProduct`:
- `amount` ← `final_price` (או `price` אם אין הנחה)
- `installments` ← `payments_count`
- `payment_day` ← `payment_day`

**מה קורה מאחורי הקלעים:**

1. **יצירת Payer בנדרים פלוס:**
```json
POST https://api.nedarimplus.co.il/v1/payers
{
  "mosad_id": "YOUR_MOSAD_ID",
  "payer_name": "ישראל ישראלי",
  "payer_tz": "123456789",
  "payer_phone": "0501234567",
  "payer_email": "israel@example.com"
}
```

2. **יצירת Donation בנדרים פלוס:**
```json
POST https://api.nedarimplus.co.il/v1/donations
{
  "mosad_id": "YOUR_MOSAD_ID",
  "payer_id": "PAY_123456",
  "amount": 950,
  "currency": "ILS",
  "payment_method": "credit_card",
  "installments": 10,
  "recurring_day": 15,
  "redirect_url": "https://yourcrm.com/payment-success?payment_id=789",
  "webhook_url": "https://yourcrm.com/api/webhooks/nedarim",
  "metadata": {
    "lead_id": 123,
    "product_id": 3,
    "payment_day": 15
  }
}
```

3. **שמירה במערכת:**
- נוצרת רשומת `Payment` בסטטוס "ממתין"
- `Lead.nedarim_payment_link` מתעדכן עם הלינק
- `Payment.nedarim_donation_id` מתעדכן

**תגובה:**
```json
{
  "payment_id": 789,
  "lead_id": 123,
  "nedarim_donation_id": "DON_abc123",
  "payment_link": "https://secure.nedarimplus.co.il/pay/DON_abc123",
  "amount": 950,
  "installments": 10,
  "payment_day": 15,
  "status": "ממתין"
}
```

---

### שלב 5: שליחת הלינק ללקוח

איש המכירות שולח את הלינק ללקוח דרך:
- SMS
- מייל
- וואטסאפ
- העתקה ידנית

הלקוח נכנס ללינק ומזין פרטי כרטיס אשראי **בדף מאובטח של נדרים פלוס**.

---

### שלב 6: קבלת Webhook מנדרים

כשהלקוח משלם, נדרים פלוס שולח webhook:

```http
POST /api/webhooks/nedarim
Content-Type: application/json
X-Nedarim-Signature: {HMAC-SHA256}

{
  "event_type": "donation.completed",
  "donation_id": "DON_abc123",
  "payer_id": "PAY_123456",
  "amount": 950,
  "status": "completed",
  "timestamp": "2026-02-10T22:30:00Z",
  "metadata": {
    "lead_id": 123,
    "product_id": 3
  }
}
```

**מה קורה במערכת:**

1. **עדכון Payment:**
   - `Payment.status` → "שולם"
   - `Payment.payment_date` → תאריך נוכחי

2. **עדכון Lead:**
   - `Lead.first_payment` → `true`
   - `Lead.first_payment_id` → ID של התשלום
   - `Lead.status` → "נסלק"

3. **יצירת Collection (אם יש תשלומים חוזרים):**
   - נוצרת רשומת `Collection` ראשונה
   - `Collection.status` → "נגבה"
   - `Collection.installment_number` → 1

**קוד רלוונטי:**
```python
# בקובץ services/nedarim_plus.py - process_webhook()
if event_type == "donation.completed":
    payment.status = "שולם"
    payment.payment_date = datetime.now().date()
    
    if payment.lead_id:
        lead.first_payment = True
        lead.first_payment_id = payment.id
        lead.status = "נסלק"
```

---

### שלב 7: תשלומים חוזרים (Recurring)

אם הוגדרו תשלומים (installments > 1), נדרים פלוס יחייב אוטומטית כל חודש:

```http
POST /api/webhooks/nedarim
{
  "event_type": "subscription.charged",
  "subscription_id": "SUB_xyz789",
  "donation_id": "DON_def456",
  "amount": 950,
  "timestamp": "2026-03-15T10:00:00Z"
}
```

**מה קורה:**

1. **נוצר Payment חדש:**
```python
payment = Payment(
    student_id=commitment.student_id,
    commitment_id=commitment.id,
    amount=950,
    status="שולם",
    payment_date=datetime.now().date(),
    nedarim_donation_id="DON_def456"
)
```

2. **נוצרת Collection:**
```python
collection = Collection(
    student_id=commitment.student_id,
    commitment_id=commitment.id,
    payment_id=payment.id,
    amount=950,
    installment_number=2,  # תשלום שני
    total_installments=10,
    status="נגבה",
    collected_at=datetime.now()
)
```

3. **עדכון Student.total_paid:**
```python
student.total_paid += 950
if student.total_paid >= student.total_price:
    student.payment_status = "שולם"
```

---

### שלב 8: בדיקת סטטוס תשלום

בכל עת, ניתן לבדוק את סטטוס התשלום:

```http
GET /api/leads/{lead_id}/payment-status
```

**תגובה:**
```json
{
  "lead_id": 123,
  "first_payment": true,
  "first_payment_id": 789,
  "nedarim_payment_link": "https://secure.nedarimplus.co.il/pay/DON_abc123",
  "selected_product_id": 456,
  "payments": [
    {
      "id": 789,
      "amount": 950,
      "status": "שולם",
      "payment_date": "2026-02-10",
      "nedarim_donation_id": "DON_abc123",
      "created_at": "2026-02-10T20:00:00Z"
    }
  ]
}
```

---

## 🎯 מבנה הנתונים

### טבלת Lead
```python
class Lead:
    # ... שדות קיימים ...
    
    # Payment tracking
    first_payment: bool = False
    first_payment_id: int | None
    nedarim_payment_link: str | None
    
    # Selected product
    selected_product_id: int | None
```

### טבלת LeadProduct
```python
class LeadProduct:
    lead_id: int
    product_id: int
    
    # Pricing
    price: Decimal  # מחיר מקורי
    discount_amount: Decimal | None  # סכום הנחה
    final_price: Decimal | None  # מחיר סופי
    
    # Installments
    payments_count: int
    monthly_payment: Decimal
    payment_day: int | None  # יום בחודש לחיוב
    payment_type: str  # "הוראת קבע" / "אשראי רגיל"
```

### טבלת Payment
```python
class Payment:
    lead_id: int | None  # לפני המרה
    student_id: int | None  # אחרי המרה
    
    amount: Decimal
    installments: int
    charge_day: int | None
    status: str  # "ממתין" / "שולם" / "נכשל"
    
    # Nedarim integration
    nedarim_donation_id: str
    nedarim_transaction_id: str
```

### טבלת Collection
```python
class Collection:
    student_id: int
    commitment_id: int
    payment_id: int | None
    
    amount: Decimal
    due_date: date
    installment_number: int
    total_installments: int
    status: str  # "ממתין" / "נגבה" / "נכשל"
    
    # Nedarim integration
    nedarim_donation_id: str
    nedarim_subscription_id: str
```

---

## 📊 תרשים זרימה מלא

```
┌─────────────────────────────────────────────────────────────┐
│                    תהליך תשלום ליד                          │
│                                                              │
│  1. בחירת מוצר                                              │
│     POST /api/leads/{id}/select-product                     │
│     ↓                                                        │
│     LeadProduct נוצר                                        │
│     price: 10,000 ₪                                         │
│     payments_count: 10                                      │
│                                                              │
│  2. הגדרת הנחה (אופציונלי)                                 │
│     PATCH /api/leads/{id}/update-discount                   │
│     ↓                                                        │
│     discount_amount: 500 ₪                                  │
│     final_price: 9,500 ₪ (חישוב אוטומטי)                   │
│     monthly_payment: 950 ₪                                  │
│                                                              │
│  3. יצירת לינק תשלום                                       │
│     POST /api/leads/{id}/create-payment-link                │
│     ↓                                                        │
│     ┌──────────────────────────────────┐                   │
│     │  Nedarim Plus API                │                   │
│     │  1. Create Payer                 │                   │
│     │  2. Create Donation              │                   │
│     │  3. Return payment_link          │                   │
│     └──────────────────────────────────┘                   │
│     ↓                                                        │
│     Payment נוצר (status: "ממתין")                         │
│     Lead.nedarim_payment_link מתעדכן                       │
│                                                              │
│  4. שליחת לינק ללקוח                                       │
│     SMS / מייל / וואטסאפ                                   │
│     ↓                                                        │
│     לקוח מזין פרטי כרטיס בדף נדרים                        │
│                                                              │
│  5. Webhook מנדרים                                         │
│     POST /api/webhooks/nedarim                              │
│     event_type: "donation.completed"                        │
│     ↓                                                        │
│     Payment.status → "שולם"                                 │
│     Lead.first_payment → true                               │
│     Lead.status → "נסלק"                                    │
│                                                              │
│  6. תשלומים חוזרים (אם installments > 1)                   │
│     Nedarim מחייב אוטומטית כל חודש                         │
│     ↓                                                        │
│     Webhook: "subscription.charged"                         │
│     ↓                                                        │
│     Payment חדש נוצר                                        │
│     Collection נוצרת                                        │
│     Student.total_paid מתעדכן                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 API Endpoints - סיכום

| Method | Endpoint | תיאור |
|--------|----------|--------|
| POST | `/api/leads/{id}/select-product` | בחירת מוצר לליד |
| PATCH | `/api/leads/{id}/update-discount` | עדכון הנחה ומחיר סופי |
| POST | `/api/leads/{id}/calculate-pricing` | חישוב מקדים (ללא שמירה) |
| POST | `/api/leads/{id}/create-payment-link` | יצירת לינק תשלום בנדרים |
| GET | `/api/leads/{id}/payment-status` | בדיקת סטטוס תשלום |
| POST | `/api/webhooks/nedarim` | קבלת עדכונים מנדרים |

---

## 💡 דוגמאות שימוש

### דוגמה 1: תהליך מלא - ליד חדש עד תשלום

```bash
# 1. בחירת מוצר
curl -X POST http://localhost:8000/api/leads/123/select-product \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 3,
    "price": 10000,
    "payments_count": 10,
    "payment_day": 15
  }'

# 2. הוספת הנחה
curl -X PATCH http://localhost:8000/api/leads/123/update-discount \
  -H "Content-Type: application/json" \
  -d '{
    "discount_amount": 500
  }'

# 3. יצירת לינק תשלום (ישתמש בנתונים מ-LeadProduct)
curl -X POST http://localhost:8000/api/leads/123/create-payment-link \
  -H "Content-Type: application/json" \
  -d '{}'

# תגובה:
# {
#   "payment_link": "https://secure.nedarimplus.co.il/pay/DON_abc123",
#   "amount": 9500,
#   "installments": 10,
#   "payment_day": 15
# }

# 4. בדיקת סטטוס
curl http://localhost:8000/api/leads/123/payment-status
```

### דוגמה 2: חישוב מקדים בזמן אמת

```javascript
// Frontend - חישוב בזמן אמת כשמשנים הנחה
async function calculatePricing(leadId, productId, discountAmount) {
  const response = await fetch(`/api/leads/${leadId}/calculate-pricing`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: productId, discount_amount: discountAmount })
  });
  
  const data = await response.json();
  
  // עדכון UI
  document.getElementById('final-price').textContent = data.final_price;
  document.getElementById('monthly-payment').textContent = data.monthly_payment;
}
```

---

## 🔐 אבטחה

### 1. Webhook Signature Verification
כל webhook מנדרים מאומת באמצעות HMAC-SHA256:

```python
def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.NEDARIM_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

### 2. פרטי כרטיס אשראי
- ❌ **לעולם לא** שומרים פרטי כרטיס במערכת שלנו
- ✅ הלקוח מזין פרטים **רק בדף נדרים פלוס** (PCI compliant)
- ✅ נדרים מחזירים רק tokens מוצפנים

### 3. API Keys
- מאוחסנים ב-`.env` (לא ב-Git)
- נטענים דרך `settings` (Pydantic)
- בפרודקשן: AWS Secrets Manager / Azure Key Vault

---

## 🚨 טיפול בשגיאות

### שגיאות נפוצות

| שגיאה | סיבה | פתרון |
|-------|------|--------|
| `No product selected` | לא נבחר מוצר לליד | לקרוא ל-`select-product` קודם |
| `Amount must be provided` | לא הועבר amount ואין מוצר | להעביר amount או לבחור מוצר |
| `Nedarim API Error 401` | API Key לא תקין | לבדוק `.env` |
| `Webhook signature invalid` | חתימה לא תקינה | לבדוק `NEDARIM_WEBHOOK_SECRET` |

### לוגים

```python
# בקובץ services/nedarim_plus.py
logger.info(f"Created Nedarim payment link for lead {lead_id}: {payment_link}")
logger.warning(f"Payment not found for Nedarim donation {donation_id}")
logger.error(f"Nedarim API error: {status_code}")
```

---

## ✅ סיכום

המערכת תומכת בתהליך תשלום מלא ללידים:

1. ✅ בחירת מוצר עם מחיר וברירת מחדל לתשלומים
2. ✅ הגדרת הנחות עם חישוב אוטומטי של מחיר סופי
3. ✅ דריסת מספר תשלומים לפי שיקול דעת
4. ✅ יצירת לינק תשלום מאובטח בנדרים פלוס
5. ✅ העברת payment_day לתשלומים חוזרים
6. ✅ קבלת webhooks ועדכון סטטוס אוטומטי
7. ✅ חיבור לישות Collection לניהול תשלומים חוזרים
8. ✅ מעקב מלא אחר היסטוריית תשלומים

**הכל מוכן לשימוש!** 🚀
