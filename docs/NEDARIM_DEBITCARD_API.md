# נדרים פלוס - DebitCard API - תיעוד רשמי

**מקור:** https://matara.pro/nedarimplus/ApiDocumentation.html?v=61  
**תאריך עדכון אחרון:** 15 פברואר 2026

---

## 📋 סקירה כללית

ה-DebitCard API של נדרים פלוס מאפשר חיוב ישיר של כרטיסי אשראי ללא צורך במעבר דרך דף תשלום.

### כתובת API
```
POST https://www.matara.pro/nedarimplus/V6/Files/WebServices/DebitCard.aspx
```

### סוג תוכן
```
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

---

## 🔑 פרמטרים נדרשים

| פרמטר | חובה | תיאור | דוגמה |
|-------|------|-------|-------|
| `Mosad` | ✅ | מזהה מוסד (7 ספרות) | `1234567` |
| `ApiPassword` | ✅ | סיסמת API | `xxxxxxx` |
| `ClientName` | ✅ | שם מלא של הלקוח | `יוסי כהן` |
| `CardNumber` | ✅ | מספר כרטיס אשראי (13-16 ספרות) | `4580123456789012` |
| `Tokef` | ✅ | תוקף בפורמט MMYY | `1226` |
| `CVV` | ✅ | CVV (3-4 ספרות) | `123` |
| `Amount` | ✅ | סכום לחיוב | `100.00` |
| `Currency` | ✅ | מטבע: `1` (₪) או `2` ($) | `1` |
| `PaymentType` | ✅ | `RAGIL` (רגיל) או `HK` (הוראת קבע) | `RAGIL` |

### פרמטרים אופציונליים

| פרמטר | תיאור | דוגמה |
|-------|-------|-------|
| `Mail` | כתובת מייל | `yossi@example.com` |
| `Phone` | טלפון | `0501234567` |
| `Avour` | הערות/תיאור | `תשלום עבור קורס` |
| `Groupe` | קטגוריה/קבוצה | `קורס א'` |
| `Param1` | פרמטר נוסף (למשל: שם איש מכירות) | `משה לוי` |
| `Tashloumim` | מספר תשלומים (רק ל-RAGIL) | `1` |
| `AjaxId` | מזהה ייחודי לבקשה | `1708001234567` |

---

## ⚠️ כללים קריטיים - הוראת קבע (HK)

### 🚨 **חשוב מאוד!**

**כאשר `PaymentType=HK` (הוראת קבע):**

1. **אסור לשלוח את הפרמטר `Tashloumim` בכלל!**
   - אם שולחים `Tashloumim` עם `HK` → השרת יחזיר שגיאה
   - כרטיסי חיוב ישיר (Direct Debit) דוחים כל ערך של `Tashloumim` עם `HK`

2. **הוראת הקבע עצמה מטפלת בחיובים החודשיים**
   - אין צורך לציין מספר תשלומים
   - המערכת תחייב אוטומטית כל חודש
   - ביטול נעשה ידנית דרך ממשק נדרים פלוס

3. **הסכום ב-`Amount` הוא הסכום החודשי**
   - לא הסכום הכולל
   - זה הסכום שיחויב כל חודש

### דוגמה נכונה - הוראת קבע

```http
POST https://www.matara.pro/nedarimplus/V6/Files/WebServices/DebitCard.aspx
Content-Type: application/x-www-form-urlencoded

Mosad=1234567
&ApiPassword=xxxxxxx
&ClientName=יוסי כהן
&CardNumber=4580123456789012
&Tokef=1226
&CVV=123
&Amount=500.00
&Currency=1
&PaymentType=HK
&Mail=yossi@example.com
&Phone=0501234567
&Avour=הוראת קבע - קורס א'
&Groupe=קורס א'
&AjaxId=1708001234567
```

**שים לב:** אין `Tashloumim` בכלל!

### דוגמה נכונה - תשלום רגיל

```http
POST https://www.matara.pro/nedarimplus/V6/Files/WebServices/DebitCard.aspx
Content-Type: application/x-www-form-urlencoded

Mosad=1234567
&ApiPassword=xxxxxxx
&ClientName=יוסי כהן
&CardNumber=4580123456789012
&Tokef=1226
&CVV=123
&Amount=5000.00
&Currency=1
&PaymentType=RAGIL
&Tashloumim=1
&Mail=yossi@example.com
&Phone=0501234567
&Avour=תשלום חד-פעמי
&Groupe=קורס א'
&AjaxId=1708001234567
```

**שים לב:** יש `Tashloumim=1` כי זה `RAGIL`

---

## 📤 תגובת API

### הצלחה
```json
{
  "Status": "OK",
  "TransactionId": "123456789",
  "Confirmation": "0123456",
  "Amount": "500.00",
  "TransactionTime": "2026-02-15 12:30:45",
  "LastNum": "9012",
  "ReceiptDocNum": "1001"
}
```

### כישלון
```json
{
  "Status": "Error",
  "Message": "כרטיס נדחה",
  "BackMessage": "Insufficient funds"
}
```

---

## 🐛 הבעיה שזוהתה במערכת

### הבעיה
בקוד הקיים ב-`DirectChargeDialog.tsx` (שורה 93):
```typescript
installments: paymentType === 'HK' ? 0 : 1,
```

**זה שולח `Tashloumim=0` כאשר בוחרים HK!**

### הפתרון
**אסור לשלוח את הפרמטר בכלל** כאשר `PaymentType=HK`.

בקוד Python ב-`nedarim_debit_card.py` (שורות 127-138) - **זה נכון!**
```python
if payment_type == 'HK':
    # Never send Tashloumim with HK - causes "direct card" errors
    pass
else:
    # For regular payment: must have installments
    payload['Tashloumim'] = str(installments)
```

**הקוד ב-Python עובד נכון - הוא לא שולח את הפרמטר בכלל עבור HK.**

---

## 🔧 תיקון נדרש

### ב-Frontend (`DirectChargeDialog.tsx`)

במקום לשלוח `installments: 0`, צריך **לא לשלוח את השדה בכלל**:

```typescript
const payload: any = {
  card_number: cleanCardNumber,
  expiry: cleanExpiry,
  cvv: cvv,
  amount: amount,
  payment_type: paymentType,
  comments: comments || undefined
}

// Add installments ONLY for RAGIL
if (paymentType === 'RAGIL') {
  payload.installments = 1
}
// For HK: don't send installments at all

const response = await api.post<any>(`/leads/${leadId}/charge-card-direct`, payload)
```

### ב-Backend (`leads_api.py`)

צריך לוודא שה-API endpoint לא מעביר `installments` כאשר הוא `None` או `0`:

```python
# In charge_lead_card function call
installments = data.get('installments')
if payment_type == 'HK':
    installments = None  # Don't pass to service
```

---

## 📊 סיכום ההבדלים

| תכונה | RAGIL (רגיל) | HK (הוראת קבע) |
|-------|-------------|----------------|
| `PaymentType` | `RAGIL` | `HK` |
| `Tashloumim` | **חובה** (1-36) | **אסור לשלוח!** |
| `Amount` | סכום כולל | סכום חודשי |
| חיוב | חד-פעמי | חודשי אוטומטי |
| ביטול | אוטומטי אחרי התשלום | ידני דרך נדרים פלוס |

---

## 🔗 קישורים נוספים

- **דוקומנטציה מלאה:** https://matara.pro/nedarimplus/ApiDocumentation.html?v=61
- **תמיכה טכנית:** 03-7630543
- **מייל תמיכה:** a037630543@gmail.com

---

## 📝 הערות חשובות

1. **אבטחה:** אל תשמור מספרי כרטיס אשראי מלאים במסד הנתונים
2. **Timeout:** המערכת ממתינה עד 30 שניות לתגובה
3. **שגיאות נפוצות:**
   - `Tashloumim` עם `HK` → שגיאת "direct card"
   - CVV שגוי → "Invalid CVV"
   - כרטיס פג תוקף → "Card expired"
4. **Mock Mode:** כאשר `ApiPassword=ou946` המערכת עובדת במצב דמה (לפיתוח)

---

**עדכון אחרון:** 15/02/2026  
**גרסת API:** V6
