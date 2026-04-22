"""
Tasks email service — email notifications for tasks.
Sends reminder emails for tasks and daily summaries.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SalesTask, Salesperson
from services import email_service


async def send_task_reminder_email(
    db: AsyncSession,
    task_id: int,
) -> bool:
    """
    Send a reminder email for a specific task to the assigned salesperson.
    
    Args:
        db: Database session
        task_id: ID of the task to send reminder for
    
    Returns:
        True if email sent successfully, False otherwise
    """
    print(f"[send_task_reminder_email] Starting for task #{task_id}")
    # Get task with salesperson
    stmt = (
        select(SalesTask)
        .where(SalesTask.id == task_id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        print(f"[task_reminder] Task #{task_id} not found")
        return False
    
    # Check if reminder should be sent
    if not task.send_reminder:
        print(f"[task_reminder] Task #{task_id} has send_reminder=False, skipping")
        return False
    
    if not task.salesperson_id:
        print(f"[task_reminder] Task #{task_id} has no salesperson assigned")
        return False
    
    # Get salesperson
    sp_stmt = select(Salesperson).where(Salesperson.id == task.salesperson_id)
    sp_result = await db.execute(sp_stmt)
    salesperson = sp_result.scalar_one_or_none()
    
    if not salesperson or not salesperson.email:
        print(f"[task_reminder] Salesperson #{task.salesperson_id} not found or has no email")
        return False
    
    # Format due date
    due_date_str = ""
    if task.due_date:
        due_date_str = task.due_date.strftime("%d/%m/%Y %H:%M")
    
    # Build email content
    subject = f"תזכורת משימה: {task.title}"
    
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="color: white; margin: 0; font-size: 24px;">תזכורת משימה</h2>
        </div>
        
        <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0;">
            <h3 style="color: #333; margin-top: 0;">{task.title}</h3>
            
            {f'<p><strong>תיאור:</strong> {task.description}</p>' if task.description else ''}
            
            <p><strong>סטטוס:</strong> {task.status}</p>
            {f'<p><strong>תאריך יעד:</strong> {due_date_str}</p>' if due_date_str else ''}
            
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <p style="margin: 0; color: #856404;">זו תזכורת אוטומטית למשימה שנקבעה לך במערכת CRM.</p>
            </div>
        </div>
        
        <p style="color: #999; font-size: 12px; text-align: center; margin-top: 20px;">
            Kinyan CRM — קניין הוראה
        </p>
    </div>
    """
    
    text_body = f"""תזכורת משימה — Kinyan CRM

{task.title}
{'תיאור: ' + task.description if task.description else ''}
סטטוס: {task.status}
{f'תאריך יעד: {due_date_str}' if due_date_str else ''}

זו תזכורת אוטומטית למשימה שנקבעה לך במערכת CRM.

Kinyan CRM — קניין הוראה"""
    
    success = await email_service.send_email(
        to_email=salesperson.email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )
    
    if success:
        print(f"[task_reminder] Email sent to {salesperson.email} for task #{task_id}")
    else:
        print(f"[task_reminder] Failed to send email to {salesperson.email} for task #{task_id}")
    
    return success


async def send_daily_summary_email(
    db: AsyncSession,
    salesperson_id: int,
) -> bool:
    """
    Send a daily summary email with all tasks for today to a salesperson.
    
    Args:
        db: Database session
        salesperson_id: ID of the salesperson
    
    Returns:
        True if email sent successfully, False otherwise
    """
    # Get salesperson
    sp_stmt = select(Salesperson).where(Salesperson.id == salesperson_id)
    sp_result = await db.execute(sp_stmt)
    salesperson = sp_result.scalar_one_or_none()
    
    if not salesperson or not salesperson.email:
        print(f"[daily_summary] Salesperson #{salesperson_id} not found or has no email")
        return False
    
    # Get today's date range (UTC)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Get tasks for today (due today OR created today and still open)
    stmt = (
        select(SalesTask)
        .where(SalesTask.salesperson_id == salesperson_id)
        .where(
            (SalesTask.due_date >= today_start) & (SalesTask.due_date <= today_end) |
            (SalesTask.created_at >= today_start) & (SalesTask.created_at <= today_end)
        )
        .where(SalesTask.status.in_(["חדש", "בטיפול"]))
    )
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())
    
    # Build email content
    subject = f"סיכום משימות יומי - {now.strftime('%d/%m/%Y')}"
    
    if not tasks:
        # No tasks email
        html_body = f"""
        <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="color: white; margin: 0; font-size: 24px;">סיכום משימות יומי</h2>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0;">
                <div style="text-align: center; padding: 20px;">
                    <p style="font-size: 18px; color: #4CAF50; margin: 0;">אין משימות פתוחות להיום</p>
                    <p style="color: #666; margin-top: 10px;">נהדר! כל המשימות שלך להיום טופלו.</p>
                </div>
            </div>
            
            <p style="color: #999; font-size: 12px; text-align: center; margin-top: 20px;">
                Kinyan CRM — קניין הוראה
            </p>
        </div>
        """
        
        text_body = f"""סיכום משימות יומי — Kinyan CRM
תאריך: {now.strftime('%d/%m/%Y')}

אין משימות פתוחות להיום.
נהדר! כל המשימות שלך להיום טופלו.

Kinyan CRM — קניין הוראה"""
    else:
        # Tasks list email
        tasks_html = ""
        for task in tasks:
            due_date_str = task.due_date.strftime("%H:%M") if task.due_date else ""
            priority_badge = {
                0: '<span style="background: #e0e0e0; color: #333; padding: 2px 8px; border-radius: 10px; font-size: 12px;">רגיל</span>',
                1: '<span style="background: #90caf9; color: #0d47a1; padding: 2px 8px; border-radius: 10px; font-size: 12px;">נמוך</span>',
                2: '<span style="background: #ffcc80; color: #e65100; padding: 2px 8px; border-radius: 10px; font-size: 12px;">גבוה</span>',
                3: '<span style="background: #ef5350; color: #b71c1c; padding: 2px 8px; border-radius: 10px; font-size: 12px;">דחוף</span>',
            }.get(task.priority, '<span style="background: #e0e0e0; color: #333; padding: 2px 8px; border-radius: 10px; font-size: 12px;">רגיל</span>')
            
            tasks_html += f"""
            <div style="background: white; padding: 15px; margin-bottom: 10px; border-radius: 5px; border: 1px solid #e0e0e0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <h4 style="margin: 0; color: #333;">{task.title}</h4>
                    {priority_badge}
                </div>
                {f'<p style="margin: 5px 0; color: #666; font-size: 14px;">{task.description}</p>' if task.description else ''}
                <p style="margin: 5px 0; color: #666; font-size: 13px;">
                    <strong>סטטוס:</strong> {task.status} | 
                    {f'<strong>שעה:</strong> {due_date_str}' if due_date_str else ''}
                </p>
            </div>
            """
        
        html_body = f"""
        <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="color: white; margin: 0; font-size: 24px;">סיכום משימות יומי</h2>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">{now.strftime('%d/%m/%Y')} - {len(tasks)} משימות</p>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0;">
                {tasks_html}
            </div>
            
            <p style="color: #999; font-size: 12px; text-align: center; margin-top: 20px;">
                Kinyan CRM — קניין הוראה
            </p>
        </div>
        """
        
        tasks_text = ""
        for i, task in enumerate(tasks, 1):
            due_date_str = task.due_date.strftime("%H:%M") if task.due_date else ""
            tasks_text += f"\n{i}. {task.title}\n   סטטוס: {task.status} | {f'שעה: {due_date_str}' if due_date_str else ''}\n"
        
        text_body = f"""סיכום משימות יומי — Kinyan CRM
תאריך: {now.strftime('%d/%m/%Y')}
{len(tasks)} משימות פתוחות

{tasks_text}

Kinyan CRM — קניין הוראה"""
    
    success = await email_service.send_email(
        to_email=salesperson.email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )
    
    if success:
        print(f"[daily_summary] Email sent to {salesperson.email} for salesperson #{salesperson_id}")
    else:
        print(f"[daily_summary] Failed to send email to {salesperson.email} for salesperson #{salesperson_id}")
    
    return success


async def send_daily_summary_to_all_salespeople(db: AsyncSession) -> dict:
    """
    Send daily summary emails to all active salespeople.
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with success/failure counts
    """
    # Get all active salespeople with email
    stmt = select(Salesperson).where(
        Salesperson.is_active == True,
        Salesperson.email.isnot(None),
        Salesperson.email != ""
    )
    result = await db.execute(stmt)
    salespeople = list(result.scalars().all())
    
    success_count = 0
    failure_count = 0
    
    for sp in salespeople:
        success = await send_daily_summary_email(db, sp.id)
        if success:
            success_count += 1
        else:
            failure_count += 1
    
    print(f"[daily_summary_all] Sent to {success_count} salespeople, {failure_count} failed")
    
    return {
        "total": len(salespeople),
        "success": success_count,
        "failure": failure_count,
    }
