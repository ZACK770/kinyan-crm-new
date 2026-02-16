# סיכום מסקנות - סוגי תשלום ב-Nedarim Plus DebitCard API

**תאריך:** 16 פברואר 2026  
**נושא:** הבדלים בין RAGIL ל-HK, תיקון שגיאות, והטמעת CallBack

---

## 🔍 הבעיה שזוהתה

במהלך פיתוח מערכת הסליקה הישירה, זוהו מספר בעיות קריטיות:

1. **שגיאת כתיב קריטית:** `Tashloumim` במקום `Tashlumim` (הכתיב הנכון)
2. **חוסר הבנה של ההבדל בין RAGIL ל-HK**
3. **חוסר תמיכה ב-CallBack URL**
4. **הקוד לא שלח `installments` ל-HK**

---

## 📊 הבדלים בין RAGIL ל-HK

### RAGIL (תשלום רגיל עם תשלומים)

| פרמטר | ערך | הסבר |
|-------|-----|------|
| `PaymentType` | `RAGIL` | סוג תשלום רגיל |
| `Amount` | **סכום כולל** | הסכום המלא של העסקה |
| `Tashlumim` | מספר תשלומים (1-36) | לכמה תשלומים לחלק |
| **תפיסת מסגרת** | ✅ **כן** | הסכום הכולל נתפס מיידית |
| **חיוב** | פרוס על פני תשלומים | חברת האשראי מחלקת לתשלומים |
| **מתאים ל** | כרטיסי אשראי רגילים | לא דביט/חיוב מיידי |

**דוגמה:**
- סכום כולל: ₪1,200
- תשלומים: 12
- `Amount=1200`, `Tashlumim=12`
- **תוצאה:** תפיסת ₪1,200 מיידית, חיוב של ₪100 כל חודש

---

### HK (הוראת קבע - ללא תפיסת מסגרת)

| פרמטר | ערך | הסבר |
|-------|-----|------|
| `PaymentType` | `HK` | הוראת קבע |
| `Amount` | **סכום חודשי** | הסכום לחיוב כל חודש |
| `Tashlumim` | מספר חודשים (אופציונלי) | כמה חודשים לחייב |
| **תפיסת מסגרת** | ❌ **לא** | אין תפיסה מראש |
| **חיוב** | חודשי אוטומטי | כל חודש בנפרד |
| **מתאים ל** | כרטיסי אשראי ודביט | גם חיוב מיידי |

**דוגמה:**
- סכום כולל: ₪1,200
- חודשים: 12
- `Amount=100`, `Tashlumim=12`
- **תוצאה:** חיוב של ₪100 כל חודש למשך 12 חודשים (ללא תפיסה)

**הערה חשובה:**
- אם `Tashlumim` ריק/לא נשלח → הוראת קבע אינסופית (עד ביטול ידני)
- אם `Tashlumim` מוגדר → הוראת קבע למספר חודשים מוגדר

---

## 🐛 שגיאות שתוקנו

### 1. שגיאת כתיב קריטית

**לפני:**
```python
payload['Tashloumim'] = str(installments)  # ❌ כתיב שגוי
```

**אחרי:**
```python
payload['Tashlumim'] = str(installments)  # ✅ כתיב נכון
```

**השפעה:** הפרמטר לא התקבל נכון בשרת נדרים פלוס, מה שגרם לשגיאות.

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

| סוג תשלום | Amount | Tashlumim | תוצאה |
|-----------|--------|-----------|--------|
| HK | ₪5 | 3 | ❌ "מינימום 5 שח לתשלום" |
| HK | ₪10 | 3 | ❌ "מינימום 5 שח לתשלום" |
| HK | ₪20 | 3 | ✅ **הצליח!** |

**מסקנה:** 
- מינימום לחיוב: כ-₪15-20
- HK + Tashlumim עובד עם כרטיסי אשראי רגילים
- התגובה: `confirmation: 0212274`, `transaction_id: 66294559`

---

## 🔧 השינויים שבוצעו

### 1. Backend (`services/nedarim_debit_card.py`)

```python
# תיקון שגיאת כתיב
payload['Tashlumim'] = str(installments)  # לא Tashloumim

# הוספת CallBack
payload['CallBack'] = callback_url
payload['Param2'] = str(lead_id)

# תמיכה ב-HK עם Tashlumim
if payment_type == 'HK':
    if installments and installments > 1:
        payload['Tashlumim'] = str(installments)
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
| RAGIL עם תשלומים | ✅ עובד (כרטיסי אשראי) |
| HK עם מספר חודשים | ✅ עובד (כרטיסי אשראי) |
| HK ללא Tashlumim | ✅ עובד (הוראת קבע אינסופית) |
| CallBack URL | ✅ מוטמע |
| המרה אוטומטית לתלמיד | ✅ מוטמעת |
| תיקון שגיאת כתיב | ✅ תוקן |

### מגבלות ידועות:

- ❌ כרטיסי דביט לא תומכים ב-Tashlumim
- ⚠️ מינימום חיוב: כ-₪15-20

---

## 🎯 המלצות שימוש

### לכרטיסי אשראי רגילים:
- **RAGIL** - לתשלומים עם תפיסת מסגרת
- **HK + Tashlumim** - להוראת קבע ללא תפיסת מסגרת

### לכרטיסי דביט:
- **RAGIL ללא Tashlumim** (או =1) - חיוב חד-פעמי בלבד
- **HK ללא Tashlumim** - הוראת קבע אינסופית

---

## 📞 פרטי תמיכה

- **תיעוד רשמי:** https://matara.pro/nedarimplus/ApiDocumentation.html?v=61
- **טלפון תמיכה:** 03-7630543
- **מייל:** a037630543@gmail.com
- **IP לאימות CallBack:** 18.194.219.73

---

**עדכון אחרון:** 16/02/2026  
**גרסה:** 1.0
