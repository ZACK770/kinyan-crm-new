"""
Scheduler Service - Generic task scheduling using APScheduler
Supports recurring and one-time scheduled tasks for any application use case.
"""
import logging
from datetime import datetime
from typing import Callable, Optional, Any, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Generic scheduler service for managing scheduled tasks.
    Supports:
    - Cron-based recurring tasks (daily, hourly, etc.)
    - One-time scheduled tasks at specific date/time
    - Dynamic job management (add, remove, pause, resume)
    """
    
    def __init__(self):
        """Initialize the scheduler with memory job store and async executor."""
        self.scheduler = AsyncIOScheduler(
            jobstores={
                'default': MemoryJobStore()
            },
            executors={
                'default': AsyncIOExecutor()
            },
            job_defaults={
                'coalesce': True,  # Combine multiple pending executions into one
                'max_instances': 1,  # Only one instance of a job can run at a time
                'misfire_grace_time': 300  # Allow 5 minutes grace time for misfired jobs
            },
            timezone='Asia/Jerusalem'
        )
        self.running = False
    
    def start(self):
        """Start the scheduler."""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.info("[scheduler] Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.running:
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("[scheduler] Scheduler shutdown")
    
    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        cron_expression: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        replace_existing: bool = True,
        description: Optional[str] = None,
    ) -> None:
        """
        Add a cron-based recurring job.
        
        Args:
            func: The async function to execute
            job_id: Unique identifier for the job
            cron_expression: Cron expression (e.g., "0 8 * * *" for daily at 8 AM)
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            replace_existing: Whether to replace existing job with same ID
            description: Human-readable description of the job
        """
        try:
            self.scheduler.add_job(
                func,
                CronTrigger.from_crontab(cron_expression, timezone='Asia/Jerusalem'),
                id=job_id,
                args=args,
                kwargs=kwargs,
                replace_existing=replace_existing,
                description=description
            )
            logger.info(f"[scheduler] Added cron job: {job_id} - {cron_expression}")
        except Exception as e:
            logger.error(f"[scheduler] Failed to add cron job {job_id}: {e}")
            raise
    
    def add_date_job(
        self,
        func: Callable,
        job_id: str,
        run_date: datetime,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        replace_existing: bool = True,
        description: Optional[str] = None,
    ) -> None:
        """
        Add a one-time job at a specific date/time.
        
        Args:
            func: The async function to execute
            job_id: Unique identifier for the job
            run_date: When to execute the job
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            replace_existing: Whether to replace existing job with same ID
            description: Human-readable description of the job
        """
        try:
            # If run_date already has timezone, don't specify timezone in DateTrigger
            if run_date.tzinfo is not None:
                trigger = DateTrigger(run_date=run_date)
                print(f"[scheduler] Adding job {job_id} with timezone-aware run_date: {run_date}")
            else:
                trigger = DateTrigger(run_date=run_date, timezone='Asia/Jerusalem')
                print(f"[scheduler] Adding job {job_id} with naive run_date: {run_date}, using Asia/Jerusalem timezone")
            
            self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                args=args,
                kwargs=kwargs,
                replace_existing=replace_existing,
                description=description
            )
            
            # Log the job's next run time
            job = self.scheduler.get_job(job_id)
            if job:
                print(f"[scheduler] Job {job_id} scheduled, next run time: {job.next_run_time}")
            
            logger.info(f"[scheduler] Added date job: {job_id} - {run_date}")
        except Exception as e:
            logger.error(f"[scheduler] Failed to add date job {job_id}: {e}")
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job by ID.
        
        Args:
            job_id: Unique identifier of the job to remove
            
        Returns:
            True if job was removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"[scheduler] Removed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"[scheduler] Failed to remove job {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a job by ID.
        
        Args:
            job_id: Unique identifier of the job to pause
            
        Returns:
            True if job was paused, False if not found
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"[scheduler] Paused job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"[scheduler] Failed to pause job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job by ID.
        
        Args:
            job_id: Unique identifier of the job to resume
            
        Returns:
            True if job was resumed, False if not found
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"[scheduler] Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"[scheduler] Failed to resume job {job_id}: {e}")
            return False
    
    def get_jobs(self) -> list:
        """
        Get all scheduled jobs.
        
        Returns:
            List of job objects
        """
        return self.scheduler.get_jobs()
    
    def get_job(self, job_id: str):
        """
        Get a specific job by ID.
        
        Args:
            job_id: Unique identifier of the job
            
        Returns:
            Job object or None if not found
        """
        return self.scheduler.get_job(job_id)


# Global scheduler instance
scheduler_service = SchedulerService()
