"""
Rate limiter for API calls to prevent quota exhaustion.
"""
import time
from collections import deque
from threading import Lock


class RateLimiter:
    """Rate limiter using sliding window algorithm."""
    
    def __init__(self, max_calls, time_window_seconds):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window_seconds: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window_seconds
        self.calls = deque()
        self.lock = Lock()
    
    def can_call(self):
        """Check if a call can be made without exceeding the rate limit."""
        with self.lock:
            now = time.time()
            # Remove old calls outside the time window
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a call timestamp."""
        with self.lock:
            self.calls.append(time.time())
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded, then record the call."""
        while not self.can_call():
            time.sleep(0.5)
        self.record_call()
    
    def get_wait_time(self):
        """Get the time to wait before next call can be made."""
        with self.lock:
            if self.can_call():
                return 0
            
            now = time.time()
            # Remove old calls
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            if len(self.calls) < self.max_calls:
                return 0
            
            # Calculate wait time until oldest call expires
            oldest_call = self.calls[0]
            wait_time = (oldest_call + self.time_window) - now
            return max(0, wait_time)
    
    def reset(self):
        """Reset the rate limiter."""
        with self.lock:
            self.calls.clear()


class MultiProviderRateLimiter:
    """Rate limiter for multiple API providers."""
    
    def __init__(self):
        self.limiters = {}
    
    def add_provider(self, provider_name, max_calls, time_window_seconds):
        """Add a rate limiter for a specific provider."""
        self.limiters[provider_name] = RateLimiter(max_calls, time_window_seconds)
    
    def wait_if_needed(self, provider_name):
        """Wait if needed for the specified provider."""
        if provider_name in self.limiters:
            self.limiters[provider_name].wait_if_needed()
    
    def can_call(self, provider_name):
        """Check if a call can be made for the provider."""
        if provider_name in self.limiters:
            return self.limiters[provider_name].can_call()
        return True
    
    def get_wait_time(self, provider_name):
        """Get wait time for the provider."""
        if provider_name in self.limiters:
            return self.limiters[provider_name].get_wait_time()
        return 0
