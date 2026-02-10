# תכנית אינטגרציה: נדרים פלוס (Nedarim Plus)
**תאריך**: 8 בדצמבר 2025  
**סטטוס**: לאישור לפני יישום

---

## 📋 תקציר מנהלים

אינטגרציה מלאה עם נדרים פלוס (Payment Gateway) למערכת CRM, כוללת:

1. **יצירת תשלומים** - חיוב כרטיסי אשראי מול נדרים פלוס
2. **ניהול משלמים** - סנכרון נתוני תורמים דו-כיווני
3. **Webhooks** - קבלת עדכונים בזמן אמת על סטטוס תשלומים
4. **תשלומים קבועים** - ניהול הוראות קבע והפקת קבלות אוטומטיות
5. **רקונסיליאציה** - התאמה אוטומטית בין תשלומים למערכת הפיננסית

---

## 🎯 מטרות העסקיות

### בעיות שנפתור
1. ✅ **חיוב אוטומטי** - חיסכון בזמן הזנה ידנית של כרטיסי אשראי
2. ✅ **מעקב תשלומים** - ראיית סטטוס תשלום בזמן אמת (אושר/נדחה)
3. ✅ **הוראות קבע** - ניהול תשלומים חוזרים בקלות
4. ✅ **קבלות אוטומטיות** - שליחת קבלה מס מיידית לאחר תשלום מוצלח
5. ✅ **הפחתת שגיאות** - מניעת טעויות בהקלדת פרטי אשראי

### ROI צפוי
- חיסכון של **~15 דקות** לכל תרומה (הזנה ידנית → אוטומטית)
- שיפור שיעור המרה ב-**~20%** (חוויית משתמש חלקה)
- הפחתת טעויות רישום ב-**~95%**

---

## 🏗️ ארכיטקטורה מוצעת

### רכיבים למימוש

```
app/
└── services/
    └── nedarim/
        ├── __init__.py
        ├── client.py              # HTTP Client + Auth
        ├── payer_service.py       # Payer management
        ├── payment_service.py     # Payment transactions
        └── webhook_handler.py     # Webhook processing

app/modules/finance/
├── router.py                      # הוספת endpoints חדשים
└── service.py                     # שימוש ב-NedarimService

alembic/versions/
└── [new]_add_nedarim_fields.py   # הוספת שדות לטבלאות
```

---

## 📊 שינויים בסכימת Database

### שינויים נדרשים

#### 1. טבלת `people` - הוספת שדות
```sql
ALTER TABLE people ADD COLUMN nedarim_payer_id VARCHAR(100) UNIQUE;
ALTER TABLE people ADD COLUMN nedarim_last_sync TIMESTAMP;
CREATE INDEX idx_people_nedarim ON people(nedarim_payer_id);
```

**כבר קיים**: ✅ השדה `nedarim_payer_id` כבר קיים במודל

#### 2. טבלת `donations` - הוספת שדות
```sql
ALTER TABLE donations ADD COLUMN nedarim_donation_id VARCHAR(100) UNIQUE;
ALTER TABLE donations ADD COLUMN nedarim_transaction_id VARCHAR(100);
ALTER TABLE donations ADD COLUMN nedarim_payment_link VARCHAR(500);
ALTER TABLE donations ADD COLUMN payment_error_code VARCHAR(50);
ALTER TABLE donations ADD COLUMN payment_error_message TEXT;
CREATE INDEX idx_donations_nedarim ON donations(nedarim_donation_id);
```

**כבר קיים**: ✅ השדה `nedarim_donation_id` כבר קיים

**נדרש להוסיף**:
- `nedarim_transaction_id` - מזהה טרנזקציה מנדרים (שונה מ-donation_id)
- `nedarim_payment_link` - קישור לתשלום (לשליחה ללקוח)
- `payment_error_code` - קוד שגיאה במקרה של כישלון
- `payment_error_message` - הסבר מפורט על השגיאה

#### 3. טבלה חדשה: `recurring_donations`
```sql
CREATE TABLE recurring_donations (
    id UUID PRIMARY KEY,
    
    -- Relations
    person_id UUID NOT NULL REFERENCES people(id),
    campaign_id UUID REFERENCES campaigns(id),
    
    -- Recurring Details
    frequency VARCHAR(20) NOT NULL,  -- monthly, quarterly, yearly
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'ILS',
    payment_method VARCHAR(50) NOT NULL,
    
    -- Schedule
    start_date DATE NOT NULL,
    end_date DATE,
    next_charge_date DATE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, paused, cancelled, completed
    successful_charges INTEGER DEFAULT 0,
    failed_charges INTEGER DEFAULT 0,
    total_amount_collected DECIMAL(12,2) DEFAULT 0,
    
    -- Nedarim Integration
    nedarim_subscription_id VARCHAR(100) UNIQUE,
    nedarim_credit_card_token VARCHAR(255),  -- Encrypted token
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (person_id) REFERENCES people(id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

CREATE INDEX idx_recurring_person ON recurring_donations(person_id);
CREATE INDEX idx_recurring_status ON recurring_donations(status);
CREATE INDEX idx_recurring_next_charge ON recurring_donations(next_charge_date);
```

**מטרה**: ניהול הוראות קבע והפקת תשלומים חוזרים אוטומטית

---

## 🔌 API Endpoints של נדרים פלוס

### 1. יצירת משלם (Create Payer)
```http
POST https://api.nedarimplus.co.il/v1/payers
Headers:
  Authorization: Bearer {NEDARIM_API_KEY}
  Content-Type: application/json

Body:
{
  "mosad_id": "{NEDARIM_MOSAD_ID}",
  "payer_name": "יוסי כהן",
  "payer_tz": "123456789",
  "payer_phone": "0501234567",
  "payer_email": "yossi@example.com"
}

Response 201:
{
  "payer_id": "PAY_123456",
  "status": "active"
}
```

### 2. יצירת תרומה/תשלום (Create Donation)
```http
POST https://api.nedarimplus.co.il/v1/donations
Headers:
  Authorization: Bearer {NEDARIM_API_KEY}
  Content-Type: application/json

Body:
{
  "mosad_id": "{NEDARIM_MOSAD_ID}",
  "payer_id": "PAY_123456",
  "amount": 100.00,
  "currency": "ILS",
  "payment_method": "credit_card",
  "installments": 1,
  "redirect_url": "https://yourcrm.org/payment-success",
  "webhook_url": "https://yourcrm.org/api/finance/webhooks/nedarim"
}

Response 201:
{
  "donation_id": "DON_789012",
  "transaction_id": "TRX_345678",
  "payment_link": "https://secure.nedarimplus.co.il/pay/DON_789012",
  "status": "pending"
}
```

### 3. בדיקת סטטוס תשלום (Get Donation Status)
```http
GET https://api.nedarimplus.co.il/v1/donations/{donation_id}
Headers:
  Authorization: Bearer {NEDARIM_API_KEY}

Response 200:
{
  "donation_id": "DON_789012",
  "payer_id": "PAY_123456",
  "amount": 100.00,
  "status": "completed",  // pending, completed, failed, refunded
  "payment_date": "2025-12-08T14:30:00Z",
  "error_code": null,
  "error_message": null
}
```

### 4. יצירת הוראת קבע (Create Recurring)
```http
POST https://api.nedarimplus.co.il/v1/subscriptions
Headers:
  Authorization: Bearer {NEDARIM_API_KEY}
  Content-Type: application/json

Body:
{
  "mosad_id": "{NEDARIM_MOSAD_ID}",
  "payer_id": "PAY_123456",
  "amount": 100.00,
  "frequency": "monthly",  // monthly, quarterly, yearly
  "start_date": "2025-01-01",
  "credit_card_token": "tok_xxxxxxxxxx"
}

Response 201:
{
  "subscription_id": "SUB_456789",
  "status": "active",
  "next_charge_date": "2025-01-01"
}
```

---

## 🎣 Webhooks - קבלת עדכונים מנדרים

### Webhook Endpoint שלנו
```http
POST https://yourcrm.org/api/finance/webhooks/nedarim
Headers:
  X-Nedarim-Signature: {HMAC-SHA256 signature}
  Content-Type: application/json

Body:
{
  "event_type": "donation.completed",  // donation.completed, donation.failed, subscription.charged
  "donation_id": "DON_789012",
  "payer_id": "PAY_123456",
  "amount": 100.00,
  "status": "completed",
  "timestamp": "2025-12-08T14:30:00Z",
  "metadata": {
    "error_code": null,
    "error_message": null
  }
}
```

### סוגי Events
| Event Type | תיאור | פעולה במערכת |
|------------|-------|--------------|
| `donation.completed` | תשלום הושלם בהצלחה | עדכון status → COMPLETED, שליחת קבלה |
| `donation.failed` | תשלום נכשל | עדכון status → FAILED, שמירת error |
| `donation.refunded` | תשלום זוכה | עדכון status → REFUNDED |
| `subscription.charged` | חיוב חודשי הוראת קבע | יצירת Donation חדשה |
| `subscription.failed` | חיוב חודשי נכשל | שליחת התראה למנהל |

---

## 💻 קוד מוצע - Service Layer

### קובץ: `app/services/nedarim/client.py`
```python
"""
Nedarim Plus API Client
HTTP client with authentication and error handling
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
import hmac
import hashlib

class NedarimClient:
    """HTTP Client for Nedarim Plus API"""
    
    def __init__(self):
        self.base_url = settings.NEDARIM_API_URL
        self.api_key = settings.NEDARIM_API_KEY
        self.mosad_id = settings.NEDARIM_MOSAD_ID
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30.0
        )
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with error handling"""
        # Add mosad_id to all requests
        data["mosad_id"] = self.mosad_id
        
        response = await self.client.post(endpoint, json=data)
        
        if response.status_code >= 400:
            error_data = response.json()
            raise NedarimAPIError(
                status_code=response.status_code,
                error_code=error_data.get("error_code"),
                message=error_data.get("message")
            )
        
        return response.json()
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """GET request with error handling"""
        response = await self.client.get(endpoint)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> bool:
        """Verify webhook signature using HMAC-SHA256"""
        expected = hmac.new(
            settings.NEDARIM_WEBHOOK_TOKEN.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)


class NedarimAPIError(Exception):
    """Custom exception for Nedarim API errors"""
    def __init__(self, status_code: int, error_code: str, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(f"Nedarim API Error {error_code}: {message}")
```

---

### קובץ: `app/services/nedarim/payer_service.py`
```python
"""
Nedarim Payer Management
Sync Person ↔ Nedarim Payer
"""
from typing import Optional
from app.services.nedarim.client import NedarimClient
from app.models.people import Person

class PayerService:
    """Service for managing Nedarim payers"""
    
    def __init__(self):
        self.client = NedarimClient()
    
    async def create_or_get_payer(self, person: Person) -> str:
        """
        Create payer in Nedarim or return existing payer_id
        
        Returns:
            str: Nedarim payer_id (e.g., "PAY_123456")
        """
        # If already synced, return existing ID
        if person.nedarim_payer_id:
            return person.nedarim_payer_id
        
        # Create new payer in Nedarim
        payload = {
            "payer_name": person.full_name,
            "payer_tz": person.teudat_zehut,
            "payer_phone": person.phone,
            "payer_email": person.email
        }
        
        response = await self.client.post("/payers", payload)
        payer_id = response["payer_id"]
        
        return payer_id
    
    async def sync_payer_to_nedarim(self, person: Person, db) -> str:
        """Create payer and update Person record"""
        payer_id = await self.create_or_get_payer(person)
        
        # Update Person with Nedarim ID
        person.nedarim_payer_id = payer_id
        person.nedarim_last_sync = datetime.utcnow()
        await db.commit()
        
        return payer_id
```

---

### קובץ: `app/services/nedarim/payment_service.py`
```python
"""
Nedarim Payment Processing
Create donations, handle payment links
"""
from typing import Optional, Dict, Any
from decimal import Decimal
from app.services.nedarim.client import NedarimClient
from app.services.nedarim.payer_service import PayerService
from app.models.finance import Donation, DonationStatus
from app.models.people import Person

class PaymentService:
    """Service for processing payments via Nedarim"""
    
    def __init__(self):
        self.client = NedarimClient()
        self.payer_service = PayerService()
    
    async def create_payment_link(
        self,
        donation: Donation,
        person: Person,
        db,
        redirect_url: str = None
    ) -> str:
        """
        Create payment link in Nedarim
        
        Returns:
            str: Payment link URL for customer
        """
        # Ensure payer exists in Nedarim
        payer_id = await self.payer_service.sync_payer_to_nedarim(person, db)
        
        # Create donation in Nedarim
        payload = {
            "payer_id": payer_id,
            "amount": float(donation.amount),
            "currency": donation.currency,
            "payment_method": "credit_card",
            "installments": 1,
            "redirect_url": redirect_url or f"{settings.APP_URL}/payment-success",
            "webhook_url": f"{settings.APP_URL}/api/finance/webhooks/nedarim"
        }
        
        response = await self.client.post("/donations", payload)
        
        # Update Donation with Nedarim IDs
        donation.nedarim_donation_id = response["donation_id"]
        donation.nedarim_transaction_id = response["transaction_id"]
        donation.nedarim_payment_link = response["payment_link"]
        donation.status = DonationStatus.PENDING
        await db.commit()
        
        return response["payment_link"]
    
    async def check_payment_status(self, donation: Donation, db) -> DonationStatus:
        """
        Check payment status from Nedarim
        
        Returns:
            DonationStatus: Updated status
        """
        if not donation.nedarim_donation_id:
            raise ValueError("No Nedarim donation ID found")
        
        response = await self.client.get(f"/donations/{donation.nedarim_donation_id}")
        
        # Map Nedarim status to our status
        status_map = {
            "pending": DonationStatus.PENDING,
            "completed": DonationStatus.COMPLETED,
            "failed": DonationStatus.FAILED,
            "refunded": DonationStatus.REFUNDED
        }
        
        new_status = status_map.get(response["status"], DonationStatus.PENDING)
        
        # Update donation
        donation.status = new_status
        if response.get("error_code"):
            donation.payment_error_code = response["error_code"]
            donation.payment_error_message = response["error_message"]
        
        await db.commit()
        
        return new_status
```

---

## 🔐 Security Considerations

### 1. API Key Storage
- ✅ מאוחסן ב-`.env` (לא ב-Git)
- ✅ נטען דרך `settings` (Pydantic BaseSettings)
- ⚠️ בפרודקשן: להשתמש ב-AWS Secrets Manager / Azure Key Vault

### 2. Webhook Signature Verification
```python
# In webhook handler
async def verify_nedarim_webhook(request: Request):
    signature = request.headers.get("X-Nedarim-Signature")
    body = await request.body()
    
    if not NedarimClient.verify_webhook_signature(body, signature):
        raise HTTPException(401, "Invalid webhook signature")
```

### 3. Credit Card Token Storage
- ❌ **לעולם לא לשמור** מספר כרטיס אשראי מלא
- ✅ לשמור רק `nedarim_credit_card_token` (טוקן מוצפן מנדרים)
- ✅ Encrypt tokens with Fernet before DB storage

---

## 📋 תכנית יישום (Implementation Plan)

### Phase 1: Infrastructure Setup (1-2 ימים)
- [ ] הוספת משתני סביבה ל-`.env`
- [ ] יצירת `NedarimClient` עם authentication
- [ ] יצירת migration לשדות חדשים בטבלאות
- [ ] בדיקות חיבור ל-API (Sandbox)

### Phase 2: Core Services (2-3 ימים)
- [ ] מימוש `PayerService` - יצירת/סנכרון משלמים
- [ ] מימוש `PaymentService` - יצירת תשלומים ובדיקת סטטוס
- [ ] הוספת endpoints ל-`finance/router.py`:
  - `POST /donations/{id}/create-payment-link`
  - `GET /donations/{id}/payment-status`

### Phase 3: Webhooks (1-2 ימים)
- [ ] מימוש `POST /webhooks/nedarim`
- [ ] אימות חתימת webhook
- [ ] עדכון אוטומטי של סטטוס תשלום
- [ ] שליחת קבלה אוטומטית (אינטגרציה עם Brevo)

### Phase 4: Recurring Donations (2-3 ימים)
- [ ] יצירת טבלת `recurring_donations`
- [ ] מימוש `RecurringService` - ניהול הוראות קבע
- [ ] Background task: חיוב חודשי אוטומטי
- [ ] Endpoints:
  - `POST /recurring-donations`
  - `GET /recurring-donations`
  - `PATCH /recurring-donations/{id}/pause`
  - `DELETE /recurring-donations/{id}/cancel`

### Phase 5: Frontend Integration (2-3 ימים)
- [ ] כפתור "צור קישור תשלום" בעמוד תרומה
- [ ] מסך success page לאחר תשלום מוצלח
- [ ] דף ניהול הוראות קבע
- [ ] Dashboard widget: תשלומים ממתינים

### Phase 6: Testing & Documentation (1-2 ימים)
- [ ] Unit tests לכל Service
- [ ] Integration tests עם Nedarim Sandbox
- [ ] תיעוד API endpoints
- [ ] תיעוד שגיאות נפוצות

---

## 🧪 Test Cases

### 1. Happy Path - תרומה מוצלחת
```
1. יצירת Person חדש
2. יצירת Donation (amount=100, status=PENDING)
3. קריאה ל-create_payment_link()
4. בדיקה: nedarim_payment_link לא ריק
5. סימולציה של Webhook: donation.completed
6. בדיקה: donation.status == COMPLETED
7. בדיקה: קבלה נשלחה למייל
```

### 2. Failed Payment - תשלום נכשל
```
1. יצירת Donation
2. יצירת payment link
3. סימולציה של Webhook: donation.failed
4. בדיקה: donation.status == FAILED
5. בדיקה: payment_error_code מולא
6. בדיקה: התראה נשלחה למנהל
```

### 3. Recurring Donation - הוראת קבע
```
1. יצירת RecurringDonation (monthly, amount=100)
2. Background task רץ בתאריך המתוכנן
3. יצירת Donation חדשה אוטומטית
4. חיוב מול נדרים
5. עדכון next_charge_date ל-חודש הבא
```

---

## 📊 Success Metrics

### KPIs למעקב
- **Conversion Rate**: אחוז תשלומים מוצלחים מתוך כלל הניסיונות
- **Processing Time**: זמן ממוצע מיצירת תרומה לאישור תשלום
- **Failed Payments**: שיעור כישלונות (יעד: < 5%)
- **Recurring Success**: שיעור הצלחת חיובים חודשיים (יעד: > 95%)

### Dashboard Widgets
- "תשלומים ממתינים היום" (count)
- "סה״כ הכנסות חודש זה" (sum)
- "תשלומים שנכשלו השבוע" (count + alert)
- "הוראות קבע פעילות" (count)

---

## 🚨 Error Handling

### שגיאות נפוצות
| Error Code | תיאור | פעולה |
|------------|-------|-------|
| `401_unauthorized` | API Key לא תקין | בדיקת הגדרות `.env` |
| `400_invalid_amount` | סכום שלילי/0 | ולידציה בצד לקוח |
| `404_payer_not_found` | Payer לא קיים בנדרים | יצירת Payer מחדש |
| `402_payment_failed` | כרטיס נדחה | שמירת error_message למשתמש |
| `429_rate_limit` | יותר מדי בקשות | Exponential backoff |

---

## 📚 Documentation Links

- [Nedarim Plus API Docs](https://docs.nedarimplus.co.il) (אם קיים)
- `Integration_Config_Summary.md` - פרטי התחברות
- `SYSTEM_ARCHITECTURE_SCHEMA.md` - מבנה המערכת

---

## ✅ סיכום והחלטות נדרשות

### החלטות לאישור:
1. **שדות חדשים בטבלאות** - האם לאשר?
2. **טבלת recurring_donations** - האם לאשר?
3. **Webhook endpoint** - איזה URL לספק לנדרים?
4. **Background tasks** - APScheduler או Celery?
5. **Sandbox testing** - האם יש גישה ל-Nedarim sandbox?

### שאלות פתוחות:
1. האם יש תבנית קבלה ספציפית שנדרים מצפים לה?
2. מה קורה במקרה של זיכוי (refund)? האם צריך אישור ידני?
3. האם יש מגבלת rate limit ב-API של נדרים?
4. האם צריך לשמור היסטוריה של כל ניסיונות החיוב?

---

**סטטוס**: 🟡 **ממתין לאישור לפני התחלת פיתוח**

**אנא אשר:**
1. ✅ / ❌ שדות נוספים בטבלאות
2. ✅ / ❌ טבלת recurring_donations
3. ✅ / ❌ מבנה Services המוצע
4. ✅ / ❌ Webhook flow
5. ✅ / ❌ תכנית היישום (Phases 1-6)

לאחר קבלת אישור - אתחיל ביישום מיידי! 🚀
