"""
Route optimization utilities for settlement tasks using Google Maps APIs
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from .routing_service import get_routing_service

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def extract_day_from_range(day_range: str) -> int:
    """
    Extract the starting day number from a day range string.
    
    Args:
        day_range: String like "Day 1", "Day 3-5", "Day 1 (May 04)"
        
    Returns:
        Starting day number
    """
    # Extract "Day X" or "Day X-Y"
    import re
    match = re.search(r'Day (\d+)', day_range)
    if match:
        return int(match.group(1))
    return 1

def group_tasks_by_day(tasks: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Group tasks by their starting day.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Dictionary mapping day number to list of tasks
    """
    tasks_by_day = {}
    
    for task in tasks:
        day = extract_day_from_range(task.get("day_range", "Day 1"))
        if day not in tasks_by_day:
            tasks_by_day[day] = []
        tasks_by_day[day].append(task)
    
    return tasks_by_day

async def optimize_daily_route(tasks: List[Dict[str, Any]], start_location: Dict[str, Any] = None, travel_mode: str = "walking") -> List[Dict[str, Any]]:
    """
    Optimize the order of tasks for a single day using Google Maps APIs.

    Args:
        tasks: List of tasks for the day
        start_location: Optional starting location (e.g., hotel, home)
        travel_mode: Travel mode ("walking", "driving", "bicycling", "transit")

    Returns:
        Reordered list of tasks following optimal route
    """
    if len(tasks) <= 1:
        return tasks

    # Separate tasks with and without locations
    tasks_with_location = [t for t in tasks if t.get("location") is not None]
    tasks_without_location = [t for t in tasks if t.get("location") is None]

    if len(tasks_with_location) <= 1:
        # If only 0-1 tasks have locations, no optimization needed
        return tasks

    try:
        # Get routing service
        routing_service = get_routing_service()

        # Prepare coordinates for optimization
        coordinates = []
        task_indices = []

        # Add start location if provided
        if start_location:
            coordinates.append((start_location["longitude"], start_location["latitude"]))
            task_indices.append(None)  # None indicates start location

        # Add all task locations
        for task in tasks_with_location:
            loc = task["location"]
            coordinates.append((loc["longitude"], loc["latitude"]))
            task_indices.append(task)

        # Use Google Maps to optimize route
        optimization_result = await routing_service.optimize_trip(
            coordinates,
            profile=travel_mode,
            source="first" if start_location else "any",
            destination="any"
        )

        if optimization_result and optimization_result.get("optimized_order"):
            optimized_order = optimization_result["optimized_order"]

            # Reorder tasks based on optimized order
            optimized_tasks = []

            # Skip the start location in the results if it was included
            start_offset = 1 if start_location else 0

            for idx in optimized_order[start_offset:]:
                if idx < len(task_indices) and task_indices[idx] is not None:
                    optimized_tasks.append(task_indices[idx])

            # Add any remaining tasks that weren't in the optimization
            for task in tasks_with_location:
                if task not in optimized_tasks:
                    optimized_tasks.append(task)

            # Add tasks without locations at the end
            optimized_tasks.extend(tasks_without_location)

            return optimized_tasks

    except Exception as e:
        print(f"Error using Google Maps for route optimization: {e}")
        # Fall back to simple nearest neighbor algorithm
        pass

    # Fallback: Use simple nearest neighbor algorithm with Haversine distance
    return _optimize_with_nearest_neighbor(tasks_with_location, tasks_without_location, start_location)


def _optimize_with_nearest_neighbor(tasks_with_location: List[Dict[str, Any]], tasks_without_location: List[Dict[str, Any]], start_location: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Fallback optimization using nearest neighbor algorithm with Haversine distance.

    Args:
        tasks_with_location: Tasks that have location data
        tasks_without_location: Tasks without location data
        start_location: Optional starting location

    Returns:
        Reordered list of tasks
    """
    # Start from the first task or start_location
    optimized = []
    remaining = tasks_with_location.copy()

    # Determine starting point
    if start_location:
        current_lat = start_location.get("latitude")
        current_lng = start_location.get("longitude")
    else:
        # Start from the first task
        first_task = remaining.pop(0)
        optimized.append(first_task)
        current_lat = first_task["location"]["latitude"]
        current_lng = first_task["location"]["longitude"]

    # Nearest neighbor algorithm
    while remaining:
        nearest_task = None
        nearest_distance = float('inf')

        for task in remaining:
            loc = task["location"]
            distance = calculate_distance(
                current_lat, current_lng,
                loc["latitude"], loc["longitude"]
            )

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_task = task

        if nearest_task:
            optimized.append(nearest_task)
            remaining.remove(nearest_task)
            current_lat = nearest_task["location"]["latitude"]
            current_lng = nearest_task["location"]["longitude"]

    # Add tasks without locations at the end
    optimized.extend(tasks_without_location)

    return optimized

async def optimize_settlement_tasks(tasks: List[Dict[str, Any]], office_coords: tuple = None, travel_mode: str = "walking") -> List[Dict[str, Any]]:
    """
    Optimize all settlement tasks by grouping by day and optimizing each day's route using Google Maps.

    Args:
        tasks: List of all tasks
        office_coords: Optional office coordinates (lat, lng)
        travel_mode: Travel mode for route optimization

    Returns:
        Reordered list of tasks with optimized routes
    """
    # Group tasks by day
    tasks_by_day = group_tasks_by_day(tasks)

    # Optimize each day's tasks
    optimized_tasks = []

    for day in sorted(tasks_by_day.keys()):
        day_tasks = tasks_by_day[day]

        # For Day 1, we might start from airport
        # For other days, we might start from office or home
        start_location = None
        if day == 1 and day_tasks and day_tasks[0].get("location"):
            # Day 1 starts from airport (first task)
            start_location = day_tasks[0]["location"]
        elif office_coords:
            start_location = {
                "latitude": office_coords[0],
                "longitude": office_coords[1]
            }

        # Optimize this day's route using Google Maps
        optimized_day_tasks = await optimize_daily_route(day_tasks, start_location, travel_mode)
        optimized_tasks.extend(optimized_day_tasks)

    return optimized_tasks

def extract_service_locations(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract unique service locations from tasks.
    
    Args:
        tasks: List of tasks
        
    Returns:
        List of unique service location dictionaries
    """
    locations = []
    seen_ids = set()
    
    for task in tasks:
        location = task.get("location")
        if location and location.get("id") not in seen_ids:
            seen_ids.add(location["id"])
            locations.append(location)
    
    return locations
