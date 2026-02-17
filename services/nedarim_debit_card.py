"""
Nedarim Plus DebitCard API Service
Direct credit card charging via Nedarim Plus
"""
import logging
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import settings
from db.models import Lead, Payment, Salesperson, Course, Commitment

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
        email: Optional[str] = None,
        phone: Optional[str] = None,
        comments: Optional[str] = None,
        payment_type: str = "RAGIL",  # RAGIL (regular) or HK (standing order)
        groupe: Optional[str] = None,
        param1: Optional[str] = None,
        param2: Optional[str] = None,
        callback_url: Optional[str] = None,
        zeout: Optional[str] = None,
        day: Optional[int] = None,
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
            email: Client email (optional)
            phone: Client phone (optional)
            comments: Transaction comments (optional)
            payment_type: RAGIL (regular one-time) or HK (standing order/הוראת קבע)
            zeout: ID number for HK (optional)
            day: Day of month for HK charge (optional, defaults to today)
        
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
            return await self._charge_keva(client_name, card_number_clean, expiry_clean, cvv, amount, installments, email, phone, comments, groupe, zeout, day)
        else:
            return await self._charge_ragil(client_name, card_number_clean, expiry_clean, cvv, amount, installments, email, phone, comments, groupe, param1, param2, callback_url)
        
    async def _charge_ragil(
        self, client_name, card_number, expiry, cvv, amount, installments,
        email, phone, comments, groupe, param1, param2, callback_url
    ) -> Dict[str, Any]:
        """RAGIL payment via DebitCard.aspx — Amount=total, Tashloumim=split count"""
        payload = {
            'Mosad': self.mosad_id,
            'ApiPassword': self.api_password,
            'ClientName': client_name,
            'Mail': email or '',
            'Phone': phone or '',
            'CardNumber': card_number,
            'Tokef': expiry,
            'CVV': cvv,
            'Amount': f"{amount:.2f}",
            'Currency': '1',
            'PaymentType': 'RAGIL',
            'Avour': comments or 'תשלום CRM',
            'Groupe': groupe or '',
            'Param1': param1 or '',
            'Param2': param2 or '',
            'CallBack': callback_url or '',
            'Tashloumim': str(installments),
            'AjaxId': str(int(time.time() * 1000)),
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
        email, phone, comments, groupe, zeout, day
    ) -> Dict[str, Any]:
        """HK (standing order) via DebitKeva.aspx — Amount=monthly, Tashloumim=months"""
        from datetime import datetime as dt
        payload = {
            'MosadId': self.mosad_id,
            'ClientName': client_name,
            'Street': '',
            'City': '',
            'Mail': email or '',
            'Phone': phone or '',
            'CardNumber': card_number,
            'Tokef': expiry,
            'CVV': cvv,
            'Amount': f"{monthly_amount:.2f}",
            'Currency': '1',
            'Groupe': groupe or '',
            'Avour': comments or 'תשלום CRM',
            'Zeout': zeout or '',
            'Day': str(day or dt.now().day),
            'ChoosedCard': '',
            'AjaxId': str(int(time.time() * 1000)),
        }
        # IMPORTANT: Tashloumim for Keva = number of months to charge
        if months and months > 1:
            payload['Tashloumim'] = str(months)
        
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
                    headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
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
    
    # Get salesperson name for Param1
    salesperson_name = None
    if lead.salesperson_id:
        sp_stmt = select(Salesperson).where(Salesperson.id == lead.salesperson_id)
        sp_result = await db.execute(sp_stmt)
        sp = sp_result.scalar_one_or_none()
        if sp:
            salesperson_name = sp.name
    
    # Prepare detailed comments with lead info
    if not comments:
        comments_parts = [f"ליד #{lead_id}"]
        if lead.full_name:
            comments_parts.append(lead.full_name)
        if lead.phone:
            comments_parts.append(f"טל: {lead.phone}")
        comments = " | ".join(comments_parts)
    
    # Build callback URL for Nedarim to notify us when payment is processed
    from db import settings
    base_url = getattr(settings, 'BASE_URL', 'https://kinyan-crm-new-1.onrender.com')
    callback_url = f"{base_url}/webhooks/nedarim-debitcard"
    
    logger.info(f"=== DIRECT CHARGE REQUEST from frontend ===")
    logger.info(f"lead_id={lead_id}, payment_type={payment_type}, amount={amount}, installments={installments}")
    
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
            comments=comments,
            groupe=groupe,
            param1=salesperson_name,
            param2=str(lead_id),  # Pass lead_id in Param2 for callback identification
            callback_url=callback_url,
        )
        
        is_hk = payment_type == 'HK'
        
        if is_hk:
            # HK: amount is monthly, total = monthly * months
            payment_amount = result.get('monthly_amount', amount)
            total = result.get('total_amount', amount * installments)
            tx_type = "נדרים פלוס - הוראת קבע"
        else:
            # RAGIL: amount is total
            payment_amount = result['amount']
            total = result['amount']
            tx_type = "נדרים פלוס - סליקה ישירה"
        
        # Create payment record
        payment = Payment(
            lead_id=lead_id,
            course_id=lead.selected_course_id,
            amount=payment_amount,
            currency="ILS",
            payment_method="כרטיס אשראי",
            installments=installments,
            transaction_type=tx_type,
            status="שולם",
            payment_date=datetime.now().date(),
            nedarim_donation_id=result.get('transaction_id'),
            nedarim_transaction_id=result.get('confirmation') or result.get('keva_id'),
            reference=result.get('confirmation') or result.get('keva_id'),
        )
        db.add(payment)
        await db.flush()
        
        # Update lead
        lead.first_payment = True
        lead.first_payment_id = payment.id
        lead.status = "נסלק"
        
        await db.flush()
        
        logger.info(f"Payment record created for lead {lead_id}: {payment.id} (type={payment_type})")
        
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
            transaction_type=f"נדרים פלוס - {'הוראת קבע' if payment_type == 'HK' else 'סליקה ישירה'}",
            status="נכשל",
            reference=f"Error: {e.message}",
        )
        db.add(payment)
        await db.flush()
        
        logger.error(f"Payment failed for lead {lead_id}: {e.message}")
        raise
