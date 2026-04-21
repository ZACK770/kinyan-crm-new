from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db, models
from typing import Optional
import logging

from services.email_service import send_email
import os

router = APIRouter(prefix="/api/test-netfree", tags=["test-netfree"])
logger = logging.getLogger(__name__)

THANK_YOU_HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>תודה רבה</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; background: #f4f4f9; }
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: inline-block; }
        h1 { color: #2563eb; }
    </style>
</head>
<body>
    <div class="card">
        <h1>הפעולה הושלמה בהצלחה</h1>
        <p>תודה רבה על שיתוף הפעולה.</p>
    </div>
</body>
</html>
"""

@router.get("/direct", response_class=HTMLResponse)
async def test_direct(
    request: Request,
    test_type: str = Query(...),
    user_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """URL 1: Direct CRM Endpoint"""
    # Log request
    log = models.TestLog(
        test_type=test_type,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(log)
    await db.commit()
    
    return THANK_YOU_HTML

@router.get("/pixel")
async def test_pixel(
    request: Request,
    user_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Tracking Pixel Endpoint"""
    log = models.TestLog(
        test_type="pixel",
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(log)
    await db.commit()
    
    # Return 1x1 transparent GIF
    from fastapi.responses import Response
    pixel_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return Response(content=pixel_data, media_type="image/gif")

@router.get("/results")
async def get_test_results(
    db: AsyncSession = Depends(get_db)
):
    """Endpoint to retrieve results (for admin)"""
    from sqlalchemy import select
    stmt = select(models.TestLog).order_by(models.TestLog.created_at.desc())
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "type": l.test_type,
            "user_id": l.user_id,
            "ip": l.ip_address,
            "ua": l.user_agent,
            "time": l.created_at.isoformat()
        }
        for l in logs
    ]

@router.post("/send-test-email")
async def send_test_netfree_email(
    user_id: int = Query(...),
    email: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Send the test email with 4 buttons to a specific email address"""
    try:
        # Read the template
        template_path = "docs/netfree_test_email.html"
        if not os.path.exists(template_path):
            return {"success": False, "error": "Template file not found"}
            
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        # Replace placeholder
        html_content = html_content.replace("{{user_id}}", str(user_id))
        
        # Send via email service
        success = await send_email(
            to_email=email,
            subject="בדיקת מערכת אישור תקנון - קניין הוראה",
            html_body=html_content
        )
        
        if success:
            return {"success": True, "message": f"Email sent to {email}"}
        else:
            return {"success": False, "error": "Failed to send email"}
            
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        return {"success": False, "error": str(e)}
