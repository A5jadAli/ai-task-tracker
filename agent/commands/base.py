"""
Base classes for command system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class CommandResult:
    """Result of command execution.
    
    Attributes:
        success: Whether the command executed successfully
        message: Human-readable result message
        data: Optional structured data from command execution
        error: Optional error message if command failed
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Command(ABC):
    """Base class for all commands.
    
    To create a new command:
    1. Inherit from this class
    2. Implement all abstract properties and methods
    3. Register the command in CommandRegistry
    
    Example:
        class MyCommand(Command):
            @property
            def name(self) -> str:
                return "my-command"
            
            @property
            def description(self) -> str:
                return "Does something useful"
            
            @property
            def usage(self) -> str:
                return "agent my-command <arg1> <arg2>"
            
            async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
                # Implementation
                return CommandResult(success=True, message="Done!")
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name (e.g., 'create-pr').
        
        This is the primary identifier for the command.
        Should be lowercase with hyphens for multi-word commands.
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what the command does.
        
        Used in help text and command listings.
        """
        pass
    
    @property
    @abstractmethod
    def usage(self) -> str:
        """Usage example showing command syntax.
        
        Should include the command prefix and all required/optional arguments.
        Example: "agent create-pr <branch> [to <base>]"
        """
        pass
    
    @property
    def aliases(self) -> List[str]:
        """Alternative names for this command.
        
        Returns:
            List of alias strings (default: empty list)
        """
        return []
    
    @property
    def category(self) -> str:
        """Command category for grouping in help.
        
        Returns:
            Category name (default: "General")
        """
        return "General"
    
    @abstractmethod
    async def execute(self, args: List[str], context: Dict[str, Any]) -> CommandResult:
        """Execute the command.
        
        Args:
            args: List of command arguments (parsed from user input)
            context: Execution context containing:
                - channel: Slack channel ID
                - thread_ts: Thread timestamp for replies
                - event: Original Slack event
                - user_id: User who issued the command
                - Additional context from daemon
        
        Returns:
            CommandResult with success status and message
        
        Raises:
            Exception: Any exception will be caught by executor and reported
        """
        pass
    
    def validate_args(self, args: List[str]) -> bool:
        """Validate command arguments.
        
        Override this method to add custom argument validation.
        
        Args:
            args: List of command arguments
        
        Returns:
            True if arguments are valid, False otherwise
        """
        return True
    
    def get_help_text(self) -> str:
        """Get formatted help text for this command.
        
        Returns:
            Formatted help string
        """
        help_text = f"**{self.name}**"
        if self.aliases:
            help_text += f" (aliases: {', '.join(self.aliases)})"
        help_text += f"\n{self.description}\n"
        help_text += f"Usage: `{self.usage}`"
        return help_text
