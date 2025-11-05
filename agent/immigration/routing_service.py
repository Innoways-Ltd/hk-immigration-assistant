"""
Routing service using OSRM (Open Source Routing Machine) API
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RoutingService:
    """Service for route optimization using OSRM API"""
    
    def __init__(self):
        # Use public OSRM demo server
        self.base_url = "https://router.project-osrm.org"
    
    async def get_route(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "foot"
    ) -> Optional[Dict[str, Any]]:
        """
        Get route between multiple coordinates.
        
        Args:
            coordinates: List of (longitude, latitude) tuples
            profile: Routing profile ("car", "bike", "foot")
            
        Returns:
            Dictionary with route information (distance, duration, geometry)
        """
        try:
            # Format coordinates as "lon,lat;lon,lat;..."
            coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
            
            url = f"{self.base_url}/route/v1/{profile}/{coords_str}"
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "overview": "full",
                    "geometries": "geojson",
                    "steps": "true"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("code") == "Ok" and data.get("routes"):
                            route = data["routes"][0]
                            return {
                                "distance": route.get("distance"),  # meters
                                "duration": route.get("duration"),  # seconds
                                "geometry": route.get("geometry"),
                                "legs": route.get("legs", [])
                            }
                    else:
                        logger.warning(f"Routing failed: HTTP {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting route: {e}")
            return None
    
    async def optimize_trip(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "foot",
        source: str = "first",
        destination: str = "last"
    ) -> Optional[Dict[str, Any]]:
        """
        Optimize the order of waypoints for the shortest route.
        
        Args:
            coordinates: List of (longitude, latitude) tuples
            profile: Routing profile ("car", "bike", "foot")
            source: "first" (start from first coord) or "any"
            destination: "last" (end at last coord) or "any"
            
        Returns:
            Dictionary with optimized route and waypoint order
        """
        try:
            # Format coordinates
            coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
            
            url = f"{self.base_url}/trip/v1/{profile}/{coords_str}"
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "source": source,
                    "destination": destination,
                    "overview": "full",
                    "geometries": "geojson"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("code") == "Ok" and data.get("trips"):
                            trip = data["trips"][0]
                            waypoints = data.get("waypoints", [])
                            
                            # Extract optimized order
                            optimized_order = [wp.get("waypoint_index") for wp in waypoints]
                            
                            return {
                                "distance": trip.get("distance"),  # meters
                                "duration": trip.get("duration"),  # seconds
                                "geometry": trip.get("geometry"),
                                "optimized_order": optimized_order,
                                "waypoints": waypoints
                            }
                    else:
                        logger.warning(f"Trip optimization failed: HTTP {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error optimizing trip: {e}")
            return None
    
    async def get_distance_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "foot"
    ) -> Optional[Dict[str, Any]]:
        """
        Get distance matrix between all pairs of coordinates.
        
        Args:
            coordinates: List of (longitude, latitude) tuples
            profile: Routing profile ("car", "bike", "foot")
            
        Returns:
            Dictionary with distance and duration matrices
        """
        try:
            coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
            
            url = f"{self.base_url}/table/v1/{profile}/{coords_str}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("code") == "Ok":
                            return {
                                "distances": data.get("distances"),  # 2D array in meters
                                "durations": data.get("durations")   # 2D array in seconds
                            }
                    else:
                        logger.warning(f"Distance matrix failed: HTTP {response.status}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting distance matrix: {e}")
            return None


# Singleton instance
_routing_service = None

def get_routing_service() -> RoutingService:
    """Get or create the routing service singleton"""
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService()
    return _routing_service
