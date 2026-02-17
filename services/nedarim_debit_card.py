"""
Nedarim Plus DebitCard API Service
Direct credit card charging via Nedarim Plus
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import settings
from db.models import Lead, Payment, Course, Commitment, HistoryEntry

logger = logging.getLogger(__name__)


class NedarimDebitCardError(Exception):
    """Exception for Nedarim DebitCard API errors"""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class NedarimDebitCardService:
    """Service for direct credit card charging via Nedarim Plus DebitCard API"""
    
    def __init__(self):
        self.base_url = "https://www.matara.pro/nedarimplus/V6/Files/WebServices"
        self.debit_card_endpoint = "/DebitCard.aspx"
        self.debit_keva_endpoint = "/DebitKeva.aspx"
        self.mosad_id = settings.NEDARIM_MOSAD_ID
        self.api_password = getattr(settings, 'NEDARIM_API_PASSWORD', settings.NEDARIM_API_KEY)
        
        if not self.mosad_id or not self.api_password:
            raise ValueError(
                "Nedarim Plus credentials not configured. "
                "Please set NEDARIM_MOSAD_ID and NEDARIM_API_PASSWORD in environment variables."
            )
    
    async def charge_card(
        self,
        client_name: str,
        card_number: str,
        expiry: str,
        cvv: str,
        amount: float,
        installments: int = 1,
        phone: Optional[str] = None,
        comments: Optional[str] = None,
        payment_type: str = "RAGIL",  # RAGIL (regular) or HK (standing order)
        groupe: Optional[str] = None,
        zeout: Optional[str] = None,
        day: Optional[int] = None,
        adresse: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Charge a credit card directly via Nedarim Plus
        
        Routes to the correct endpoint:
        - RAGIL → DebitCard.aspx (regular payment, Amount=total, Tashloumim=split count)
        - HK → DebitKeva.aspx (standing order, Amount=monthly, Tashloumim=months)
        
        Args:
            client_name: Full name of the client
            card_number: Credit card number (13-16 digits)
            expiry: Card expiry in MMYY format (4 digits)
            cvv: Card CVV (3-4 digits)
            amount: For RAGIL: total amount. For HK: monthly amount.
            installments: For RAGIL: split count (1-36). For HK: number of months.
            phone: Client phone (optional)
            comments: Transaction comments (optional)
            payment_type: RAGIL (regular one-time) or HK (standing order/הוראת קבע)
            groupe: Course name (optional)
            zeout: ID number (optional)
            day: Day of month for HK charge (optional, defaults to today)
            adresse: Client address (optional, for RAGIL)
        
        Returns:
            Dict with transaction details
        
        Raises:
            NedarimDebitCardError: If the transaction fails
        """
        # Validate inputs
        card_number_clean = card_number.replace(' ', '').replace('-', '')
        if not card_number_clean.isdigit() or len(card_number_clean) < 13 or len(card_number_clean) > 16:
            raise NedarimDebitCardError("Invalid card number (must be 13-16 digits)")
        
        expiry_clean = expiry.replace('/', '')
        if not expiry_clean.isdigit() or len(expiry_clean) != 4:
            raise NedarimDebitCardError("Invalid expiry date (must be MMYY - 4 digits)")
        
        if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
            raise NedarimDebitCardError("Invalid CVV (must be 3-4 digits)")
        
        if amount <= 0:
            raise NedarimDebitCardError("Amount must be positive")
        
        if payment_type != 'HK' and (installments < 1 or installments > 36):
            raise NedarimDebitCardError("Installments must be between 1 and 36")
        
        # Route to correct endpoint based on payment type
        if payment_type == 'HK':
            return await self._charge_keva(client_name, card_number_clean, expiry_clean, cvv, amount, installments, phone, comments, groupe, zeout, day)
        else:
            return await self._charge_ragil(client_name, card_number_clean, expiry_clean, cvv, amount, installments, phone, comments, groupe, zeout, adresse)
        
    async def _charge_ragil(
        self, client_name, card_number, expiry, cvv, amount, installments,
        phone, comments, groupe, zeout, adresse
    ) -> Dict[str, Any]:
        """RAGIL payment via DebitCard.aspx — Amount=total, Tashloumim=split count"""
        payload = {
            'Mosad': self.mosad_id,
            'ClientName': client_name,
            'Adresse': adresse or '',
            'Phone': phone or '',
            'ClientId': '',
            'CardNumber': card_number,
            'Tokef': expiry,
            'CVV': cvv,
            'Amount': amount,
            'Tashloumim': str(installments),
            'Currency': '1',
            'Groupe': groupe or '',
            'Avour': comments or 'תשלום CRM',
            'Token': '',
            'Zeout': zeout or '',
            'MasofId': 'Online',
        }
        url = f"{self.base_url}{self.debit_card_endpoint}"
        result = await self._send_request(url, payload, 'RAGIL')
        return {
            'success': True,
            'transaction_id': result.get('TransactionId'),
            'confirmation': result.get('Confirmation'),
            'amount': float(result.get('Amount', amount)),
            'transaction_time': result.get('TransactionTime'),
            'card_last_4': result.get('LastNum'),
            'receipt_number': result.get('ReceiptDocNum'),
            'installments': installments,
            'message': f'Transaction successful. Confirmation: {result.get("Confirmation")}'
        }

    async def _charge_keva(
        self, client_name, card_number, expiry, cvv, monthly_amount, months,
        phone, comments, groupe, zeout, day
    ) -> Dict[str, Any]:
        """HK (standing order) via DebitKeva.aspx — Amount=monthly, Tashloumim=months"""
        from datetime import datetime as dt
        payload = {
            'MosadId': self.mosad_id,
            'ClientName': client_name,
            'Street': '',
            'City': '',
            'mail': '',
            'Phone': phone or '',
            'ClientId': '',
            'CardNumber': card_number,
            'Tokef': expiry,
            'Amount': monthly_amount,
            'Tashloumim': str(months or 1),
            'Groupe': groupe or '',
            'Avour': comments or 'תשלום CRM',
            'Token': '',
            'CVV': cvv,
            'Day': str(day or dt.now().day),
            'Zeout': zeout or '',
            'Currency': '1',
            'ChoosedCard': '',
            'MasofId': 'Online',
        }
        
        url = f"{self.base_url}{self.debit_keva_endpoint}"
        result = await self._send_request(url, payload, 'HK')
        return {
            'success': True,
            'keva_id': result.get('KevaId'),
            'transaction_id': result.get('TransactionId'),
            'confirmation': result.get('Confirmation'),
            'amount': float(result.get('Amount', monthly_amount)),
            'monthly_amount': monthly_amount,
            'months': months,
            'total_amount': monthly_amount * (months or 1),
            'transaction_time': result.get('TransactionTime'),
            'card_last_4': result.get('LastNum'),
            'receipt_number': result.get('ReceiptDocNum'),
            'installments': months,
            'message': f'הוראת קבע נוצרה בהצלחה. KevaId: {result.get("KevaId")}'
        }

    async def _send_request(self, url: str, payload: dict, payment_type: str) -> dict:
        """Send request to Nedarim and handle response"""
        # Log (mask sensitive data)
        safe_payload = {k: v for k, v in payload.items()}
        if 'CardNumber' in safe_payload:
            safe_payload['CardNumber'] = f"****{safe_payload['CardNumber'][-4:]}"
        if 'CVV' in safe_payload:
            safe_payload['CVV'] = '***'
        if 'ApiPassword' in safe_payload:
            safe_payload['ApiPassword'] = '***'
        logger.info(f"=== NEDARIM {payment_type} REQUEST ===")
        logger.info(f"URL: {url}")
        logger.info(f"Full payload: {json.dumps(safe_payload, ensure_ascii=False)}")
        print(f"\n=== NEDARIM {payment_type} REQUEST ===")
        print(f"URL: {url}")
        print(f"Full payload: {json.dumps(safe_payload, ensure_ascii=False)}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    data=payload,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                logger.info(f"=== NEDARIM {payment_type} RESPONSE ===")
                logger.info(f"Full response: {json.dumps(result, ensure_ascii=False)}")
                print(f"\n=== NEDARIM {payment_type} RESPONSE ===")
                print(f"Full response: {json.dumps(result, ensure_ascii=False)}")
                
                if result.get('Status') == 'OK':
                    logger.info(f"Transaction successful")
                    return result
                else:
                    error_msg = result.get('Message', 'Transaction failed')
                    error_details = result.get('BackMessage', '')
                    logger.error(f"Transaction failed: {error_msg} - {error_details}")
                    raise NedarimDebitCardError(
                        message=error_msg,
                        details=error_details
                    )
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during transaction: {e.response.status_code}")
            raise NedarimDebitCardError(f"HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Connection error during transaction: {str(e)}")
            raise NedarimDebitCardError(f"Connection error: {str(e)}")
        except NedarimDebitCardError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during transaction: {str(e)}")
            raise NedarimDebitCardError(f"Unexpected error: {str(e)}")


async def charge_lead_card(
    db: AsyncSession,
    lead_id: int,
    card_number: str,
    expiry: str,
    cvv: str,
    amount: Optional[float] = None,
    installments: Optional[int] = None,
    payment_type: str = "RAGIL",
    comments: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Charge a lead's credit card and create payment record
    
    Args:
        db: Database session
        lead_id: Lead ID
        card_number: Credit card number
        expiry: Card expiry (MMYY)
        cvv: Card CVV
        amount: Amount to charge (if None, uses lead's selected_price)
        installments: Number of installments (if None, uses lead's selected_payments_count)
        payment_type: RAGIL (regular) or HK (standing order)
        comments: Transaction comments
    
    Returns:
        Dict with transaction details and payment_id
    """
    # Get lead
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    
    # Use lead's selected values if not provided
    if amount is None:
        amount = float(lead.selected_price) if lead.selected_price else 0
    if installments is None:
        installments = lead.selected_payments_count or 1
    
    if amount <= 0:
        raise ValueError("Amount must be specified or lead must have selected_price")
    
    # Create service and charge card
    service = NedarimDebitCardService()
    
    # Get course name for Groupe
    groupe = None
    if lead.selected_course_id:
        course_stmt = select(Course).where(Course.id == lead.selected_course_id)
        course_result = await db.execute(course_stmt)
        course = course_result.scalar_one_or_none()
        if course:
            groupe = course.name
    
    # Prepare comments with lead info for Avour field
    if not comments:
        comments_parts = []
        if groupe:
            comments_parts.append(f"קורס: {groupe}")
        if lead.full_name:
            comments_parts.append(f"תלמיד: {lead.full_name}")
        comments = " | ".join(comments_parts) if comments_parts else f"ליד #{lead_id}"
    
    # Build address from lead data
    adresse_parts = []
    if lead.address:
        adresse_parts.append(lead.address)
    if lead.city:
        adresse_parts.append(lead.city)
    adresse = ", ".join(adresse_parts) if adresse_parts else ""
    
    logger.info(f"=== DIRECT CHARGE REQUEST from frontend ===")
    logger.info(f"lead_id={lead_id}, payment_type={payment_type}, amount={amount}, installments={installments}")
    
    is_hk = payment_type == 'HK'
    
    try:
        result = await service.charge_card(
            client_name=lead.full_name,
            card_number=card_number,
            expiry=expiry,
            cvv=cvv,
            amount=amount,
            installments=installments,
            phone=lead.phone,
            payment_type=payment_type,
            comments=comments,
            groupe=groupe,
            zeout=getattr(lead, 'id_number', None),
            day=lead.selected_payment_day,
            adresse=adresse,
        )
        
        if is_hk:
            # HK: DebitKeva succeeded = standing order CREATED (not yet charged)
            # Amount = monthly amount, Tashloumim = number of months
            # Don't count as "שולם" — the actual charges come via keva webhooks
            tx_type = "נדרים פלוס - הקמת הוראת קבע"
            payment = Payment(
                lead_id=lead_id,
                course_id=lead.selected_course_id,
                amount=amount,  # monthly amount
                currency="ILS",
                payment_method="כרטיס אשראי",
                installments=installments,
                transaction_type=tx_type,
                status="הוקם",  # NOT שולם — HK setup only
                payment_date=datetime.now().date(),
                nedarim_donation_id=result.get('transaction_id'),
                nedarim_transaction_id=result.get('keva_id'),
                reference=f"KevaId: {result.get('keva_id')}",
            )
        else:
            # RAGIL: DebitCard succeeded = actual charge completed
            tx_type = "נדרים פלוס - סליקה ישירה"
            payment = Payment(
                lead_id=lead_id,
                course_id=lead.selected_course_id,
                amount=result['amount'],  # total amount charged
                currency="ILS",
                payment_method="כרטיס אשראי",
                installments=installments,
                transaction_type=tx_type,
                status="שולם",
                payment_date=datetime.now().date(),
                nedarim_donation_id=result.get('transaction_id'),
                nedarim_transaction_id=result.get('confirmation'),
                reference=f"{result.get('confirmation')} | {result.get('card_last_4', '')}",
            )
        
        db.add(payment)
        await db.flush()
        
        # Update lead — for RAGIL mark as charged, for HK mark as HK setup
        if is_hk:
            # HK setup — don't mark first_payment yet (actual charge hasn't happened)
            if lead.status not in ["תלמיד", "נסלק"]:
                lead.status = "הוקם הו\"ק"
            
            # Create Commitment record so keva webhook can find it by KevaId
            keva_id = result.get('keva_id')
            if keva_id:
                commitment = Commitment(
                    student_id=0,  # Will be linked when lead converts to student
                    course_id=lead.selected_course_id,
                    monthly_amount=amount,
                    total_amount=amount * installments,
                    installments=installments,
                    charge_day=lead.selected_payment_day,
                    payment_method="כרטיס אשראי - הוראת קבע",
                    status="פעיל",
                    nedarim_subscription_id=str(keva_id),
                    reference=f"KevaId: {keva_id}",
                )
                # Commitment requires student_id (NOT NULL) — we'll set it to 0 temporarily
                # and the keva webhook will update it when the first charge comes in
                # Actually, student_id is required. Let's check if lead already has a student
                if lead.student_id:
                    commitment.student_id = lead.student_id
                    db.add(commitment)
                    await db.flush()
                    payment.commitment_id = commitment.id
                    logger.info(f"Created commitment {commitment.id} for KevaId {keva_id}")
                else:
                    # No student yet — commitment will be created by keva webhook when first charge arrives
                    logger.info(f"HK setup for lead {lead_id} — commitment will be created when student exists (KevaId={keva_id})")
        else:
            # RAGIL — actual charge happened
            lead.first_payment = True
            lead.first_payment_id = payment.id
            lead.status = "נסלק"
        
        # Create HistoryEntry
        history_entry = HistoryEntry(
            lead_id=lead_id,
            action_type="הקמת הוראת קבע" if is_hk else "סליקה ישירה",
            description=(
                f"הוראת קבע הוקמה בהצלחה: ₪{amount} × {installments} חודשים (KevaId: {result.get('keva_id')})"
                if is_hk else
                f"סליקה ישירה בוצעה בהצלחה: ₪{result['amount']} (אישור: {result.get('confirmation')})"
            ),
            extra_data={
                "payment_id": payment.id,
                "payment_type": payment_type,
                "amount": float(amount),
                "installments": installments,
                "confirmation": result.get('confirmation'),
                "keva_id": result.get('keva_id'),
                "transaction_id": result.get('transaction_id'),
            }
        )
        db.add(history_entry)
        
        await db.flush()
        
        logger.info(f"Payment record created for lead {lead_id}: {payment.id} (type={payment_type})")
        
        return {
            **result,
            'payment_id': payment.id,
            'lead_id': lead_id,
            'is_hk_setup': is_hk,
        }
    
    except NedarimDebitCardError as e:
        # Create failed payment record
        payment = Payment(
            lead_id=lead_id,
            course_id=lead.selected_course_id,
            amount=amount,
            currency="ILS",
            payment_method="כרטיס אשראי",
            installments=installments,
            transaction_type=f"נדרים פלוס - {'הקמת הוראת קבע' if is_hk else 'סליקה ישירה'}",
            status="נכשל",
            reference=f"Error: {e.message}",
        )
        db.add(payment)
        await db.flush()
        
        logger.error(f"Payment failed for lead {lead_id}: {e.message}")
        raise
