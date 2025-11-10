"""
Core Tasks Generator - Generates essential/core activities based on user requirements
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .state import SettlementTask, CustomerInfo, TaskType
import uuid


def generate_core_tasks(customer_info: CustomerInfo) -> List[SettlementTask]:
    """
    Generate core/essential tasks ONLY for dates explicitly provided by the user.
    Only creates tasks for activities where the user has specified a preferred date.
    
    Args:
        customer_info: Customer information including preferred dates for activities
        
    Returns:
        List of core tasks for user-specified dates only
    """
    import logging
    logger = logging.getLogger(__name__)
    
    tasks = []
    
    # Parse arrival date
    arrival_date = None
    if customer_info.get("arrival_date"):
        try:
            arrival_date = datetime.strptime(customer_info["arrival_date"], "%Y-%m-%d")
            logger.info(f"Parsed arrival date: {arrival_date}")
        except Exception as e:
            logger.error(f"Failed to parse arrival_date: {e}")
            pass
    
    # Get preferred dates from customer info
    preferred_dates = customer_info.get("preferred_dates", {})
    logger.info(f"Preferred dates from customer_info: {preferred_dates}")
    
    # Only generate tasks if user provided specific dates for activities
    if not preferred_dates and not arrival_date:
        logger.warning("No preferred_dates or arrival_date found - returning empty task list")
        return tasks  # No dates provided, return empty list
    
    # Day 1: Arrival tasks (only if arrival_date is provided)
    if arrival_date:
        arrival_tasks = _generate_arrival_core_tasks(customer_info, arrival_date)
        logger.info(f"Generated {len(arrival_tasks)} arrival tasks")
        tasks.extend(arrival_tasks)
    
    # Housing tasks (only if user specified home_viewing date)
    has_home_viewing = preferred_dates.get("home_viewing")
    has_housing_info = customer_info.get("housing_budget") or customer_info.get("bedrooms")
    logger.info(f"Housing check - has_home_viewing: {has_home_viewing}, has_housing_info: {has_housing_info}")
    
    if has_home_viewing and has_housing_info:
        housing_tasks = _generate_housing_core_tasks(customer_info, arrival_date)
        logger.info(f"Generated {len(housing_tasks)} housing tasks")
        tasks.extend(housing_tasks)
    elif has_home_viewing and not has_housing_info:
        logger.warning("home_viewing date specified but no housing_budget or bedrooms found")
    elif not has_home_viewing:
        logger.info("No home_viewing date specified, skipping housing tasks")
    
    # Identity tasks (only if user specified identity_card date)
    if preferred_dates.get("identity_card"):
        tasks.extend(_generate_identity_core_tasks(customer_info, arrival_date))
    
    # Banking tasks (only if user specified bank_account date)
    if preferred_dates.get("bank_account"):
        tasks.extend(_generate_banking_core_tasks(customer_info, arrival_date))
    
    # Daily life tasks (only if user specified mobile_phone or transport_card dates)
    if preferred_dates.get("mobile_phone") or preferred_dates.get("transport_card"):
        tasks.extend(_generate_daily_life_core_tasks(customer_info, arrival_date))
    
    # Driver's license (only if user needs car AND specified driver_license date)
    if customer_info.get("needs_car") and preferred_dates.get("driver_license"):
        tasks.extend(_generate_driving_core_tasks(customer_info, arrival_date))
    
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
    
    # Determine temporary accommodation location based on user's preferred areas
    preferred_areas = customer_info.get("preferred_areas", [])
    temp_area = preferred_areas[0] if preferred_areas else "Wan Chai"
    
    # Default coordinates for common Hong Kong areas
    area_coords = {
        "Wan Chai": (22.2783, 114.1747),
        "Sheung Wan": (22.2850, 114.1550),
        "Central": (22.2810, 114.1580),
        "Causeway Bay": (22.2800, 114.1850),
        "Tsim Sha Tsui": (22.2950, 114.1720),
    }
    
    # Get coordinates for the area (default to Wan Chai if not found)
    temp_lat, temp_lng = area_coords.get(temp_area, (22.2783, 114.1747))
    
    tasks.append({
        "id": str(uuid.uuid4()),
        "title": "Check-in to Temporary Accommodation",
        "description": "Check-in to hotel/serviced apartment",
        "day_range": day_str,
        "priority": "high",
        "task_type": TaskType.CORE.value,
        "core_activity_id": None,
        "relevance_score": None,
        "recommendation_reason": None,
        "location": {
            "id": "temp-accommodation",
            "name": f"Temporary Accommodation in {temp_area}",
            "address": f"{temp_area}, Hong Kong",
            "latitude": temp_lat,
            "longitude": temp_lng,
            "rating": 4.0,
            "type": "accommodation",
            "description": f"Serviced apartment or hotel in {temp_area}"
        },
        "documents_needed": ["Passport", "Booking confirmation"],
        "estimated_duration": "30 minutes",
        "status": "pending",
        "dependencies": [tasks[0]["id"]]  # After airport pickup
    })
    
    return tasks


def _generate_housing_core_tasks(
    customer_info: CustomerInfo,
    arrival_date: Optional[datetime]
) -> List[SettlementTask]:
    """Generate core housing search tasks for user-specified date only"""
    tasks = []
    
    # Get user's preferred date for home viewing
    preferred_dates = customer_info.get("preferred_dates", {})
    preferred_home_viewing = preferred_dates.get("home_viewing")
    
    if not preferred_home_viewing:
        return tasks  # No date specified by user, return empty
    
    # Parse the user-specified date
    try:
        search_date = datetime.strptime(preferred_home_viewing, "%Y-%m-%d")
        if arrival_date:
            start_day = (search_date - arrival_date).days + 1
            day_str = f"Day {start_day} ({search_date.strftime('%b %d')})"
        else:
            day_str = search_date.strftime('%b %d')
    except:
        return tasks  # Invalid date format, skip this task
    
    budget = customer_info.get("housing_budget", 0)
    bedrooms = customer_info.get("bedrooms", 1)
    preferred_areas = customer_info.get("preferred_areas", [])
    areas_str = ", ".join(preferred_areas) if preferred_areas else "near office"
    
    # Determine property viewing location based on user's preferred areas
    viewing_area = preferred_areas[0] if preferred_areas else "Wan Chai"
    
    # Default coordinates for common Hong Kong residential areas
    area_coords = {
        "Wan Chai": (22.2783, 114.1747),
        "Sheung Wan": (22.2850, 114.1550),
        "Central": (22.2810, 114.1580),
        "Causeway Bay": (22.2800, 114.1850),
        "Tsim Sha Tsui": (22.2950, 114.1720),
        "Admiralty": (22.2780, 114.1650),
        "Mid-Levels": (22.2750, 114.1500),
    }
    
    # Get coordinates for the viewing area (default to Wan Chai if not found)
    viewing_lat, viewing_lng = area_coords.get(viewing_area, (22.2783, 114.1747))
    
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
        "location": {
            "id": "property-viewing-area",
            "name": f"Property Viewing in {areas_str}",
            "address": f"{areas_str}, Hong Kong",
            "latitude": viewing_lat,
            "longitude": viewing_lng,
            "rating": 4.0,
            "type": "residential",
            "description": f"Residential area for property viewing in {viewing_area}"
        },
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
    """Generate core identity tasks for user-specified date only"""
    tasks = []
    
    # Get user's preferred date for identity card application
    preferred_dates = customer_info.get("preferred_dates", {})
    preferred_identity_card = preferred_dates.get("identity_card")
    
    if not preferred_identity_card:
        return tasks  # No date specified by user, return empty
    
    # Parse the user-specified date
    try:
        hkid_date = datetime.strptime(preferred_identity_card, "%Y-%m-%d")
        if arrival_date:
            start_day = (hkid_date - arrival_date).days + 1
            day_str = f"Day {start_day} ({hkid_date.strftime('%b %d')})"
        else:
            day_str = hkid_date.strftime('%b %d')
    except:
        return tasks  # Invalid date format, skip this task
    
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
        "location": {
            "id": "immigration-dept",
            "name": "Immigration Department",
            "address": "Immigration Tower, 7 Gloucester Road, Wan Chai",
            "latitude": 22.2783,
            "longitude": 114.1747,
            "rating": 3.5,
            "type": "government",
            "description": "Hong Kong Immigration Department Headquarters"
        },
        "documents_needed": ["Passport", "Visa", "Employment letter", "Proof of address"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": []
    })
    
    return tasks


def _generate_banking_core_tasks(
    customer_info: CustomerInfo,
    arrival_date: Optional[datetime]
) -> List[SettlementTask]:
    """Generate core banking tasks for user-specified date only"""
    tasks = []
    
    # Get user's preferred date for bank account opening
    preferred_dates = customer_info.get("preferred_dates", {})
    preferred_bank_account = preferred_dates.get("bank_account")
    
    if not preferred_bank_account:
        return tasks  # No date specified by user, return empty
    
    # Parse the user-specified date
    try:
        bank_date = datetime.strptime(preferred_bank_account, "%Y-%m-%d")
        if arrival_date:
            bank_day = (bank_date - arrival_date).days + 1
            day_str = f"Day {bank_day} ({bank_date.strftime('%b %d')})"
        else:
            day_str = bank_date.strftime('%b %d')
    except:
        return tasks  # Invalid date format, skip this task
    
    # Find identity task for dependency (if it exists)
    identity_task_id = None
    
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
        "location": {
            "id": "central-banking",
            "name": "Central Banking District",
            "address": "Central, Hong Kong",
            "latitude": 22.2810,
            "longitude": 114.1580,
            "rating": 4.0,
            "type": "banking",
            "description": "Major banking area with HSBC, Standard Chartered, Bank of China, and other major banks"
        },
        "documents_needed": ["Passport", "Resident ID (if available)", "Proof of address", "Employment letter"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": []
    })
    
    return tasks


def _generate_daily_life_core_tasks(
    customer_info: CustomerInfo,
    arrival_date: Optional[datetime]
) -> List[SettlementTask]:
    """Generate core daily life setup tasks for user-specified dates only"""
    tasks = []
    
    preferred_dates = customer_info.get("preferred_dates", {})
    
    # Mobile phone task (only if user specified date)
    preferred_mobile = preferred_dates.get("mobile_phone")
    if preferred_mobile:
        try:
            mobile_date = datetime.strptime(preferred_mobile, "%Y-%m-%d")
            if arrival_date:
                day = (mobile_date - arrival_date).days + 1
                day_str = f"Day {day} ({mobile_date.strftime('%b %d')})"
            else:
                day_str = mobile_date.strftime('%b %d')
        except:
            day_str = None
        
        if day_str:
    
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
                "location": {
                    "id": "mobile-shop-causeway-bay",
                    "name": "Mobile Service Shop - Causeway Bay",
                    "address": "Causeway Bay, Hong Kong",
                    "latitude": 22.2800,
                    "longitude": 114.1850,
                    "rating": 4.2,
                    "type": "retail",
                    "description": "Mobile carrier service centers (CSL, 3HK, China Mobile) available in major shopping areas"
                },
                "documents_needed": ["Passport"],
                "estimated_duration": "30 minutes",
                "status": "pending",
                "dependencies": []
            })
    
    # Transportation card task (only if user specified date)
    preferred_transport = preferred_dates.get("transport_card")
    if preferred_transport:
        try:
            transport_date = datetime.strptime(preferred_transport, "%Y-%m-%d")
            if arrival_date:
                day = (transport_date - arrival_date).days + 1
                day_str = f"Day {day} ({transport_date.strftime('%b %d')})"
            else:
                day_str = transport_date.strftime('%b %d')
        except:
            day_str = None
        
        if day_str:
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
                "location": {
                    "id": "mtr-station-central",
                    "name": "MTR Station - Central",
                    "address": "Central MTR Station, Hong Kong",
                    "latitude": 22.2810,
                    "longitude": 114.1580,
                    "rating": 4.5,
                    "type": "transportation",
                    "description": "Purchase Octopus Card at any MTR station customer service center"
                },
                "documents_needed": [],
                "estimated_duration": "15 minutes",
                "status": "pending",
                "dependencies": []
            })
    
    return tasks


def _generate_driving_core_tasks(
    customer_info: CustomerInfo,
    arrival_date: Optional[datetime]
) -> List[SettlementTask]:
    """Generate core driving/license tasks for user-specified date only"""
    tasks = []
    
    # Get user's preferred date for driver's license
    preferred_dates = customer_info.get("preferred_dates", {})
    preferred_license = preferred_dates.get("driver_license")
    
    if not preferred_license:
        return tasks  # No date specified by user, return empty
    
    # Parse the user-specified date
    try:
        license_date = datetime.strptime(preferred_license, "%Y-%m-%d")
        if arrival_date:
            license_day = (license_date - arrival_date).days + 1
            day_str = f"Day {license_day} ({license_date.strftime('%b %d')})"
        else:
            day_str = license_date.strftime('%b %d')
    except:
        return tasks  # Invalid date format, skip this task
    
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
