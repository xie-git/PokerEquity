import time
import functools
from collections import OrderedDict
from typing import Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class LruTtlCache:
    """LRU cache with TTL expiration. Interface-compatible for future Redis swap."""
    
    def __init__(self, maxsize: int = 100_000, ttl: int = 30*24*3600):
        self.maxsize = maxsize
        self.ttl = ttl
        self.store: OrderedDict[str, Tuple[float, Any]] = OrderedDict()
        
    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        item = self.store.get(key)
        if not item:
            return None
            
        expires_at, value = item
        if expires_at < now:
            self.store.pop(key, None)
            return None
            
        # Move to end (mark as recently used)
        self.store.move_to_end(key)
        return value
    
    def set(self, key: str, value: Any) -> None:
        now = time.time()
        self.store[key] = (now + self.ttl, value)
        self.store.move_to_end(key)
        
        # Evict oldest if over max size
        if len(self.store) > self.maxsize:
            self.store.popitem(last=False)
    
    def clear(self) -> None:
        self.store.clear()
    
    def size(self) -> int:
        return len(self.store)

class MetricsLogger:
    """Simple metrics logger for request timing."""
    
    def __init__(self):
        self.request_times = []
        self.max_samples = 1000  # Keep last 1000 requests
        
    def log_request(self, endpoint: str, duration_ms: float) -> None:
        self.request_times.append({
            'endpoint': endpoint,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })
        
        # Keep only recent samples
        if len(self.request_times) > self.max_samples:
            self.request_times = self.request_times[-self.max_samples:]
    
    def get_stats(self) -> dict:
        if not self.request_times:
            return {'count': 0}
            
        durations = [r['duration_ms'] for r in self.request_times[-100:]]  # Last 100
        durations.sort()
        
        return {
            'count': len(self.request_times),
            'avg_ms': sum(durations) / len(durations),
            'p50_ms': durations[len(durations)//2],
            'p95_ms': durations[int(len(durations)*0.95)] if len(durations) > 20 else durations[-1]
        }

# Global instances
equity_cache = LruTtlCache()
metrics = MetricsLogger()

def timed_endpoint(endpoint_name: str):
    """Decorator to time API endpoints."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics.log_request(endpoint_name, duration_ms)
                logger.info(f"{endpoint_name}: {duration_ms:.1f}ms")
        return wrapper
    return decorator