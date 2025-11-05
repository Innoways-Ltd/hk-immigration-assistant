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


async def generate_all_tasks_async(customer_info: dict) -> List[Dict[str, Any]]:
    """
    Generate all tasks with geocoded locations.
    
    This function generates tasks and geocodes them in parallel to minimize wait time.
    """
    arrival_date = customer_info.get('arrival_date')
    temp_days = customer_info.get('temporary_accommodation_days', 30)
    office_address = customer_info.get('office_address', 'Wan Chai, Hong Kong')
    preferred_areas = customer_info.get('preferred_areas', ['Wan Chai', 'Sheung Wan'])
    has_children = customer_info.get('has_children', False)
    
    plan_duration = calculate_plan_duration(customer_info)
    
    tasks = []
    task_id = 1
    
    # Define all tasks with their location search terms
    task_definitions = [
        {
            "title": "Airport Pickup",
            "description": "Arrange pickup from Hong Kong International Airport to temporary accommodation",
            "day_range": format_day_range(1, None, arrival_date),
            "priority": "high",
            "location_search": "Hong Kong International Airport",
            "location_type": "airport",
            "documents_needed": ["Passport", "Visa", "Flight Itinerary"],
            "estimated_duration": "1-2 hours"
        },
        {
            "title": "Get Mobile SIM Card",
            "description": "Purchase local SIM card from CSL, 3HK, or China Mobile",
            "day_range": format_day_range(1, None, arrival_date),
            "priority": "high",
            "location_search": f"CSL Store near {office_address}",
            "location_type": "store",
            "documents_needed": ["Passport"],
            "estimated_duration": "30 minutes"
        },
        {
            "title": "Purchase Octopus Card",
            "description": "Buy Octopus card for public transportation at MTR station or convenience store",
            "day_range": format_day_range(1, None, arrival_date),
            "priority": "high",
            "location_search": f"MTR Station near {office_address}",
            "location_type": "transit",
            "documents_needed": [],
            "estimated_duration": "15 minutes"
        },
        {
            "title": "Check-in to Temporary Accommodation",
            "description": f"Check-in to hotel/serviced apartment for {temp_days} days",
            "day_range": format_day_range(1, None, arrival_date),
            "priority": "high",
            "location_search": f"Hotel near {office_address}",
            "location_type": "hotel",
            "documents_needed": ["Passport", "Booking confirmation"],
            "estimated_duration": "30 minutes"
        }
    ]
    
    # Add housing task if plan is long enough
    if plan_duration >= 5:
        viewing_start = min(3, temp_days - 2)
        viewing_end = min(7, temp_days)
        area = preferred_areas[0] if preferred_areas else "Wan Chai"
        
        task_definitions.append({
            "title": "Property Viewing - First Batch",
            "description": f"View shortlisted properties in {', '.join(preferred_areas) if preferred_areas else 'preferred areas'}",
            "day_range": format_day_range(viewing_start, viewing_end, arrival_date),
            "priority": "high",
            "location_search": f"{area}, Hong Kong",
            "location_type": "residential",
            "documents_needed": ["Passport", "Employment letter", "Proof of income"],
            "estimated_duration": "3-4 hours"
        })
    
    # Add banking task
    bank_start = min(3, plan_duration - 4)
    bank_end = min(7, plan_duration - 3)
    
    task_definitions.append({
        "title": "Open Bank Account",
        "description": "Open bank account at HSBC, Standard Chartered, or Bank of China",
        "day_range": format_day_range(bank_start, bank_end, arrival_date),
        "priority": "high",
        "location_search": f"HSBC near {office_address}",
        "location_type": "bank",
        "documents_needed": ["Passport", "Proof of address", "Employment letter"],
        "estimated_duration": "1-2 hours"
    })
    
    # Add HKID task if plan is long enough
    if plan_duration >= 10:
        hkid_start = min(7, plan_duration - 7)
        hkid_end = min(14, plan_duration - 2)
        
        task_definitions.append({
            "title": "Apply for Hong Kong Identity Card",
            "description": "Register for HKID at Immigration Department within 30 days of arrival",
            "day_range": format_day_range(hkid_start, hkid_end, arrival_date),
            "priority": "high",
            "location_search": "Immigration Tower Wan Chai",
            "location_type": "government",
            "documents_needed": ["Passport", "Visa", "Proof of address", "Employment letter"],
            "estimated_duration": "2-3 hours"
        })
    
    # Add office visit task
    if plan_duration >= 7:
        office_start = min(5, plan_duration - 5)
        office_end = min(10, plan_duration - 2)
        
        task_definitions.append({
            "title": "Visit Office Location",
            "description": "Familiarize with office location and commute route",
            "day_range": format_day_range(office_start, office_end, arrival_date),
            "priority": "medium",
            "location_search": office_address,
            "location_type": "office",
            "documents_needed": [],
            "estimated_duration": "2-3 hours"
        })
    
    # Geocode all locations in parallel (with rate limiting)
    logger.info(f"Geocoding {len(task_definitions)} locations...")
    
    geocoding_tasks = []
    for task_def in task_definitions:
        geocoding_tasks.append(
            geocode_location(task_def["location_search"], task_def["location_type"])
        )
    
    # Execute geocoding with delays to respect rate limits
    locations = []
    for i, geocoding_task in enumerate(geocoding_tasks):
        location = await geocoding_task
        locations.append(location)
        # Add delay between requests (except for the last one)
        if i < len(geocoding_tasks) - 1:
            await asyncio.sleep(1.2)  # 1.2 seconds to be safe
    
    # Create tasks with geocoded locations
    for task_def, location in zip(task_definitions, locations):
        task = {
            "id": f"task_{task_id:03d}",
            "title": task_def["title"],
            "description": task_def["description"],
            "day_range": task_def["day_range"],
            "priority": task_def["priority"],
            "location": location,  # May be None if geocoding failed
            "documents_needed": task_def["documents_needed"],
            "estimated_duration": task_def["estimated_duration"],
            "status": "pending",
            "dependencies": [],
            "task_type": TaskType.CORE.value  # Mark as core task
        }
        tasks.append(task)
        task_id += 1
    
    logger.info(f"Generated {len(tasks)} tasks with locations")
    
    return tasks


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


def calculate_plan_duration(customer_info: dict) -> int:
    """Calculate plan duration based on temporary accommodation days."""
    temp_days = customer_info.get('temporary_accommodation_days', 30)
    
    # Plan should be at least 14 days (for HKID application)
    # and extend beyond temporary accommodation
    plan_duration = max(14, temp_days + 7)
    
    return plan_duration
