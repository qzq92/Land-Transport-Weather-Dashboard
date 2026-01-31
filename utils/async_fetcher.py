"""
Async data fetching utilities using ThreadPoolExecutor for parallel API calls.

Since Dash callbacks are synchronous, we use concurrent.futures.ThreadPoolExecutor
to parallelize I/O-bound operations (API calls) without blocking.
"""
import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Callable, Any, Optional, Tuple
from functools import wraps
from dotenv import load_dotenv

load_dotenv(override=True)

# Shared thread pool for all async operations
# Using max_workers=10 is reasonable for I/O-bound tasks
_executor = ThreadPoolExecutor(max_workers=10)

# Global cache for 2-minute interval updates
# Maps URL to {'data': json_dict, 'bucket': timestamp}
_2min_dynamic_cache: Dict[str, Any] = {}

# Global cache for 10-minute interval updates
# Maps URL to {'data': json_dict, 'bucket': timestamp}
_10min_dynamic_cache: Dict[str, Any] = {}


def get_current_2min_bucket() -> int:
    """Get the current 2-minute bucket start time (Unix timestamp)."""
    return int(time.time() // 120) * 120


def get_current_10min_bucket() -> int:
    """Get the current 10-minute bucket start time (Unix timestamp)."""
    return int(time.time() // 600) * 600


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
    global _2min_dynamic_cache
    
    current_bucket = get_current_2min_bucket()
    
    # Check cache
    if url in _2min_dynamic_cache:
        cached_item = _2min_dynamic_cache[url]
        if cached_item['bucket'] == current_bucket:
            # print(f"Serving from 2-minute cache: {url}")
            return cached_item['data']
            
    # Fetch fresh data
    # print(f"Fetching fresh data for 2-minute bucket: {url}")
    data = fetch_url(url, headers, timeout)
    
    if data is not None:
        _2min_dynamic_cache[url] = {
            'data': data,
            'bucket': current_bucket
        }
        
    return data


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
    global _10min_dynamic_cache

    current_bucket = get_current_10min_bucket()

    # Check cache
    if url in _10min_dynamic_cache:
        cached_item = _10min_dynamic_cache[url]
        if cached_item['bucket'] == current_bucket:
            # print(f"Serving from 10-minute cache: {url}")
            return cached_item['data']

    # Fetch fresh data
    # print(f"Fetching fresh data for 10-minute bucket: {url}")
    data = fetch_url(url, headers, timeout)

    if data is not None:
        _10min_dynamic_cache[url] = {
            'data': data,
            'bucket': current_bucket
        }

    return data


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


def fetch_multiple_async(
    urls: List[str],
    headers: Optional[Dict] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Fetch multiple URLs in parallel using threading.
    
    Args:
        urls: List of URLs to fetch
        headers: Optional headers dict (shared for all requests)
        timeout: Request timeout in seconds
    
    Returns:
        Dict mapping URL to response data (or None if failed)
    """
    if headers is None:
        headers = get_default_headers()
    
    futures = {
        _executor.submit(fetch_url, url, headers, timeout): url
        for url in urls
    }
    
    results = {}
    for future in as_completed(futures):
        url = futures[future]
        try:
            results[url] = future.result()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            results[url] = None
    
    return results


def fetch_with_callbacks(
    fetch_configs: List[Tuple[str, Callable[[Any], Any]]],
    headers: Optional[Dict] = None,
    timeout: int = 10
) -> List[Any]:
    """
    Fetch multiple URLs and apply callbacks to transform results.
    
    Args:
        fetch_configs: List of tuples (url, callback_fn) where callback_fn
                      transforms the raw API response
        headers: Optional headers dict
        timeout: Request timeout in seconds
    
    Returns:
        List of transformed results in the same order as fetch_configs
    """
    if headers is None:
        headers = get_default_headers()
    
    # Submit all fetch tasks
    futures_map = {}
    for idx, (url, callback) in enumerate(fetch_configs):
        future = _executor.submit(fetch_url, url, headers, timeout)
        futures_map[future] = (idx, callback)
    
    # Collect results maintaining order
    results = [None] * len(fetch_configs)
    for future in as_completed(futures_map):
        idx, callback = futures_map[future]
        try:
            data = future.result()
            results[idx] = callback(data) if callback else data
        except Exception as e:
            print(f"Error processing result {idx}: {e}")
            results[idx] = None
    
    return results


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


def run_parallel(*funcs_with_args: Tuple[Callable, tuple, dict]) -> List[Any]:
    """
    Run multiple functions in parallel and wait for all to complete.
    
    Args:
        funcs_with_args: Tuples of (function, args_tuple, kwargs_dict)
    
    Returns:
        List of results in the same order as input functions
    
    Usage:
        results = run_parallel(
            (fetch_temp, (), {}),
            (fetch_rainfall, (), {}),
            (fetch_humidity, (), {})
        )
    """
    futures = []
    for func, args, kwargs in funcs_with_args:
        future = _executor.submit(func, *args, **kwargs)
        futures.append(future)
    
    # Wait for all and collect results
    return [f.result() for f in futures]


# Cleanup function to shutdown executor gracefully
def shutdown_executor():
    """Shutdown the thread pool executor gracefully."""
    _executor.shutdown(wait=True)

