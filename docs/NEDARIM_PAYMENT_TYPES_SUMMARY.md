# סיכום מסקנות - סוגי תשלום ב-Nedarim Plus DebitCard API

**תאריך:** 16 פברואר 2026 (עדכון אחרון: 16/02/2026 21:30)  
**נושא:** הבדלים בין RAGIL ל-HK, תיקון שגיאות, והטמעת CallBack

---

## 🔍 הבעיה שזוהתה

במהלך פיתוח מערכת הסליקה הישירה, זוהו מספר בעיות קריטיות:

1. **שגיאת כתיב קריטית:** הקוד שלח `Tashlumim` (בלי ou) — נדרים **מתעלם** מזה! הכתיב הנכון: **`Tashloumim`** (עם ou)
2. **DebitCard.aspx לא תומך ב-HK אמיתי** — `PaymentType=HK` מתעלם. רק פריסה לתשלומים עובדת.
3. **חוסר תמיכה ב-CallBack URL**
4. **הקוד לא שלח `installments` ל-HK**

---

## 📊 הבדלים בין RAGIL ל-HK

### RAGIL (תשלום רגיל עם תשלומים)

| פרמטר | ערך | הסבר |
|-------|-----|------|
| `PaymentType` | `RAGIL` | סוג תשלום רגיל |
| `Amount` | **סכום כולל** | הסכום המלא של העסקה |
| `Tashloumim` | מספר תשלומים (1-36) | לכמה תשלומים לחלק |
| **תפיסת מסגרת** | ✅ **כן** | הסכום הכולל נתפס מיידית |
| **חיוב** | פרוס על פני תשלומים | חברת האשראי מחלקת לתשלומים |
| **מתאים ל** | כרטיסי אשראי רגילים | לא דביט/חיוב מיידי |

**דוגמה:**
- סכום כולל: ₪1,200
- תשלומים: 12
- `Amount=1200`, `Tashloumim=12`
- **תוצאה:** תפיסת ₪1,200 מיידית, חיוב של ₪100 כל חודש

---

### HK (הוראת קבע - ללא תפיסת מסגרת)

| פרמטר | ערך | הסבר |
|-------|-----|------|
| `PaymentType` | `HK` | הוראת קבע |
| `Amount` | **סכום חודשי** | הסכום לחיוב כל חודש |
| `Tashloumim` | מספר תשלומים | לכמה תשלומים לפרוס |
| **תפיסת מסגרת** | ❌ **לא (לפי תיעוד iframe)** | ב-DebitCard.aspx מתנהג כתשלומים רגילים |
| **חיוב** | פריסה לתשלומים | DebitCard.aspx מפרס כמו RAGIL |
| **מתאים ל** | כרטיסי אשראי רגילים | כרטיסי דביט לא תומכים בתשלומים |

**דוגמה:**
- סכום כולל: ₪1,200
- חודשים: 12
- `Amount=1200`, `Tashloumim=12`
- **תוצאה ב-DebitCard.aspx:** פריסה ל-12 תשלומים של ₪100 (TransactionType=תשלומים)

**⚠️ הערה קריטית:**
- **DebitCard.aspx לא יוצר הוראת קבע אמיתית (KevaId ריק תמיד)**
- `PaymentType=HK` מתעלם ב-DebitCard.aspx — התוצאה תמיד עסקה רגילה/תשלומים
- הוראת קבע אמיתית (עם KevaId) אפשרית רק דרך ה-iframe API
- מינימום ₪5 לכל תשלום

---

## 🐛 שגיאות שתוקנו

### 1. שגיאת כתיב קריטית

**הבעיה:** הקוד שלח `Tashlumim` (בלי ou) — נדרים **מתעלם לחלוטין** מפרמטר זה!

```python
payload['Tashlumim'] = str(installments)  # ❌ נדרים מתעלם!
```

**התיקון:**
```python
payload['Tashloumim'] = str(installments)  # ✅ נדרים מזהה!
```

**הוכחה מבדיקות 16/02/2026:**
- `Tashlumim=2` → נדרים מתעלם, מחזיר `Tashloumim=1`, `TransactionType=רגיל`
- `Tashloumim=2` → נדרים מזהה, מחזיר `Tashloumim=2`, `TransactionType=תשלומים`, confirmation=0419317

---

### 2. חישוב Amount שגוי

**לפני:** הקוד לא שלח `installments` ל-HK בכלל.

**אחרי:**
```typescript
// HK: Amount = monthly payment (total / installments)
// RAGIL: Amount = total amount (full)
const monthlyAmount = totalAmount / installments
const amount = paymentType === 'HK' ? monthlyAmount : totalAmount
```

---

### 3. חוסר תמיכה ב-CallBack

**נוסף:**
```python
callback_url = f"{base_url}/webhooks/nedarim-debitcard"
param2 = str(lead_id)  # For callback identification
```

**תוצאה:** המערכת מקבלת עדכון אוטומטי כשהתשלום מאושר.

---

## 🧪 בדיקות שבוצעו

### בדיקה עם כרטיס דביט

**כרטיס:** 5326141204526337 (לא פעיל)

| סוג תשלום | Tashlumim | תוצאה |
|-----------|-----------|--------|
| RAGIL - 1 תשלום | 1 | ⚠️ שגיאת אבטחה (002) |
| RAGIL - מספר תשלומים | 3/6/12 | ❌ "דיירקט לא יכול תשלומים" |
| HK ללא Tashlumim | - | ⚠️ שגיאת אבטחה (002) |
| HK + Tashlumim | 3/6/12 | ❌ "דיירקט לא יכול תשלומים" |

**מסקנה:** כרטיסי דביט לא תומכים ב-`Tashlumim` בכלל.

---

### בדיקה עם כרטיס אשראי אמיתי

**כרטיס:** 4580170008989957

| סוג תשלום | Amount | Tashloumim | תוצאה |
|-----------|--------|-----------|--------|
| HK | ₪5 | 3 | ❌ "מינימום 5 שח לתשלום" (5/3=1.67) |
| HK | ₪10 | 3 | ❌ "מינימום 5 שח לתשלום" (10/3=3.33) |
| HK | ₪20 | 3 | ✅ **הצליח!** (20/3=6.67) confirmation=0212274 |
| HK | ₪11 | 2 | ✅ **הצליח!** (11/2=5.50) confirmation=0419317 |

**מסקנה:** 
- מינימום ₪5 **לכל תשלום** (Amount / Tashloumim >= 5)
- `Tashloumim` (עם ou) עובד עם כרטיסי אשראי רגילים
- `Tashlumim` (בלי ou) — נדרים **מתעלם לחלוטין**
- `PaymentType=HK` מתעלם ב-DebitCard.aspx — התוצאה תמיד תשלומים רגילים

---

## 🔧 השינויים שבוצעו

### 1. Backend (`services/nedarim_debit_card.py`)

```python
# IMPORTANT: Tashloumim with 'ou'! Nedarim ignores 'Tashlumim' (without ou)
payload['Tashloumim'] = str(installments)

# הוספת CallBack
payload['CallBack'] = callback_url
payload['Param2'] = str(lead_id)

# תמיכה בתשלומים
if payment_type == 'HK':
    if installments and installments > 1:
        payload['Tashloumim'] = str(installments)
```

---

### 2. Frontend (`DirectChargeDialog.tsx`)

```typescript
// ברירת מחדל: HK (לא RAGIL)
const [paymentType, setPaymentType] = useState<'RAGIL' | 'HK'>('HK')

// חישוב נכון של Amount
const monthlyAmount = totalAmount / installments
const amount = paymentType === 'HK' ? monthlyAmount : totalAmount

// שליחת installments גם ל-HK
if (installments && installments > 0) {
  payload.installments = installments
}
```

---

### 3. Webhook (`webhooks/nedarim_debitcard.py`)

וובהוק חדש שמטפל בקאלבק מנדרים ומבצע:

1. ✅ מציאת התשלום (לפי confirmation או lead_id)
2. ✅ עדכון סטטוס התשלום ל-"שולם"
3. ✅ עדכון הליד ל-"נסלק"
4. ✅ **המרה אוטומטית לתלמיד** אם:
   - יש תשלום ראשון
   - יש קורס נבחר
   - הליד עדיין לא תלמיד

---

## 📋 סיכום טכני

### מה עובד עכשיו:

| תכונה | סטטוס |
|-------|-------|
| RAGIL עם תשלומים (Tashloumim) | ✅ עובד (כרטיסי אשראי) |
| HK עם Tashloumim (פריסה לתשלומים) | ✅ עובד (כרטיסי אשראי) |
| HK אמיתי (הוראת קבע עם KevaId) | ❌ לא נתמך ב-DebitCard.aspx |
| CallBack URL | ✅ מוטמע |
| המרה אוטומטית לתלמיד | ✅ מוטמעת |
| תיקון כתיב Tashloumim (ou) | ✅ תוקן |

### מגבלות ידועות:

- ❌ כרטיסי דביט לא תומכים בתשלומים (Tashloumim)
- ❌ DebitCard.aspx לא יוצר הוראת קבע אמיתית (KevaId תמיד ריק)
- ⚠️ מינימום ₪5 לכל תשלום (Amount / Tashloumim >= 5)
- ⚠️ `Tashlumim` (בלי ou) — נדרים מתעלם! חובה `Tashloumim` (עם ou)

---

## 🎯 המלצות שימוש

### לכרטיסי אשראי רגילים:
- **RAGIL + Tashloumim** - לתשלומים עם תפיסת מסגרת
- **HK + Tashloumim** - פריסה לתשלומים (ב-DebitCard.aspx מתנהג כמו RAGIL)

### לכרטיסי דביט:
- **RAGIL ללא Tashloumim** (או =1) - חיוב חד-פעמי בלבד
- תשלומים לא נתמכים בכרטיסי דביט

---

## 📞 פרטי תמיכה

- **תיעוד רשמי:** https://matara.pro/nedarimplus/ApiDocumentation.html?v=61
- **טלפון תמיכה:** 03-7630543
- **מייל:** a037630543@gmail.com
- **IP לאימות CallBack:** 18.194.219.73

---

**עדכון אחרון:** 16/02/2026 21:30  
**גרסה:** 2.0 — תיקון כתיב Tashloumim, תיעוד מגבלות DebitCard.aspx
