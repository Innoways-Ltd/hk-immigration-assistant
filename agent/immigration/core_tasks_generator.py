"""
Core Tasks Generator - Generates essential/core activities based on user requirements
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .state import SettlementTask, CustomerInfo, TaskType
import uuid


def generate_core_tasks(customer_info: CustomerInfo) -> List[SettlementTask]:
    """
    Generate core/essential tasks based on customer information.
    These are the must-do activities that the user explicitly needs or are legally required.
    
    Args:
        customer_info: Customer information including arrival date, housing needs, etc.
        
    Returns:
        List of core tasks
    """
    tasks = []
    
    # Parse arrival date
    arrival_date = None
    if customer_info.get("arrival_date"):
        try:
            arrival_date = datetime.strptime(customer_info["arrival_date"], "%Y-%m-%d")
        except:
            pass
    
    # Calculate plan duration based on temporary accommodation days
    temp_days = customer_info.get("temporary_accommodation_days", 30)
    plan_duration = max(14, temp_days + 7)  # At least 14 days for HKID processing
    
    # Day 1: Arrival tasks (CORE)
    tasks.extend(_generate_arrival_core_tasks(customer_info, arrival_date))
    
    # Day 3-7: Housing tasks (CORE if user mentioned housing needs)
    if customer_info.get("housing_budget") or customer_info.get("bedrooms"):
        tasks.extend(_generate_housing_core_tasks(customer_info, arrival_date, temp_days))
    
    # Day 7-14: Identity and banking tasks (CORE - legally required)
    tasks.extend(_generate_identity_core_tasks(customer_info, arrival_date))
    
    # Day 14+: Work and daily life setup (CORE based on user needs)
    tasks.extend(_generate_daily_life_core_tasks(customer_info, arrival_date, plan_duration))
    
    return tasks


def _generate_arrival_core_tasks(
    customer_info: CustomerInfo,
    arrival_date: Optional[datetime]
) -> List[SettlementTask]:
    """Generate core arrival tasks for Day 1"""
    tasks = []
    day_str = "Day 1"
    if arrival_date:
        day_str = f"Day 1 ({arrival_date.strftime('%b %d')})"
    
    # Airport pickup - CORE
    tasks.append({
        "id": str(uuid.uuid4()),
        "title": "Airport Pickup",
        "description": "Arrange pickup from Hong Kong International Airport to temporary accommodation",
        "day_range": day_str,
        "priority": "high",
        "task_type": TaskType.CORE.value,
        "core_activity_id": None,
        "relevance_score": None,
        "recommendation_reason": None,
        "location": {
            "id": "hk-airport",
            "name": "Hong Kong International Airport",
            "address": "Hong Kong International Airport",
            "latitude": 22.3080,
            "longitude": 113.9185,
            "rating": 4.5,
            "type": "airport",
            "description": "Main international airport"
        },
        "documents_needed": ["Passport", "Visa", "Flight Itinerary"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": []
    })
    
    # Check-in to temporary accommodation - CORE
    temp_days = customer_info.get("temporary_accommodation_days", 7)
    tasks.append({
        "id": str(uuid.uuid4()),
        "title": "Check-in to Temporary Accommodation",
        "description": f"Check-in to hotel/serviced apartment for {temp_days} days",
        "day_range": day_str,
        "priority": "high",
        "task_type": TaskType.CORE.value,
        "core_activity_id": None,
        "relevance_score": None,
        "recommendation_reason": None,
        "location": None,  # Will be geocoded based on user's choice
        "documents_needed": ["Passport", "Booking confirmation"],
        "estimated_duration": "30 minutes",
        "status": "pending",
        "dependencies": [tasks[0]["id"]]  # After airport pickup
    })
    
    return tasks


def _generate_housing_core_tasks(
    customer_info: CustomerInfo,
    arrival_date: Optional[datetime],
    temp_days: int
) -> List[SettlementTask]:
    """Generate core housing search tasks"""
    tasks = []
    
    # Start housing search on Day 3 (after settling in)
    start_day = 3
    if arrival_date:
        search_date = arrival_date + timedelta(days=start_day - 1)
        day_str = f"Day {start_day} ({search_date.strftime('%b %d')})"
    else:
        day_str = f"Day {start_day}"
    
    budget = customer_info.get("housing_budget", 0)
    bedrooms = customer_info.get("bedrooms", 1)
    preferred_areas = customer_info.get("preferred_areas", [])
    areas_str = ", ".join(preferred_areas) if preferred_areas else "near office"
    
    tasks.append({
        "id": str(uuid.uuid4()),
        "title": "Property Viewing - First Batch",
        "description": f"View shortlisted properties in {areas_str} ({bedrooms} bedroom, budget: HKD {budget:,}/month)",
        "day_range": day_str,
        "priority": "high",
        "task_type": TaskType.CORE.value,
        "core_activity_id": None,
        "relevance_score": None,
        "recommendation_reason": None,
        "location": None,  # Will be geocoded based on properties
        "documents_needed": ["Passport", "Employment letter", "Proof of income"],
        "estimated_duration": "3-4 hours",
        "status": "pending",
        "dependencies": []
    })
    
    return tasks


def _generate_identity_core_tasks(
    customer_info: CustomerInfo,
    arrival_date: Optional[datetime]
) -> List[SettlementTask]:
    """Generate core identity and banking tasks"""
    tasks = []
    
    # HKID application - Day 7 (legally required)
    start_day = 7
    if arrival_date:
        hkid_date = arrival_date + timedelta(days=start_day - 1)
        day_str = f"Day {start_day} ({hkid_date.strftime('%b %d')})"
    else:
        day_str = f"Day {start_day}"
    
    tasks.append({
        "id": str(uuid.uuid4()),
        "title": "Apply for Resident Identity Card",
        "description": "Apply for local resident identity card at immigration office (check local requirements for timing)",
        "day_range": day_str,
        "priority": "high",
        "task_type": TaskType.CORE.value,
        "core_activity_id": None,
        "relevance_score": None,
        "recommendation_reason": None,
        "location": None,  # Will be geocoded based on local immigration office
        "documents_needed": ["Passport", "Visa", "Employment letter", "Proof of address"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": []
    })
    
    # Bank account - Day 10 (essential for salary and daily life)
    bank_day = 10
    if arrival_date:
        bank_date = arrival_date + timedelta(days=bank_day - 1)
        day_str = f"Day {bank_day} ({bank_date.strftime('%b %d')})"
    else:
        day_str = f"Day {bank_day}"
    
    tasks.append({
        "id": str(uuid.uuid4()),
        "title": "Open Bank Account",
        "description": "Open local bank account at a major bank (research local banks and requirements)",
        "day_range": day_str,
        "priority": "high",
        "task_type": TaskType.CORE.value,
        "core_activity_id": None,
        "relevance_score": None,
        "recommendation_reason": None,
        "location": None,  # Will be geocoded based on nearest bank
        "documents_needed": ["Passport", "Resident ID (if available)", "Proof of address", "Employment letter"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": [tasks[0]["id"]]  # After resident ID
    })
    
    return tasks


def _generate_daily_life_core_tasks(
    customer_info: CustomerInfo,
    arrival_date: Optional[datetime],
    plan_duration: int
) -> List[SettlementTask]:
    """Generate core daily life setup tasks"""
    tasks = []
    
    # Mobile phone - Day 1 or 2 (essential for communication)
    day = 1
    if arrival_date:
        date = arrival_date + timedelta(days=day - 1)
        day_str = f"Day {day} ({date.strftime('%b %d')})"
    else:
        day_str = f"Day {day}"
    
    tasks.append({
        "id": str(uuid.uuid4()),
        "title": "Get Mobile SIM Card",
        "description": "Purchase local SIM card from CSL, 3HK, or China Mobile",
        "day_range": day_str,
        "priority": "high",
        "task_type": TaskType.CORE.value,
        "core_activity_id": None,
        "relevance_score": None,
        "recommendation_reason": None,
        "location": None,  # Will be geocoded
        "documents_needed": ["Passport"],
        "estimated_duration": "30 minutes",
        "status": "pending",
        "dependencies": []
    })
    
    # Transportation card - Day 1 (essential for public transport)
    tasks.append({
        "id": str(uuid.uuid4()),
        "title": "Get Transportation Card",
        "description": "Purchase local transportation card for public transit (e.g., metro, bus)",
        "day_range": day_str,
        "priority": "high",
        "task_type": TaskType.CORE.value,
        "core_activity_id": None,
        "relevance_score": None,
        "recommendation_reason": None,
        "location": None,  # Will be geocoded
        "documents_needed": [],
        "estimated_duration": "15 minutes",
        "status": "pending",
        "dependencies": []
    })
    
    # Driver's license (if user needs car)
    if customer_info.get("needs_car"):
        license_day = 14
        if arrival_date:
            date = arrival_date + timedelta(days=license_day - 1)
            day_str = f"Day {license_day} ({date.strftime('%b %d')})"
        else:
            day_str = f"Day {license_day}"
        
        tasks.append({
            "id": str(uuid.uuid4()),
            "title": "Convert Driver's License",
            "description": "Convert foreign driver's license to local license at transport authority",
            "day_range": day_str,
            "priority": "medium",
            "task_type": TaskType.CORE.value,
            "core_activity_id": None,
            "relevance_score": None,
            "recommendation_reason": None,
            "location": {
                "id": "transport-dept",
                "name": "Transport Department",
                "address": "3 Kai Shing Street, Kowloon Bay",
                "latitude": 22.3227,
                "longitude": 114.2095,
                "rating": 3.8,
                "type": "government",
                "description": "Transport Department Licensing Office"
            },
            "documents_needed": ["Passport", "HKID", "Foreign driver's license", "Proof of address"],
            "estimated_duration": "2-3 hours",
            "status": "pending",
            "dependencies": []
        })
    
    return tasks


def identify_core_task_categories(customer_info: CustomerInfo) -> List[str]:
    """
    Identify which categories of core tasks are needed based on customer info.
    This helps in generating relevant extended activities.
    
    Returns:
        List of category names: ["arrival", "housing", "identity", "banking", "transportation", "work"]
    """
    categories = ["arrival", "identity", "banking", "transportation"]  # Always needed
    
    if customer_info.get("housing_budget") or customer_info.get("bedrooms"):
        categories.append("housing")
    
    if customer_info.get("needs_car"):
        categories.append("driving")
    
    if customer_info.get("has_children"):
        categories.append("education")
    
    return categories
