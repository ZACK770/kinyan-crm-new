# Webhooks Integration Guide

## Overview

The CRM receives leads and call data from two main sources:
1. **Elementor** - Website form submissions
2. **Yemot HaMashiach** - IVR phone system calls

Both webhooks share the same logic:
- Search for existing lead by phone number
- If found → Add a new interaction (פניה חוזרת)
- If not found → Create new lead + assign salesperson + create interaction

## Endpoints

| Source | URL | Method |
|--------|-----|--------|
| Website Forms | `POST /webhooks/elementor` | JSON |
| IVR Calls | `POST /webhooks/yemot` | JSON or form-data |
| Unified Lead Ingestion | `GET/POST /webhooks/lead` | GET for diagnostics, POST for payloads |
| Nedarim DebitCard | `POST /webhooks/nedarim-debitcard` | JSON or form-data |
| Nedarim Keva (הוראת קבע) | `POST /webhooks/nedarim-keva` | JSON or form-data |

## Unified Lead Webhook

Single endpoint for all lead sources:
- `POST /webhooks/lead` processes Elementor, Yemot, or generic lead payloads
- `GET /webhooks/lead` confirms the route is deployed and registered

### Diagnostic Response
```json
{
    "success": true,
    "endpoint": "/webhooks/lead",
    "methods": ["GET", "POST"],
    "status": "registered",
    "supports": ["elementor", "yemot", "generic"],
    "message": "Unified lead webhook is deployed. Use POST to submit lead payloads."
}
```

### Source Detection
- `fields` + `form` or `meta` -> Elementor
- `Phone` / `Folder` / `QueueStatus` -> Yemot
- Anything else -> Generic lead parser

## Elementor (Website) Webhook

### Example Payload
```json
{
    "form": {
        "id": "b61ca57",
        "name": "טופס הרשמה"
    },
    "fields": {
        "name": {
            "id": "name",
            "type": "text",
            "title": "Name",
            "value": "גולדשמידט"
        },
        "field_6f8642e": {
            "id": "field_6f8642e",
            "type": "tel",
            "title": "טלפון",
            "value": "0548492322"
        },
        "field_fb4ae08": {
            "id": "field_fb4ae08",
            "type": "select",
            "title": "בחר מסלול",
            "value": "הלכות שבת"
        },
        "field_b1e584d": {
            "id": "field_b1e584d",
            "type": "textarea",
            "title": "תוכן ההודעה",
            "value": "מה מחיר מסלול?"
        }
    },
    "meta": {
        "date": {"title": "תאריך", "value": "פברואר 10, 2026"},
        "time": {"title": "זמן", "value": "2:45 am"},
        "page_url": {"title": "קישור", "value": "https://www.kinyanhoraah.co.il/thank/"}
    }
}
```

### Field Mapping
| Elementor Title | CRM Field |
|-----------------|-----------|
| `שם מלא` / `Name` / `שם` | `full_name` |
| `טלפון` / `phone` / `נייד` | `phone` |
| `אימייל` / `email` | `email` |
| `עיר` / `city` | `city` |
| `בחר מסלול` / `מוצר` / `קורס` | `form_product` |
| `תוכן ההודעה` / `הודעה` | `source_message` |
| `מקור` / `utm_source` | `campaign_name` |

### Stored Data
- **LeadInteraction.interaction_type**: `website_form`
- **LeadInteraction.form_product**: The selected course/product
- **LeadInteraction.form_content**: Date and time of submission
- **Lead.source_type**: `elementor`
- **Lead.source_name**: Form name
- **Lead.source_details**: Page URL

---

## Yemot HaMashiach (IVR) Webhook

### Example Payload
```json
{
    "CustomerDID": "0795792345",
    "RealDID": "023135176",
    "Folder": "99999/2",
    "Phone": "0527109371",
    "Date": "10/02/2026",
    "Time": "14:29:44",
    "HebrewDate": "כ״ג שבט תשפ״ו",
    "Module": "queue",
    "QueueStatus": "CONTINUE",
    "QueueTotalSeconds": "1317",
    "QueueTotalTime": "0:21:57",
    "QueueWaitingSeconds": "17",
    "QueueWaitingTime": "0:0:17",
    "AnswerSeconds": "1300",
    "AnswerTime": "0:21:40",
    "AnswerNumber": "0527635459",
    "YemotCallID": "d6f86f37-5729-4323-ab83-91bfed3d4edc"
}
```

### Key Fields
| Yemot Field | Description | CRM Field |
|-------------|-------------|-----------|
| `Phone` | Caller's phone number | `phone` |
| `Folder` | Extension path (e.g., `99999/2`) | Used to determine `ivr_product` |
| `Date`, `Time` | Call timestamp | Stored in `source_details` |
| `QueueStatus` | Call status (CONTINUE=answered) | `call_status` |
| `AnswerSeconds` / `AnswerTime` | Total call duration | `call_duration` |
| `QueueWaitingTime` | Wait time before answer | `wait_time` |
| `AnswerNumber` | Extension that answered | Stored in `source_details` |

### Extension → Product Mapping
The extension number (after `/` in Folder) maps to courses:

| Extension | Product |
|-----------|---------|
| 1 | שבת |
| 2 | איסור והיתר |
| 3 | טהרה |
| 4 | ממונות |
| 5 | נזיקין |
| 6 | סמיכה |

### Stored Data
- **LeadInteraction.interaction_type**: `ivr_call`
- **LeadInteraction.call_status**: `נענה` / `לא ענה` / etc.
- **LeadInteraction.call_duration**: Total call time
- **LeadInteraction.wait_time**: Wait time before answer
- **LeadInteraction.ivr_product**: Course based on extension
- **Lead.source_type**: `yemot`
- **Lead.source_details**: Full call info (date, time, answered by, extension)

---

## Response Format

### Success - New Lead
```json
{
    "success": true,
    "action": "created",
    "lead_id": 123,
    "salesperson": "שם איש המכירות"
}
```

### Success - Existing Lead (פניה חוזרת)
```json
{
    "success": true,
    "action": "updated",
    "lead_id": 123
}
```

### Error
```json
{
    "success": false,
    "error": "Invalid phone number"
}
```

---

## Database Tables

### Lead (לידים)
Main lead record with contact info and source tracking.

### LeadInteraction (פניות חוזרות)
Each call or form submission creates a new interaction record:
- Tracks all touchpoints with the lead
- Stores IVR-specific data (call duration, status)
- Stores web form data (selected course, message)

---

## Testing

### Test Elementor Webhook
```powershell
$body = '{"form": {"id": "test"}, "fields": {"name": {"title": "Name", "value": "Test"}, "field_phone": {"title": "טלפון", "value": "0501234567"}}}'
Invoke-RestMethod -Uri "http://localhost:8000/webhooks/elementor" -Method Post -Body $body -ContentType "application/json"
```

### Test Unified Lead Webhook Deployment
```powershell
Invoke-RestMethod -Uri "https://kinyan-crm-new-1.onrender.com/webhooks/lead" -Method Get
```

### Test Unified Lead Webhook With Payload
```powershell
$body = '{"phone": "0501234567", "name": "Test Lead", "source_type": "manual-test"}'
Invoke-RestMethod -Uri "https://kinyan-crm-new-1.onrender.com/webhooks/lead" -Method Post -Body $body -ContentType "application/json"
```

### Test Yemot Webhook
```powershell
$body = '{"Phone": "0527109371", "Folder": "99999/2", "QueueStatus": "CONTINUE", "AnswerSeconds": "600"}'
Invoke-RestMethod -Uri "http://localhost:8000/webhooks/yemot" -Method Post -Body $body -ContentType "application/json"
```

---

## Nedarim Plus Webhooks

### Nedarim DebitCard Webhook

Handles direct credit card charges (RAGIL payments) from the DebitCard.aspx API.

**Endpoint:** `POST /webhooks/nedarim-debitcard`

**Key Fields:**
- `Confirmation`: Payment confirmation number
- `Amount`: Charged amount
- `Tashloumim`: Number of installments (spelled with 'ou', not 'um'!)
- `LastNum`: Last 4 digits of card
- `TransactionId`: Nedarim transaction ID
- `ClientName`: Payer name
- `Comments`: Format "קורס: X | תלמיד: Y"
- `KevaId`: Present if charge is from a standing order

**Important Notes:**
- Does NOT require signature verification
- Nedarim silently ignores `Tashlumim` - must use `Tashloumim` (with 'ou')
- Minimum per installment: 5 ILS

### Nedarim Keva (הוראת קבע) Webhook

Handles recurring charge callbacks from Nedarim's standing order system.

**Endpoint:** `POST /webhooks/nedarim-keva`

**Key Fields:**
- `KevaId`: Unique standing order ID (stored in `Commitment.nedarim_subscription_id`)
- `ClientName`: Payer name
- `Amount`: Monthly charge amount
- `Confirmation`: Payment confirmation
- `TransactionId`: Nedarim transaction ID
- `Comments`: Format "קורס: X | תלמיד: Y"
- `TransactionType`: "הו\"ק"
- `Makor`: "נדרים - הוראת קבע"
- `CreditTerms`: Number of monthly charges

**Matching Logic:**
1. Try to find `Commitment` by `KevaId`
2. Try to find `Student` by name (from Comments or ClientName)
3. Try to find `Lead` by name
4. Try to find `Course` from Comments

**Important Notes:**
- Does NOT require signature verification
- Has NO `Param2` (unlike DebitCard callbacks)
- Creates/updates `Commitment` records
- Creates `Collection` records with installment tracking



---

## Configuration

### Adding New Products/Extensions
Edit `webhooks/yemot.py`:
```python
FOLDER_TO_PRODUCT = {
    "1": "שבת",
    "2": "איסור והיתר",
    # Add more mappings here
}
```

### Adding New Form Fields
Edit `webhooks/elementor.py`:
```python
FIELD_MAP = {
    "שדה חדש": "crm_field_name",
    # Add more mappings here
}
```
