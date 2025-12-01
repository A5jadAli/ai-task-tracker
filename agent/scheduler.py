"""
Task scheduler with cron-style and interval-based scheduling.
"""
import time
from datetime import datetime
from typing import Callable, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    """Scheduler for automated task execution."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
        self.running = False
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.scheduler.start()
        self.running = True
        logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.scheduler.shutdown(wait=True)
        self.running = False
        logger.info("Task scheduler stopped")
    
    def add_cron_task(self, task_id: str, func: Callable, cron_expression: str, **kwargs):
        """
        Add a cron-style scheduled task.
        
        Args:
            task_id: Unique task identifier
            func: Function to execute
            cron_expression: Cron expression (e.g., "0 9 * * 1-5" for 9 AM weekdays)
            **kwargs: Additional arguments to pass to func
        
        Returns:
            Job object
        """
        try:
            # Parse cron expression
            parts = cron_expression.split()
            
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                
                trigger = CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                )
            else:
                logger.error(f"Invalid cron expression: {cron_expression}")
                return None
            
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=task_id,
                kwargs=kwargs,
                replace_existing=True
            )
            
            self.jobs[task_id] = job
            logger.info(f"Added cron task '{task_id}': {cron_expression}")
            return job
        
        except Exception as e:
            logger.error(f"Failed to add cron task '{task_id}': {e}", exc_info=True)
            return None
    
    def add_interval_task(self, task_id: str, func: Callable, 
                         seconds: int = 0, minutes: int = 0, hours: int = 0, **kwargs):
        """
        Add an interval-based task.
        
        Args:
            task_id: Unique task identifier
            func: Function to execute
            seconds: Interval in seconds
            minutes: Interval in minutes
            hours: Interval in hours
            **kwargs: Additional arguments to pass to func
        
        Returns:
            Job object
        """
        try:
            trigger = IntervalTrigger(
                seconds=seconds,
                minutes=minutes,
                hours=hours
            )
            
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=task_id,
                kwargs=kwargs,
                replace_existing=True
            )
            
            self.jobs[task_id] = job
            interval_str = f"{hours}h {minutes}m {seconds}s"
            logger.info(f"Added interval task '{task_id}': every {interval_str}")
            return job
        
        except Exception as e:
            logger.error(f"Failed to add interval task '{task_id}': {e}", exc_info=True)
            return None
    
    def add_one_time_task(self, task_id: str, func: Callable, run_date: datetime, **kwargs):
        """
        Add a one-time scheduled task.
        
        Args:
            task_id: Unique task identifier
            func: Function to execute
            run_date: When to run the task
            **kwargs: Additional arguments to pass to func
        
        Returns:
            Job object
        """
        try:
            trigger = DateTrigger(run_date=run_date)
            
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=task_id,
                kwargs=kwargs,
                replace_existing=True
            )
            
            self.jobs[task_id] = job
            logger.info(f"Added one-time task '{task_id}' at {run_date}")
            return job
        
        except Exception as e:
            logger.error(f"Failed to add one-time task '{task_id}': {e}", exc_info=True)
            return None
    
    def remove_task(self, task_id: str):
        """
        Remove a scheduled task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            bool: True if removed
        """
        try:
            if task_id in self.jobs:
                self.scheduler.remove_job(task_id)
                del self.jobs[task_id]
                logger.info(f"Removed task '{task_id}'")
                return True
            else:
                logger.warning(f"Task '{task_id}' not found")
                return False
        except Exception as e:
            logger.error(f"Failed to remove task '{task_id}': {e}")
            return False
    
    def pause_task(self, task_id: str):
        """Pause a task."""
        try:
            self.scheduler.pause_job(task_id)
            logger.info(f"Paused task '{task_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to pause task '{task_id}': {e}")
            return False
    
    def resume_task(self, task_id: str):
        """Resume a paused task."""
        try:
            self.scheduler.resume_job(task_id)
            logger.info(f"Resumed task '{task_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to resume task '{task_id}': {e}")
            return False
    
    def get_jobs(self) -> Dict[str, Any]:
        """Get all scheduled jobs."""
        return {
            job_id: {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            }
            for job_id, job in self.jobs.items()
        }
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.running
