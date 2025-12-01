"""
Event dispatcher - routes events to appropriate handlers and workflows.
"""
from typing import Dict, Any, Callable, List
from utils.logger import get_logger

logger = get_logger(__name__)


class EventDispatcher:
    """Central event dispatcher for routing events to handlers."""
    
    def __init__(self):
        """Initialize event dispatcher."""
        self.handlers = {}
        self.workflows = {}
    
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function(event_data)
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    def register_workflow(self, event_type: str, workflow_name: str, workflow_func: Callable):
        """
        Register a workflow for an event type.
        
        Args:
            event_type: Type of event that triggers workflow
            workflow_name: Name of the workflow
            workflow_func: Workflow function(event_data)
        """
        if event_type not in self.workflows:
            self.workflows[event_type] = {}
        
        self.workflows[event_type][workflow_name] = workflow_func
        logger.info(f"Registered workflow '{workflow_name}' for event: {event_type}")
    
    def dispatch(self, event_type: str, event_data: Any):
        """
        Dispatch an event to all registered handlers and workflows.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        logger.debug(f"Dispatching event: {event_type}")
        
        # Execute handlers
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Error in handler for {event_type}: {e}", exc_info=True)
        
        # Execute workflows
        if event_type in self.workflows:
            for workflow_name, workflow_func in self.workflows[event_type].items():
                try:
                    logger.info(f"Executing workflow '{workflow_name}' for {event_type}")
                    workflow_func(event_data)
                except Exception as e:
                    logger.error(f"Error in workflow '{workflow_name}': {e}", exc_info=True)
    
    def unregister_handler(self, event_type: str, handler: Callable):
        """Unregister an event handler."""
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            logger.info(f"Unregistered handler for {event_type}")
    
    def unregister_workflow(self, event_type: str, workflow_name: str):
        """Unregister a workflow."""
        if event_type in self.workflows and workflow_name in self.workflows[event_type]:
            del self.workflows[event_type][workflow_name]
            logger.info(f"Unregistered workflow '{workflow_name}' for {event_type}")
    
    def get_registered_events(self) -> List[str]:
        """Get list of all registered event types."""
        return list(set(list(self.handlers.keys()) + list(self.workflows.keys())))
