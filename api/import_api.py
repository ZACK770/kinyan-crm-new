"""
API endpoint for importing leads from Excel files.
Temporary utility for migrating data from the old system.
"""
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
import io

router = APIRouter()

# מיפוי אנשי מכירות (שם באקסל -> שם במערכת)
SALESPERSON_MAPPING = {
    "שרוליק": "ישראל ברים",
    "שלוימי גרוס": "שלמה גרוס",
    "אהרן מאירוביץ": "אהרן מאירוביץ",
    "משה גרינהויז": "משה גרינהויז",
    "נתנאל גפנר": "נתנאל גפנר",
    "שלמה דנציגר": "שלמה דנציגר",
    "N/A": None,
}

# מיפוי קורסים (שם באקסל -> שם במערכת)
COURSE_MAPPING = {
    "הלכות שבת": "שבת",
    "ממונות (חושן משפט)": None,
    "הלכות נידה/טהרה": "טהרה",
    "איסור והיתר": "איסור והיתר",
    "מסלול קניין שבת": "שבת",
    "השלים מבחן - טרם בחר הטבה": None,
    "מתעניין במסלול::": None,
}

# מיפוי סטטוסים (אקסל -> מערכת)
STATUS_MAPPING = {
    "ליד חדש": "ליד חדש",
    "ליד בתהליך": "ליד בתהליך",
    "חיוג ראשון": "ליד חדש",
    "לא רלוונטי": "לא רלוונטי",
    "ליד סגור - לקוח": "ליד סגור - לקוח",
}

# מיפוי סטטוס מענה
RESPONSE_MAPPING = {
    "נענה": "מעוניין",
    "ניתוק": "לא זמין",
    "לא נענה (Timeout)": "לא זמין",
    "פניה כללית": None,
}


def parse_date(d):
    """המרת תאריך מפורמט DD/MM/YYYY HH:MM:SS"""
    if not d:
        return None
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"]:
        try:
            return datetime.strptime(str(d), fmt)
        except ValueError:
            pass
    return None


@router.post("/import-leads")
async def import_leads_from_excel(
    file: UploadFile = File(...),
    duplicate_mode: str = Query(default="skip", description="skip / merge / overwrite"),
):
    """
    ייבוא לידים מקובץ אקסל.
    
    duplicate_mode:
    - skip: דילוג על לידים עם טלפון קיים
    - merge: מיזוג - עדכון שדות ריקים בלבד (לא דורס נתונים קיימים)
    - overwrite: דריסה מלאה של הליד הקיים
    """
    import openpyxl
    from db import SessionLocal
    from db.models import Lead, Salesperson, Course
    from sqlalchemy import select

    # קריאת הקובץ
    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    total_rows = ws.max_row - 1

    stats = {"created": 0, "merged": 0, "overwritten": 0, "skipped_dup": 0, "skipped_no_phone": 0, "errors": 0}
    error_details = []

    async with SessionLocal() as session:
        # טעינת מיפויים
        sp_res = await session.execute(select(Salesperson))
        sp_ids = {sp.name: sp.id for sp in sp_res.scalars()}
        c_res = await session.execute(select(Course))
        c_ids = {c.name: c.id for c in c_res.scalars()}

        for row_idx in range(2, ws.max_row + 1):
            row = {}
            for i in range(len(headers)):
                if headers[i]:
                    row[headers[i]] = ws.cell(row_idx, i + 1).value

            phone = row.get("טלפון ראשי")
            if not phone:
                stats["skipped_no_phone"] += 1
                continue
            phone = str(phone).strip()

            # חישוב שדות
            try:
                full_name = row.get("שם מלא") or "ליד ללא שם"
                sp_n = row.get("איש מכירות ")
                sp_id = sp_ids.get(SALESPERSON_MAPPING.get(sp_n.strip())) if sp_n else None
                c_n = row.get("מוצר שמתעניין")
                c_id = c_ids.get(COURSE_MAPPING.get(c_n.strip())) if c_n else None
                resp = row.get("סטטוס מענה")
                lead_response = RESPONSE_MAPPING.get(resp.strip()) if resp else None
                status = STATUS_MAPPING.get(row.get("סטאטוס ליד", "ליד חדש"), "ליד חדש")
                arrival = parse_date(row.get("תאריך יצירה")) or datetime.now()
                last_contact = parse_date(row.get("תאריך פניה אחרונה"))

                new_data = dict(
                    full_name=full_name,
                    phone=phone,
                    email=row.get("מייל לקוח"),
                    city=row.get("עיר מגורים"),
                    address=row.get("כתובת"),
                    notes=row.get("הערות ליד"),
                    source_type="ייבוא ממערכת ישנה",
                    source_message=row.get("הודעה מהליד"),
                    source_name=row.get("שלוחת מוצר"),
                    campaign_name=row.get("שם המפרסם"),
                    arrival_date=arrival,
                    last_contact_date=last_contact,
                    status=status,
                    lead_response=lead_response,
                    salesperson_id=sp_id,
                    course_id=c_id,
                    created_by="import_script",
                )
            except Exception as e:
                stats["errors"] += 1
                error_details.append({"row": row_idx - 1, "error": str(e)})
                continue

            # בדיקת כפילות
            ex_result = await session.execute(select(Lead).where(Lead.phone == phone))
            existing = ex_result.scalar_one_or_none()

            if existing:
                if duplicate_mode == "skip":
                    stats["skipped_dup"] += 1
                    continue
                elif duplicate_mode == "merge":
                    # מיזוג - עדכון שדות ריקים בלבד
                    for key, val in new_data.items():
                        if val is not None and key != "phone":
                            current = getattr(existing, key, None)
                            if current is None or current == "" or current == "ליד ללא שם":
                                setattr(existing, key, val)
                    # הערות - צירוף
                    if new_data.get("notes") and existing.notes:
                        if new_data["notes"] not in existing.notes:
                            existing.notes = existing.notes + "\n---\n" + new_data["notes"]
                    stats["merged"] += 1
                elif duplicate_mode == "overwrite":
                    # דריסה מלאה
                    for key, val in new_data.items():
                        if key != "phone":
                            setattr(existing, key, val)
                    stats["overwritten"] += 1
            else:
                # ליד חדש
                session.add(Lead(**new_data))
                stats["created"] += 1

        await session.commit()

    return {
        "message": "ייבוא הושלם!",
        "total_rows": total_rows,
        "stats": stats,
        "errors": error_details[:20],  # מקסימום 20 שגיאות
    }


@router.get("/import-leads/preview")
async def preview_excel_columns():
    """מחזיר את רשימת העמודות הנתמכות לייבוא"""
    return {
        "supported_columns": [
            {"excel": "שם מלא", "field": "full_name", "required": True},
            {"excel": "טלפון ראשי", "field": "phone", "required": True},
            {"excel": "מייל לקוח", "field": "email", "required": False},
            {"excel": "עיר מגורים", "field": "city", "required": False},
            {"excel": "כתובת", "field": "address", "required": False},
            {"excel": "הערות ליד", "field": "notes", "required": False},
            {"excel": "איש מכירות ", "field": "salesperson_id", "required": False},
            {"excel": "מוצר שמתעניין", "field": "course_id", "required": False},
            {"excel": "סטאטוס ליד", "field": "status", "required": False},
            {"excel": "סטטוס מענה", "field": "lead_response", "required": False},
            {"excel": "הודעה מהליד", "field": "source_message", "required": False},
            {"excel": "שם המפרסם", "field": "campaign_name", "required": False},
            {"excel": "תאריך יצירה", "field": "arrival_date", "required": False},
            {"excel": "תאריך פניה אחרונה", "field": "last_contact_date", "required": False},
        ],
        "duplicate_modes": [
            {"value": "skip", "label": "דילוג", "description": "דילוג על לידים עם טלפון קיים"},
            {"value": "merge", "label": "מיזוג", "description": "עדכון שדות ריקים בלבד (לא דורס נתונים קיימים)"},
            {"value": "overwrite", "label": "דריסה", "description": "דריסה מלאה של הליד הקיים"},
        ],
        "status_mapping": STATUS_MAPPING,
        "salesperson_mapping": SALESPERSON_MAPPING,
        "course_mapping": COURSE_MAPPING,
    }
