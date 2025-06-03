"""
Simple size-limited cache for DevRev MCP server.

Prevents unbounded memory growth by limiting cache size and using simple LRU eviction.
"""

from collections import OrderedDict
from typing import Any, Dict, Optional, Union
import json

# Cache configuration constants
DEFAULT_CACHE_SIZE = 500


class SimpleCache:
    """Simple LRU cache with size limit to prevent memory leaks."""
    
    def __init__(self, max_size: int = DEFAULT_CACHE_SIZE):
        """Initialize cache with maximum size limit."""
        self.max_size = max_size
        self._cache: OrderedDict[str, str] = OrderedDict()
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache, moving it to end (most recently used)."""
        if key in self._cache:
            # Move to end (most recently used)
            value = self._cache.pop(key)
            self._cache[key] = value
            return value
        return None
    
    def set(self, key: str, value: Union[str, Dict[str, Any]]) -> None:
        """Set value in cache, evicting oldest if needed."""
        # Convert dict to JSON string if needed
        if isinstance(value, dict):
            cache_value = json.dumps(value, indent=2)
        else:
            cache_value = str(value)
        
        # Remove if already exists
        if key in self._cache:
            del self._cache[key]
        
        # Add to end
        self._cache[key] = cache_value
        
        # Evict oldest if over limit
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)  # Remove oldest (first item)
    
    def delete(self, key: str) -> bool:
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def size(self) -> int:
        """Get current number of cache entries."""
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache


# Global cache instance - replaces devrev_cache = {}
devrev_cache = SimpleCache(max_size=DEFAULT_CACHE_SIZE)