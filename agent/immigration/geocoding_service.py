"""
Geocoding service using OpenStreetMap Nominatim API
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for geocoding addresses to coordinates using Nominatim API"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.headers = {
            "User-Agent": "HK-Immigration-Assistant/1.0"
        }
    
    async def geocode_address(self, address: str, city: str = "Hong Kong") -> Optional[Dict[str, Any]]:
        """
        Geocode an address to coordinates.
        
        Args:
            address: Address or place name to geocode
            city: City name (default: Hong Kong)
            
        Returns:
            Dictionary with latitude, longitude, and display_name, or None if not found
        """
        try:
            # Construct search query
            query = f"{address}, {city}"
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1
                }
                
                async with session.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        results = await response.json()
                        
                        if results and len(results) > 0:
                            result = results[0]
                            return {
                                "latitude": float(result["lat"]),
                                "longitude": float(result["lon"]),
                                "display_name": result.get("display_name", address),
                                "address": result.get("address", {})
                            }
                    else:
                        logger.warning(f"Geocoding failed for '{query}': HTTP {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            return None
    
    async def geocode_poi(self, poi_name: str, poi_type: str = None, city: str = "Hong Kong") -> Optional[Dict[str, Any]]:
        """
        Geocode a point of interest (POI) like "Hong Kong International Airport".
        
        Args:
            poi_name: Name of the POI
            poi_type: Type of POI (e.g., "airport", "bank", "mtr_station")
            city: City name (default: Hong Kong)
            
        Returns:
            Dictionary with latitude, longitude, and display_name, or None if not found
        """
        try:
            # Construct search query
            query = f"{poi_name}, {city}"
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "format": "json",
                    "limit": 1
                }
                
                async with session.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        results = await response.json()
                        
                        if results and len(results) > 0:
                            result = results[0]
                            return {
                                "latitude": float(result["lat"]),
                                "longitude": float(result["lon"]),
                                "display_name": result.get("display_name", poi_name),
                                "type": poi_type
                            }
                    else:
                        logger.warning(f"POI geocoding failed for '{query}': HTTP {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding POI '{poi_name}': {e}")
            return None
    
    async def batch_geocode(self, locations: List[Dict[str, str]]) -> List[Optional[Dict[str, Any]]]:
        """
        Geocode multiple locations in batch.
        
        Args:
            locations: List of dictionaries with 'name' and optional 'type' keys
            
        Returns:
            List of geocoding results (same order as input)
        """
        tasks = []
        for loc in locations:
            name = loc.get("name", "")
            loc_type = loc.get("type")
            
            if loc_type:
                tasks.append(self.geocode_poi(name, loc_type))
            else:
                tasks.append(self.geocode_address(name))
        
        # Add delay between requests to respect rate limits
        results = []
        for task in tasks:
            result = await task
            results.append(result)
            await asyncio.sleep(1)  # 1 second delay between requests
        
        return results


# Singleton instance
_geocoding_service = None

def get_geocoding_service() -> GeocodingService:
    """Get or create the geocoding service singleton"""
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service
