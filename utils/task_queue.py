"""
Background task queue with worker threads.
"""
import queue
import threading
import time
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskQueue:
    """Thread-safe task queue with worker pool."""
    
    def __init__(self, num_workers=3, max_queue_size=100):
        """
        Initialize task queue.
        
        Args:
            num_workers: Number of worker threads
            max_queue_size: Maximum queue size (0 = unlimited)
        """
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.workers = []
        self.running = False
        self.num_workers = num_workers
        self.task_count = 0
        self.completed_count = 0
        self.failed_count = 0
    
    def start(self):
        """Start worker threads."""
        if self.running:
            logger.warning("Task queue already running")
            return
        
        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker,
                name=f"TaskWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.num_workers} worker threads")
    
    def stop(self, wait=True):
        """
        Stop worker threads.
        
        Args:
            wait: Wait for all tasks to complete
        """
        if not self.running:
            return
        
        self.running = False
        
        if wait:
            self.wait_completion()
        
        # Add sentinel values to wake up workers
        for _ in range(self.num_workers):
            self.queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        logger.info("Stopped all worker threads")
    
    def _worker(self):
        """Worker thread function."""
        while self.running:
            try:
                # Get task from queue (with timeout to check running flag)
                task_data = self.queue.get(timeout=1)
                
                # Check for sentinel value
                if task_data is None:
                    break
                
                task_func, args, kwargs, callback = task_data
                
                try:
                    # Execute task
                    result = task_func(*args, **kwargs)
                    self.completed_count += 1
                    
                    # Call callback if provided
                    if callback:
                        callback(result, None)
                    
                except Exception as e:
                    self.failed_count += 1
                    logger.error(f"Task failed: {e}", exc_info=True)
                    
                    # Call callback with error
                    if callback:
                        callback(None, e)
                
                finally:
                    self.queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
    
    def add_task(self, task_func, *args, callback=None, **kwargs):
        """
        Add task to queue.
        
        Args:
            task_func: Function to execute
            *args: Positional arguments for task_func
            callback: Optional callback(result, error)
            **kwargs: Keyword arguments for task_func
        
        Returns:
            bool: True if task was added
        """
        if not self.running:
            logger.error("Task queue not running")
            return False
        
        try:
            task_data = (task_func, args, kwargs, callback)
            self.queue.put(task_data, block=False)
            self.task_count += 1
            return True
        except queue.Full:
            logger.error("Task queue is full")
            return False
    
    def wait_completion(self, timeout=None):
        """
        Wait for all tasks to complete.
        
        Args:
            timeout: Maximum time to wait (None = wait forever)
        
        Returns:
            bool: True if all tasks completed
        """
        try:
            if timeout:
                self.queue.join()
                return True
            else:
                # Wait with timeout
                start_time = time.time()
                while not self.queue.empty():
                    if time.time() - start_time > timeout:
                        return False
                    time.sleep(0.1)
                self.queue.join()
                return True
        except Exception as e:
            logger.error(f"Error waiting for completion: {e}")
            return False
    
    def get_stats(self):
        """Get queue statistics."""
        return {
            'running': self.running,
            'workers': len(self.workers),
            'queue_size': self.queue.qsize(),
            'total_tasks': self.task_count,
            'completed': self.completed_count,
            'failed': self.failed_count,
            'pending': self.task_count - self.completed_count - self.failed_count
        }
