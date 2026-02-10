"""
Nedarim Plus API Client & Services.
Integration for payments, donations, and recurring charges.
"""
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db import settings
from db.models import Student, Payment, Commitment

logger = logging.getLogger(__name__)


# ============================================================
# Exceptions
# ============================================================
class NedarimAPIError(Exception):
    """Custom exception for Nedarim API errors."""
    def __init__(self, status_code: int, error_code: Optional[str], message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(f"Nedarim API Error [{status_code}] {error_code}: {message}")


# ============================================================
# HTTP Client
# ============================================================
class NedarimClient:
    """HTTP Client for Nedarim Plus API."""
    
    def __init__(self):
        self.base_url = settings.NEDARIM_API_URL
        self.api_key = settings.NEDARIM_API_KEY
        self.mosad_id = settings.NEDARIM_MOSAD_ID
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with automatic mosad_id injection."""
        data["mosad_id"] = self.mosad_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=self._get_headers()
            )
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                except:
                    error_data = {"message": response.text}
                raise NedarimAPIError(
                    status_code=response.status_code,
                    error_code=error_data.get("error_code"),
                    message=error_data.get("message", "Unknown error")
                )
            
            return response.json()
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """GET request with auth."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Nedarim webhook signature using HMAC-SHA256."""
    if not settings.NEDARIM_WEBHOOK_SECRET:
        logger.warning("NEDARIM_WEBHOOK_SECRET not configured - skipping signature verification")
        return True
    
    expected = hmac.new(
        settings.NEDARIM_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


# ============================================================
# Payer Service
# ============================================================
async def create_payer(
    db: AsyncSession,
    student: Student,
) -> str:
    """
    Create payer in Nedarim Plus or return existing payer_id.
    Updates student.nedarim_payer_id in DB.
    
    Returns:
        str: Nedarim payer_id (e.g., "PAY_123456")
    """
    # If already synced, return existing ID
    if student.nedarim_payer_id:
        return student.nedarim_payer_id
    
    client = NedarimClient()
    
    payload = {
        "payer_name": student.full_name,
        "payer_tz": student.id_number or "",
        "payer_phone": student.phone,
        "payer_email": student.email or ""
    }
    
    response = await client.post("/payers", payload)
    payer_id = response["payer_id"]
    
    # Update student with Nedarim payer ID
    student.nedarim_payer_id = payer_id
    await db.flush()
    
    logger.info(f"Created Nedarim payer {payer_id} for student {student.id}")
    return payer_id


async def ensure_payer_exists(db: AsyncSession, student_id: int) -> str:
    """Get or create Nedarim payer for a student."""
    stmt = select(Student).where(Student.id == student_id)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    
    if not student:
        raise ValueError(f"Student {student_id} not found")
    
    return await create_payer(db, student)


# ============================================================
# Lead Payment Service (for pre-conversion payments)
# ============================================================
async def create_lead_payment_link(
    db: AsyncSession,
    lead_id: int,
    amount: float = None,
    currency: str = "ILS",
    payment_method: str = "credit_card",
    installments: int = None,
    payment_day: int = None,
    redirect_url: Optional[str] = None,
    course_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a payment link for a Lead (before conversion to student).
    Used by sales team to charge leads directly.
    
    If amount/installments/payment_day not provided, will use values from Lead's selected course.
    
    Returns:
        dict with: payment_id, nedarim_donation_id, payment_link, lead_id
    """
    from db.models import Lead, Course
    
    # Get the lead
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    
    # Get selected course details if not provided
    selected_course = None
    if lead.selected_course_id:
        stmt = select(Course).where(Course.id == lead.selected_course_id)
        result = await db.execute(stmt)
        selected_course = result.scalar_one_or_none()
    
    # Use Lead's selected course values as defaults
    if selected_course:
        if amount is None:
            amount = float(lead.selected_price or selected_course.price or 0)
        if installments is None:
            installments = lead.selected_payments_count or selected_course.payments_count or 1
        if payment_day is None:
            payment_day = lead.selected_payment_day
    
    # Fallback defaults
    if amount is None:
        raise ValueError("Amount must be provided or course must be selected")
    if installments is None:
        installments = 1
    
    # Create payer from lead data (temporary, not a Student yet)
    client = NedarimClient()
    
    payer_payload = {
        "payer_name": lead.full_name,
        "payer_tz": lead.id_number or "",
        "payer_phone": lead.phone,
        "payer_email": lead.email or ""
    }
    
    payer_response = await client.post("/payers", payer_payload)
    payer_id = payer_response["payer_id"]
    
    # Create payment record linked to lead (not student)
    payment = Payment(
        lead_id=lead_id,
        course_id=course_id or lead.course_id,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        installments=installments,
        charge_day=payment_day,
        transaction_type="נדרים פלוס",
        status="ממתין",
    )
    db.add(payment)
    await db.flush()
    
    # Build redirect URL
    if not redirect_url:
        redirect_url = f"{settings.FRONTEND_URL}/payment-success?payment_id={payment.id}&lead_id={lead_id}"
    
    # Build webhook URL
    webhook_url = f"{settings.FRONTEND_URL}/api/webhooks/nedarim"
    
    payment_payload = {
        "payer_id": payer_id,
        "amount": amount,
        "currency": currency,
        "payment_method": payment_method,
        "installments": installments,
        "redirect_url": redirect_url,
        "webhook_url": webhook_url,
        "metadata": {
            "lead_id": lead_id,
            "course_id": course_id or lead.selected_course_id,
            "payment_day": payment_day,
        }
    }
    
    # Add payment_day for recurring payments
    if installments > 1 and payment_day:
        payment_payload["recurring_day"] = payment_day
    
    response = await client.post("/donations", payment_payload)
    
    # Update payment with Nedarim IDs
    payment.nedarim_donation_id = response["donation_id"]
    payment.nedarim_transaction_id = response.get("transaction_id")
    payment.reference = response["donation_id"]
    
    # Update lead with payment link
    lead.nedarim_payment_link = response["payment_link"]
    
    await db.flush()
    
    logger.info(f"Created Nedarim payment link for lead {lead_id}: {response['payment_link']} (amount={amount}, installments={installments}, day={payment_day})")
    
    return {
        "payment_id": payment.id,
        "lead_id": lead_id,
        "nedarim_donation_id": response["donation_id"],
        "payment_link": response["payment_link"],
        "amount": amount,
        "installments": installments,
        "payment_day": payment_day,
        "status": "ממתין"
    }


# ============================================================
# Payment / Donation Service
# ============================================================
async def create_payment_link(
    db: AsyncSession,
    student_id: int,
    amount: float,
    currency: str = "ILS",
    payment_method: str = "credit_card",
    installments: int = 1,
    redirect_url: Optional[str] = None,
    commitment_id: Optional[int] = None,
    course_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a payment link via Nedarim Plus.
    Creates a Payment record in pending status.
    
    Returns:
        dict with: payment_id, nedarim_donation_id, payment_link
    """
    # Get student and ensure payer exists
    stmt = select(Student).where(Student.id == student_id)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    if not student:
        raise ValueError(f"Student {student_id} not found")
    
    payer_id = await create_payer(db, student)
    
    # Create payment record in DB first
    payment = Payment(
        student_id=student_id,
        course_id=course_id,
        commitment_id=commitment_id,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        installments=installments,
        transaction_type="נדרים פלוס",
        status="ממתין",
    )
    db.add(payment)
    await db.flush()
    
    # Build redirect URL
    if not redirect_url:
        redirect_url = f"{settings.FRONTEND_URL}/payment-success?payment_id={payment.id}"
    
    # Build webhook URL
    webhook_url = f"{settings.FRONTEND_URL}/api/webhooks/nedarim"
    
    client = NedarimClient()
    
    payload = {
        "payer_id": payer_id,
        "amount": amount,
        "currency": currency,
        "payment_method": payment_method,
        "installments": installments,
        "redirect_url": redirect_url,
        "webhook_url": webhook_url,
    }
    
    response = await client.post("/donations", payload)
    
    # Update payment with Nedarim IDs
    payment.nedarim_donation_id = response["donation_id"]
    payment.nedarim_transaction_id = response.get("transaction_id")
    payment.reference = response["donation_id"]  # Use donation_id as reference
    await db.flush()
    
    logger.info(f"Created Nedarim payment link: {response['payment_link']} for payment {payment.id}")
    
    return {
        "payment_id": payment.id,
        "nedarim_donation_id": response["donation_id"],
        "payment_link": response["payment_link"],
        "status": "ממתין"
    }


async def check_payment_status(
    db: AsyncSession,
    payment_id: int,
) -> Dict[str, Any]:
    """
    Check payment status from Nedarim Plus API.
    Updates the Payment record accordingly.
    """
    stmt = select(Payment).where(Payment.id == payment_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise ValueError(f"Payment {payment_id} not found")
    
    if not payment.nedarim_donation_id:
        return {"payment_id": payment_id, "status": payment.status, "error": "No Nedarim donation ID"}
    
    client = NedarimClient()
    response = await client.get(f"/donations/{payment.nedarim_donation_id}")
    
    # Map Nedarim status to our status
    status_map = {
        "pending": "ממתין",
        "completed": "שולם",
        "failed": "נכשל",
        "refunded": "הוחזר"
    }
    
    new_status = status_map.get(response["status"], "ממתין")
    payment.status = new_status
    
    if response.get("payment_date"):
        try:
            payment.payment_date = datetime.fromisoformat(response["payment_date"].replace("Z", "+00:00")).date()
        except:
            pass
    
    # Store error info if failed
    if response.get("error_code"):
        # Store in reference field or add notes
        payment.reference = f"{payment.nedarim_donation_id} | Error: {response.get('error_code')}"
    
    await db.flush()
    
    return {
        "payment_id": payment_id,
        "nedarim_donation_id": payment.nedarim_donation_id,
        "status": new_status,
        "amount": float(payment.amount),
        "payment_date": str(payment.payment_date) if payment.payment_date else None
    }


async def get_payment_by_nedarim_id(
    db: AsyncSession,
    nedarim_donation_id: str,
) -> Optional[Payment]:
    """Find a Payment by its Nedarim donation ID."""
    stmt = select(Payment).where(Payment.nedarim_donation_id == nedarim_donation_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ============================================================
# Subscription / Recurring Service
# ============================================================
async def create_subscription(
    db: AsyncSession,
    student_id: int,
    amount: float,
    frequency: str = "monthly",  # monthly, quarterly, yearly
    start_date: Optional[str] = None,
    commitment_id: Optional[int] = None,
    course_id: Optional[int] = None,
    credit_card_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a recurring payment subscription in Nedarim Plus.
    Links to an existing Commitment if provided.
    
    Returns:
        dict with: commitment_id, nedarim_subscription_id, status, next_charge_date
    """
    payer_id = await ensure_payer_exists(db, student_id)
    
    # If no commitment provided, create one
    if commitment_id:
        stmt = select(Commitment).where(Commitment.id == commitment_id)
        result = await db.execute(stmt)
        commitment = result.scalar_one_or_none()
        if not commitment:
            raise ValueError(f"Commitment {commitment_id} not found")
    else:
        commitment = Commitment(
            student_id=student_id,
            course_id=course_id,
            monthly_amount=amount,
            payment_method="הוראת קבע",
            status="פעיל",
        )
        db.add(commitment)
        await db.flush()
    
    client = NedarimClient()
    
    payload = {
        "payer_id": payer_id,
        "amount": amount,
        "frequency": frequency,
        "start_date": start_date or datetime.now().strftime("%Y-%m-%d"),
    }
    
    if credit_card_token:
        payload["credit_card_token"] = credit_card_token
    
    response = await client.post("/subscriptions", payload)
    
    # Update commitment with Nedarim subscription ID
    commitment.nedarim_subscription_id = response["subscription_id"]
    commitment.reference = response["subscription_id"]
    await db.flush()
    
    logger.info(f"Created Nedarim subscription {response['subscription_id']} for commitment {commitment.id}")
    
    return {
        "commitment_id": commitment.id,
        "nedarim_subscription_id": response["subscription_id"],
        "status": response["status"],
        "next_charge_date": response.get("next_charge_date")
    }


# ============================================================
# Webhook Processing
# ============================================================
async def process_webhook(
    db: AsyncSession,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process incoming Nedarim webhook event.
    Updates Payment/Commitment status based on event type.
    
    Event types:
    - donation.completed: Payment successful
    - donation.failed: Payment failed
    - donation.refunded: Payment refunded
    - subscription.charged: Recurring payment charged
    - subscription.failed: Recurring payment failed
    """
    event_type = data.get("event_type")
    donation_id = data.get("donation_id")
    subscription_id = data.get("subscription_id")
    payer_id = data.get("payer_id")
    amount = data.get("amount", 0)
    status = data.get("status")
    timestamp = data.get("timestamp")
    metadata = data.get("metadata", {})
    
    logger.info(f"Processing Nedarim webhook: {event_type} | donation={donation_id} | subscription={subscription_id}")
    
    result = {"event_type": event_type, "processed": False}
    
    # Handle donation events
    if event_type in ["donation.completed", "donation.failed", "donation.refunded"]:
        if not donation_id:
            return {"error": "Missing donation_id", "processed": False}
        
        payment = await get_payment_by_nedarim_id(db, donation_id)
        if not payment:
            logger.warning(f"Payment not found for Nedarim donation {donation_id}")
            return {"error": f"Payment not found for {donation_id}", "processed": False}
        
        # Map status
        status_map = {
            "donation.completed": "שולם",
            "donation.failed": "נכשל",
            "donation.refunded": "הוחזר",
        }
        payment.status = status_map.get(event_type, payment.status)
        
        # Set payment date if completed
        if event_type == "donation.completed":
            if timestamp:
                try:
                    payment.payment_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date()
                except:
                    payment.payment_date = datetime.now().date()
            else:
                payment.payment_date = datetime.now().date()
            
            # Update student total_paid (if student exists)
            if payment.student_id:
                stmt = select(Student).where(Student.id == payment.student_id)
                res = await db.execute(stmt)
                student = res.scalar_one_or_none()
                if student:
                    student.total_paid = (student.total_paid or 0) + float(payment.amount)
                    if student.total_price and student.total_paid >= student.total_price:
                        student.payment_status = "שולם"
            
            # Handle lead first payment (pre-conversion payment)
            if payment.lead_id:
                from db.models import Lead
                stmt = select(Lead).where(Lead.id == payment.lead_id)
                res = await db.execute(stmt)
                lead = res.scalar_one_or_none()
                if lead:
                    lead.first_payment = True
                    lead.first_payment_id = payment.id
                    lead.status = "נסלק"  # Move lead to "charged" status
                    logger.info(f"Lead {lead.id} payment completed - marked as נסלק")
        
        # Store error info if failed
        if metadata.get("error_code"):
            payment.reference = f"{donation_id} | Error: {metadata['error_code']} - {metadata.get('error_message', '')}"
        
        await db.flush()
        result["processed"] = True
        result["payment_id"] = payment.id
        result["new_status"] = payment.status
    
    # Handle subscription events
    elif event_type in ["subscription.charged", "subscription.failed"]:
        if not subscription_id:
            return {"error": "Missing subscription_id", "processed": False}
        
        # Find commitment by Nedarim subscription ID
        stmt = select(Commitment).where(Commitment.nedarim_subscription_id == subscription_id)
        res = await db.execute(stmt)
        commitment = res.scalar_one_or_none()
        
        if not commitment:
            logger.warning(f"Commitment not found for Nedarim subscription {subscription_id}")
            return {"error": f"Commitment not found for {subscription_id}", "processed": False}
        
        if event_type == "subscription.charged":
            # Create a new payment record for the recurring charge
            payment = Payment(
                student_id=commitment.student_id,
                course_id=commitment.course_id,
                commitment_id=commitment.id,
                amount=amount or commitment.monthly_amount,
                currency="₪",
                payment_method="הוראת קבע",
                transaction_type="הוראת קבע",
                status="שולם",
                payment_date=datetime.now().date(),
                nedarim_donation_id=donation_id,
                reference=f"SUB:{subscription_id} | DON:{donation_id}",
            )
            db.add(payment)
            await db.flush()
            
            # Create Collection record for this charge
            from db.models import Collection
            
            # Calculate installment number based on existing collections
            stmt = select(func.count(Collection.id)).where(
                Collection.commitment_id == commitment.id,
                Collection.status == "נגבה"
            )
            res = await db.execute(stmt)
            installment_num = res.scalar() + 1
            
            collection = Collection(
                student_id=commitment.student_id,
                commitment_id=commitment.id,
                payment_id=payment.id,
                course_id=commitment.course_id,
                amount=float(payment.amount),
                due_date=datetime.now().date(),
                charge_day=commitment.charge_day,
                installment_number=installment_num,
                total_installments=commitment.installments,
                status="נגבה",
                collected_at=func.now(),
                nedarim_donation_id=donation_id,
                nedarim_subscription_id=subscription_id,
                reference=f"SUB:{subscription_id} | DON:{donation_id}",
            )
            db.add(collection)
            
            # Update student total_paid
            stmt = select(Student).where(Student.id == commitment.student_id)
            res = await db.execute(stmt)
            student = res.scalar_one_or_none()
            if student:
                student.total_paid = (student.total_paid or 0) + float(payment.amount)
                if student.total_price and student.total_paid >= student.total_price:
                    student.payment_status = "שולם"
            
            await db.flush()
            result["processed"] = True
            result["payment_id"] = payment.id
            result["collection_id"] = collection.id
            result["commitment_id"] = commitment.id
            result["installment_number"] = installment_num
        
        elif event_type == "subscription.failed":
            # Create a failed collection record
            from db.models import Collection
            
            # Calculate installment number
            stmt = select(func.count(Collection.id)).where(
                Collection.commitment_id == commitment.id
            )
            res = await db.execute(stmt)
            installment_num = res.scalar() + 1
            
            collection = Collection(
                student_id=commitment.student_id,
                commitment_id=commitment.id,
                course_id=commitment.course_id,
                amount=float(amount or commitment.monthly_amount),
                due_date=datetime.now().date(),
                charge_day=commitment.charge_day,
                installment_number=installment_num,
                total_installments=commitment.installments,
                status="נכשל",
                attempts=1,
                nedarim_subscription_id=subscription_id,
                notes=metadata.get("error_message", "Charge failed"),
            )
            db.add(collection)
            await db.flush()
            
            # Log the failure - could trigger notification
            logger.warning(f"Subscription charge failed for commitment {commitment.id}: {metadata}")
            result["processed"] = True
            result["commitment_id"] = commitment.id
            result["collection_id"] = collection.id
            result["error"] = metadata.get("error_message", "Charge failed")
    
    else:
        logger.warning(f"Unknown Nedarim event type: {event_type}")
        return {"error": f"Unknown event type: {event_type}", "processed": False}
    
    return result
