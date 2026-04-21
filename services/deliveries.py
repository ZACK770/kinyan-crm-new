"""
Delivery Service - שירות ניהול משלומים
מנהל את המשלומים ללידים שהפכו ל"נסלק"
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from db.models import Delivery, Lead
from services.audit_logs import log_action


async def get_pending_deliveries(session: AsyncSession) -> List[Delivery]:
    """
    מחזיר רשימה של משלומים שעדיין לא נשלחו (is_sent=False)
    """
    result = await session.execute(
        select(Delivery)
        .where(Delivery.is_sent == False)
        .order_by(Delivery.created_at.desc())
    )
    return list(result.scalars().all())


async def get_delivery_history(session: AsyncSession) -> List[Delivery]:
    """
    מחזיר רשימה של כל המשלומים שכבר נשלחו (is_sent=True) - היסטוריה
    """
    result = await session.execute(
        select(Delivery)
        .where(Delivery.is_sent == True)
        .order_by(Delivery.sent_date.desc())
    )
    return list(result.scalars().all())


async def create_delivery_from_lead(
    session: AsyncSession,
    lead: Lead
) -> Delivery:
    """
    יוצר רשומת משלוח חדשה מליד שהפך ל"נסלק"
    מעתיק את פרטי הלקוח מהליד
    """
    delivery = Delivery(
        lead_id=lead.id,
        full_name=lead.full_name,
        address=lead.address or lead.shipping_full_address,
        city=lead.city or lead.shipping_city,
        phone=lead.shipping_phone if lead.shipping_phone else lead.phone,
        email=lead.email,
        is_sent=False,
        sent_date=None
    )
    session.add(delivery)
    await session.flush()
    return delivery


async def mark_delivery_sent(
    session: AsyncSession,
    delivery_id: int,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    מסמן משלוך כנשלח ומעדכן את תאריך השליחה
    """
    result = await session.execute(
        select(Delivery).where(Delivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    
    if not delivery:
        return {"success": False, "error": "Delivery not found"}
    
    delivery.is_sent = True
    delivery.sent_date = datetime.now(timezone.utc)
    
    # סימון shipping_details_complete ב-Lead כ-V
    lead_result = await session.execute(
        select(Lead).where(Lead.id == delivery.lead_id)
    )
    lead = lead_result.scalar_one_or_none()
    
    if lead:
        lead.shipping_details_complete = True
        await log_action(
            session,
            user_id,
            "delivery_sent",
            f"משלוך #{delivery_id} סומן כנשלח עבור ליד #{delivery.lead_id}",
            lead_id=delivery.lead_id
        )
    
    await session.flush()
    return {"success": True, "delivery": delivery}


async def get_leads_needing_delivery(session: AsyncSession) -> List[Lead]:
    """
    מחזיר רשימה של לידים עם סטטוס "נסלק" שעדיין אין להם רשומת משלוח
    """
    result = await session.execute(
        select(Lead)
        .where(Lead.status == "נסלק")
        .where(~Lead.id.in_(
            select(Delivery.lead_id).where(Delivery.lead_id == Lead.id)
        ))
        .order_by(Lead.conversion_date.desc())
    )
    return list(result.scalars().all())


async def auto_create_deliveries_for_sold_leads(session: AsyncSession) -> Dict[str, Any]:
    """
    יוצר אוטומטית רשומות משלוח עבור לידים שהפכו ל"נסלק" ועדיין אין להם משלוח
    """
    leads_needing_delivery = await get_leads_needing_delivery(session)
    created_count = 0
    
    for lead in leads_needing_delivery:
        await create_delivery_from_lead(session, lead)
        created_count += 1
    
    await session.flush()
    
    return {
        "success": True,
        "created_count": created_count,
        "leads_processed": len(leads_needing_delivery)
    }


async def update_delivery(
    session: AsyncSession,
    delivery_id: int,
    full_name: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    מעדכן פרטי משלוח
    """
    result = await session.execute(
        select(Delivery).where(Delivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    
    if not delivery:
        return {"success": False, "error": "Delivery not found"}
    
    if full_name is not None:
        delivery.full_name = full_name
    if address is not None:
        delivery.address = address
    if city is not None:
        delivery.city = city
    if phone is not None:
        delivery.phone = phone
    if email is not None:
        delivery.email = email
    if notes is not None:
        delivery.notes = notes
    
    await log_action(
        session,
        user_id,
        "delivery_updated",
        f"פרטי משלוך #{delivery_id} עודכנו",
        lead_id=delivery.lead_id
    )
    
    await session.flush()
    return {"success": True, "delivery": delivery}
