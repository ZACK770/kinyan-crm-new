"""
Email service — async SMTP for password reset and notifications.
Available system-wide via: from services.email_service import send_email, send_password_reset_email
"""
import logging
from typing import Optional

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from db import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> bool:
    """
    Send an email via SMTP.
    Returns True on success, False on failure (logs the error).
    """
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured — email not sent to %s", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_PORT == 465,
            start_tls=settings.SMTP_PORT == 587,
        )
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False


async def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """Send a password reset email with a clickable link."""
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"

    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">איפוס סיסמה — Kinyan CRM</h2>
        <p>קיבלנו בקשה לאיפוס הסיסמה שלך.</p>
        <p>לחץ על הכפתור למטה כדי לאפס את הסיסמה:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background-color: #2563eb; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 6px; font-size: 16px;">
                איפוס סיסמה
            </a>
        </div>
        <p style="color: #666; font-size: 14px;">
            הקישור תקף ל-30 דקות בלבד.<br>
            אם לא ביקשת איפוס סיסמה, ניתן להתעלם מהודעה זו.
        </p>
        <hr style="border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">Kinyan CRM — קניין הוראה</p>
    </div>
    """

    text_body = f"איפוס סיסמה — Kinyan CRM\n\nלאיפוס סיסמה היכנס לקישור:\n{reset_url}\n\nהקישור תקף ל-30 דקות."

    return await send_email(to_email, "איפוס סיסמה — Kinyan CRM", html_body, text_body)


async def send_welcome_email(to_email: str, full_name: str) -> bool:
    """Send a welcome email to newly registered users."""
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">ברוכים הבאים ל-Kinyan CRM!</h2>
        <p>שלום {full_name},</p>
        <p>ההרשמה בוצעה בהצלחה.</p>
        <p>מנהל המערכת יגדיר לך הרשאות בקרוב, ואז תוכל להיכנס למערכת המלאה.</p>
        <hr style="border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">Kinyan CRM — קניין הוראה</p>
    </div>
    """
    return await send_email(to_email, "ברוכים הבאים — Kinyan CRM", html_body)


async def send_lead_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
) -> bool:
    """
    Send an email to a lead.
    Reply-To is set to the system email so replies come back to us.
    Wraps the body in a branded RTL template.
    """
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        {body_html}
        <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="color: #999; font-size: 12px;">קניין הוראה — מחלקת רישום</p>
    </div>
    """

    return await send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=body_text,
        reply_to=settings.SMTP_FROM_EMAIL,
    )
