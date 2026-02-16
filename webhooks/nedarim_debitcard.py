"""
Nedarim Plus DebitCard API webhook handler.
Processes callback notifications from direct credit card charges.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead, Payment, Student

logger = logging.getLogger(__name__)


async def handle_nedarim_debitcard_webhook(
    db: AsyncSession,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle incoming Nedarim Plus DebitCard callback.
    
    The callback is sent as an email-like notification with transaction details.
    We need to parse it and update the payment status and lead conversion.
    
    Expected data structure (from email/callback):
    {
        "transaction_date": "16/02/2026 16:25",
        "client_name": "Test User - Real Card 20 ILS",
        "amount": "20.00",
        "installments": "3",
        "category": "",
        "comments": "Test HK - 3 חודשים של ₪20 (סה\"כ ₪60)",
        "card_last_4": "9957",
        "card_brand": "ויזה",
        "confirmation": "0212274",
        "terminal_location": "Online",
        "phone": "0501234567",
        "email": "test@example.com",
        "param1": "Salesperson Name",  # Optional
        "param2": "123"  # lead_id
    }
    
    Returns:
        Processing result dict
    """
    logger.info(f"Received Nedarim DebitCard callback: {data}")
    
    try:
        # Extract key fields - fields come with capital letters from Nedarim
        confirmation = data.get('Confirmation') or data.get('confirmation') or data.get('מספר אישור')
        amount_str = data.get('Amount') or data.get('amount') or data.get('סכום', '0')
        installments_str = data.get('Tashloumim') or data.get('installments') or data.get('תשלומים', '1')
        card_last_4 = data.get('LastNum') or data.get('card_last_4') or data.get('4 ספרות אחרונות')
        comments = data.get('Comments') or data.get('comments') or data.get('הערות', '')
        param2 = data.get('Param2') or data.get('param2')  # lead_id
        transaction_id = data.get('TransactionId') or data.get('transaction_id')  # Nedarim transaction ID
        
        # Parse amount
        try:
            amount = float(amount_str.replace('₪', '').replace(',', '').strip())
        except (ValueError, AttributeError):
            amount = 0
        
        # Parse installments
        try:
            installments = int(installments_str)
        except (ValueError, AttributeError):
            installments = 1
        
        if not confirmation:
            logger.error("No confirmation number in callback")
            return {"success": False, "error": "Missing confirmation number"}
        
        # Try to find the payment by confirmation number or transaction_id
        payment = None
        if confirmation:
            stmt = select(Payment).where(Payment.nedarim_transaction_id == confirmation)
            result = await db.execute(stmt)
            payment = result.scalar_one_or_none()
        
        if not payment and transaction_id:
            stmt = select(Payment).where(Payment.nedarim_donation_id == transaction_id)
            result = await db.execute(stmt)
            payment = result.scalar_one_or_none()
        
        # If not found by confirmation/transaction_id, try by lead_id from param2
        if not payment and param2:
            try:
                lead_id = int(param2)
                # Find the most recent payment for this lead
                stmt = select(Payment).where(
                    Payment.lead_id == lead_id,
                    Payment.status.in_(["ממתין", "בתהליך", "שולם"])
                ).order_by(Payment.created_at.desc())
                result = await db.execute(stmt)
                payment = result.scalar_one_or_none()
            except (ValueError, TypeError):
                pass
        
        if not payment:
            logger.warning(f"Payment not found for confirmation {confirmation}")
            # Create a new payment record from callback
            # Try to extract lead_id from comments or param2
            lead_id = None
            if param2:
                try:
                    lead_id = int(param2)
                except (ValueError, TypeError):
                    pass
            
            if not lead_id and 'ליד #' in comments:
                try:
                    lead_id = int(comments.split('ליד #')[1].split()[0])
                except (ValueError, IndexError):
                    pass
            
            if lead_id:
                payment = Payment(
                    lead_id=lead_id,
                    amount=amount,
                    currency="ILS",
                    payment_method="כרטיס אשראי",
                    installments=installments,
                    transaction_type="נדרים פלוס - סליקה ישירה (callback)",
                    status="שולם",
                    payment_date=datetime.now().date(),
                    nedarim_transaction_id=confirmation,
                    reference=f"{confirmation} | {card_last_4}",
                )
                db.add(payment)
                await db.flush()
                logger.info(f"Created new payment record from callback: {payment.id}")
            else:
                logger.error("Cannot create payment - no lead_id found")
                return {"success": False, "error": "Cannot identify lead"}
        else:
            # Update existing payment
            payment.status = "שולם"
            payment.payment_date = datetime.now().date()
            if not payment.nedarim_transaction_id:
                payment.nedarim_transaction_id = confirmation
            if not payment.nedarim_donation_id and transaction_id:
                payment.nedarim_donation_id = transaction_id
            if card_last_4:
                payment.reference = f"{confirmation} | {card_last_4}"
            logger.info(f"Updated payment {payment.id} from callback")
        
        # Update lead status and handle conversion
        if payment.lead_id:
            stmt = select(Lead).where(Lead.id == payment.lead_id)
            result = await db.execute(stmt)
            lead = result.scalar_one_or_none()
            
            if lead:
                # Mark first payment
                if not lead.first_payment:
                    lead.first_payment = True
                    lead.first_payment_id = payment.id
                
                # Update lead status to "נסלק" (charged)
                if lead.status not in ["תלמיד", "נסלק"]:
                    lead.status = "נסלק"
                    logger.info(f"Lead {lead.id} status updated to נסלק")
                
                # Check if lead should be converted to student
                # Convert if: has first payment, has selected course, and not already a student
                if lead.first_payment and lead.selected_course_id and lead.status != "תלמיד":
                    # Check if student already exists
                    stmt = select(Student).where(Student.lead_id == lead.id)
                    result = await db.execute(stmt)
                    existing_student = result.scalar_one_or_none()
                    
                    if not existing_student:
                        # Create student
                        student = Student(
                            lead_id=lead.id,
                            full_name=lead.full_name,
                            family_name=lead.family_name,
                            phone=lead.phone,
                            phone2=lead.phone2,
                            email=lead.email,
                            city=lead.city,
                            address=lead.address,
                            course_id=lead.selected_course_id,
                            total_price=lead.selected_price,
                            total_paid=amount,
                            payment_status="שולם חלקי" if amount < (lead.selected_price or 0) else "שולם",
                            enrollment_date=datetime.now().date(),
                            salesperson_id=lead.salesperson_id,
                        )
                        db.add(student)
                        await db.flush()
                        
                        # Update lead status to "תלמיד"
                        lead.status = "תלמיד"
                        lead.conversion_date = datetime.now()
                        
                        # Link payment to student
                        payment.student_id = student.id
                        
                        logger.info(f"✅ Lead {lead.id} converted to student {student.id}")
                        
                        return {
                            "success": True,
                            "payment_id": payment.id,
                            "lead_id": lead.id,
                            "student_id": student.id,
                            "converted": True,
                            "message": f"Payment confirmed and lead converted to student"
                        }
        
        await db.flush()
        
        return {
            "success": True,
            "payment_id": payment.id,
            "lead_id": payment.lead_id,
            "message": "Payment confirmed"
        }
    
    except Exception as e:
        logger.error(f"Error processing Nedarim DebitCard callback: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
