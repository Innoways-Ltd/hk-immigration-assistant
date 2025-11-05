"""
Extended Task Generator - Generates AI-suggested tasks around core tasks
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from immigration.state import SettlementTask, TaskType, CustomerInfo
from immigration.nearby_services import (
    find_extended_activities_for_task,
    calculate_distance_km
)
from immigration.geocoding_service import get_geocoding_service

logger = logging.getLogger(__name__)


async def generate_extended_tasks(
    core_tasks: List[SettlementTask],
    customer_info: CustomerInfo,
    max_per_task: int = 2
) -> List[SettlementTask]:
    """
    Generate extended (AI-suggested) tasks around core tasks.
    
    This function analyzes core tasks and suggests relevant activities based on:
    1. Temporal proximity (same day or next day)
    2. Geographical nearness (within 2km radius)
    3. Lifestyle convenience (based on user profile)
    
    **Optimization**: Implements deduplication to avoid recommending similar
    activities multiple times (e.g., multiple cafes in the same area).
    
    Args:
        core_tasks: List of core tasks
        customer_info: Customer information
        max_per_task: Maximum extended tasks to generate per core task
        
    Returns:
        List of extended tasks (deduplicated)
    """
    extended_tasks = []
    task_id_counter = 1000  # Start extended task IDs from 1000
    
    # Track recommended activities to avoid duplicates
    # Key: (service_type, district) tuple, Value: List of days already recommended
    recommended_footprints: Dict[Tuple[str, str], List[int]] = {}
    
    # Group core tasks by day
    tasks_by_day = _group_tasks_by_day(core_tasks)
    
    # For each day with core tasks, find extended activities
    for day, day_tasks in tasks_by_day.items():
        # Find the most suitable core task for that day (usually the first one)
        anchor_task = _select_anchor_task(day_tasks)
        
        if not anchor_task or not anchor_task.get("location"):
            continue
        
        # Find extended activities around this anchor task
        try:
            activities = await find_extended_activities_for_task(
                anchor_task,
                customer_info,
                max_activities=max_per_task * 2  # Get more candidates for filtering
            )
            
            # Convert activities to extended tasks with deduplication
            for service, score, reason in activities:
                # Check for duplicates based on service type and location
                service_type = service.get("type", "unknown")
                district = _extract_district(service.get("address", ""))
                footprint = (service_type, district)
                
                # Skip if we've already recommended this type in this area
                # Allow same type in different areas, but not in same area
                if footprint in recommended_footprints:
                    # Check if it's on a different day (allow if days are far apart)
                    existing_days = recommended_footprints[footprint]
                    if day in existing_days or any(abs(day - d) <= 2 for d in existing_days):
                        continue  # Skip duplicate
                
                extended_task = _create_extended_task(
                    service,
                    reason,
                    day,
                    anchor_task,
                    customer_info,
                    task_id_counter
                )
                
                if extended_task:
                    extended_tasks.append(extended_task)
                    task_id_counter += 1
                    
                    # Track this recommendation
                    if footprint not in recommended_footprints:
                        recommended_footprints[footprint] = []
                    recommended_footprints[footprint].append(day)
                    
        except Exception as e:
            logger.error(f"Error generating extended tasks for day {day}: {e}")
            continue
    
    return extended_tasks


def _extract_district(address: str) -> str:
    """
    Extract district name from address (e.g., "Wan Chai", "Central").
    
    Returns:
        District name or "unknown"
    """
    # Common Hong Kong districts
    districts = [
        "Wan Chai", "Central", "Admiralty", "Causeway Bay", "Sheung Wan",
        "Mid-Levels", "Quarry Bay", "Tai Koo", "Tsim Sha Tsui", "Mong Kok",
        "Yau Ma Tei", "Jordan", "Kowloon", "Sha Tin", "Tuen Mun"
    ]
    
    address_lower = address.lower()
    for district in districts:
        if district.lower() in address_lower:
            return district
    
    return "unknown"


def _group_tasks_by_day(tasks: List[SettlementTask]) -> Dict[int, List[SettlementTask]]:
    """
    Group tasks by their start day.
    
    Returns:
        Dictionary mapping day number to list of tasks
    """
    tasks_by_day = {}
    
    for task in tasks:
        day_range = task.get("day_range", "")
        
        # Extract start day from day_range (e.g., "Day 1" or "Day 1-3")
        try:
            if "Day" in day_range:
                day_part = day_range.split("(")[0].strip()  # Remove date part
                if "-" in day_part:
                    start_day = int(day_part.split("-")[0].replace("Day", "").strip())
                else:
                    start_day = int(day_part.replace("Day", "").strip())
                
                if start_day not in tasks_by_day:
                    tasks_by_day[start_day] = []
                
                tasks_by_day[start_day].append(task)
        except:
            continue
    
    return tasks_by_day


def _select_anchor_task(day_tasks: List[SettlementTask]) -> Optional[SettlementTask]:
    """
    Select the best anchor task for finding extended activities.
    
    Priority:
    1. High priority tasks with locations (excluding special locations like airports)
    2. First task of the day with location (excluding special locations)
    3. Any task with location (excluding special locations)
    
    Special locations (airports, transit hubs) are skipped because they typically
    don't have regular amenities like supermarkets, cafes, etc.
    """
    # Special location types to skip
    skip_location_types = ["airport", "transit", "station"]
    
    # First, try high priority tasks with non-special locations
    for task in day_tasks:
        if task.get("priority") == "high" and task.get("location"):
            loc_type = task["location"].get("type", "")
            if loc_type not in skip_location_types:
                return task
    
    # Then, try first task with non-special location
    for task in day_tasks:
        if task.get("location"):
            loc_type = task["location"].get("type", "")
            if loc_type not in skip_location_types:
                return task
    
    return None


def _create_extended_task(
    service: Dict[str, Any],
    reason: str,
    day: int,
    anchor_task: SettlementTask,
    customer_info: CustomerInfo,
    task_id: int
) -> Optional[SettlementTask]:
    """
    Create an extended task from a service location.
    """
    arrival_date = customer_info.get("arrival_date")
    
    # Format day range
    day_range = f"Day {day}"
    if arrival_date:
        try:
            arrival = datetime.fromisoformat(arrival_date)
            task_date = arrival + timedelta(days=day - 1)
            day_range += f" ({task_date.strftime('%b %d')})"
        except:
            pass
    
    # Determine task title based on service type
    service_type = service.get("type", "").replace("_", " ").title()
    task_title = f"Visit {service.get('name', service_type)}"
    
    # Create task description with recommendation reason
    description = f"{service.get('description', '')}. {reason}"
    
    # Create location object
    location = {
        "id": service.get("id", f"ext_loc_{task_id}"),
        "name": service.get("name", ""),
        "address": service.get("address", ""),
        "latitude": service["latitude"],
        "longitude": service["longitude"],
        "type": service.get("type", "extended_service")
    }
    
    # Calculate estimated duration based on service type
    duration = _estimate_duration(service.get("type", ""))
    
    return {
        "id": f"task_ext_{task_id:03d}",
        "title": task_title,
        "description": description,
        "day_range": day_range,
        "priority": "low",  # Extended tasks are suggestions
        "location": location,
        "documents_needed": [],
        "estimated_duration": duration,
        "status": "pending",
        "dependencies": [],
        "task_type": TaskType.EXTENDED.value,
        "recommendation_reason": reason,
        "related_core_task": anchor_task.get("id")
    }


def _estimate_duration(service_type: str) -> str:
    """
    Estimate duration for visiting a service.
    """
    duration_map = {
        "supermarket": "30-45 minutes",
        "pharmacy": "15-20 minutes",
        "convenience_store": "10-15 minutes",
        "restaurant": "1-1.5 hours",
        "cafe": "30-45 minutes",
        "gym": "1-2 hours",
        "clinic": "30-60 minutes",
        "mall": "1-2 hours",
        "market": "45-60 minutes",
        "bank": "30-45 minutes",
        "atm": "5-10 minutes",
    }
    
    return duration_map.get(service_type, "30 minutes")


async def merge_and_optimize_tasks(
    core_tasks: List[SettlementTask],
    extended_tasks: List[SettlementTask]
) -> List[SettlementTask]:
    """
    Merge core and extended tasks, maintaining optimal order.
    
    Extended tasks are inserted after their related core tasks.
    """
    merged_tasks = []
    
    # Create a mapping of core task IDs to their extended tasks
    extended_by_core = {}
    for ext_task in extended_tasks:
        core_id = ext_task.get("related_core_task")
        if core_id:
            if core_id not in extended_by_core:
                extended_by_core[core_id] = []
            extended_by_core[core_id].append(ext_task)
    
    # Merge tasks
    for core_task in core_tasks:
        # Add core task
        merged_tasks.append(core_task)
        
        # Add related extended tasks
        core_id = core_task.get("id")
        if core_id in extended_by_core:
            # Sort extended tasks by distance from core task
            extended = extended_by_core[core_id]
            if core_task.get("location"):
                core_lat = core_task["location"]["latitude"]
                core_lon = core_task["location"]["longitude"]
                
                extended.sort(key=lambda t: calculate_distance_km(
                    core_lat, core_lon,
                    t["location"]["latitude"],
                    t["location"]["longitude"]
                ) if t.get("location") else float('inf'))
            
            merged_tasks.extend(extended)
    
    return merged_tasks


def filter_extended_tasks_by_acceptance(
    tasks: List[SettlementTask],
    accepted_task_ids: List[str]
) -> List[SettlementTask]:
    """
    Filter tasks to include only accepted extended tasks.
    
    Args:
        tasks: All tasks (core + extended)
        accepted_task_ids: List of accepted extended task IDs
        
    Returns:
        Filtered task list with core tasks + accepted extended tasks
    """
    filtered = []
    
    for task in tasks:
        task_type = task.get("task_type", TaskType.CORE.value)
        
        # Always include core tasks
        if task_type == TaskType.CORE.value:
            filtered.append(task)
        # Include extended tasks only if accepted
        elif task_type == TaskType.EXTENDED.value:
            if task.get("id") in accepted_task_ids:
                filtered.append(task)
    
    return filtered
