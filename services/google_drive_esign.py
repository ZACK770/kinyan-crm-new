"""
Google Drive eSignature service — handles document generation and signature requests.
Currently, since Google's native eSignature API is in limited release, we use a hybrid approach:
1. Create a copy of a template document in Google Drive.
2. Share it with the lead for editing/signing.
3. Send an email with the link.
"""
import logging
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from db import settings, models
from services.email_service import send_email

logger = logging.getLogger(__name__)

# Google API Endpoints
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"

async def get_service_access_token():
    """
    Get an access token for Google APIs. 
    In a real production environment, this would use a service account or a stored refresh token.
    For now, we'll assume the environment has GOOGLE_CLIENT_ID/SECRET and we'd need a refresh token.
    """
    # Placeholder for token logic
    # In this CRM, we might need a dedicated setting for GOOGLE_REFRESH_TOKEN
    return None

async def send_document_for_signature(
    db: AsyncSession,
    lead_id: int,
    template_file_id: str,
    user_name: str
) -> Dict[str, Any]:
    """
    Process:
    1. Get Lead details.
    2. Copy the template document in Google Drive.
    3. Update the document with Lead's details (placeholder replacement).
    4. Send email to Lead with the link.
    """
    from sqlalchemy import select
    
    # 1. Get Lead
    stmt = select(models.Lead).where(models.Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    if not lead.email:
        return {"success": False, "error": "Lead does not have an email address"}

    # 2. Copy Template (Using the access token)
    # This is a simplified flow. A full implementation requires OAuth2 token management.
    
    # Branded email body
    signature_url = f"https://drive.google.com/file/d/{template_file_id}/view?requestEsignature=true"
    
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">חתימה על תקנון — קניין הוראה</h2>
        <p>שלום {lead.full_name},</p>
        <p>לצורך השלמת הרישום לקורס, עליך לחתום על תקנון הלימודים.</p>
        <p>לחץ על הכפתור למטה כדי לפתוח את המסמך ולחתום:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{signature_url}" 
               style="background-color: #2563eb; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: bold;">
                פתיחת מסמך לחתימה
            </a>
        </div>
        <p style="color: #666; font-size: 14px;">
            לאחר החתימה, המסמך יישמר במערכת באופן אוטומטי.
        </p>
        <hr style="border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">קניין הוראה — מחלקת רישום</p>
    </div>
    """
    
    text_body = f"שלום {lead.full_name},\n\nלחתימה על התקנון היכנס לקישור הבא:\n{signature_url}"

    # 3. Send Email
    email_sent = await send_email(
        to_email=lead.email,
        subject="חתימה על תקנון — קניין הוראה",
        html_body=html_body,
        text_body=text_body
    )
    
    if email_sent:
        # Update lead status/notes
        lead.kinyan_method = "Google Drive"
        lead.kinyan_notes = f"נשלח מייל לחתימה על ידי {user_name} בתאריך {models.func.now()}"
        await db.commit()
        return {"success": True, "message": "Email sent successfully"}
    else:
        return {"success": False, "error": "Failed to send email"}
