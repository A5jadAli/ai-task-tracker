"""
Configuration parser with YAML support and environment variable expansion.
"""
import os
import yaml
import re
from typing import Any, Dict
from pathlib import Path


class ConfigParser:
    """Parse and manage agent configuration."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize config parser.
        
        Args:
            config_path: Path to YAML config file
        """
        self.config_path = config_path
        self.config = {}
        
        if config_path and os.path.exists(config_path):
            self.load(config_path)
    
    def load(self, config_path: str):
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML file
        """
        self.config_path = config_path
        
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        # Expand environment variables
        self.config = self._expand_env_vars(raw_config)
    
    def _expand_env_vars(self, obj: Any) -> Any:
        """
        Recursively expand environment variables in config.
        
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        
        Args:
            obj: Config object (dict, list, str, etc.)
        
        Returns:
            Object with expanded environment variables
        """
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._expand_string(obj)
        else:
            return obj
    
    def _expand_string(self, s: str) -> str:
        """
        Expand environment variables in a string.
        
        Args:
            s: String with potential ${VAR} references
        
        Returns:
            String with expanded variables
        """
        # Pattern: ${VAR_NAME} or ${VAR_NAME:default}
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ''
            return os.getenv(var_name, default_value)
        
        return re.sub(pattern, replacer, s)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., 'monitoring.slack.enabled')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by dot-notation key.
        
        Args:
            key: Dot-notation key
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, output_path: str = None):
        """
        Save configuration to YAML file.
        
        Args:
            output_path: Path to save (uses original path if not specified)
        """
        path = output_path or self.config_path
        
        if not path:
            raise ValueError("No output path specified")
        
        with open(path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def to_dict(self) -> Dict:
        """Get configuration as dictionary."""
        return self.config.copy()


def load_config(config_path: str) -> ConfigParser:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        ConfigParser instance
    """
    return ConfigParser(config_path)
