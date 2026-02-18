"""
Import Nedarim Plus CSV exports into CRM database.

Two CSV files:
1. ExportHistory — all transactions (both RAGIL and HK charges)
2. ExportKeva — standing orders (הוראות קבע) with their status

Logic:
- Step 1: Import Keva CSV → create/update Commitment records per KevaId
- Step 2: Import History CSV → create Payment + Collection records
  - HK rows (מספר הו"ק present) → link to Commitment, create Collection
  - RAGIL rows (no מספר הו"ק) → create Payment + Collection (standalone)
- Matching: student name from comments ("תלמיד: X") or from שם field
  → match to Student.full_name or Lead.full_name in DB
- Course matching: from comments ("קורס: X") or קטגוריה field
  → match to Course.name in DB

Usage:
  python scripts/import_nedarim_csv.py --history "path/to/history.csv" --keva "path/to/keva.csv" [--dry-run]
"""
import asyncio
import argparse
import csv
import re
import sys
import os
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Tuple
from collections import defaultdict

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set DB URL if not set
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from db import SessionLocal
from db.models import Student, Lead, Course, Payment, Commitment, Collection, HistoryEntry

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ─── CSV Parsing Helpers ───────────────────────────────────────────

def read_csv(path: str):
    """Read Nedarim CSV (UTF-16, tab-delimited)"""
    with open(path, 'r', encoding='utf-16') as f:
        reader = csv.reader(f, delimiter='\t')
        rows = list(reader)
    header = rows[0]
    data = rows[1:]
    logger.info(f"Read {len(data)} rows from {os.path.basename(path)}")
    return header, data


def clean_confirmation(val: str) -> str:
    """Remove =\"...\" wrapping from confirmation numbers"""
    val = val.strip()
    if val.startswith('="') and val.endswith('"'):
        val = val[2:-1]
    return val


def parse_amount(val: str) -> float:
    """Parse amount string to float"""
    try:
        return float(val.replace('₪', '').replace(',', '').strip())
    except (ValueError, AttributeError):
        return 0.0


def parse_date(val: str) -> Optional[date]:
    """Parse date from various Nedarim formats"""
    val = val.strip()
    if not val:
        return None
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(val: str) -> Optional[datetime]:
    """Parse datetime from various Nedarim formats"""
    val = val.strip()
    if not val:
        return None
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


def extract_student_name(comments: str, name_field: str = "") -> Optional[str]:
    """Extract student name from comments field or name field"""
    # Try "תלמיד: X" pattern in comments
    if comments:
        m = re.search(r'תלמיד:\s*(.+?)(?:\s*\||$)', comments)
        if m:
            return m.group(1).strip()
    # Fall back to name field
    if name_field and name_field.strip():
        return name_field.strip()
    return None


def extract_course_name(comments: str, category: str = "") -> Optional[str]:
    """Extract course name from comments or category"""
    if comments:
        m = re.search(r'קורס:\s*(.+?)(?:\s*\||$)', comments)
        if m:
            return m.group(1).strip()
    if category and category.strip():
        return category.strip()
    return None


# ─── DB Matching Helpers ───────────────────────────────────────────

def normalize_phone(phone: str) -> str:
    """Normalize phone number: remove dashes, spaces, leading 0/+972"""
    if not phone:
        return ""
    p = re.sub(r'[\s\-\(\)\.]', '', phone.strip())
    if p.startswith('+972'):
        p = '0' + p[4:]
    if p.startswith('972') and len(p) > 9:
        p = '0' + p[3:]
    return p


def name_words(name: str) -> set:
    """Get set of meaningful words from a name (ignore short words)"""
    if not name:
        return set()
    return {w.strip() for w in name.strip().split() if len(w.strip()) >= 2}


class EntityCache:
    """Cache for DB lookups with multi-parameter matching"""
    def __init__(self):
        # Primary indexes
        self.students: list = []  # all Student objects
        self.leads: list = []     # all Lead objects
        self.students_by_name: Dict[str, Student] = {}
        self.leads_by_name: Dict[str, Lead] = {}
        # Phone indexes
        self.students_by_phone: Dict[str, Student] = {}
        self.leads_by_phone: Dict[str, Lead] = {}
        # Email indexes
        self.students_by_email: Dict[str, Student] = {}
        self.leads_by_email: Dict[str, Lead] = {}
        # ID number index
        self.students_by_id_number: Dict[str, Student] = {}
        self.leads_by_id_number: Dict[str, Lead] = {}
        # Courses & commitments
        self.courses_by_name: Dict[str, Course] = {}
        self.commitments_by_keva: Dict[str, Commitment] = {}
        self.existing_tx_ids: set = set()
        # Match cache (avoid re-matching same name)
        self._match_cache: Dict[str, Optional[Tuple]] = {}
        self.loaded = False

    async def load(self, db: AsyncSession):
        """Pre-load all entities for fast matching"""
        logger.info("Loading entities from DB...")

        # Students
        result = await db.execute(select(Student))
        for s in result.scalars().all():
            self.students.append(s)
            if s.full_name:
                self.students_by_name[s.full_name.strip()] = s
            if s.phone:
                self.students_by_phone[normalize_phone(s.phone)] = s
            if getattr(s, 'phone2', None):
                self.students_by_phone[normalize_phone(s.phone2)] = s
            if s.email:
                self.students_by_email[s.email.strip().lower()] = s
            if s.id_number:
                self.students_by_id_number[s.id_number.strip()] = s

        # Leads
        result = await db.execute(select(Lead))
        for l in result.scalars().all():
            self.leads.append(l)
            if l.full_name:
                self.leads_by_name[l.full_name.strip()] = l
            if l.phone:
                self.leads_by_phone[normalize_phone(l.phone)] = l
            if getattr(l, 'phone2', None):
                self.leads_by_phone[normalize_phone(l.phone2)] = l
            if l.email:
                self.leads_by_email[l.email.strip().lower()] = l
            if getattr(l, 'id_number', None):
                self.leads_by_id_number[l.id_number.strip()] = l

        # Courses
        result = await db.execute(select(Course).where(Course.is_active == True))
        for c in result.scalars().all():
            if c.name:
                self.courses_by_name[c.name.strip()] = c

        # Existing commitments by keva ID
        result = await db.execute(select(Commitment).where(Commitment.nedarim_subscription_id.isnot(None)))
        for c in result.scalars().all():
            self.commitments_by_keva[c.nedarim_subscription_id] = c

        # Existing transaction IDs (to detect duplicates)
        result = await db.execute(select(Payment.nedarim_donation_id).where(Payment.nedarim_donation_id.isnot(None)))
        self.existing_tx_ids = {r[0] for r in result.all()}

        logger.info(f"  Students: {len(self.students)} (phones: {len(self.students_by_phone)}, emails: {len(self.students_by_email)})")
        logger.info(f"  Leads: {len(self.leads)} (phones: {len(self.leads_by_phone)}, emails: {len(self.leads_by_email)})")
        logger.info(f"  Courses: {len(self.courses_by_name)}")
        logger.info(f"  Existing commitments: {len(self.commitments_by_keva)}")
        logger.info(f"  Existing transaction IDs: {len(self.existing_tx_ids)}")
        self.loaded = True

    def find_student(self, name: Optional[str] = None, phone: Optional[str] = None,
                     email: Optional[str] = None, id_number: Optional[str] = None) -> Optional[Student]:
        """
        Find student using multiple parameters (priority order):
        1. ID number (ת.ז)
        2. Phone (exact normalized)
        3. Email (exact lowercase)
        4. Name — exact match
        5. Name — reversed word order
        6. Name — word-set overlap (≥2 shared words)
        7. Name — substring containment
        """
        # 1. ID number
        if id_number and id_number.strip():
            s = self.students_by_id_number.get(id_number.strip())
            if s:
                return s

        # 2. Phone
        if phone:
            p = normalize_phone(phone)
            if p and p in self.students_by_phone:
                return self.students_by_phone[p]

        # 3. Email
        if email and email.strip():
            s = self.students_by_email.get(email.strip().lower())
            if s:
                return s

        if not name:
            return None
        name = name.strip()
        if not name:
            return None

        # 4. Exact name match
        if name in self.students_by_name:
            return self.students_by_name[name]

        # 5. Reversed name
        parts = name.split()
        if len(parts) >= 2:
            # Try all rotation permutations for multi-word names
            for i in range(1, len(parts)):
                rotated = " ".join(parts[i:] + parts[:i])
                if rotated in self.students_by_name:
                    return self.students_by_name[rotated]

        # 6. Word-set overlap (at least 2 shared words for names with 2+ words)
        search_words = name_words(name)
        if len(search_words) >= 2:
            best_match = None
            best_overlap = 0
            for sname, student in self.students_by_name.items():
                s_words = name_words(sname)
                overlap = len(search_words & s_words)
                if overlap >= 2 and overlap > best_overlap:
                    best_overlap = overlap
                    best_match = student
            if best_match:
                return best_match

        # 7. Substring containment (only if name is long enough)
        if len(name) >= 4:
            for sname, student in self.students_by_name.items():
                if name in sname or sname in name:
                    return student

        return None

    def find_lead(self, name: Optional[str] = None, phone: Optional[str] = None,
                  email: Optional[str] = None, id_number: Optional[str] = None) -> Optional[Lead]:
        """Find lead using multiple parameters (same logic as find_student)"""
        if id_number and id_number.strip():
            l = self.leads_by_id_number.get(id_number.strip())
            if l:
                return l

        if phone:
            p = normalize_phone(phone)
            if p and p in self.leads_by_phone:
                return self.leads_by_phone[p]

        if email and email.strip():
            l = self.leads_by_email.get(email.strip().lower())
            if l:
                return l

        if not name:
            return None
        name = name.strip()
        if not name:
            return None

        if name in self.leads_by_name:
            return self.leads_by_name[name]

        parts = name.split()
        if len(parts) >= 2:
            for i in range(1, len(parts)):
                rotated = " ".join(parts[i:] + parts[:i])
                if rotated in self.leads_by_name:
                    return self.leads_by_name[rotated]

        search_words = name_words(name)
        if len(search_words) >= 2:
            best_match = None
            best_overlap = 0
            for lname, lead in self.leads_by_name.items():
                l_words = name_words(lname)
                overlap = len(search_words & l_words)
                if overlap >= 2 and overlap > best_overlap:
                    best_overlap = overlap
                    best_match = lead
            if best_match:
                return best_match

        if len(name) >= 4:
            for lname, lead in self.leads_by_name.items():
                if name in lname or lname in name:
                    return lead

        return None

    def find_person(self, name: Optional[str] = None, phone: Optional[str] = None,
                    email: Optional[str] = None, id_number: Optional[str] = None) -> Tuple[Optional[Student], Optional[Lead]]:
        """
        Find student or lead using all available parameters.
        Returns (student, lead) — student takes priority.
        If lead has a linked student, returns that student.
        """
        # Build cache key
        cache_key = f"{name}|{phone}|{email}|{id_number}"
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]

        student = self.find_student(name=name, phone=phone, email=email, id_number=id_number)
        if student:
            self._match_cache[cache_key] = (student, None)
            return (student, None)

        lead = self.find_lead(name=name, phone=phone, email=email, id_number=id_number)
        if lead:
            # Check if lead has a linked student
            if lead.student_id:
                for s in self.students:
                    if s.id == lead.student_id:
                        self._match_cache[cache_key] = (s, lead)
                        return (s, lead)
            self._match_cache[cache_key] = (None, lead)
            return (None, lead)

        self._match_cache[cache_key] = (None, None)
        return (None, None)

    def find_course(self, name: Optional[str]) -> Optional[Course]:
        """Find course by name (fuzzy)"""
        if not name:
            return None
        name = name.strip()
        if name in self.courses_by_name:
            return self.courses_by_name[name]
        # Fuzzy — substring
        for cname, course in self.courses_by_name.items():
            if name in cname or cname in name:
                return course
        # Word overlap
        search_words = name_words(name)
        if len(search_words) >= 1:
            best_match = None
            best_overlap = 0
            for cname, course in self.courses_by_name.items():
                c_words = name_words(cname)
                overlap = len(search_words & c_words)
                if overlap >= 1 and overlap > best_overlap:
                    best_overlap = overlap
                    best_match = course
            if best_match:
                return best_match
        return None


# ─── Import Logic ──────────────────────────────────────────────────

class ImportStats:
    def __init__(self):
        self.commitments_created = 0
        self.commitments_updated = 0
        self.commitments_skipped = 0
        self.payments_created = 0
        self.payments_skipped_dup = 0
        self.collections_created = 0
        self.history_entries_created = 0
        self.unmatched_students = []
        self.errors = []

    def summary(self):
        print("\n" + "=" * 70)
        print("  IMPORT SUMMARY")
        print("=" * 70)
        print(f"  Students created:       {getattr(self, 'students_created', 0)}")
        print(f"  Commitments created:    {self.commitments_created}")
        print(f"  Commitments updated:    {self.commitments_updated}")
        print(f"  Commitments skipped:    {self.commitments_skipped}")
        print(f"  Payments created:       {self.payments_created}")
        print(f"  Payments skipped (dup): {self.payments_skipped_dup}")
        print(f"  Collections created:    {self.collections_created}")
        print(f"  History entries:        {self.history_entries_created}")
        print(f"  Unmatched students:     {len(self.unmatched_students)}")
        print(f"  Errors:                 {len(self.errors)}")
        if self.unmatched_students:
            print("\n  ── Unmatched Students ──")
            seen = set()
            for name, source in self.unmatched_students:
                key = name or "?"
                if key not in seen:
                    seen.add(key)
                    print(f"    • {key} ({source})")
        if self.errors:
            print("\n  ── Errors ──")
            for e in self.errors[:20]:
                print(f"    • {e}")
        print("=" * 70)


async def import_keva_csv(db: AsyncSession, keva_path: str, cache: EntityCache, stats: ImportStats, dry_run: bool, create_missing: bool = False):
    """
    Step 1: Import Keva CSV → Commitment records.
    Each row = one standing order (הוראת קבע).
    If create_missing=True, creates Student records for unmatched entries.
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"STEP 1: Importing Keva (Standing Orders) from {os.path.basename(keva_path)}")
    logger.info(f"{'='*70}")

    header, rows = read_csv(keva_path)
    BATCH_SIZE = 50
    pending = 0

    for idx, row in enumerate(rows):
        keva_id = row[0].strip()
        status_raw = row[1].strip()
        name_field = row[2].strip()
        id_number = row[3].strip()
        phone = row[6].strip()
        monthly_amount = parse_amount(row[8])
        category = row[9].strip()
        comments = row[10].strip()
        remaining = int(row[11]) if row[11].strip().isdigit() else 0
        done = int(row[12]) if row[12].strip().isdigit() else 0

        if not keva_id:
            continue

        status_map = {"פעיל": "פעיל", "לא פעיל": "בוטל"}
        status = status_map.get(status_raw, status_raw)

        total_installments = done + remaining
        total_amount = monthly_amount * total_installments if total_installments > 0 else 0

        student_name = extract_student_name(comments, name_field)
        course_name = extract_course_name(comments, category)

        student, lead = cache.find_person(
            name=student_name,
            phone=phone,
            email=row[7].strip() if row[7].strip() else None,
            id_number=id_number if id_number else None,
        )
        course = cache.find_course(course_name)

        if not student:
            if create_missing and (student_name or name_field):
                new_name = student_name or name_field
                new_phone = phone or "0000000000"
                new_student = Student(
                    full_name=new_name,
                    phone=new_phone,
                    id_number=id_number or None,
                    email=row[7].strip() or None,
                    address=row[4].strip() or None,
                    city=row[5].strip() or None,
                    status="תלמיד פעיל",
                    total_price=Decimal(str(monthly_amount * total_installments)) if total_installments > 0 else None,
                    total_paid=Decimal("0"),
                    payment_status="חייב",
                    notes=f"נוצר אוטומטית מייבוא נדרים פלוס (KevaId: {keva_id})",
                )
                if not dry_run:
                    db.add(new_student)
                    await db.flush()  # need ID immediately for commitment FK
                    cache.students.append(new_student)
                    cache.students_by_name[new_name] = new_student
                    if new_phone and new_phone != "0000000000":
                        cache.students_by_phone[normalize_phone(new_phone)] = new_student
                    if new_student.email:
                        cache.students_by_email[new_student.email.strip().lower()] = new_student
                    if new_student.id_number:
                        cache.students_by_id_number[new_student.id_number.strip()] = new_student
                else:
                    # In dry-run, still add to cache for matching in step 2
                    cache.students_by_name[new_name] = new_student
                    if new_phone and new_phone != "0000000000":
                        cache.students_by_phone[normalize_phone(new_phone)] = new_student
                student = new_student
                stats.students_created = getattr(stats, 'students_created', 0) + 1
                logger.info(f"  ✨ Created student: {new_name} (phone={new_phone})")
            else:
                stats.unmatched_students.append((student_name or name_field or f"KevaId={keva_id}", "keva"))
                stats.commitments_skipped += 1
                continue

        # Check if commitment already exists
        if keva_id in cache.commitments_by_keva:
            existing = cache.commitments_by_keva[keva_id]
            existing.status = status
            existing.monthly_amount = monthly_amount
            existing.total_amount = total_amount
            existing.installments = total_installments
            if course:
                existing.course_id = course.id
            stats.commitments_updated += 1
            continue

        # Create new commitment
        commitment = Commitment(
            student_id=student.id,
            course_id=course.id if course else None,
            monthly_amount=monthly_amount,
            total_amount=total_amount,
            installments=total_installments,
            payment_method="כרטיס אשראי - הוראת קבע",
            status=status,
            nedarim_subscription_id=keva_id,
            reference=f"KevaId: {keva_id}",
        )

        if not dry_run:
            db.add(commitment)
            pending += 1
            if pending >= BATCH_SIZE:
                await db.flush()
                pending = 0
            cache.commitments_by_keva[keva_id] = commitment
        else:
            cache.commitments_by_keva[keva_id] = commitment

        stats.commitments_created += 1
        logger.info(f"  [{idx+1}/{len(rows)}] Created commitment KevaId={keva_id} → student={student.full_name}, ₪{monthly_amount}×{total_installments}")

    if not dry_run and pending > 0:
        await db.flush()
    logger.info(f"  Step 1 done: {stats.commitments_created} created, {stats.commitments_updated} updated, {stats.commitments_skipped} skipped")


async def import_history_csv(db: AsyncSession, history_path: str, cache: EntityCache, stats: ImportStats, dry_run: bool):
    """
    Step 2: Import History CSV → Payment + Collection records.
    Each row = one transaction (charge).
    - If מספר הו"ק is present → HK charge → link to Commitment
    - If not → RAGIL charge → standalone Payment
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"STEP 2: Importing History (Transactions) from {os.path.basename(history_path)}")
    logger.info(f"{'='*70}")

    header, rows = read_csv(history_path)
    BATCH_SIZE = 100
    pending = 0
    total_rows = len(rows)

    # Track charges per commitment for installment numbering
    commitment_charge_counts: Dict[str, int] = defaultdict(int)

    for idx, row in enumerate(rows):
        id_number = row[0].strip()
        name_field = row[1].strip()
        phone = row[3].strip()
        amount = parse_amount(row[5])
        tx_date = parse_date(row[7])
        tx_datetime = parse_datetime(row[7])
        confirmation = clean_confirmation(row[8])
        card_last_4 = row[9].strip()
        tashloumim_raw = row[11].strip()
        category = row[12].strip()
        comments = row[13].strip()
        keva_id = row[18].strip()
        transaction_id = row[19].strip()

        if amount <= 0:
            continue

        # Duplicate check by transaction_id
        if transaction_id and transaction_id in cache.existing_tx_ids:
            stats.payments_skipped_dup += 1
            continue

        is_hk = bool(keva_id)

        # Parse tashloumim
        if tashloumim_raw == 'הו"ק' or tashloumim_raw == "הו\"ק":
            tashloumim = 1
        elif tashloumim_raw.isdigit():
            tashloumim = int(tashloumim_raw)
        else:
            tashloumim = 1

        # Find student using all available parameters
        student_name = extract_student_name(comments, name_field)
        course_name = extract_course_name(comments, category)
        email = row[4].strip() if row[4].strip() else None

        student, lead = cache.find_person(
            name=student_name,
            phone=phone,
            email=email,
            id_number=id_number if id_number else None,
        )
        course = cache.find_course(course_name)

        # Find commitment for HK charges — and use commitment's student if we didn't find one
        commitment = None
        if is_hk and keva_id in cache.commitments_by_keva:
            commitment = cache.commitments_by_keva[keva_id]
            if not student and commitment.student_id:
                # Resolve student from commitment
                for s in cache.students:
                    if s.id == commitment.student_id:
                        student = s
                        break

        if not student and not lead:
            stats.unmatched_students.append((student_name or name_field or f"tx={transaction_id}", "history"))
            # Still create payment as orphan (no student/lead link)

        # Determine transaction type
        tx_type = "נדרים פלוס - הוראת קבע" if is_hk else "נדרים פלוס - סליקה ישירה"

        # Create Payment
        payment = Payment(
            student_id=student.id if student else None,
            lead_id=lead.id if lead and not student else None,
            course_id=course.id if course else (commitment.course_id if commitment else None),
            commitment_id=commitment.id if commitment else None,
            amount=amount,
            currency="ILS",
            payment_method="כרטיס אשראי",
            installments=tashloumim,
            transaction_type=tx_type,
            status="שולם",
            payment_date=tx_date or date.today(),
            nedarim_donation_id=transaction_id or None,
            nedarim_transaction_id=confirmation or None,
            reference=f"{confirmation} | {card_last_4}" if card_last_4 else confirmation,
        )

        if not dry_run:
            db.add(payment)
            cache.existing_tx_ids.add(transaction_id)

        stats.payments_created += 1

        # Update student total_paid
        if student and not dry_run:
            student.total_paid = (student.total_paid or 0) + Decimal(str(amount))
            if student.total_price and float(student.total_paid) >= float(student.total_price):
                student.payment_status = "שולם"
            else:
                student.payment_status = "שולם חלקי"

        # Create Collection record — for any row where we have a student
        if student:
            installment_number = None
            total_installments_for_collection = None
            if commitment:
                commitment_charge_counts[keva_id] += 1
                installment_number = commitment_charge_counts[keva_id]
                total_installments_for_collection = commitment.installments

            collection = Collection(
                student_id=student.id,
                commitment_id=commitment.id if commitment else None,
                payment_id=None,  # will be set after flush if needed
                course_id=course.id if course else (commitment.course_id if commitment else None),
                amount=amount,
                due_date=tx_date or date.today(),
                installment_number=installment_number,
                total_installments=total_installments_for_collection,
                status="נגבה",
                collected_at=tx_datetime or datetime.now(),
                reference=confirmation,
                nedarim_donation_id=transaction_id or None,
                nedarim_transaction_id=confirmation or None,
                nedarim_subscription_id=keva_id if is_hk else None,
            )

            if not dry_run:
                db.add(collection)

            stats.collections_created += 1

        # Create HistoryEntry (if we have a lead)
        lead_id_for_history = None
        if lead:
            lead_id_for_history = lead.id
        elif student and student.lead_id:
            lead_id_for_history = student.lead_id

        if lead_id_for_history:
            desc = (
                f"חיוב הו\"ק בסך ₪{amount} (KevaId: {keva_id})"
                if is_hk else
                f"תשלום בסך ₪{amount} (אישור: {confirmation})"
            )
            history = HistoryEntry(
                lead_id=lead_id_for_history,
                action_type="תשלום התקבל" if not is_hk else "חיוב הוראת קבע",
                description=desc,
                extra_data={
                    "source": "csv_import",
                    "transaction_id": transaction_id,
                    "confirmation": confirmation,
                    "amount": float(amount),
                    "keva_id": keva_id,
                    "card_last_4": card_last_4,
                }
            )
            if not dry_run:
                db.add(history)
            stats.history_entries_created += 1

        # Batch flush for performance
        if not dry_run:
            pending += 1
            if pending >= BATCH_SIZE:
                await db.flush()
                pending = 0
                logger.info(f"  Progress: {idx+1}/{total_rows} rows processed...")

    if not dry_run and pending > 0:
        await db.flush()
    logger.info(f"  Step 2 done: {stats.payments_created} payments, {stats.collections_created} collections, {stats.payments_skipped_dup} duplicates skipped")


# ─── Main ──────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Import Nedarim Plus CSV exports into CRM")
    parser.add_argument("--history", required=True, help="Path to ExportHistory CSV")
    parser.add_argument("--keva", required=True, help="Path to ExportKeva CSV")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to DB, just show what would happen")
    parser.add_argument("--create-missing", action="store_true", help="Create new Student records for unmatched Keva entries")
    args = parser.parse_args()

    if not os.path.exists(args.history):
        print(f"ERROR: History file not found: {args.history}")
        sys.exit(1)
    if not os.path.exists(args.keva):
        print(f"ERROR: Keva file not found: {args.keva}")
        sys.exit(1)

    print("=" * 70)
    print("  NEDARIM PLUS CSV IMPORT")
    print(f"  History: {args.history}")
    print(f"  Keva:    {args.keva}")
    print(f"  Mode:    {'DRY RUN (no DB writes)' if args.dry_run else 'LIVE (writing to DB)'}")
    if args.create_missing:
        print(f"  Create:  Will create Student records for unmatched Keva entries")
    print("=" * 70)

    stats = ImportStats()
    cache = EntityCache()

    async with SessionLocal() as db:
        await cache.load(db)

        # Step 1: Import Keva → Commitments (+ create missing students if flag set)
        await import_keva_csv(db, args.keva, cache, stats, args.dry_run, create_missing=args.create_missing)

        # Step 2: Import History → Payments + Collections
        await import_history_csv(db, args.history, cache, stats, args.dry_run)

        if not args.dry_run:
            await db.commit()
            logger.info("✅ All changes committed to database")
        else:
            logger.info("🔍 DRY RUN — no changes written to database")

    stats.summary()


if __name__ == "__main__":
    asyncio.run(main())
