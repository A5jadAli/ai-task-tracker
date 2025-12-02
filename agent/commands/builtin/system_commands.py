"""
System commands for agent control and information.
"""
from typing import List, Dict, Any
from ..base import Command, CommandResult
from ..registry import CommandRegistry
from utils.logger import get_logger

logger = get_logger(__name__)


class HelpCommand(Command):
    """Show help information for commands."""
    
    def __init__(self, registry: CommandRegistry):
        """Initialize command.
        
        Args:
            registry: CommandRegistry instance
        """
        self.registry = registry
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "Show help information"
    
    @property
    def usage(self) -> str:
        return "agent help [command]"
    
    @property
    def aliases(self) -> List[str]:
        return ["?", "h"]
    
    @property
    def category(self) -> str:
        return "System"
    
    async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """Execute command."""
        if args:
            # Help for specific command
            command_name = args[0]
            help_text = self.registry.get_help(command_name)
        else:
            # General help
            help_text = self.registry.get_help()
        
        return CommandResult(
            success=True,
            message=help_text
        )


class StatusCommand(Command):
    """Show agent status."""
    
    def __init__(self, daemon=None):
        """Initialize command.
        
        Args:
            daemon: AgentDaemon instance (optional)
        """
        self.daemon = daemon
    
    @property
    def name(self) -> str:
        return "status"
    
    @property
    def description(self) -> str:
        return "Show agent status"
    
    @property
    def usage(self) -> str:
        return "agent status"
    
    @property
    def category(self) -> str:
        return "System"
    
    async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """Execute command."""
        if not self.daemon:
            return CommandResult(
                success=True,
                message="Agent is running (status details not available)"
            )
        
        try:
            status = self.daemon.get_status()
            
            # Format status message
            message = "**Agent Status**\n\n"
            message += f"• Running: {'✅ Yes' if status.get('running') else '❌ No'}\n"
            
            # Monitors
            monitors = status.get('monitors', {})
            message += f"\n**Monitors:**\n"
            for name, running in monitors.items():
                status_icon = '✅' if running else '❌'
                message += f"• {name}: {status_icon}\n"
            
            # Task queue
            queue_stats = status.get('task_queue_stats', {})
            if queue_stats:
                message += f"\n**Task Queue:**\n"
                message += f"• Pending: {queue_stats.get('pending', 0)}\n"
                message += f"• Workers: {queue_stats.get('workers', 0)}\n"
            
            # Scheduled jobs
            jobs = status.get('scheduled_jobs', {})
            if jobs:
                message += f"\n**Scheduled Jobs:** {len(jobs)}\n"
            
            return CommandResult(
                success=True,
                message=message,
                data=status
            )
        
        except Exception as e:
            logger.error(f"Failed to get status: {e}", exc_info=True)
            return CommandResult(
                success=False,
                message="Failed to get agent status",
                error=str(e)
            )


class ListCommandsCommand(Command):
    """List all available commands."""
    
    def __init__(self, registry: CommandRegistry):
        """Initialize command.
        
        Args:
            registry: CommandRegistry instance
        """
        self.registry = registry
    
    @property
    def name(self) -> str:
        return "commands"
    
    @property
    def description(self) -> str:
        return "List all available commands"
    
    @property
    def usage(self) -> str:
        return "agent commands"
    
    @property
    def aliases(self) -> List[str]:
        return ["list", "list-commands"]
    
    @property
    def category(self) -> str:
        return "System"
    
    async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """Execute command."""
        categories = self.registry.list_by_category()
        
        message = f"**Available Commands** ({len(self.registry)} total)\n\n"
        
        for category in sorted(categories.keys()):
            message += f"**{category}**\n"
            commands = sorted(categories[category], key=lambda c: c.name)
            
            for cmd in commands:
                message += f"• `{cmd.name}` - {cmd.description}\n"
            
            message += "\n"
        
        message += "Use `agent help <command>` for detailed usage."
        
        return CommandResult(
            success=True,
            message=message,
            data={"count": len(self.registry)}
        )
