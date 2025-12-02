"""
Command executor for running commands asynchronously.
"""
import asyncio
from typing import Dict, Any, Callable, Optional
from .base import Command, CommandResult
from .parser import ParsedCommand
from .registry import CommandRegistry
from utils.logger import get_logger

logger = get_logger(__name__)


class CommandExecutor:
    """Executes commands asynchronously with status reporting.
    
    Handles command lookup, validation, execution, and error handling.
    Reports status updates via callback function.
    """
    
    def __init__(
        self,
        registry: CommandRegistry,
        status_callback: Optional[Callable] = None,
        timeout: int = 300
    ):
        """Initialize executor.
        
        Args:
            registry: CommandRegistry for looking up commands
            status_callback: Optional async function to call for status updates
            timeout: Command execution timeout in seconds (default: 300)
        """
        self.registry = registry
        self.status_callback = status_callback
        self.timeout = timeout
    
    async def execute(
        self,
        parsed_cmd: ParsedCommand,
        context: Dict[str, Any]
    ) -> CommandResult:
        """Execute a parsed command.
        
        Args:
            parsed_cmd: Parsed command to execute
            context: Execution context
        
        Returns:
            CommandResult with execution status and message
        """
        # Get command from registry
        command = self.registry.get(parsed_cmd.command)
        
        if not command:
            result = CommandResult(
                success=False,
                message=f"Unknown command: `{parsed_cmd.command}`",
                error=f"Use `{parsed_cmd.prefix} help` to see available commands"
            )
            
            if self.status_callback:
                await self.status_callback(
                    f"❌ {result.message}\n{result.error}",
                    context
                )
            
            return result
        
        # Validate arguments
        if not command.validate_args(parsed_cmd.args):
            result = CommandResult(
                success=False,
                message=f"Invalid arguments for `{parsed_cmd.command}`",
                error=f"Usage: `{command.usage}`"
            )
            
            if self.status_callback:
                await self.status_callback(
                    f"❌ {result.message}\n{result.error}",
                    context
                )
            
            return result
        
        # Send starting status
        if self.status_callback:
            await self.status_callback(
                f"✓ Starting: {command.description}...",
                context
            )
        
        try:
            # Execute command with timeout
            logger.info(
                f"Executing command: {parsed_cmd.command} "
                f"with args: {parsed_cmd.args}"
            )
            
            result = await asyncio.wait_for(
                command.execute(parsed_cmd.args, context),
                timeout=self.timeout
            )
            
            # Send completion status
            if self.status_callback:
                if result.success:
                    message = f"✅ {result.message}"
                    if result.data:
                        # Add data to message
                        for key, value in result.data.items():
                            if isinstance(value, str) and (
                                value.startswith('http://') or
                                value.startswith('https://')
                            ):
                                message += f"\n{value}"
                    
                    await self.status_callback(message, context)
                else:
                    error_msg = f"❌ {result.message}"
                    if result.error:
                        error_msg += f"\n```\n{result.error}\n```"
                    await self.status_callback(error_msg, context)
            
            logger.info(
                f"Command {parsed_cmd.command} completed: "
                f"success={result.success}"
            )
            
            return result
        
        except asyncio.TimeoutError:
            logger.error(f"Command {parsed_cmd.command} timed out after {self.timeout}s")
            
            result = CommandResult(
                success=False,
                message=f"Command timed out after {self.timeout} seconds",
                error="The command took too long to execute"
            )
            
            if self.status_callback:
                await self.status_callback(
                    f"❌ Timeout: {result.message}",
                    context
                )
            
            return result
        
        except Exception as e:
            logger.error(
                f"Command {parsed_cmd.command} failed with exception: {e}",
                exc_info=True
            )
            
            result = CommandResult(
                success=False,
                message=f"Command failed: {parsed_cmd.command}",
                error=str(e)
            )
            
            if self.status_callback:
                await self.status_callback(
                    f"❌ Error: {str(e)}",
                    context
                )
            
            return result
    
    async def execute_batch(
        self,
        commands: list[ParsedCommand],
        context: Dict[str, Any]
    ) -> list[CommandResult]:
        """Execute multiple commands in sequence.
        
        Args:
            commands: List of parsed commands to execute
            context: Execution context
        
        Returns:
            List of CommandResults
        """
        results = []
        
        for cmd in commands:
            result = await self.execute(cmd, context)
            results.append(result)
            
            # Stop on first failure if configured
            if not result.success and context.get('stop_on_error', False):
                break
        
        return results
