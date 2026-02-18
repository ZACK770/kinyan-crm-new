"""
API endpoint for importing leads from Excel files.
Temporary utility for migrating data from the old system.
"""
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import Optional
import io
from utils.phone import normalize_phone

router = APIRouter()

# מיפוי אנשי מכירות (שם באקסל -> שם במערכת)
SALESPERSON_MAPPING = {
    "שרוליק": "ישראל ברים",
    "שלוימי גרוס": "שלמה גרוס",
    "אהרן מאירוביץ": "אהרן מאירוביץ",
    "משה גרינהויז": "משה גרינהויז",
    "נתנאל גפנר": "נתנאל גפנר",
    "שלמה דנציגר": "שלמה דנציגר",
    "אברימי ברים": "אברימי ברים",
    "דודי וצלר": "דודי וצלר",
    "נפתלי לרנר": "נפתלי לרנר",
    "מוטי העכט": "מוטי העכט",
    "חיים ברים": "חיים ברים",
    "מרדכי ארנפלד": "מרדכי ארנפלד",
    "מוטי דבלינגר": "מוטי דבלינגר",
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
    "חיוג ראשון": "חיוג ראשון",
    "נסלק": "נסלק",
    "תלמיד פעיל": "תלמיד פעיל",
    "לא רלוונטי": "לא רלוונטי",
    # Legacy mappings — old values → new values
    "במעקב": "ליד בתהליך",
    "מתעניין": "ליד בתהליך",
    "ליד סגור - לקוח": "נסלק",
    "ליד סגור - לא רלוונטי": "לא רלוונטי",
    "converted": "נסלק",
}

# מיפוי סטטוס מענה
RESPONSE_MAPPING = {
    "נענה": "מעוניין",
    "ניתוק": "לא זמין",
    "לא נענה (Timeout)": "לא זמין",
    "פניה כללית": None,
}


def _get_cell(row: dict, *keys):
    """מחזיר את הערך הראשון שנמצא מתוך מספר שמות אפשריים לעמודה"""
    for k in keys:
        val = row.get(k)
        if val is not None and str(val).strip():
            return val
    return None


def parse_date(d):
    """המרת תאריך — תומך ב-datetime objects מ-openpyxl וגם בפורמטי טקסט"""
    if not d:
        return None
    # openpyxl מחזיר datetime object ישירות אם התא מפורמט כתאריך
    if isinstance(d, datetime):
        if d.tzinfo is None:
            return d.replace(tzinfo=timezone.utc)
        return d
    # ניסיון פרסור מטקסט
    text = str(d).strip()
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"]:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


@router.post("/import-leads")
async def import_leads_from_excel(
    file: UploadFile = File(...),
    duplicate_mode: str = Query(default="skip", description="skip / merge / overwrite / update_field"),
    update_field_name: Optional[str] = Query(default=None, description="שם השדה לעדכון במצב update_field"),
):
    """
    ייבוא לידים מקובץ אקסל.
    
    duplicate_mode:
    - skip: דילוג על לידים עם טלפון קיים
    - merge: מיזוג - עדכון שדות ריקים בלבד (לא דורס נתונים קיימים)
    - overwrite: דריסה מלאה של הליד הקיים
    - update_field: עדכון שדה ספציפי בלבד (צריך לציין update_field_name)
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

    stats = {"created": 0, "merged": 0, "overwritten": 0, "updated": 0, "skipped_dup": 0, "skipped_no_phone": 0, "skipped_not_found": 0, "errors": 0}
    error_details = []
    
    # במצב update_field - חייב לציין את שם השדה
    if duplicate_mode == "update_field" and not update_field_name:
        return {"message": "שגיאה: במצב update_field חובה לציין את update_field_name", "stats": stats}

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

            phone_raw = row.get("טלפון ראשי")
            phone = normalize_phone(str(phone_raw)) if phone_raw else ""
            if not phone:
                stats["skipped_no_phone"] += 1
                continue

            # חישוב שדות
            try:
                full_name = row.get("שם מלא") or "ליד ללא שם"
                family_name = row.get("משפחה")
                # איש מכירות — תומך בשם עם ובלי רווח בסוף
                sp_n = _get_cell(row, "איש מכירות", "איש מכירות ")
                sp_mapped = SALESPERSON_MAPPING.get(sp_n.strip()) if sp_n else None
                sp_id = sp_ids.get(sp_mapped) if sp_mapped else None
                # מוצר שמתעניין — טקסט חופשי (ממספר עמודות אפשריות)
                requested_course = _get_cell(row, "מוצר שמתעניין", "מוצר", "שם קורס", "קורס")
                if requested_course:
                    requested_course = str(requested_course).strip()
                # קורס — ניסיון מיפוי ל-ID
                c_id = None
                if requested_course:
                    mapped_course = COURSE_MAPPING.get(requested_course)
                    if mapped_course:
                        c_id = c_ids.get(mapped_course)
                # סטטוס מענה
                resp = _get_cell(row, "סטטוס מענה")
                lead_response = RESPONSE_MAPPING.get(resp.strip()) if resp else None
                # סטטוס ליד
                status_raw = _get_cell(row, "סטאטוס ליד") or "ליד חדש"
                status = STATUS_MAPPING.get(str(status_raw).strip(), "ליד חדש")
                # תאריכים
                created_date = parse_date(_get_cell(row, "תאריך יצירה", "תאריך הגעה")) or datetime.now(timezone.utc)
                last_contact = parse_date(_get_cell(row, "תאריך פניה אחרונה"))
                # שדות נוספים
                phone2_raw = row.get("טלפון נוסף")
                phone2 = normalize_phone(str(phone2_raw)) if phone2_raw else None
                id_number = row.get("תעודת זהות")
                if id_number:
                    id_number = str(id_number).strip()
                # הערות — מיזוג משני שדות
                notes_parts = []
                for nk in ["הערות ליד", "הערות על הליד"]:
                    v = row.get(nk)
                    if v and str(v).strip():
                        notes_parts.append(str(v).strip())
                notes = "\n".join(notes_parts) if notes_parts else None

                new_data = dict(
                    full_name=full_name,
                    family_name=family_name,
                    phone=phone,
                    phone2=phone2,
                    email=row.get("מייל לקוח"),
                    city=row.get("עיר מגורים"),
                    address=row.get("כתובת"),
                    id_number=id_number,
                    notes=notes,
                    source_type=_get_cell(row, "מקור הגעה כללי") or "ייבוא ממערכת ישנה",
                    source_message=row.get("הודעה מהליד"),
                    campaign_name=str(_get_cell(row, "שם המפרסם", "שם קמפיין") or "").strip() or None,
                    requested_course=requested_course,
                    arrival_date=created_date,
                    last_contact_date=last_contact,
                    status=status,
                    lead_response=lead_response,
                    salesperson_id=sp_id,
                    course_id=c_id,
                    created_at=created_date,  # תאריך יצירה אמיתי מהאקסל
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
                    # created_at — תמיד מעדכן מהאקסל (תאריך יצירה אמיתי)
                    if new_data.get("created_at"):
                        existing.created_at = new_data["created_at"]
                        existing.arrival_date = new_data["created_at"]
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
                elif duplicate_mode == "update_field":
                    # עדכון שדה ספציפי בלבד
                    if update_field_name in new_data:
                        val = new_data[update_field_name]
                        if val is not None:
                            setattr(existing, update_field_name, val)
                            stats["updated"] += 1
                        else:
                            stats["skipped_dup"] += 1
                    else:
                        stats["errors"] += 1
                        error_details.append({"row": row_idx - 1, "error": f"שדה {update_field_name} לא נמצא בנתונים"})
            else:
                # במצב update_field - אם הליד לא קיים, דלג
                if duplicate_mode == "update_field":
                    stats["skipped_not_found"] += 1
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
