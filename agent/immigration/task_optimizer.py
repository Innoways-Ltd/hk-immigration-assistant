"""
Task Optimizer Module

Implements intelligent optimization for settlement tasks:
- Load balancing (max tasks per day)
- Path optimization
- Time window validation
- Dependency verification
"""

import logging
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


def calculate_distance(loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
    """
    Calculate distance between two locations using Haversine formula.
    
    Args:
        loc1: Location 1 with latitude and longitude
        loc2: Location 2 with latitude and longitude
        
    Returns:
        Distance in kilometers
    """
    if not loc1 or not loc2:
        return float('inf')
    
    lat1 = loc1.get('latitude')
    lon1 = loc1.get('longitude')
    lat2 = loc2.get('latitude')
    lon2 = loc2.get('longitude')
    
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    
    # Haversine formula
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def optimize_geographic_clustering(
    tasks: List[Dict[str, Any]],
    max_distance_km: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Optimize task scheduling by clustering geographically close tasks on the same day.
    
    This function groups tasks that are within max_distance_km of each other
    to minimize travel time and improve convenience.
    
    Args:
        tasks: List of tasks with location information
        max_distance_km: Maximum distance (km) to consider tasks as "nearby"
        
    Returns:
        Optimized task list with improved geographic clustering
    """
    if not tasks:
        return tasks
    
    logger.info(f"Starting geographic clustering optimization with max_distance={max_distance_km}km")
    
    # Group tasks by day
    tasks_by_day = defaultdict(list)
    for task in tasks:
        day_offset = task.get("day_offset", 0)
        tasks_by_day[day_offset].append(task)
    
    optimized_tasks = []
    
    # For each day, sort tasks by geographic proximity
    for day, day_tasks in tasks_by_day.items():
        if len(day_tasks) <= 1:
            optimized_tasks.extend(day_tasks)
            continue
        
        # Separate tasks with and without locations
        tasks_with_location = [t for t in day_tasks if t.get("location")]
        tasks_without_location = [t for t in day_tasks if not t.get("location")]
        
        if not tasks_with_location:
            optimized_tasks.extend(day_tasks)
            continue
        
        # Sort tasks by geographic clustering
        # Start with the first task (usually the most important)
        clustered_tasks = [tasks_with_location[0]]
        remaining_tasks = tasks_with_location[1:]
        
        # Greedy algorithm: Always add the nearest task to the cluster
        while remaining_tasks:
            last_task = clustered_tasks[-1]
            last_location = last_task.get("location")
            
            # Find the nearest task
            nearest_task = None
            nearest_distance = float('inf')
            
            for task in remaining_tasks:
                task_location = task.get("location")
                distance = calculate_distance(last_location, task_location)
                
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_task = task
            
            if nearest_task:
                clustered_tasks.append(nearest_task)
                remaining_tasks.remove(nearest_task)
                logger.info(f"Day {day}: Clustered '{nearest_task['name']}' (distance: {nearest_distance:.2f}km from previous task)")
        
        # Add tasks without location at the end
        optimized_tasks.extend(clustered_tasks + tasks_without_location)
    
    logger.info(f"Geographic clustering complete: optimized {len(tasks)} tasks")
    return optimized_tasks


def balance_task_load(
    tasks: List[Dict[str, Any]],
    max_tasks_per_day: int = 4,
    arrival_date: str = None
) -> List[Dict[str, Any]]:
    """
    Balance task load across days, ensuring no day has too many tasks.
    
    Args:
        tasks: List of scheduled tasks
        max_tasks_per_day: Maximum number of tasks allowed per day (default: 4)
        arrival_date: Arrival date in YYYY-MM-DD format
        
    Returns:
        Rebalanced task list
    """
    if not tasks:
        return tasks
    
    # Group tasks by day_offset
    tasks_by_day = defaultdict(list)
    for task in tasks:
        day_offset = task.get("day_offset", 0)
        tasks_by_day[day_offset].append(task)
    
    # Sort days
    sorted_days = sorted(tasks_by_day.keys())
    
    # Rebalance
    rebalanced_tasks = []
    overflow_tasks = []
    
    for day in sorted_days:
        day_tasks = tasks_by_day[day]
        
        # Separate tasks by priority
        essential_tasks = [t for t in day_tasks if t.get("activity_type") == "essential"]
        core_tasks = [t for t in day_tasks if t.get("activity_type") == "core"]
        extended_tasks = [t for t in day_tasks if t.get("activity_type") == "extended"]
        
        # Priority order: essential > core > extended
        all_tasks_sorted = essential_tasks + core_tasks + extended_tasks
        
        # STRICT LIMIT: Take only first max_tasks_per_day tasks
        if len(all_tasks_sorted) > max_tasks_per_day:
            kept_tasks = all_tasks_sorted[:max_tasks_per_day]
            overflow = all_tasks_sorted[max_tasks_per_day:]
            
            rebalanced_tasks.extend(kept_tasks)
            overflow_tasks.extend(overflow)
            
            logger.warning(
                f"Day {day}: Limited to {max_tasks_per_day} tasks "
                f"({len(essential_tasks)} essential, {len(core_tasks)} core, {len(extended_tasks)} extended). "
                f"Deferred {len(overflow)} tasks."
            )
        else:
            # All tasks fit
            rebalanced_tasks.extend(all_tasks_sorted)
            logger.info(f"Day {day}: {len(all_tasks_sorted)} tasks (within limit)")
    
    # Try to reschedule overflow tasks to later days
    if overflow_tasks:
        logger.info(f"Attempting to reschedule {len(overflow_tasks)} overflow tasks")
        
        # Find the last day with tasks
        last_day = max(sorted_days) if sorted_days else 0
        
        # Distribute overflow tasks to subsequent days
        current_day = last_day + 1
        for task in overflow_tasks:
            # Check if this day already has tasks
            day_count = len([t for t in rebalanced_tasks if t.get("day_offset") == current_day])
            
            if day_count < max_tasks_per_day:
                task["day_offset"] = current_day
                rebalanced_tasks.append(task)
                logger.info(f"Rescheduled '{task['name']}' to day {current_day}")
            else:
                current_day += 1
                task["day_offset"] = current_day
                rebalanced_tasks.append(task)
                logger.info(f"Rescheduled '{task['name']}' to day {current_day}")
    
    logger.info(f"Load balancing complete: {len(rebalanced_tasks)} tasks across {len(set(t.get('day_offset', 0) for t in rebalanced_tasks))} days")
    
    return rebalanced_tasks


def validate_dependencies(tasks: List[Dict[str, Any]]) -> bool:
    """
    Validate that all task dependencies are satisfied.
    
    Args:
        tasks: List of tasks to validate
        
    Returns:
        True if all dependencies are satisfied
    """
    task_by_name = {task["name"]: task for task in tasks}
    
    for task in tasks:
        dependencies = task.get("dependencies", [])
        task_day = task.get("day_offset", 0)
        
        for dep_name in dependencies:
            if dep_name not in task_by_name:
                logger.warning(f"Task '{task['name']}' depends on '{dep_name}' which doesn't exist")
                continue
            
            dep_task = task_by_name[dep_name]
            dep_day = dep_task.get("day_offset", 0)
            
            if dep_day > task_day:
                logger.error(f"Dependency violation: '{task['name']}' (day {task_day}) depends on '{dep_name}' (day {dep_day})")
                return False
    
    return True


def calculate_plan_summary(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for the settlement plan.
    
    Args:
        tasks: List of tasks
        
    Returns:
        Summary dictionary with counts and statistics
    """
    summary = {
        "total_tasks": len(tasks),
        "core_tasks": len([t for t in tasks if t.get("activity_type") == "core"]),
        "extended_tasks": len([t for t in tasks if t.get("activity_type") == "extended"]),
        "essential_tasks": len([t for t in tasks if t.get("activity_type") == "essential"]),
        "total_days": len(set(t.get("day_offset", 0) for t in tasks)),
        "total_duration_hours": sum(t.get("duration_hours", 2) for t in tasks),
        "tasks_with_location": len([t for t in tasks if t.get("location")]),
        "high_priority_tasks": len([t for t in tasks if t.get("priority") == "high"])
    }
    
    return summary


def generate_plan_explanation(summary: Dict[str, Any]) -> str:
    """
    Generate a user-friendly explanation of the settlement plan.
    
    Args:
        summary: Plan summary dictionary
        
    Returns:
        Explanation text
    """
    core_count = summary.get("core_tasks", 0)
    extended_count = summary.get("extended_tasks", 0)
    essential_count = summary.get("essential_tasks", 0)
    total_days = summary.get("total_days", 0)
    
    explanation = f"""I've created a comprehensive {total_days}-day settlement plan for you:

✅ {core_count} core tasks based on your specific needs
💡 {extended_count} recommended activities to help you settle in more comfortably
📋 {essential_count} essential tasks that every new immigrant should complete

The plan is designed to:
• Prioritize your most important activities
• Suggest nearby services around your main activities for convenience
• Balance the workload (max 5 tasks per day)
• Respect dependencies between tasks

You can always adjust or remove any suggested activities to fit your preferences!"""
    
    return explanation
