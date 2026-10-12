# Create a traffic callback to extract latest traffic from link ID 2701 (causeway) and 4713 (second link ) via lta API

from typing import Dict
import base64
import requests
import numpy as np
from datetime import datetime
from utils.async_fetcher import run_in_thread, fetch_url_2min_cached, get_default_headers

from conf.api_urls import TRAFFIC_IMAGES_API_URL as _TRAFFIC_IMAGES_URL


def query_traffic_metadata() -> Dict:
    """
    Fetch traffic camera metadata from the data.gov.sg API, served from the
    shared 2-minute bucket cache so repeated calls within the same window
    never hit the network more than once.

    Returns:
        Dict keyed by camera_id, each value containing timestamp, image_url,
        lat, lon and md5.  Returns an empty dict on error.
    """
    data = fetch_url_2min_cached(_TRAFFIC_IMAGES_URL, headers=get_default_headers())
    if not data:
        print("No response received for traffic camera metadata")
        return {}
    items = data.get("items", [])
    if not items:
        return {}
    all_traffic_metadata_dict: Dict = {}
    for camera_feed in items[0].get("cameras", []):
        all_traffic_metadata_dict[camera_feed["camera_id"]] = {
            "timestamp": camera_feed["timestamp"],
            "image_url": camera_feed["image"],
            "lat": camera_feed["location"]["latitude"],
            "lon": camera_feed["location"]["longitude"],
            "md5": camera_feed["image_metadata"]["md5"],
        }
    return all_traffic_metadata_dict


@run_in_thread
def get_camera_image_base64_async(metadata_dict: Dict, camera_id: str, agent_id: str = "test_qzq") -> str:
    """
    Get camera feed image and convert to base64 string for display in Dash.
    
    Args:
        metadata_dict: Dictionary containing camera metadata
        camera_id: Camera ID to fetch
        agent_id: User agent ID for request header
    
    Returns:
        Base64 encoded image string or None if error
    """
    try:
        # Get image URL directly from metadata instead of using get_camera_feed
        if camera_id not in metadata_dict:
            return None
        
        image_url = metadata_dict[camera_id].get("image_url")
        if not image_url:
            return None
        
        # Randomised agent id
        rand_agent_id = agent_id + str(np.random.randint(0, 500))
        
        # Fetch image with timeout and stream=False to avoid blocking
        response = requests.get(
            image_url,
            stream=False,  # Changed to False to avoid blocking issues
            headers={'User-agent': rand_agent_id},
            timeout=5
        )
        
        response.raise_for_status()
        
        # Read the response content directly (not from raw stream)
        image_data = response.content
        
        # Convert to base64
        base64_string = base64.b64encode(image_data).decode('utf-8')
        
        # Determine image format (assuming JPEG, but could be PNG)
        # Most traffic camera feeds are JPEG
        image_format = "jpeg"
        
        # Return data URI format
        return f"data:image/{image_format};base64,{base64_string}"
    except (IOError, ValueError, AttributeError, requests.exceptions.RequestException) as error:
        print(f"Error converting image to base64 for camera {camera_id}: {error}")
        return None


def register_camera_feed_callbacks(app):
    """
    Register callbacks for displaying camera feed images on the main page.
    """
    from dash import Input, Output, State, html, no_update

    @app.callback(
        [Output('camera-feed-2701-container', 'children'),
         Output('camera-feed-4713-container', 'children'),
         Output('camera-2701-metadata', 'children'),
         Output('camera-4713-metadata', 'children')],
        Input('interval-component', 'n_intervals'),
        State('navigation-tabs', 'value')
    )
    def update_camera_feeds(n_intervals, active_tab):
        """
        Update camera feed images periodically.

        Args:
            n_intervals: Number of intervals (from dcc.Interval component)

        Returns:
            Tuple of (image_container_2701, image_container_4713, metadata_2701, metadata_4713)
        """
        _ = n_intervals
        if active_tab != 'main':
            return no_update, no_update, no_update, no_update

        # Default error response
        no_image_text = html.Div(
            "Image not available",
            style={
                "color": "#999",
                "fontSize": "0.875rem",
                "textAlign": "center",
            }
        )
        default_meta = "Metadata unavailable"
        
        try:
            # Metadata is served from the shared 2-minute cache — no extra
            # HTTP call is made if another callback already fetched this URL
            # in the current 2-minute window.
            metadata_dict = query_traffic_metadata()

            if not metadata_dict:
                return no_image_text, no_image_text, default_meta, default_meta

            # Get images for specific cameras with error handling
            img_2701 = None
            img_4713 = None
            try:
                future_2701 = get_camera_image_base64_async(metadata_dict, "2701")
                img_2701 = future_2701.result() if hasattr(future_2701, "result") else future_2701
            except Exception as e:
                print(f"Error fetching image for camera 2701: {e}")
            
            try:
                future_4713 = get_camera_image_base64_async(metadata_dict, "4713")
                img_4713 = future_4713.result() if hasattr(future_4713, "result") else future_4713
            except Exception as e:
                print(f"Error fetching image for camera 4713: {e}")

            # Extract timestamps and locations for captions
            timestamp_2701 = ""
            timestamp_4713 = ""
            
            if metadata_dict.get("2701"):
                timestamp = metadata_dict["2701"].get('timestamp', '')
                if timestamp and timestamp != 'N/A':
                    try:
                        if isinstance(timestamp, str):
                            parsed_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_time = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                            timestamp_2701 = f"{formatted_time} (Causeway)"
                        else:
                            timestamp_2701 = f"{str(timestamp)} (Causeway)"
                    except (ValueError, AttributeError):
                        timestamp_2701 = f"{str(timestamp)} (Causeway)" if timestamp else ""
            
            if metadata_dict.get("4713"):
                timestamp = metadata_dict["4713"].get('timestamp', '')
                if timestamp and timestamp != 'N/A':
                    try:
                        if isinstance(timestamp, str):
                            parsed_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_time = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                            timestamp_4713 = f"{formatted_time} (Second Link)"
                        else:
                            timestamp_4713 = f"{str(timestamp)} (Second Link)"
                    except (ValueError, AttributeError):
                        timestamp_4713 = f"{str(timestamp)} (Second Link)" if timestamp else ""

            # Create image containers
            if img_2701:
                container_2701 = html.Img(
                    src=img_2701,
                    style={
                        "width": "100%",
                        "height": "100%",
                        "objectFit": "cover",
                        "display": "block",
                    }
                )
            else:
                container_2701 = no_image_text

            if img_4713:
                container_4713 = html.Img(
                    src=img_4713,
                    style={
                        "width": "100%",
                        "height": "100%",
                        "objectFit": "cover",
                        "display": "block",
                    }
                )
            else:
                container_4713 = no_image_text

            # Return images and timestamps as captions
            return container_2701, container_4713, timestamp_2701, timestamp_4713
        except Exception as error:
            print(f"Error updating camera feeds: {error}")
            import traceback
            traceback.print_exc()
            return no_image_text, no_image_text, default_meta, default_meta
