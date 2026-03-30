---
description: Public Exam Registration API (Kinyan CRM)
---

# Public Exam Registration API — Documentation

**Base URL (Production / Render):**
- `https://kinyan-crm-new-1.onrender.com`

**API Prefix:**
- `/public/exam-registration`

This API is intended for **public, external integrations** (e.g. Nedarim Plus) to:
- List upcoming active exam dates and the exams available for registration.
- Register an examinee to a specific exam on a specific exam date.
- Retrieve existing registrations by phone.

## Authentication

Currently these endpoints are **public** (no CRM auth cookies required).

## Common Conventions

- **Content-Type:** `application/json`
- **Dates:** returned as ISO date strings (e.g. `"2026-04-06"`).
- **Timestamps:** returned as ISO datetime strings.
- **Errors:** returned as JSON with `detail`.

Example error:
```json
{ "detail": "Exam date not found" }
```

---

# 1) List upcoming exam dates

## GET `/public/exam-registration/exam-dates/upcoming`

Returns upcoming **active** exam dates and their associated exams available for registration.

### Query params
None.

### Response 200 (JSON array)
```json
[
  {
    "exam_date_id": 1,
    "date": "2026-04-06",
    "description": "מועד א",
    "max_registrations": 30,
    "is_active": true,
    "exams": [
      {
        "exam_id": 10,
        "exam_name": "מבחן דמו 1",
        "exam_type": "בכתב",
        "course_id": 3,
        "course_name": "קורס לדוגמה"
      }
    ]
  }
]
```

### Notes
- Only exam dates marked `is_active = true` are returned.
- Only future dates are returned (upcoming).

---

# 2) Create a new exam registration

## POST `/public/exam-registration/register`

Creates a registration for an examinee to a specific exam on a specific exam date.

### Request body
```json
{
  "exam_date_id": 1,
  "exam_id": 10,
  "phone": "0501234567",
  "name": "ישראל ישראלי"
}
```

### Field validation
- `exam_date_id` (number) — required
- `exam_id` (number) — required
- `phone` (string) — required
- `name` (string) — optional (currently stored only if the Examinee schema supports it; the registration will still succeed without it)

### Response 200
```json
{
  "registration_id": 123,
  "registration_code": "4Y143LHB",
  "status": "registered",
  "exam_date": "2026-04-06",
  "exam_id": 10,
  "exam_name": "מבחן דמו 1",
  "exam_type": "בכתב",
  "course_id": 3,
  "course_name": "קורס לדוגמה",
  "examinee_phone": "0501234567",
  "created_at": "2026-03-30T14:21:52.870798+03:00"
}
```

### Errors
- `404` — if exam date or exam not found / not active
- `409` — if already registered for the same (exam_date_id + exam_id + phone)
- `400` — validation errors

---

# 3) List registrations by phone

## GET `/public/exam-registration/registrations/{phone}`

Returns all registrations for a specific phone number.

### Path params
- `phone` — examinee phone number (string)

### Response 200 (JSON array)
```json
[
  {
    "registration_id": 123,
    "registration_code": "4Y143LHB",
    "exam_date": "2026-04-06",
    "exam_id": 10,
    "exam_name": "מבחן דמו 1",
    "exam_type": "בכתב",
    "course_id": 3,
    "course_name": "קורס לדוגמה",
    "status": "registered",
    "notes": null,
    "created_at": "2026-03-30T14:21:52.870798+03:00"
  }
]
```

---

# Integration Flow (Recommended)

## A) Load dropdown options (Exam Dates + Exams)
1. Call `GET /public/exam-registration/exam-dates/upcoming`
2. Build a dropdown grouped by `date`/`description`.
3. Each selectable item should include `{ exam_date_id, exam_id }`.

## B) Register examinee
1. Collect phone (and optionally name)
2. POST to `/public/exam-registration/register`
3. Save/display `registration_code` to the user

## C) Show history
1. Call `GET /public/exam-registration/registrations/{phone}`
2. Display existing registrations.

---

# Sandbox / Demo

A demo UX page exists (for manual testing):
- `GET /public/demo/exams-ux`

---

# Support

If you need additional endpoints (cancel registration, capacity enforcement, registration status changes), they can be added on request.
