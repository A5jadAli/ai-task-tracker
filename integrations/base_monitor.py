"""
Base monitor class for event monitoring.
"""
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseMonitor(ABC):
    """Base class for all event monitors."""
    
    def __init__(self, name: str):
        """
        Initialize monitor.
        
        Args:
            name: Monitor name
        """
        self.name = name
        self.running = False
        self.callbacks = {}
        self.config = {}
    
    @abstractmethod
    def start(self, config: Dict[str, Any]):
        """
        Start monitoring.
        
        Args:
            config: Monitor configuration
        """
        pass
    
    @abstractmethod
    def stop(self):
        """Stop monitoring."""
        pass
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Register callback for event type.
        
        Args:
            event_type: Type of event
            callback: Callback function(event_data)
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
        logger.info(f"Registered callback for {event_type} in {self.name}")
    
    def trigger_callbacks(self, event_type: str, event_data: Any):
        """
        Trigger all callbacks for an event type.
        
        Args:
            event_type: Type of event
            event_data: Event data to pass to callbacks
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(event_data)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {e}", exc_info=True)
    
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self.running
