"""
Command parser for extracting commands from text.
"""
import re
import shlex
from typing import Optional, List
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedCommand:
    """Parsed command data.
    
    Attributes:
        prefix: Command prefix used (e.g., "agent")
        command: Command name (e.g., "create-pr")
        args: List of command arguments
        raw_text: Original text that was parsed
    """
    prefix: str
    command: str
    args: List[str]
    raw_text: str


class CommandParser:
    """Parses command strings from text.
    
    Supports various command formats:
    - Simple: "agent help"
    - With args: "agent create-pr feature-auth"
    - With quoted args: "agent send-message 'Hello world'"
    - Case insensitive: "AGENT HELP" or "Agent Help"
    """
    
    def __init__(self, prefix: str = "agent"):
        """Initialize parser.
        
        Args:
            prefix: Command prefix to look for (default: "agent")
        """
        self.prefix = prefix.lower()
        
        # Pattern: prefix + command + optional args
        # Matches: "agent command arg1 arg2"
        self.command_pattern = re.compile(
            rf"^\s*{re.escape(self.prefix)}\s+(\S+)(?:\s+(.+))?\s*$",
            re.IGNORECASE
        )
    
    def is_command(self, text: str) -> bool:
        """Check if text contains a command.
        
        Args:
            text: Text to check
        
        Returns:
            True if text starts with command prefix
        """
        if not text:
            return False
        
        return bool(self.command_pattern.match(text.strip()))
    
    def parse(self, text: str) -> Optional[ParsedCommand]:
        """Parse command from text.
        
        Args:
            text: Text containing command
        
        Returns:
            ParsedCommand if valid command found, None otherwise
        
        Example:
            >>> parser = CommandParser("agent")
            >>> cmd = parser.parse("agent create-pr feature-auth to main")
            >>> cmd.command
            'create-pr'
            >>> cmd.args
            ['feature-auth', 'to', 'main']
        """
        if not text:
            return None
        
        match = self.command_pattern.match(text.strip())
        if not match:
            return None
        
        command = match.group(1).lower()
        args_str = match.group(2) or ""
        
        # Parse arguments, respecting quotes
        args = self._parse_args(args_str)
        
        logger.debug(f"Parsed command: {command}, args: {args}")
        
        return ParsedCommand(
            prefix=self.prefix,
            command=command,
            args=args,
            raw_text=text
        )
    
    def _parse_args(self, args_str: str) -> List[str]:
        """Parse arguments from string, respecting quotes.
        
        Args:
            args_str: Arguments string
        
        Returns:
            List of parsed arguments
        
        Example:
            >>> parser._parse_args('arg1 "arg with spaces" arg3')
            ['arg1', 'arg with spaces', 'arg3']
        """
        if not args_str:
            return []
        
        try:
            # Use shlex to properly handle quoted strings
            return shlex.split(args_str)
        except ValueError as e:
            # If shlex fails (e.g., unclosed quote), fall back to simple split
            logger.warning(f"Failed to parse args with shlex: {e}, using simple split")
            return args_str.split()
    
    def extract_flags(self, args: List[str]) -> tuple[List[str], dict]:
        """Extract flags from arguments.
        
        Flags are arguments starting with -- or -.
        
        Args:
            args: List of arguments
        
        Returns:
            Tuple of (remaining_args, flags_dict)
        
        Example:
            >>> extract_flags(['arg1', '--flag', 'value', '-f'])
            (['arg1'], {'flag': 'value', 'f': True})
        """
        remaining = []
        flags = {}
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg.startswith('--'):
                # Long flag: --flag or --flag=value
                if '=' in arg:
                    key, value = arg[2:].split('=', 1)
                    flags[key] = value
                else:
                    key = arg[2:]
                    # Check if next arg is the value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        flags[key] = args[i + 1]
                        i += 1
                    else:
                        flags[key] = True
            elif arg.startswith('-') and len(arg) > 1:
                # Short flag: -f
                flags[arg[1:]] = True
            else:
                remaining.append(arg)
            
            i += 1
        
        return remaining, flags
