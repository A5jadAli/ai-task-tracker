"""
Command registry for managing available commands.
"""
from typing import Dict, Optional, List
from .base import Command
from utils.logger import get_logger

logger = get_logger(__name__)


class CommandRegistry:
    """Registry for all available commands.
    
    Manages command registration, lookup, and help text generation.
    Supports both primary command names and aliases.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._commands: Dict[str, Command] = {}
        self._primary_commands: List[Command] = []
    
    def register(self, command: Command):
        """Register a command.
        
        Registers both the primary command name and all aliases.
        
        Args:
            command: Command instance to register
        
        Raises:
            ValueError: If command name or alias is already registered
        """
        # Check for conflicts
        if command.name in self._commands:
            existing = self._commands[command.name]
            if existing != command:
                raise ValueError(
                    f"Command '{command.name}' is already registered"
                )
            return  # Already registered
        
        # Register primary name
        self._commands[command.name] = command
        self._primary_commands.append(command)
        
        # Register aliases
        for alias in command.aliases:
            if alias in self._commands:
                raise ValueError(
                    f"Alias '{alias}' conflicts with existing command"
                )
            self._commands[alias] = command
        
        logger.info(f"Registered command: {command.name}")
        if command.aliases:
            logger.debug(f"  Aliases: {', '.join(command.aliases)}")
    
    def unregister(self, command_name: str):
        """Unregister a command.
        
        Args:
            command_name: Name of command to unregister
        """
        if command_name not in self._commands:
            return
        
        command = self._commands[command_name]
        
        # Remove primary name
        if command.name in self._commands:
            del self._commands[command.name]
        
        # Remove from primary list
        if command in self._primary_commands:
            self._primary_commands.remove(command)
        
        # Remove aliases
        for alias in command.aliases:
            if alias in self._commands:
                del self._commands[alias]
        
        logger.info(f"Unregistered command: {command_name}")
    
    def get(self, name: str) -> Optional[Command]:
        """Get command by name or alias.
        
        Args:
            name: Command name or alias (case-insensitive)
        
        Returns:
            Command instance if found, None otherwise
        """
        return self._commands.get(name.lower())
    
    def has(self, name: str) -> bool:
        """Check if command exists.
        
        Args:
            name: Command name or alias
        
        Returns:
            True if command is registered
        """
        return name.lower() in self._commands
    
    def list_commands(self) -> List[Command]:
        """List all unique commands (excluding aliases).
        
        Returns:
            List of Command instances
        """
        return self._primary_commands.copy()
    
    def list_by_category(self) -> Dict[str, List[Command]]:
        """List commands grouped by category.
        
        Returns:
            Dictionary mapping category names to command lists
        """
        categories: Dict[str, List[Command]] = {}
        
        for command in self._primary_commands:
            category = command.category
            if category not in categories:
                categories[category] = []
            categories[category].append(command)
        
        return categories
    
    def get_help(self, command_name: Optional[str] = None) -> str:
        """Get help text.
        
        Args:
            command_name: Optional specific command to get help for
        
        Returns:
            Formatted help text
        """
        if command_name:
            # Help for specific command
            command = self.get(command_name)
            if not command:
                return f"Unknown command: {command_name}"
            return command.get_help_text()
        
        # Help for all commands, grouped by category
        categories = self.list_by_category()
        
        help_text = "**Available Commands**\n\n"
        
        for category in sorted(categories.keys()):
            help_text += f"**{category}**\n"
            commands = sorted(categories[category], key=lambda c: c.name)
            
            for cmd in commands:
                help_text += f"• `{cmd.name}`"
                if cmd.aliases:
                    help_text += f" (aliases: {', '.join(f'`{a}`' for a in cmd.aliases)})"
                help_text += f" - {cmd.description}\n"
            
            help_text += "\n"
        
        help_text += "Use `agent help <command>` for detailed usage information."
        
        return help_text
    
    def __len__(self) -> int:
        """Get number of registered commands (excluding aliases)."""
        return len(self._primary_commands)
    
    def __contains__(self, name: str) -> bool:
        """Check if command exists (supports 'in' operator)."""
        return self.has(name)
