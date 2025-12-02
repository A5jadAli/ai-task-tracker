"""
Status reporter for sending command updates to Slack.
"""
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class StatusReporter:
    """Reports command status updates to Slack.
    
    Handles formatting and sending status messages back to the user
    in the appropriate channel/thread.
    """
    
    def __init__(self, slack_monitor):
        """Initialize reporter.
        
        Args:
            slack_monitor: SlackMonitor instance for sending messages
        """
        self.slack = slack_monitor
    
    async def report(self, message: str, context: Dict[str, Any]):
        """Send status update to Slack.
        
        Args:
            message: Status message to send
            context: Execution context containing channel and thread info
        """
        channel = context.get('channel')
        thread_ts = context.get('thread_ts')
        
        if not channel:
            logger.warning("No channel in context for status report")
            return
        
        try:
            # Send as thread reply if thread_ts exists, otherwise as new message
            self.slack.send_message(
                channel=channel,
                text=message,
                thread_ts=thread_ts
            )
            logger.debug(f"Status reported: {message[:50]}...")
        except Exception as e:
            logger.error(f"Failed to report status: {e}", exc_info=True)
    
    async def report_start(self, command_name: str, description: str, context: Dict[str, Any]):
        """Report command start.
        
        Args:
            command_name: Name of command being executed
            description: Command description
            context: Execution context
        """
        message = f"✓ Starting: {description}..."
        await self.report(message, context)
    
    async def report_success(self, message: str, context: Dict[str, Any], data: Dict[str, Any] = None):
        """Report command success.
        
        Args:
            message: Success message
            context: Execution context
            data: Optional additional data to include
        """
        formatted = f"✅ {message}"
        
        # Add data if provided
        if data:
            for key, value in data.items():
                if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                    formatted += f"\n{key}: {value}"
        
        await self.report(formatted, context)
    
    async def report_error(self, message: str, error: str, context: Dict[str, Any]):
        """Report command error.
        
        Args:
            message: Error message
            error: Detailed error information
            context: Execution context
        """
        formatted = f"❌ {message}"
        if error:
            formatted += f"\n```\n{error}\n```"
        
        await self.report(formatted, context)
    
    async def report_progress(self, message: str, context: Dict[str, Any]):
        """Report command progress.
        
        Args:
            message: Progress message
            context: Execution context
        """
        formatted = f"⏳ {message}"
        await self.report(formatted, context)
