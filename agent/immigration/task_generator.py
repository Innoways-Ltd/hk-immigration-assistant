"""
Task generation with dynamic geocoding - Simplified version
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import hashlib

from immigration.geocoding_service import get_geocoding_service
from immigration.routing_service import get_routing_service
from immigration.state import TaskType

logger = logging.getLogger(__name__)

# Cache for geocoding results
_geocoding_cache = {}


def format_day_range(start_day: int, end_day: int = None, arrival_date: str = None) -> str:
    """Format day range with optional actual dates."""
    if end_day is None or start_day == end_day:
        day_str = f"Day {start_day}"
    else:
        day_str = f"Day {start_day}-{end_day}"
    
    if arrival_date:
        try:
            arrival = datetime.fromisoformat(arrival_date)
            start_date = arrival + timedelta(days=start_day - 1)
            
            if end_day and end_day != start_day:
                end_date = arrival + timedelta(days=end_day - 1)
                day_str += f" ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})"
            else:
                day_str += f" ({start_date.strftime('%b %d')})"
        except:
            pass
    
    return day_str


async def geocode_location(search_term: str, location_type: str = "general") -> Optional[Dict[str, Any]]:
    """
    Geocode a location with caching.
    
    Args:
        search_term: Search term for geocoding
        location_type: Type of location
        
    Returns:
        Location dictionary with id, name, latitude, longitude, type
    """
    # Check cache first
    cache_key = f"{search_term}_{location_type}"
    if cache_key in _geocoding_cache:
        return _geocoding_cache[cache_key]
    
    geocoding_service = get_geocoding_service()
    
    try:
        result = await geocoding_service.geocode_poi(search_term, location_type, "Hong Kong")
        
        if result:
            # Create consistent location object
            location = {
                "id": f"loc_{abs(hash(search_term)) % 10000}",
                "name": search_term,  # Use search term as name for consistency
                "address": result.get("display_name", search_term),
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "type": location_type
            }
            
            # Cache the result
            _geocoding_cache[cache_key] = location
            
            return location
    except Exception as e:
        logger.error(f"Error geocoding '{search_term}': {e}")
    
    # Return None if geocoding fails
    return None


# generate_all_tasks_async removed - no longer needed
# We use generate_core_tasks which only creates tasks for user-specified dates


async def optimize_tasks_with_routing(tasks: List[Dict[str, Any]], office_coords: tuple = None) -> List[Dict[str, Any]]:
    """
    Optimize task order using real routing API.
    
    Args:
        tasks: List of tasks with locations
        office_coords: Optional office coordinates (lat, lng)
        
    Returns:
        Optimized list of tasks
    """
    routing_service = get_routing_service()
    
    # Group tasks by day
    tasks_by_day = {}
    for task in tasks:
        day = extract_day_from_range(task.get("day_range", "Day 1"))
        if day not in tasks_by_day:
            tasks_by_day[day] = []
        tasks_by_day[day].append(task)
    
    optimized_tasks = []
    
    for day in sorted(tasks_by_day.keys()):
        day_tasks = tasks_by_day[day]
        
        # Extract tasks with valid locations
        tasks_with_location = [t for t in day_tasks if t.get("location") and 
                               t["location"].get("latitude") and 
                               t["location"].get("longitude")]
        tasks_without_location = [t for t in day_tasks if not (t.get("location") and 
                                                                 t["location"].get("latitude") and 
                                                                 t["location"].get("longitude"))]
        
        if len(tasks_with_location) <= 1:
            # No optimization needed
            optimized_tasks.extend(day_tasks)
            continue
        
        # Extract coordinates (longitude, latitude for OSRM)
        coordinates = [(t["location"]["longitude"], t["location"]["latitude"]) for t in tasks_with_location]
        
        try:
            # Optimize trip
            result = await routing_service.optimize_trip(coordinates, profile="foot", source="first", destination="last")
            
            if result and result.get("optimized_order"):
                # Reorder tasks based on optimized order
                optimized_order = result["optimized_order"]
                reordered = [tasks_with_location[i] for i in optimized_order]
                reordered.extend(tasks_without_location)
                optimized_tasks.extend(reordered)
                logger.info(f"Day {day}: Optimized route for {len(tasks_with_location)} tasks")
            else:
                # Fallback to original order
                optimized_tasks.extend(day_tasks)
                logger.warning(f"Day {day}: Route optimization failed, using original order")
        except Exception as e:
            logger.error(f"Day {day}: Error optimizing route: {e}")
            # Fallback to original order
            optimized_tasks.extend(day_tasks)
    
    return optimized_tasks


def extract_day_from_range(day_range: str) -> int:
    """Extract the starting day number from a day range string."""
    import re
    match = re.search(r'Day (\d+)', day_range)
    if match:
        return int(match.group(1))
    return 1


def extract_service_locations(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract unique service locations from tasks."""
    locations = []
    seen_coords = set()
    
    for task in tasks:
        location = task.get("location")
        if location:
            # Use coordinates as unique identifier
            lat = location.get("latitude")
            lon = location.get("longitude")
            
            if lat is None or lon is None:
                continue
            
            coord_key = (lat, lon)
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                # Ensure location has an id field
                if "id" not in location:
                    location["id"] = f"loc_{abs(hash(coord_key)) % 10000}"
                locations.append(location)
    
    return locations


# calculate_plan_duration removed - no longer needed
# We only generate tasks for user-specified dates
