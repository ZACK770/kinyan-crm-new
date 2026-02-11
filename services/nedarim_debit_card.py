"""
Nedarim Plus DebitCard API Service
Direct credit card charging via Nedarim Plus
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import settings
from db.models import Lead, Payment

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
        self.endpoint = "/DebitCard.aspx"
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
        email: Optional[str] = None,
        phone: Optional[str] = None,
        comments: Optional[str] = None,
        payment_type: str = "RAGIL",  # RAGIL (regular) or HK (standing order)
    ) -> Dict[str, Any]:
        """
        Charge a credit card directly via Nedarim Plus
        
        Args:
            client_name: Full name of the client
            card_number: Credit card number (13-16 digits)
            expiry: Card expiry in MMYY format (4 digits)
            cvv: Card CVV (3-4 digits)
            amount: Amount to charge in ILS
            installments: Number of installments (1-36)
            email: Client email (optional)
            phone: Client phone (optional)
            comments: Transaction comments (optional)
            payment_type: RAGIL (regular one-time) or HK (standing order/הוראת קבע)
        
        Returns:
            Dict with transaction details:
            {
                'success': bool,
                'transaction_id': str,
                'confirmation': str,
                'amount': float,
                'transaction_time': str,
                'card_last_4': str,
                'receipt_number': str,
                'message': str
            }
        
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
        
        if installments < 1 or installments > 36:
            raise NedarimDebitCardError("Installments must be between 1 and 36")
        
        # Prepare payload
        payload = {
            'Mosad': self.mosad_id,
            'ApiPassword': self.api_password,
            'ClientName': client_name,
            'Mail': email or '',
            'Phone': phone or '',
            'CardNumber': card_number_clean,
            'Tokef': expiry_clean,
            'CVV': cvv,
            'Amount': f"{amount:.2f}",
            'Currency': '1',  # 1 = ILS, 2 = USD
            'PaymentType': payment_type,  # RAGIL or HK
            'Avour': comments or 'תשלום CRM',
            'AjaxId': str(int(time.time() * 1000))
        }
        
        # Handle Tashloumim based on payment type
        # For HK (standing order): empty = unlimited, number = limited months
        # For RAGIL (regular): number of installments (must be >= 1)
        if payment_type == 'HK':
            # For standing order: if installments is 0 or None, leave empty (unlimited)
            if installments and installments > 0:
                payload['Tashloumim'] = str(installments)
            # else: leave Tashloumim empty for unlimited recurring
        else:
            # For regular payment: must have installments
            payload['Tashloumim'] = str(installments)
        
        logger.info(f"Charging card via Nedarim DebitCard API: {client_name}, Amount: {amount} ILS, Installments: {installments}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}{self.endpoint}",
                    data=payload,
                    headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Check if transaction succeeded
                if result.get('Status') == 'OK':
                    logger.info(f"Transaction successful: {result.get('Confirmation')}")
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
                else:
                    # Transaction failed
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
    
    # Prepare detailed comments with lead info
    if not comments:
        comments_parts = [f"ליד #{lead_id}"]
        if lead.full_name:
            comments_parts.append(lead.full_name)
        if lead.phone:
            comments_parts.append(f"טל: {lead.phone}")
        comments = " | ".join(comments_parts)
    
    try:
        result = await service.charge_card(
            client_name=lead.full_name,
            card_number=card_number,
            expiry=expiry,
            cvv=cvv,
            amount=amount,
            installments=installments,
            email=lead.email,
            phone=lead.phone,
            payment_type=payment_type,
            comments=comments
        )
        
        # Create payment record
        payment = Payment(
            lead_id=lead_id,
            course_id=lead.selected_course_id,
            amount=result['amount'],
            currency="ILS",
            payment_method="כרטיס אשראי",
            installments=installments,
            transaction_type="נדרים פלוס - סליקה ישירה",
            status="שולם",
            payment_date=datetime.now().date(),
            nedarim_donation_id=result['transaction_id'],
            nedarim_transaction_id=result['confirmation'],
            reference=result['confirmation'],
        )
        db.add(payment)
        await db.flush()
        
        # Update lead
        lead.first_payment = True
        lead.first_payment_id = payment.id
        lead.status = "נסלק"
        
        await db.flush()
        
        logger.info(f"Payment record created for lead {lead_id}: {payment.id}")
        
        return {
            **result,
            'payment_id': payment.id,
            'lead_id': lead_id
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
            transaction_type="נדרים פלוס - סליקה ישירה",
            status="נכשל",
            reference=f"Error: {e.message}",
        )
        db.add(payment)
        await db.flush()
        
        logger.error(f"Payment failed for lead {lead_id}: {e.message}")
        raise
