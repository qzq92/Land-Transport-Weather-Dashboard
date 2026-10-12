"""
Async data fetching utilities using ThreadPoolExecutor for parallel API calls.

Since Dash callbacks are synchronous, we use concurrent.futures.ThreadPoolExecutor
to parallelize I/O-bound operations (API calls) without blocking.
"""
import os
import time
import requests
import concurrent.futures
from typing import Dict, Callable, Any, Optional
from functools import wraps
from dotenv import load_dotenv
import threading
from collections import OrderedDict

load_dotenv(override=True)

from conf.cache_config import CACHE_TTL_2MIN, CACHE_TTL_10MIN

# Shared thread pool for all async operations
# Using max_workers=10 is reasonable for I/O-bound tasks
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

# Bounded in-memory LRU caches (URL -> {'data': ..., 'bucket': ...})
_MAX_CACHE_ENTRIES = int(os.getenv("ASYNC_FETCHER_MAX_CACHE_ENTRIES", "256"))
_MAX_INFLIGHT_KEYS = int(os.getenv("ASYNC_FETCHER_MAX_INFLIGHT_KEYS", "512"))
_INFLIGHT_WAIT_SECONDS = float(os.getenv("ASYNC_FETCHER_INFLIGHT_WAIT_SECONDS", "1.5"))

_2min_dynamic_cache: "OrderedDict[str, Any]" = OrderedDict()
_10min_dynamic_cache: "OrderedDict[str, Any]" = OrderedDict()
_inflight_events: "OrderedDict[str, threading.Event]" = OrderedDict()
_in_memory_lock = threading.Lock()


def get_current_2min_bucket() -> int:
    """Get the current 2-minute bucket start time (Unix timestamp)."""
    return int(time.time() // CACHE_TTL_2MIN) * CACHE_TTL_2MIN


def get_current_10min_bucket() -> int:
    """Get the current 10-minute bucket start time (Unix timestamp)."""
    return int(time.time() // CACHE_TTL_10MIN) * CACHE_TTL_10MIN


def fetch_url_2min_cached(url: str, headers: Optional[Dict] = None, timeout: int = 10) -> Optional[dict]:
    """
    Fetch data from a URL with 2-minute in-memory caching aligned to system clock.
    
    Args:
        url: The URL to fetch
        headers: Optional headers dict
        timeout: Request timeout in seconds
        
    Returns:
        JSON response from cache or API
    """
    return _fetch_with_bucket_cache(
        namespace="2min",
        url=url,
        headers=headers,
        timeout=timeout,
        current_bucket=get_current_2min_bucket(),
        memory_cache=_2min_dynamic_cache,
    )


def fetch_url_10min_cached(url: str, headers: Optional[Dict] = None, timeout: int = 10) -> Optional[dict]:
    """
    Fetch data from a URL with 10-minute in-memory caching aligned to system clock.

    Args:
        url: The URL to fetch
        headers: Optional headers dict
        timeout: Request timeout in seconds

    Returns:
        JSON response from cache or API
    """
    return _fetch_with_bucket_cache(
        namespace="10min",
        url=url,
        headers=headers,
        timeout=timeout,
        current_bucket=get_current_10min_bucket(),
        memory_cache=_10min_dynamic_cache,
    )


def _fetch_with_bucket_cache(
    namespace: str,
    url: str,
    headers: Optional[Dict],
    timeout: int,
    current_bucket: int,
    memory_cache: Dict[str, Any],
) -> Optional[dict]:
    """Fetch with bounded in-memory cache and in-flight dedupe."""
    return _fetch_with_in_memory_cache(namespace, url, headers, timeout, current_bucket, memory_cache)


def _fetch_with_in_memory_cache(
    namespace: str,
    url: str,
    headers: Optional[Dict],
    timeout: int,
    current_bucket: int,
    memory_cache: "OrderedDict[str, Any]",
) -> Optional[dict]:
    """Bounded LRU cache with in-flight request dedupe."""
    inflight_key = f"{namespace}:{current_bucket}:{url}"

    with _in_memory_lock:
        cached_item = memory_cache.get(url)
        if cached_item and cached_item.get("bucket") == current_bucket:
            memory_cache.move_to_end(url)
            return cached_item.get("data")
        owner_event = _inflight_events.get(inflight_key)
        if owner_event is None:
            owner_event = threading.Event()
            _inflight_events[inflight_key] = owner_event
            _evict_oldest_entries(_inflight_events, _MAX_INFLIGHT_KEYS)
            is_owner = True
        else:
            _inflight_events.move_to_end(inflight_key)
            is_owner = False

    if not is_owner:
        owner_event.wait(_INFLIGHT_WAIT_SECONDS)
        with _in_memory_lock:
            cached_item = memory_cache.get(url)
            if cached_item and cached_item.get("bucket") == current_bucket:
                memory_cache.move_to_end(url)
                return cached_item.get("data")
        # Fail-open if owner did not populate cache in time.
        data = fetch_url(url, headers, timeout)
        if data is not None:
            with _in_memory_lock:
                memory_cache[url] = {"data": data, "bucket": current_bucket}
                memory_cache.move_to_end(url)
                _evict_oldest_entries(memory_cache, _MAX_CACHE_ENTRIES)
        return data

    try:
        data = fetch_url(url, headers, timeout)
        if data is not None:
            with _in_memory_lock:
                memory_cache[url] = {"data": data, "bucket": current_bucket}
                memory_cache.move_to_end(url)
                _evict_oldest_entries(memory_cache, _MAX_CACHE_ENTRIES)
        return data
    finally:
        with _in_memory_lock:
            event = _inflight_events.pop(inflight_key, None)
            if event is not None:
                event.set()


def _evict_oldest_entries(cache: "OrderedDict[str, Any]", max_entries: int) -> None:
    """Trim ordered mapping to stay within a maximum entry limit."""
    while len(cache) > max_entries:
        cache.popitem(last=False)


def get_default_headers() -> Dict[str, str]:
    """Get default headers for Data.gov.sg API requests."""
    api_key = os.getenv('DATA_GOV_API')
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    if api_key:
        headers["X-Api-Key"] = api_key
    return headers


def fetch_url(url: str, headers: Optional[Dict] = None, timeout: int = 10, max_retries: int = 3) -> Optional[dict]:
    """
    Fetch data from a URL with error handling and exponential backoff retry for 5XX errors.
    
    Args:
        url: The URL to fetch
        headers: Optional headers dict (uses default if not provided)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        JSON response as dict, or None if error
    """
    if headers is None:
        headers = get_default_headers()
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            
            # Accept any 2xx status code as success (200 OK, 201 Created, etc.)
            if 200 <= response.status_code < 300:
                return response.json()
            
            # Check for 5XX server errors (500-599)
            if 500 <= response.status_code < 600:
                if attempt < max_retries - 1:
                    # Exponential backoff: 3 * (2^attempt) seconds (3s, 6s, 12s)
                    wait_time = 3 * (2 ** attempt)
                    print(f"API request failed with {response.status_code}: {url} - retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                print(f"API request failed after {max_retries} attempts: {url} - status={response.status_code}")
                return None
            
            # For non-5XX errors (4XX client errors), don't retry
            print(f"API request failed: {url} - status={response.status_code}")
            return None
                
        except (requests.exceptions.RequestException, ValueError) as error:
            if attempt < max_retries - 1:
                # Exponential backoff: 3 * (2^attempt) seconds (3s, 6s, 12s)
                wait_time = 3 * (2 ** attempt)
                print(f"Error fetching {url}: {error} - retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            print(f"Error fetching {url} after {max_retries} attempts: {error}")
    
    return None


def fetch_async(url: str, headers: Optional[Dict] = None, timeout: int = 10):
    """
    Submit an async fetch request to the thread pool.
    
    Args:
        url: The URL to fetch
        headers: Optional headers dict
        timeout: Request timeout in seconds
    
    Returns:
        Future object that will contain the result
    """
    return _executor.submit(fetch_url, url, headers, timeout)


def run_in_thread(func: Callable) -> Callable:
    """
    Decorator to run a function in a thread pool.
    Returns a Future that can be awaited with .result()
    
    Usage:
        @run_in_thread
        def slow_function(x):
            time.sleep(1)
            return x * 2
        
        future = slow_function(5)
        result = future.result()  # Blocks until complete
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return _executor.submit(func, *args, **kwargs)
    return wrapper

