"""
Helper functions for initiate-download API endpoints from data.gov.sg.

This module consolidates the logic for fetching datasets that require
the initiate-download pattern: first call initiate-download to get a URL,
then fetch the actual data from that URL.
"""
import os
import time
import glob
import requests
from typing import Optional, Dict, Any
from utils.async_fetcher import fetch_url
from conf.api_urls import DATASET_IDS, initiate_download_url
from conf.cache_config import TTL_INITIATE_DOWNLOAD_DATASETS

# Default cache TTL — sourced from centralised config
DEFAULT_CACHE_TTL: int = TTL_INITIATE_DOWNLOAD_DATASETS

# Global cache storage: {dataset_id: {'data': ..., 'timestamp': ...}}
_dataset_caches: Dict[str, Dict[str, Any]] = {}


def get_initiate_download_url(dataset_id: str) -> str:
    """
    Get the initiate-download URL for a given dataset ID.

    Args:
        dataset_id: Dataset ID (e.g., 'd_753090823cc9920ac41efaa6530c5893')

    Returns:
        Full URL for the initiate-download endpoint
    """
    return initiate_download_url(dataset_id)


def initiate_download(dataset_id: str) -> Optional[str]:
    """
    Call the initiate-download endpoint to get a download URL.

    Args:
        dataset_id: Dataset ID

    Returns:
        Download URL string if successful, None otherwise
    """
    url = get_initiate_download_url(dataset_id)
    print(f"Initiating download for dataset {dataset_id}: {url}")

    init_response = fetch_url(url)

    if init_response is None:
        print("Failed to initiate download: No response")
        return None

    if init_response.get('code') != 0:
        error_msg = init_response.get('errorMsg', 'Unknown error')
        print(f"Failed to initiate download: {error_msg}")
        return None

    # Extract URL from response structure: {"code": 0, "data": {"url": "..."}}
    data = init_response.get('data', {})
    download_url = data.get('url')

    if not download_url:
        print("No download URL in initiate-download response")
        print(f"Response data: {data}")
        return None

    print(f"Download URL extracted successfully: {download_url[:80]}...")
    return download_url


def fetch_dataset_via_initiate_download(
    dataset_id: str,
    dataset_name: Optional[str] = None,
    cache_ttl: int = DEFAULT_CACHE_TTL,
    use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Fetch dataset using the initiate-download pattern with caching.

    This function:
    1. Checks cache if enabled and valid
    2. Calls initiate-download to get download URL
    3. Fetches the actual data from the download URL
    4. Updates cache if successful

    Args:
        dataset_id: Dataset ID (e.g., 'd_753090823cc9920ac41efaa6530c5893')
        dataset_name: Optional name for logging (e.g., 'ERP Gantry')
        cache_ttl: Cache time-to-live in seconds (default: 24 hours)
        use_cache: Whether to use caching (default: True)

    Returns:
        Dictionary containing the dataset data or None if error
    """
    if dataset_name is None:
        dataset_name = dataset_id

    # Check cache if enabled
    if use_cache:
        cached_data = get_cached_dataset(dataset_id, cache_ttl)
        if cached_data is not None:
            print(f"Using cached {dataset_name} data")
            return cached_data

    # Step 1: Call initiate-download to get download URL
    download_url = initiate_download(dataset_id)

    if not download_url:
        print(f"Failed to get download URL for {dataset_name}")
        return None

    # Step 2: Fetch the actual data from the download URL
    print(f"Downloading {dataset_name} data from: {download_url[:80]}...")
    data = fetch_url(download_url)

    if not data:
        print(f"Failed to download {dataset_name} data from URL")
        return None

    print(f"Successfully downloaded {dataset_name} data")

    # Update cache if successful and caching is enabled
    if use_cache and data is not None:
        current_time = time.time()
        _dataset_caches[dataset_id] = {
            'data': data,
            'timestamp': current_time
        }
        print(f"{dataset_name} data cached successfully")

    return data


def get_cached_dataset(dataset_id: str, cache_ttl: int = DEFAULT_CACHE_TTL) -> Optional[Dict[str, Any]]:
    """
    Get cached dataset if it exists and is still valid.

    Args:
        dataset_id: Dataset ID
        cache_ttl: Cache time-to-live in seconds

    Returns:
        Cached data if valid, None otherwise
    """
    if dataset_id not in _dataset_caches:
        return None

    cache_entry = _dataset_caches[dataset_id]
    current_time = time.time()

    # Check if cache is valid
    if (cache_entry['data'] is not None and
            current_time - cache_entry['timestamp'] < cache_ttl):
        return cache_entry['data']

    # Cache expired
    return None


def clear_dataset_cache(dataset_id: Optional[str] = None):
    """
    Clear cache for a specific dataset or all datasets.

    Args:
        dataset_id: Dataset ID to clear. If None, clears all caches.
    """
    if dataset_id is None:
        _dataset_caches.clear()
        print("All dataset caches cleared")
    else:
        if dataset_id in _dataset_caches:
            del _dataset_caches[dataset_id]
            print(f"Cache cleared for dataset {dataset_id}")
        else:
            print(f"No cache found for dataset {dataset_id}")


# Convenience functions for specific datasets
def fetch_erp_gantry_data(use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Fetch ERP gantry GeoJSON data.

    Args:
        use_cache: Whether to use caching (default: True)

    Returns:
        Dictionary containing GeoJSON data or None if error
    """
    return fetch_dataset_via_initiate_download(
        dataset_id=DATASET_IDS['ERP_GANTRY'],
        dataset_name='ERP Gantry',
        use_cache=use_cache
    )


def fetch_pub_cctv_data(use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Fetch PUB CCTV GeoJSON data.

    Args:
        use_cache: Whether to use caching (default: True)

    Returns:
        Dictionary containing GeoJSON data or None if error
    """
    return fetch_dataset_via_initiate_download(
        dataset_id=DATASET_IDS['PUB_CCTV'],
        dataset_name='PUB CCTV',
        use_cache=use_cache
    )


def clear_csv_files(data_dir: Optional[str] = None, project_root: Optional[str] = None) -> int:
    """
    Clear all CSV files in the data directory.

    Args:
        data_dir: Optional full path to data directory.
                 If None, uses data/ relative to project root
        project_root: Optional project root directory. If None, auto-detects from this file's location

    Returns:
        Number of CSV files deleted
    """
    # Determine data directory path
    if data_dir is None:
        if project_root is None:
            # Get project root (parent of utils folder)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_file_dir)
        data_dir = os.path.join(project_root, 'data')

    if not os.path.exists(data_dir):
        print(f"Data directory does not exist: {data_dir}")
        return 0

    # Find all CSV files
    csv_pattern = os.path.join(data_dir, '*.csv')
    csv_files = glob.glob(csv_pattern)

    # Files to preserve (sourced online, should not be deleted)
    preserved_files = ['MRTStations.csv']

    deleted_count = 0
    for csv_file in csv_files:
        # Skip preserved files
        if os.path.basename(csv_file) in preserved_files:
            print(f"Preserving CSV file: {os.path.basename(csv_file)}")
            continue
        
        try:
            os.remove(csv_file)
            print(f"Deleted CSV file: {os.path.basename(csv_file)}")
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting {csv_file}: {e}")

    if deleted_count > 0:
        print(f"Cleared {deleted_count} CSV file(s) from data directory")
    else:
        print("No CSV files found to clear")

    return deleted_count


def download_hdb_carpark_csv(
    output_path: Optional[str] = None,
    project_root: Optional[str] = None,
    skip_if_exists: bool = True
) -> bool:
    """
    Download HDB carpark CSV data via initiate-download and save to file.

    This function:
    1. Checks if file exists (if skip_if_exists is True)
    2. Calls initiate-download to get S3 download URL
    3. Downloads the CSV content from S3
    4. Saves it to data/HDBCarparkInformation.csv (overwrites existing)

    Args:
        output_path: Optional full path to output CSV file.
                    If None, uses data/HDBCarparkInformation.csv relative to project root
        project_root: Optional project root directory. If None, auto-detects from this file's location
        skip_if_exists: If True, skip download if file already exists (default: True)

    Returns:
        True if download and save was successful or file already exists, False otherwise
    """
    dataset_id = DATASET_IDS['HDB_CARPARK']

    # Determine output path
    if output_path is None:
        if project_root is None:
            # Get project root (parent of utils folder)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_file_dir)
        output_path = os.path.join(project_root, 'data', 'HDBCarparkInformation.csv')

    # Check if file exists and skip if requested
    if skip_if_exists and os.path.exists(output_path):
        print(f"HDB carpark CSV file already exists: {output_path}")
        print("Skipping download (skip_if_exists=True)")
        return True

    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Step 1: Call initiate-download to get S3 URL
    print("Downloading HDB carpark data via initiate-download...")
    download_url = initiate_download(dataset_id)

    if not download_url:
        print("Failed to get download URL for HDB carpark data")
        return False

    # Step 2: Download CSV content from S3 URL
    print(f"Downloading CSV from S3: {download_url[:80]}...")
    try:
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()

        # Save CSV content to file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"Successfully downloaded and saved HDB carpark data to {output_path}")
        print(f"File size: {len(response.content)} bytes")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading CSV from S3 URL: {e}")
        return False
    except Exception as e:
        print(f"Error saving CSV file: {e}")
        import traceback
        traceback.print_exc()
        return False


def download_speed_camera_csv(
    output_path: Optional[str] = None,
    project_root: Optional[str] = None,
    skip_if_exists: bool = True
) -> bool:
    """
    Download speed camera CSV data via initiate-download and save to file.

    This function:
    1. Checks if file exists (if skip_if_exists is True)
    2. Calls initiate-download to get S3 download URL
    3. Downloads the CSV content from S3
    4. Saves it to data/speed_camera.csv (overwrites existing)

    Args:
        output_path: Optional full path to output CSV file.
                    If None, uses data/speed_camera.csv relative to project root
        project_root: Optional project root directory. If None, auto-detects from this file's location
        skip_if_exists: If True, skip download if file already exists (default: True)

    Returns:
        True if download and save was successful or file already exists, False otherwise
    """
    dataset_id = DATASET_IDS['SPEED_CAMERA']

    # Determine output path
    if output_path is None:
        if project_root is None:
            # Get project root (parent of utils folder)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_file_dir)
        output_path = os.path.join(project_root, 'data', 'speed_camera.csv')

    # Check if file exists and skip if requested
    if skip_if_exists and os.path.exists(output_path):
        print(f"Speed camera CSV file already exists: {output_path}")
        print("Skipping download (skip_if_exists=True)")
        return True

    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Step 1: Call initiate-download to get S3 URL
    print("Downloading speed camera data via initiate-download...")
    download_url = initiate_download(dataset_id)

    if not download_url:
        print("Failed to get download URL for speed camera data")
        return False

    # Step 2: Download CSV content from S3 URL
    print(f"Downloading CSV from S3: {download_url[:80]}...")
    try:
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()

        # Save CSV content to file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"Successfully downloaded and saved speed camera data to {output_path}")
        print(f"File size: {len(response.content)} bytes")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading CSV from S3 URL: {e}")
        return False
    except Exception as e:
        print(f"Error saving CSV file: {e}")
        import traceback
        traceback.print_exc()
        return False

