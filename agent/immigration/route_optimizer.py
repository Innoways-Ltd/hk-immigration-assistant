"""
Route optimization utilities for settlement tasks
"""

import math
from typing import List, Dict, Any

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

def optimize_daily_route(tasks: List[Dict[str, Any]], start_location: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Optimize the order of tasks for a single day using nearest neighbor algorithm.
    
    Args:
        tasks: List of tasks for the day
        start_location: Optional starting location (e.g., hotel, home)
        
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

def optimize_settlement_tasks(tasks: List[Dict[str, Any]], office_coords: tuple = None) -> List[Dict[str, Any]]:
    """
    Optimize all settlement tasks by grouping by day and optimizing each day's route.
    
    Args:
        tasks: List of all tasks
        office_coords: Optional office coordinates (lat, lng)
        
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
        
        # Optimize this day's route
        optimized_day_tasks = optimize_daily_route(day_tasks, start_location)
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
