"""
Task Scheduler Service - Manages scheduled task-related operations
Uses the generic SchedulerService for task reminders and daily summaries.
"""
import logging
from datetime import datetime, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import get_async_session
from db.models import SalesTask, Salesperson
from .scheduler import scheduler_service
from .tasks_email_service import send_daily_summary_to_all_salespeople

logger = logging.getLogger(__name__)


async def send_task_reminder_at_due_date(task_id: int):
    """
    Send a reminder email for a specific task at its due date.
    This function is called by the scheduler.
    
    Args:
        task_id: ID of the task to send reminder for
    """
    try:
        async for db in get_async_session():
            from .tasks_email_service import send_task_reminder_email
            success = await send_task_reminder_email(db, task_id)
            if success:
                logger.info(f"[task_scheduler] Sent reminder for task #{task_id}")
            else:
                logger.warning(f"[task_scheduler] Failed to send reminder for task #{task_id}")
            break
    except Exception as e:
        logger.error(f"[task_scheduler] Error sending reminder for task #{task_id}: {e}")


async def schedule_task_reminder(task_id: int, due_date: datetime):
    """
    Schedule a reminder email for a task at its due date.
    
    Args:
        task_id: ID of the task
        due_date: When to send the reminder
    """
    print(f"[schedule_task_reminder] Starting for task_id: {task_id}, due_date: {due_date}")
    job_id = f"task_reminder_{task_id}"
    
    # Remove existing job if any
    print(f"[schedule_task_reminder] Removing existing job if any")
    scheduler_service.remove_job(job_id)
    
    # Schedule new job
    print(f"[schedule_task_reminder] Scheduling new job")
    try:
        scheduler_service.add_date_job(
            func=send_task_reminder_at_due_date,
            job_id=job_id,
            run_date=due_date,
            args=(task_id,),
            description=f"Task reminder for task #{task_id} at {due_date}"
        )
        print(f"[schedule_task_reminder] Job scheduled successfully")
        logger.info(f"[task_scheduler] Scheduled reminder for task #{task_id} at {due_date}")
    except Exception as e:
        print(f"[schedule_task_reminder] Error scheduling job: {e}")
        logger.error(f"[task_scheduler] Error scheduling reminder for task #{task_id}: {e}")
        raise


async def cancel_task_reminder(task_id: int):
    """
    Cancel a scheduled reminder for a task.
    
    Args:
        task_id: ID of the task
    """
    job_id = f"task_reminder_{task_id}"
    scheduler_service.remove_job(job_id)
    logger.info(f"[task_scheduler] Cancelled reminder for task #{task_id}")


async def send_daily_task_summary():
    """
    Send daily summary emails to all salespeople.
    This function is called by the scheduler.
    """
    try:
        async for db in get_async_session():
            await send_daily_summary_to_all_salespeople(db)
            logger.info("[task_scheduler] Sent daily task summary to all salespeople")
            break
    except Exception as e:
        logger.error(f"[task_scheduler] Error sending daily task summary: {e}")


def schedule_daily_summary(hour: int = 8, minute: int = 0):
    """
    Schedule daily task summary emails to be sent at a specific time.
    
    Args:
        hour: Hour to send (default: 8 AM)
        minute: Minute to send (default: 0)
    """
    job_id = "daily_task_summary"
    cron_expression = f"{minute} {hour} * * *"
    
    # Remove existing job if any
    scheduler_service.remove_job(job_id)
    
    # Schedule new job
    scheduler_service.add_cron_job(
        func=send_daily_task_summary,
        job_id=job_id,
        cron_expression=cron_expression,
        description=f"Daily task summary at {hour:02d}:{minute:02d}"
    )
    
    logger.info(f"[task_scheduler] Scheduled daily task summary at {hour:02d}:{minute:02d}")


async def initialize_scheduled_tasks():
    """
    Initialize all scheduled tasks on application startup.
    This should be called during application lifespan startup.
    """
    print("[initialize_scheduled_tasks] Starting initialization")
    try:
        # Schedule daily summary at 8 AM
        print("[initialize_scheduled_tasks] Scheduling daily summary at 8:00")
        schedule_daily_summary(hour=8, minute=0)
        
        # Reschedule reminders for tasks with future due dates
        print("[initialize_scheduled_tasks] Fetching tasks with future due dates")
        async for db in get_async_session():
            stmt = select(SalesTask).where(
                SalesTask.due_date.isnot(None),
                SalesTask.due_date > datetime.now(),
                SalesTask.send_reminder == True
            )
            result = await db.execute(stmt)
            tasks = result.scalars().all()
            
            print(f"[initialize_scheduled_tasks] Found {len(tasks)} tasks with future due dates and send_reminder=True")
            
            for task in tasks:
                print(f"[initialize_scheduled_tasks] Rescheduling reminder for task #{task.id} at {task.due_date}")
                try:
                    await schedule_task_reminder(task.id, task.due_date)
                except Exception as e:
                    print(f"[initialize_scheduled_tasks] Error rescheduling task #{task.id}: {e}")
            
            logger.info(f"[task_scheduler] Rescheduled {len(tasks)} task reminders")
            print(f"[initialize_scheduled_tasks] Rescheduled {len(tasks)} task reminders")
            break
            
    except Exception as e:
        print(f"[initialize_scheduled_tasks] Error: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"[task_scheduler] Error initializing scheduled tasks: {e}")
