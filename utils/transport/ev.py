"""EV charging point data helpers."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

from conf.api_urls import EVC_BATCH_URL, EV_CHARGING_URL, ONEMAP_REVGEOCODE_URL
from utils.async_fetcher import run_in_thread


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_postal_code_from_coords(lat: Optional[float] = None, lon: Optional[float] = None) -> str:
    """Resolve a postal code from coordinates via OneMap reverse geocoding."""
    if lat is None or lon is None:
        return ""

    try:
        url = f"{ONEMAP_REVGEOCODE_URL}?latitude={lat}&longitude={lon}"
        api_token = os.getenv("ONEMAP_API_KEY")
        headers = {"Authorization": api_token} if api_token else {}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return results[0].get("POSTAL_CODE", "")
    except Exception as error:
        print(f"Error getting postal code from coordinates: {error}")
    return ""


@run_in_thread
def fetch_ev_charging_points_async(postal_code: str):
    """Fetch EV charging points near a postal code from LTA DataMall."""
    if not postal_code:
        return None

    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None

    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json",
    }
    try:
        response = requests.get(
            EV_CHARGING_URL,
            headers=headers,
            params={"PostalCode": postal_code},
            timeout=10,
        )
        if 200 <= response.status_code < 300:
            return response.json()
        print(f"EV charging API request failed: status={response.status_code}")
    except (requests.exceptions.RequestException, ValueError) as error:
        print(f"Error fetching EV charging points data: {error}")
    return None


@run_in_thread
def fetch_evc_batch_async(
    output_path: Optional[str] = None,
    skip_if_exists: bool = False,
) -> Optional[Dict[str, Any]]:
    """Download the LTA EVCBatch dataset file and return file metadata."""
    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None

    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(EVC_BATCH_URL, headers=headers, timeout=30)
        if not (200 <= response.status_code < 300):
            print(f"EVCBatch API request failed: status={response.status_code}")
            return None

        value_data = response.json().get("value")
        batch_link = None
        if isinstance(value_data, dict):
            batch_link = value_data.get("Link") or value_data.get("link") or value_data.get("url")
        elif isinstance(value_data, str) and value_data.startswith(("http://", "https://")):
            batch_link = value_data
        elif isinstance(value_data, list) and value_data:
            first_item = value_data[0]
            if isinstance(first_item, dict):
                batch_link = first_item.get("Link") or first_item.get("link") or first_item.get("url")
            elif isinstance(first_item, str) and first_item.startswith(("http://", "https://")):
                batch_link = first_item

        if not batch_link:
            print("No EVCBatch download link found in response")
            return None

        batch_response = requests.get(batch_link, timeout=120, stream=True)
        if not (200 <= batch_response.status_code < 300):
            print(f"EVCBatch download failed: status={batch_response.status_code}")
            return None

        if output_path is None:
            data_dir = _project_root() / "data"
            data_dir.mkdir(exist_ok=True)
            parsed_url = urlparse(batch_link)
            url_path = parsed_url.path.lower()
            content_type = batch_response.headers.get("Content-Type", "").lower()
            if url_path.endswith(".csv") or "csv" in content_type:
                file_ext = ".csv"
            elif url_path.endswith(".xml") or "xml" in content_type:
                file_ext = ".xml"
            else:
                file_ext = ".json"
            output_path = str(data_dir / f"EVCBatch{file_ext}")

        if skip_if_exists and os.path.exists(output_path):
            return {
                "link": batch_link,
                "file_path": output_path,
                "file_size": os.path.getsize(output_path),
                "format": Path(output_path).suffix.lstrip(".") or "unknown",
                "success": True,
                "skipped": True,
            }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        file_size = 0
        with open(output_path, "wb") as file:
            for chunk in batch_response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    file_size += len(chunk)

        return {
            "link": batch_link,
            "file_path": output_path,
            "file_size": file_size,
            "format": Path(output_path).suffix.lstrip(".") or "unknown",
            "success": True,
            "skipped": False,
        }
    except (requests.exceptions.RequestException, ValueError, OSError) as error:
        print(f"Error fetching EVCBatch data: {error}")
        return None
