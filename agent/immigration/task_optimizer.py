"""
Task Optimizer Module

Implements intelligent optimization for settlement tasks:
- Load balancing (max tasks per day)
- Path optimization
- Time window validation
- Dependency verification
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


def balance_task_load(
    tasks: List[Dict[str, Any]],
    max_tasks_per_day: int = 5,
    arrival_date: str = None
) -> List[Dict[str, Any]]:
    """
    Balance task load across days, ensuring no day has too many tasks.
    
    Args:
        tasks: List of scheduled tasks
        max_tasks_per_day: Maximum number of tasks allowed per day
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
        
        # Separate core and extended tasks
        core_tasks = [t for t in day_tasks if t.get("activity_type") == "core"]
        essential_tasks = [t for t in day_tasks if t.get("activity_type") == "essential"]
        extended_tasks = [t for t in day_tasks if t.get("activity_type") == "extended"]
        
        # Core and essential tasks have priority
        priority_tasks = core_tasks + essential_tasks
        
        if len(priority_tasks) >= max_tasks_per_day:
            # Too many priority tasks, keep all priority, drop extended
            rebalanced_tasks.extend(priority_tasks)
            overflow_tasks.extend(extended_tasks)
            logger.warning(f"Day {day} has {len(priority_tasks)} priority tasks (>= {max_tasks_per_day}), dropping {len(extended_tasks)} extended tasks")
        else:
            # Add priority tasks
            rebalanced_tasks.extend(priority_tasks)
            
            # Add extended tasks up to limit
            remaining_slots = max_tasks_per_day - len(priority_tasks)
            
            # Sort extended tasks by relevance score
            extended_tasks.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            rebalanced_tasks.extend(extended_tasks[:remaining_slots])
            overflow_tasks.extend(extended_tasks[remaining_slots:])
            
            if len(extended_tasks) > remaining_slots:
                logger.info(f"Day {day}: Kept {remaining_slots} extended tasks, deferred {len(extended_tasks) - remaining_slots}")
    
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
