import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, key, max_requests=60, window=60):
        """Check if request is allowed based on rate limit"""
        now = time.time()
        
        # Remove old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] 
                              if now - req_time < window]
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def wait_if_needed(self, key, max_requests=60, window=60):
        """Wait if rate limit would be exceeded"""
        if not self.is_allowed(key, max_requests, window):
            sleep_time = window - (time.time() - self.requests[key][0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.requests[key].append(time.time())