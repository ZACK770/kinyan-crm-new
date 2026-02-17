"""
Nedarim Plus DebitCard API webhook handler.
Processes callback notifications from direct credit card charges (RAGIL).

These callbacks come from OUR DebitCard.aspx charges.
They confirm that a regular payment (not HK) was processed.

Key fields:
- Confirmation: payment confirmation number
- TransactionId: Nedarim transaction ID
- Amount: charged amount
- Tashloumim: number of installments the charge was split into
- LastNum: last 4 digits of card
"""
import logging
from typing import Dict, Any
from datetime import datetime

from sqlalchemy import select, or_, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead, Payment, Student, Commitment, Collection, HistoryEntry, Course

logger = logging.getLogger(__name__)


async def handle_nedarim_debitcard_webhook(
    db: AsyncSession,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle incoming Nedarim Plus DebitCard callback.
    
    This webhook is triggered by OUR DebitCard.aspx charges (RAGIL payments).
    It confirms that a regular payment was processed successfully.
    
    Expected data structure:
    {
        "Confirmation": "0918185",
        "Amount": "8.00",
        "Tashloumim": "1",
        "LastNum": "9957",
        "TransactionId": "66303840",
        "ClientName": "שם הלקוח",
        "Phone": "0548403828",
        "Comments": "קורס: X | תלמיד: Y",
        ...
    }
    """
    logger.info(f"📥 Received Nedarim DebitCard callback: {data}")
    
    try:
        # ── Extract fields ──────────────────────────────────────
        confirmation = data.get('Confirmation') or data.get('confirmation', '')
        amount_str = data.get('Amount') or data.get('amount', '0')
        tashloumim_str = data.get('Tashloumim') or data.get('tashloumim', '1')
        card_last_4 = data.get('LastNum') or data.get('card_last_4', '')
        comments = data.get('Comments') or data.get('comments', '')
        transaction_id = data.get('TransactionId') or data.get('transaction_id', '')
        client_name = data.get('ClientName') or data.get('client_name', '')
        phone = data.get('Phone') or data.get('phone', '')
        transaction_time_str = data.get('TransactionTime') or ''
        keva_id = data.get('KevaId') or data.get('keva_id', '')
        
        # Parse amount
        try:
            amount = float(str(amount_str).replace('₪', '').replace(',', '').strip())
        except (ValueError, AttributeError):
            amount = 0
        
        # Parse tashloumim (installments the charge was split into)
        try:
            tashloumim = int(tashloumim_str)
        except (ValueError, AttributeError):
            tashloumim = 1
        
        # Parse transaction time
        transaction_time = None
        if transaction_time_str:
            for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M"):
                try:
                    transaction_time = datetime.strptime(transaction_time_str, fmt)
                    break
                except ValueError:
                    continue
        
        if not confirmation:
            logger.error("No confirmation number in callback")
            return {"success": False, "error": "Missing confirmation number"}
        
        # ── Determine if this is a real charge or HK setup ─────
        # DebitCard callbacks are always real charges (RAGIL).
        # If KevaId is present, this is a charge FROM a standing order (handled by keva webhook).
        is_keva_charge = bool(keva_id)
        
        # ── Check for duplicate ────────────────────────────────
        dup_stmt = select(Payment).where(
            or_(
                Payment.nedarim_transaction_id == confirmation,
                Payment.nedarim_donation_id == transaction_id,
            )
        )
        dup_result = await db.execute(dup_stmt)
        existing_payment = dup_result.scalar_one_or_none()
        
        if existing_payment:
            # Payment already exists — update it if needed
            if existing_payment.status not in ["שולם", "נגבה"]:
                existing_payment.status = "שולם"
                existing_payment.payment_date = (transaction_time.date() if transaction_time else datetime.now().date())
                if not existing_payment.nedarim_transaction_id:
                    existing_payment.nedarim_transaction_id = confirmation
                if not existing_payment.nedarim_donation_id and transaction_id:
                    existing_payment.nedarim_donation_id = transaction_id
                if card_last_4:
                    existing_payment.reference = f"{confirmation} | {card_last_4}"
                logger.info(f"Updated existing payment {existing_payment.id} status to שולם")
                await db.flush()
            else:
                logger.info(f"Duplicate webhook — payment {existing_payment.id} already recorded")
            
            return {
                "success": True,
                "payment_id": existing_payment.id,
                "message": "Payment already recorded or updated",
                "duplicate": True,
            }
        
        # ── Try to find matching lead/student ──────────────────
        lead = None
        student = None
        course = None
        
        # Try to find by client name
        if client_name:
            name_clean = client_name.strip()
            # Try student first
            stmt = select(Student).where(sa_func.trim(Student.full_name) == name_clean)
            result = await db.execute(stmt)
            student = result.scalar_one_or_none()
            
            if not student:
                # Try lead
                stmt = select(Lead).where(
                    sa_func.trim(Lead.full_name) == name_clean
                ).order_by(Lead.created_at.desc())
                result = await db.execute(stmt)
                lead = result.scalars().first()
                if lead and lead.student_id:
                    stmt = select(Student).where(Student.id == lead.student_id)
                    result = await db.execute(stmt)
                    student = result.scalar_one_or_none()
        
        # Try to find course from comments
        if comments:
            import re
            course_match = re.search(r'קורס:\s*(.+?)(?:\s*\||$)', comments)
            if course_match:
                course_name = course_match.group(1).strip()
                stmt = select(Course).where(Course.name.ilike(f"%{course_name}%"), Course.is_active == True)
                result = await db.execute(stmt)
                course = result.scalars().first()
        
        # ── Build raw_data for audit ─────────────────────────
        raw_data = {
            "source": "nedarim_debitcard_webhook",
            "confirmation": confirmation,
            "transaction_id": transaction_id,
            "client_name": client_name,
            "amount": float(amount),
            "tashloumim": tashloumim,
            "card_last_4": card_last_4,
            "comments": comments,
            "keva_id": keva_id,
        }
        
        # ── Create Payment record ────────────────────────────
        payment = Payment(
            student_id=student.id if student else None,
            lead_id=lead.id if lead and not student else (student.lead_id if student and student.lead_id else None),
            course_id=course.id if course else None,
            amount=amount,
            currency="ILS",
            payment_method="כרטיס אשראי",
            installments=tashloumim,
            transaction_type="נדרים פלוס - סליקה ישירה",
            status="שולם",
            payment_date=(transaction_time.date() if transaction_time else datetime.now().date()),
            nedarim_transaction_id=confirmation,
            nedarim_donation_id=transaction_id,
            reference=f"{confirmation} | {card_last_4}" if card_last_4 else confirmation,
        )
        db.add(payment)
        await db.flush()
        logger.info(f"Created payment {payment.id} from debitcard webhook (student={student.id if student else 'N/A'}, lead={lead.id if lead else 'N/A'})")
        
        # ── Update student total_paid ────────────────────────
        if student:
            student.total_paid = (student.total_paid or 0) + amount
            if student.total_price and float(student.total_paid) >= float(student.total_price):
                student.payment_status = "שולם"
            else:
                student.payment_status = "שולם חלקי"
        
        # ── Update lead if found ─────────────────────────────
        lead_for_update = lead
        if not lead_for_update and student and student.lead_id:
            stmt = select(Lead).where(Lead.id == student.lead_id)
            result = await db.execute(stmt)
            lead_for_update = result.scalar_one_or_none()
        
        if lead_for_update:
            if not lead_for_update.first_payment:
                lead_for_update.first_payment = True
                lead_for_update.first_payment_id = payment.id
            if lead_for_update.status not in ["תלמיד", "נסלק"]:
                lead_for_update.status = "נסלק"
                logger.info(f"Lead {lead_for_update.id} status updated to נסלק")
        
        # ── Create Collection record (actual charge) ─────────
        if student:
            collection = Collection(
                student_id=student.id,
                payment_id=payment.id,
                course_id=course.id if course else None,
                amount=amount,
                due_date=(transaction_time.date() if transaction_time else datetime.now().date()),
                installment_number=1,
                total_installments=tashloumim if tashloumim > 1 else 1,
                status="נגבה",
                collected_at=transaction_time or datetime.now(),
                reference=confirmation,
                nedarim_donation_id=transaction_id,
                nedarim_transaction_id=confirmation,
            )
            db.add(collection)
            logger.info(f"Created collection record for payment {payment.id}")
        
        # ── Create HistoryEntry ──────────────────────────────
        lead_id_for_history = None
        if lead_for_update:
            lead_id_for_history = lead_for_update.id
        elif student and student.lead_id:
            lead_id_for_history = student.lead_id
        
        if lead_id_for_history:
            history_entry = HistoryEntry(
                lead_id=lead_id_for_history,
                action_type="תשלום התקבל",
                description=(
                    f"תשלום בסך ₪{amount} התקבל בהצלחה דרך נדרים פלוס "
                    f"(אישור: {confirmation}, כרטיס: ****{card_last_4})"
                ),
                extra_data=raw_data,
            )
            db.add(history_entry)
        
        await db.flush()
        
        result_data = {
            "success": True,
            "payment_id": payment.id,
            "student_id": student.id if student else None,
            "lead_id": payment.lead_id,
            "amount": float(amount),
            "confirmation": confirmation,
            "message": "Payment confirmed, collection and history records created",
        }
        
        if not student and not lead:
            logger.warning(
                f"⚠️ DebitCard webhook: could not match to student or lead! "
                f"client_name='{client_name}', comments='{comments}'. "
                f"Payment {payment.id} created as orphan."
            )
            result_data["warning"] = "Could not match to student or lead"
        
        logger.info(f"✅ DebitCard webhook processed: {result_data}")
        return result_data
    
    except Exception as e:
        logger.error(f"Error processing Nedarim DebitCard callback: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
