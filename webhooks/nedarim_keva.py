"""
Nedarim Plus הוראת קבע (standing order / keva) webhook handler.
Processes callback notifications from Nedarim's keva system.

These webhooks arrive when Nedarim charges a standing order (הוראת קבע).
Unlike DebitCard callbacks (which we initiate), these come from Nedarim's
own recurring charge system and have different field semantics:
- No Param2 (lead_id) — must match by KevaId, student name, or lead name
- Has KevaId — unique standing order identifier
- TransactionType = "הו\"ק"
- Makor = "נדרים - הוראת קבע"
- Comments format: "קורס: X | תלמיד: Y"
"""
import logging
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy import select, or_, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.models import (
    Lead, Payment, Student, Commitment, Collection,
    HistoryEntry, Course, Enrollment
)
from services.webhook_logger import log_webhook
from utils.phone import normalize_phone

logger = logging.getLogger(__name__)


def _parse_comments(comments: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse Nedarim keva Comments field.
    Format: "קורס: טהרה ביתר + שימוש | תלמיד: שמעון קרישבסקי"
    Returns: (course_name, student_name)
    """
    course_name = None
    student_name = None

    if not comments:
        return course_name, student_name

    # Extract course name
    course_match = re.search(r'קורס:\s*(.+?)(?:\s*\||$)', comments)
    if course_match:
        course_name = course_match.group(1).strip()

    # Extract student name
    student_match = re.search(r'תלמיד:\s*(.+?)(?:\s*\||$)', comments)
    if student_match:
        student_name = student_match.group(1).strip()

    return course_name, student_name


def _parse_transaction_time(time_str: str) -> Optional[datetime]:
    """Parse Nedarim transaction time format: DD/MM/YYYY HH:MM:SS"""
    if not time_str:
        return None
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M"):
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    return None


async def _find_student_by_name(db: AsyncSession, name: str) -> Optional[Student]:
    """Find student by full_name (case-insensitive, trimmed)."""
    if not name:
        return None
    name_clean = name.strip()
    stmt = select(Student).where(
        sa_func.trim(Student.full_name) == name_clean
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_lead_by_name(db: AsyncSession, name: str) -> Optional[Lead]:
    """Find lead by full_name (case-insensitive, trimmed). Prefer latest."""
    if not name:
        return None
    name_clean = name.strip()
    stmt = select(Lead).where(
        sa_func.trim(Lead.full_name) == name_clean
    ).order_by(Lead.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().first()


async def _find_course_by_name(db: AsyncSession, name: str) -> Optional[Course]:
    """Find course by name (contains match)."""
    if not name:
        return None
    name_clean = name.strip()
    # Try exact match first
    stmt = select(Course).where(Course.name == name_clean, Course.is_active == True)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    if course:
        return course
    # Try contains match
    stmt = select(Course).where(Course.name.ilike(f"%{name_clean}%"), Course.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().first()


async def handle_nedarim_keva_webhook(
    db: AsyncSession,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle incoming Nedarim Plus הוראת קבע (standing order) callback.

    These webhooks are sent by Nedarim when a standing order charge is processed.
    
    Expected data structure:
    {
        "Shovar": "43003230",
        "ClientName": "שמעון קרישבסקי",
        "Amount": "500.00",
        "TransactionTime": "17/02/2026 01:55:52",
        "Confirmation": "0803912",
        "LastNum": "4156",
        "Tokef": "0431",
        "TransactionType": "הו\"ק",
        "Comments": "קורס: טהרה ביתר + שימוש | תלמיד: שמעון קרישבסקי",
        "Tashloumim": "1",
        "FirstTashloum": "500.00",
        "TransactionId": "66322240",
        "Makor": "נדרים - הוראת קבע",
        "KevaId": "1827990",
        "UID": "26021701555119420379217",
        ...
    }
    """
    logger.info(f"📥 Received Nedarim Keva webhook: {data}")

    try:
        # ── Extract fields ──────────────────────────────────────
        confirmation = data.get('Confirmation', '')
        amount_str = data.get('Amount', '0')
        client_name = data.get('ClientName', '').strip()
        comments = data.get('Comments', '')
        card_last_4 = data.get('LastNum', '')
        transaction_id = data.get('TransactionId', '')
        keva_id = data.get('KevaId', '')
        tashloumim_str = data.get('Tashloumim', '1')
        first_tashloum_str = data.get('FirstTashloum', '')
        transaction_time_str = data.get('TransactionTime', '')
        transaction_type = data.get('TransactionType', '')
        makor = data.get('Makor', '')
        shovar = data.get('Shovar', '')
        uid = data.get('UID', '')
        phone = normalize_phone(data.get('Phone', ''))
        email = data.get('Mail', '').strip()
        mosad_number = data.get('MosadNumber', '')
        credit_terms_str = data.get('CreditTerms', '1')

        # Parse amount
        try:
            amount = float(amount_str.replace('₪', '').replace(',', '').strip())
        except (ValueError, AttributeError):
            amount = 0

        # Parse tashloumim
        try:
            tashloumim = int(tashloumim_str)
        except (ValueError, AttributeError):
            tashloumim = 1

        # Parse CreditTerms (for HK this indicates number of monthly charges)
        try:
            credit_terms = int(credit_terms_str)
        except (ValueError, AttributeError):
            credit_terms = 1

        # Parse transaction time
        transaction_time = _parse_transaction_time(transaction_time_str)

        if not confirmation:
            logger.error("No confirmation number in keva callback")
            return {"success": False, "error": "Missing confirmation number"}

        # Parse Comments for course and student name
        course_name_from_comments, student_name_from_comments = _parse_comments(comments)
        # Use ClientName as fallback for student name
        student_name = student_name_from_comments or client_name

        logger.info(
            f"Keva webhook parsed: confirmation={confirmation}, amount={amount}, "
            f"keva_id={keva_id}, client={client_name}, "
            f"course_from_comments={course_name_from_comments}, "
            f"student_from_comments={student_name_from_comments}"
        )

        # ── Check for duplicate transaction ─────────────────────
        dup_stmt = select(Payment).where(
            or_(
                Payment.nedarim_transaction_id == confirmation,
                Payment.nedarim_donation_id == transaction_id,
            )
        )
        dup_result = await db.execute(dup_stmt)
        existing_payment = dup_result.scalar_one_or_none()
        if existing_payment:
            logger.info(f"Duplicate keva webhook — payment {existing_payment.id} already exists for confirmation {confirmation}")
            return {
                "success": True,
                "payment_id": existing_payment.id,
                "message": "Duplicate webhook — payment already recorded",
                "duplicate": True,
            }

        # ── Step 1: Try to find existing Commitment by KevaId ───
        commitment = None
        student = None
        lead = None
        course = None

        if keva_id:
            stmt = select(Commitment).where(Commitment.nedarim_subscription_id == keva_id)
            result = await db.execute(stmt)
            commitment = result.scalar_one_or_none()
            if commitment:
                # Found existing commitment — get student
                stmt = select(Student).where(Student.id == commitment.student_id)
                result = await db.execute(stmt)
                student = result.scalar_one_or_none()
                course_id = commitment.course_id
                if course_id:
                    stmt = select(Course).where(Course.id == course_id)
                    result = await db.execute(stmt)
                    course = result.scalar_one_or_none()
                logger.info(f"Found commitment {commitment.id} by KevaId {keva_id} → student {student.id if student else 'N/A'}")

        # ── Step 2: Try to find student by name ─────────────────
        if not student and student_name:
            student = await _find_student_by_name(db, student_name)
            if student:
                logger.info(f"Found student {student.id} by name '{student_name}'")

        # ── Step 3: Try to find lead by name ────────────────────
        if not student and student_name:
            lead = await _find_lead_by_name(db, student_name)
            if lead:
                logger.info(f"Found lead {lead.id} by name '{student_name}'")
                # Check if lead already has a student
                if lead.student_id:
                    stmt = select(Student).where(Student.id == lead.student_id)
                    result = await db.execute(stmt)
                    student = result.scalar_one_or_none()

        # ── Step 4: Find course from Comments ───────────────────
        if not course and course_name_from_comments:
            course = await _find_course_by_name(db, course_name_from_comments)
            if course:
                logger.info(f"Found course {course.id} ('{course.name}') from comments")

        # ── Step 5: Find course from student's enrollment ───────
        if not course and student:
            stmt = select(Enrollment).where(
                Enrollment.student_id == student.id,
                Enrollment.status == "פעיל"
            ).order_by(Enrollment.created_at.desc())
            result = await db.execute(stmt)
            enrollment = result.scalars().first()
            if enrollment and enrollment.course_id:
                stmt = select(Course).where(Course.id == enrollment.course_id)
                result = await db.execute(stmt)
                course = result.scalar_one_or_none()

        # ── Build raw_data for audit ────────────────────────────
        raw_data = {
            "source": "nedarim_keva_webhook",
            "confirmation": confirmation,
            "transaction_id": transaction_id,
            "keva_id": keva_id,
            "shovar": shovar,
            "uid": uid,
            "client_name": client_name,
            "amount": float(amount),
            "tashloumim": tashloumim,
            "credit_terms": credit_terms,
            "transaction_type": transaction_type,
            "makor": makor,
            "card_last_4": card_last_4,
            "comments": comments,
            "mosad_number": mosad_number,
        }

        # ── Create Payment record ───────────────────────────────
        payment = Payment(
            student_id=student.id if student else None,
            lead_id=lead.id if lead and not student else None,
            course_id=course.id if course else None,
            amount=amount,
            currency="ILS",
            payment_method="כרטיס אשראי",
            installments=tashloumim if tashloumim > 1 else credit_terms if credit_terms > 1 else 1,
            transaction_type="נדרים פלוס - הוראת קבע",
            status="שולם",
            payment_date=(transaction_time.date() if transaction_time else datetime.now().date()),
            nedarim_transaction_id=confirmation,
            nedarim_donation_id=transaction_id,
            reference=f"{confirmation} | {card_last_4}" if card_last_4 else confirmation,
        )
        db.add(payment)
        await db.flush()
        logger.info(f"Created payment {payment.id} from keva webhook (student={student.id if student else 'N/A'}, lead={lead.id if lead else 'N/A'})")

        # ── Update student total_paid ───────────────────────────
        if student:
            student.total_paid = (student.total_paid or 0) + amount
            if student.total_price and float(student.total_paid) >= float(student.total_price):
                student.payment_status = "שולם"
            else:
                student.payment_status = "שולם חלקי"

        # ── Update lead if found (and no student yet) ───────────
        if lead and not student:
            if not lead.first_payment:
                lead.first_payment = True
                lead.first_payment_id = payment.id
            if lead.status not in ["תלמיד", "נסלק"]:
                lead.status = "נסלק"
                logger.info(f"Lead {lead.id} status updated to נסלק")
            lead.updated_at = datetime.now(timezone.utc)

        # ── Create/Update Commitment ────────────────────────────
        if student and keva_id:
            if not commitment:
                # Check if commitment exists by keva_id (double check)
                stmt = select(Commitment).where(Commitment.nedarim_subscription_id == keva_id)
                result = await db.execute(stmt)
                commitment = result.scalar_one_or_none()

            if not commitment:
                commitment = Commitment(
                    student_id=student.id,
                    course_id=course.id if course else None,
                    monthly_amount=amount,
                    total_amount=amount * credit_terms if credit_terms > 1 else None,
                    installments=credit_terms if credit_terms > 1 else None,
                    payment_method="כרטיס אשראי - הוראת קבע",
                    status="פעיל",
                    nedarim_subscription_id=keva_id,
                    reference=confirmation,
                )
                db.add(commitment)
                await db.flush()
                logger.info(f"Created commitment {commitment.id} for student {student.id} (KevaId={keva_id})")
            else:
                # Update existing commitment reference if needed
                if not commitment.reference:
                    commitment.reference = confirmation

            # Link payment to commitment
            payment.commitment_id = commitment.id

            # ── Create Collection record ────────────────────────
            # Determine installment number
            existing_collections_stmt = select(sa_func.count()).select_from(Collection).where(
                Collection.commitment_id == commitment.id,
                Collection.status == "נגבה"
            )
            result = await db.execute(existing_collections_stmt)
            existing_count = result.scalar() or 0
            installment_number = existing_count + 1

            collection = Collection(
                student_id=student.id,
                commitment_id=commitment.id,
                payment_id=payment.id,
                course_id=course.id if course else None,
                amount=amount,
                due_date=(transaction_time.date() if transaction_time else datetime.now().date()),
                installment_number=installment_number,
                total_installments=credit_terms if credit_terms > 1 else None,
                status="נגבה",
                collected_at=transaction_time or datetime.now(),
                reference=confirmation,
                nedarim_donation_id=transaction_id,
                nedarim_transaction_id=confirmation,
                nedarim_subscription_id=keva_id,
            )
            db.add(collection)
            logger.info(f"Created collection #{installment_number} for commitment {commitment.id}")

        elif student:
            # Student found but no KevaId — single collection
            collection = Collection(
                student_id=student.id,
                payment_id=payment.id,
                course_id=course.id if course else None,
                amount=amount,
                due_date=(transaction_time.date() if transaction_time else datetime.now().date()),
                installment_number=1,
                total_installments=1,
                status="נגבה",
                collected_at=transaction_time or datetime.now(),
                reference=confirmation,
                nedarim_donation_id=transaction_id,
                nedarim_transaction_id=confirmation,
            )
            db.add(collection)

        # ── Create HistoryEntry if lead is known ────────────────
        lead_id_for_history = None
        if lead:
            lead_id_for_history = lead.id
        elif student and student.lead_id:
            lead_id_for_history = student.lead_id

        if lead_id_for_history:
            history_entry = HistoryEntry(
                lead_id=lead_id_for_history,
                action_type="תשלום הו\"ק התקבל",
                description=(
                    f"תשלום הוראת קבע בסך ₪{amount} התקבל מנדרים פלוס "
                    f"(אישור: {confirmation}, KevaId: {keva_id})"
                ),
                extra_data=raw_data,
            )
            db.add(history_entry)

        await db.flush()

        result_data = {
            "success": True,
            "payment_id": payment.id,
            "student_id": student.id if student else None,
            "lead_id": lead.id if lead else None,
            "commitment_id": commitment.id if commitment else None,
            "course_id": course.id if course else None,
            "keva_id": keva_id,
            "amount": float(amount),
            "confirmation": confirmation,
            "message": "Keva payment recorded successfully",
        }

        # Log warning if we couldn't match to any entity
        if not student and not lead:
            logger.warning(
                f"⚠️ Keva webhook: could not match to student or lead! "
                f"client_name='{client_name}', comments='{comments}', keva_id={keva_id}. "
                f"Payment {payment.id} created as orphan."
            )
            result_data["warning"] = "Could not match to student or lead — payment created as orphan"

        logger.info(f"✅ Keva webhook processed: {result_data}")
        return result_data

    except Exception as e:
        logger.error(f"Error processing Nedarim Keva webhook: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
