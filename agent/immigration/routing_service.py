"""
Routing service using Google Maps Directions API
"""

import os
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RoutingService:
    """Service for route optimization using Google Maps APIs"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            logger.error("GOOGLE_MAPS_API_KEY environment variable not set")
        self.directions_url = "https://maps.googleapis.com/maps/api/directions/json"
        self.distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    
    async def get_route(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "walking"
    ) -> Optional[Dict[str, Any]]:
        """
        Get route between two coordinates using Google Directions API.

        Args:
            coordinates: List of (longitude, latitude) tuples (max 2 points for Directions API)
            profile: Travel mode ("driving", "walking", "bicycling", "transit")

        Returns:
            Dictionary with route information (distance, duration, geometry)
        """
        if not self.api_key:
            logger.error("Google Maps API key not configured")
            return None

        if len(coordinates) < 2:
            logger.error("At least 2 coordinates required for routing")
            return None

        try:
            # Map profile to Google Directions travel mode
            travel_mode_mapping = {
                "foot": "walking",
                "walking": "walking",
                "car": "driving",
                "driving": "driving",
                "bike": "bicycling",
                "bicycling": "bicycling"
            }
            travel_mode = travel_mode_mapping.get(profile, "walking")

            # Google Directions API only supports 2 waypoints (origin and destination)
            origin = f"{coordinates[0][1]},{coordinates[0][0]}"  # lat,lng
            destination = f"{coordinates[1][1]},{coordinates[1][0]}"  # lat,lng

            params = {
                "origin": origin,
                "destination": destination,
                "mode": travel_mode,
                "key": self.api_key,
                "alternatives": "false"  # Only get one route
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.directions_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("status") == "OK" and data.get("routes"):
                            route = data["routes"][0]

                            # Convert Google Directions format to our format
                            leg = route["legs"][0]  # First (and only) leg

                            return {
                                "distance": leg["distance"]["value"],  # meters
                                "duration": leg["duration"]["value"],  # seconds
                                "geometry": self._extract_polyline(route),
                                "legs": [{
                                    "distance": leg["distance"]["value"],
                                    "duration": leg["duration"]["value"],
                                    "steps": self._extract_steps(leg.get("steps", []))
                                }]
                            }
                        else:
                            logger.warning(f"Google Directions API error: {data.get('status', 'Unknown error')}")
                    else:
                        logger.warning(f"Google Directions API HTTP error: {response.status}")

            return None

        except Exception as e:
            logger.error(f"Error getting route: {e}")
            return None

    def _extract_polyline(self, route: Dict[str, Any]) -> str:
        """Extract polyline from Google Directions route."""
        # Google Directions returns overview_polyline
        if "overview_polyline" in route:
            return route["overview_polyline"]["points"]
        return ""

    def _extract_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract steps from Google Directions leg."""
        extracted_steps = []
        for step in steps:
            extracted_steps.append({
                "distance": step["distance"]["value"],
                "duration": step["duration"]["value"],
                "instruction": step.get("html_instructions", ""),
                "maneuver": step.get("maneuver", "")
            })
        return extracted_steps
    
    async def optimize_trip(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "walking",
        source: str = "first",
        destination: str = "last"
    ) -> Optional[Dict[str, Any]]:
        """
        Optimize the order of waypoints for the shortest route using Distance Matrix API.

        Args:
            coordinates: List of (longitude, latitude) tuples
            profile: Travel mode ("driving", "walking", "bicycling", "transit")
            source: "first" (start from first coord) or "any"
            destination: "last" (end at last coord) or "any"

        Returns:
            Dictionary with optimized route and waypoint order
        """
        if len(coordinates) <= 2:
            # No optimization needed for 2 or fewer points
            return {
                "distance": 0,
                "duration": 0,
                "geometry": "",
                "optimized_order": list(range(len(coordinates))),
                "waypoints": [{"waypoint_index": i} for i in range(len(coordinates))]
            }

        try:
            # Get distance matrix
            distance_matrix = await self.get_distance_matrix(coordinates, profile)
            if not distance_matrix:
                logger.error("Failed to get distance matrix for optimization")
                return None

            # Use nearest neighbor algorithm for route optimization
            optimized_order = self._optimize_route_order(distance_matrix, source, destination)

            # Calculate total distance and duration for optimized route
            total_distance = 0
            total_duration = 0

            for i in range(len(optimized_order) - 1):
                from_idx = optimized_order[i]
                to_idx = optimized_order[i + 1]
                if distance_matrix["distances"][from_idx][to_idx]:
                    total_distance += distance_matrix["distances"][from_idx][to_idx]
                    total_duration += distance_matrix["durations"][from_idx][to_idx]

            return {
                "distance": total_distance,
                "duration": total_duration,
                "geometry": "",  # Would need to construct polyline from individual routes
                "optimized_order": optimized_order,
                "waypoints": [{"waypoint_index": idx} for idx in optimized_order]
            }

        except Exception as e:
            logger.error(f"Error optimizing trip: {e}")
            return None

    def _optimize_route_order(self, distance_matrix: Dict[str, Any], source: str, destination: str) -> List[int]:
        """
        Use nearest neighbor algorithm to optimize route order.

        Args:
            distance_matrix: Distance matrix from Distance Matrix API
            source: Starting constraint ("first" or "any")
            destination: Ending constraint ("last" or "any")

        Returns:
            Optimized order of waypoint indices
        """
        n = len(distance_matrix["distances"])
        visited = [False] * n
        order = []

        # Determine start and end points
        start_idx = 0 if source == "first" else None
        end_idx = n - 1 if destination == "last" else None

        # Start from specified point or point 0
        current = start_idx if start_idx is not None else 0
        order.append(current)
        visited[current] = True

        # Visit all other points using nearest neighbor
        for _ in range(n - 1):
            nearest = None
            min_distance = float('inf')

            for i in range(n):
                if not visited[i] and distance_matrix["distances"][current][i] is not None:
                    distance = distance_matrix["distances"][current][i]
                    if distance < min_distance:
                        min_distance = distance
                        nearest = i

            if nearest is None:
                # No more reachable points, add remaining unvisited points
                break

            order.append(nearest)
            visited[nearest] = True
            current = nearest

        # Add any remaining unvisited points
        for i in range(n):
            if not visited[i]:
                order.append(i)

        return order
    
    async def get_distance_matrix(
        self,
        coordinates: List[Tuple[float, float]],
        profile: str = "walking"
    ) -> Optional[Dict[str, Any]]:
        """
        Get distance matrix between all pairs of coordinates using Google Distance Matrix API.

        Args:
            coordinates: List of (longitude, latitude) tuples
            profile: Travel mode ("driving", "walking", "bicycling", "transit")

        Returns:
            Dictionary with distance and duration matrices
        """
        if not self.api_key:
            logger.error("Google Maps API key not configured")
            return None

        if len(coordinates) < 2:
            logger.error("At least 2 coordinates required for distance matrix")
            return None

        try:
            # Map profile to Google Distance Matrix travel mode
            travel_mode_mapping = {
                "foot": "walking",
                "walking": "walking",
                "car": "driving",
                "driving": "driving",
                "bike": "bicycling",
                "bicycling": "bicycling"
            }
            travel_mode = travel_mode_mapping.get(profile, "walking")

            # Prepare origins and destinations
            origins = "|".join([f"{lat},{lon}" for lon, lat in coordinates])
            destinations = origins  # Same as origins for all-pairs matrix

            params = {
                "origins": origins,
                "destinations": destinations,
                "mode": travel_mode,
                "key": self.api_key,
                "units": "metric"  # Return distances in meters
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.distance_matrix_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("status") == "OK":
                            # Convert Google Distance Matrix format to our format
                            rows = data.get("rows", [])
                            n = len(coordinates)

                            distances = [[None for _ in range(n)] for _ in range(n)]
                            durations = [[None for _ in range(n)] for _ in range(n)]

                            for i, row in enumerate(rows):
                                elements = row.get("elements", [])
                                for j, element in enumerate(elements):
                                    if element.get("status") == "OK":
                                        distances[i][j] = element["distance"]["value"]  # meters
                                        durations[i][j] = element["duration"]["value"]  # seconds

                            return {
                                "distances": distances,  # 2D array in meters
                                "durations": durations   # 2D array in seconds
                            }
                        else:
                            logger.warning(f"Google Distance Matrix API error: {data.get('status', 'Unknown error')}")
                    else:
                        logger.warning(f"Google Distance Matrix API HTTP error: {response.status}")

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
