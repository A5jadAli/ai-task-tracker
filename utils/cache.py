"""
Response caching to reduce redundant API calls.
"""
import json
import hashlib
import time
from datetime import datetime, timedelta
from threading import Lock


class ResponseCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, ttl_minutes=60):
        """
        Initialize cache.
        
        Args:
            ttl_minutes: Time-to-live in minutes
        """
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.lock = Lock()
    
    def get(self, key):
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if datetime.now() - timestamp < self.ttl:
                    return value
                else:
                    # Remove expired entry
                    del self.cache[key]
        return None
    
    def set(self, key, value):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            self.cache[key] = (value, datetime.now())
    
    def delete(self, key):
        """Delete a key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        with self.lock:
            now = datetime.now()
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if now - timestamp >= self.ttl
            ]
            for key in expired_keys:
                del self.cache[key]
    
    def cache_key(self, *args, **kwargs):
        """
        Generate cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            str: Hash-based cache key
        """
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def size(self):
        """Get number of cached items."""
        with self.lock:
            return len(self.cache)


def cached(cache_instance, ttl_minutes=None):
    """
    Decorator for caching function results.
    
    Args:
        cache_instance: ResponseCache instance
        ttl_minutes: Override TTL for this function
    
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_instance.cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result)
            return result
        
        return wrapper
    return decorator
