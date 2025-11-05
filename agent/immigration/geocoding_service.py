"""
Geocoding service using Google Maps Geocoding API
"""

import os
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for geocoding addresses to coordinates using Google Geocoding API"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            logger.error("GOOGLE_MAPS_API_KEY environment variable not set")
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    async def geocode_address(self, address: str, city: str = "Hong Kong") -> Optional[Dict[str, Any]]:
        """
        Geocode an address to coordinates using Google Geocoding API.

        Args:
            address: Address or place name to geocode
            city: City name (default: Hong Kong)

        Returns:
            Dictionary with latitude, longitude, and display_name, or None if not found
        """
        if not self.api_key:
            logger.error("Google Maps API key not configured")
            return None

        try:
            # Construct search query
            query = f"{address}, {city}"

            params = {
                "address": query,
                "key": self.api_key,
                "region": "hk"  # Bias results towards Hong Kong
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("status") == "OK" and data.get("results"):
                            result = data["results"][0]  # Take first result
                            location = result["geometry"]["location"]

                            return {
                                "latitude": float(location["lat"]),
                                "longitude": float(location["lng"]),
                                "display_name": result.get("formatted_address", address),
                                "address": result.get("address_components", [])
                            }
                        else:
                            logger.warning(f"Google Geocoding failed for '{query}': {data.get('status', 'Unknown error')}")
                    else:
                        logger.warning(f"Google Geocoding HTTP error for '{query}': {response.status}")

            return None

        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            return None
    
    async def geocode_poi(self, poi_name: str, poi_type: str = None, city: str = "Hong Kong") -> Optional[Dict[str, Any]]:
        """
        Geocode a point of interest (POI) like "Hong Kong International Airport" using Google Geocoding API.

        Args:
            poi_name: Name of the POI
            poi_type: Type of POI (e.g., "airport", "bank", "mtr_station")
            city: City name (default: Hong Kong)

        Returns:
            Dictionary with latitude, longitude, and display_name, or None if not found
        """
        if not self.api_key:
            logger.error("Google Maps API key not configured")
            return None

        try:
            # Construct search query
            query = f"{poi_name}, {city}"

            params = {
                "address": query,
                "key": self.api_key,
                "region": "hk"  # Bias results towards Hong Kong
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("status") == "OK" and data.get("results"):
                            result = data["results"][0]  # Take first result
                            location = result["geometry"]["location"]

                            return {
                                "latitude": float(location["lat"]),
                                "longitude": float(location["lng"]),
                                "display_name": result.get("formatted_address", poi_name),
                                "type": poi_type
                            }
                        else:
                            logger.warning(f"Google POI Geocoding failed for '{query}': {data.get('status', 'Unknown error')}")
                    else:
                        logger.warning(f"Google POI Geocoding HTTP error for '{query}': {response.status}")

            return None

        except Exception as e:
            logger.error(f"Error geocoding POI '{poi_name}': {e}")
            return None
    
    async def batch_geocode(self, locations: List[Dict[str, str]]) -> List[Optional[Dict[str, Any]]]:
        """
        Geocode multiple locations in batch using Google Geocoding API.

        Note: Google Geocoding API doesn't have true batch processing, so we make individual requests
        with rate limiting to avoid quota issues.

        Args:
            locations: List of dictionaries with 'name' and optional 'type' keys

        Returns:
            List of geocoding results (same order as input)
        """
        if not self.api_key:
            logger.error("Google Maps API key not configured")
            return [None] * len(locations)

        tasks = []
        for loc in locations:
            name = loc.get("name", "")
            loc_type = loc.get("type")

            if loc_type:
                tasks.append(self.geocode_poi(name, loc_type))
            else:
                tasks.append(self.geocode_address(name))

        # Google Geocoding API has rate limits, so we add delays between requests
        results = []
        for i, task in enumerate(tasks):
            try:
                result = await task
                results.append(result)

                # Add delay between requests (Google allows 50 requests per second for premium plans)
                # We use a conservative 200ms delay to be safe
                if i < len(tasks) - 1:  # Don't delay after last request
                    await asyncio.sleep(0.2)

            except Exception as e:
                logger.error(f"Error in batch geocoding for location {i}: {e}")
                results.append(None)
                continue

        return results


# Singleton instance
_geocoding_service = None

def get_geocoding_service() -> GeocodingService:
    """Get or create the geocoding service singleton"""
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service
