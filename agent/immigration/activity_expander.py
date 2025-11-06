"""
Activity Expander Module
Intelligently expands main activities with nearby services based on time windows and user profile
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Service categories to expand around main activities
EXPANSION_RULES = {
    "housing": {
        # Around home viewing/moving
        "services": [
            {"type": "supermarket", "priority": "P1", "name": "Explore Nearby Supermarket", "duration_hours": 1},
            {"type": "convenience_store", "priority": "P2", "name": "Find 24-Hour Convenience Store", "duration_hours": 0.5},
            {"type": "pharmacy", "priority": "P2", "name": "Locate Local Pharmacy", "duration_hours": 0.5},
            {"type": "restaurant", "priority": "P2", "name": "Discover Local Restaurants", "duration_hours": 1},
        ],
        "radius_km": 2,
        "time_window": "same_day"  # Expand on same day or next day
    },
    "finance": {
        # Around bank account opening
        "services": [
            {"type": "atm", "priority": "P2", "name": "Find Nearby ATMs", "duration_hours": 0.5},
            {"type": "tax_office", "priority": "P1", "name": "Visit Tax Office", "duration_hours": 1.5},
            {"type": "government_office", "priority": "P1", "name": "Government Service Center", "duration_hours": 1.5},
        ],
        "radius_km": 3,
        "time_window": "next_day"  # Expand to next day
    },
    "work": {
        # Around office visit
        "services": [
            {"type": "restaurant", "priority": "P2", "name": "Find Lunch Spots Near Office", "duration_hours": 1},
            {"type": "cafe", "priority": "P3", "name": "Discover Coffee Shops", "duration_hours": 0.5},
            {"type": "gym", "priority": "P3", "name": "Explore Nearby Gym", "duration_hours": 1},
        ],
        "radius_km": 1.5,
        "time_window": "same_day"
    },
    "transportation": {
        # Around transportation setup
        "services": [
            {"type": "transit_station", "priority": "P1", "name": "Learn Metro/Bus Routes", "duration_hours": 1},
            {"type": "bike_rental", "priority": "P3", "name": "Check Bike Sharing Options", "duration_hours": 0.5},
        ],
        "radius_km": 1,
        "time_window": "same_day"
    },
    "healthcare": {
        # Around medical setup
        "services": [
            {"type": "hospital", "priority": "P1", "name": "Locate Nearest Hospital", "duration_hours": 1},
            {"type": "clinic", "priority": "P2", "name": "Find Family Doctor", "duration_hours": 1},
            {"type": "pharmacy", "priority": "P2", "name": "Pharmacy Near Home", "duration_hours": 0.5},
        ],
        "radius_km": 3,
        "time_window": "next_day"
    }
}


def analyze_time_window(main_activity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze time window for expanding activities.
    
    Args:
        main_activity: Main activity with date and estimated time
        
    Returns:
        Time window information
    """
    activity_date = datetime.strptime(main_activity["date"], "%Y-%m-%d")
    duration_hours = main_activity.get("duration_hours", 2)
    
    # Estimate activity time (assume morning activities start at 10:00)
    estimated_start_hour = 10
    estimated_end_hour = estimated_start_hour + duration_hours
    
    # Determine if we can expand on same day
    can_expand_same_day = estimated_end_hour < 17  # Before 5 PM
    
    return {
        "date": main_activity["date"],
        "estimated_start_hour": estimated_start_hour,
        "estimated_end_hour": estimated_end_hour,
        "can_expand_same_day": can_expand_same_day,
        "expansion_date": main_activity["date"] if can_expand_same_day else (activity_date + timedelta(days=1)).strftime("%Y-%m-%d")
    }


def generate_expansion_candidates(
    main_activity: Dict[str, Any],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate expansion activity candidates around a main activity.
    
    Args:
        main_activity: Main activity to expand around
        customer_info: Customer profile information
        
    Returns:
        List of expansion activity candidates
    """
    category = main_activity.get("category", "general")
    expansion_rule = EXPANSION_RULES.get(category)
    
    if not expansion_rule:
        logger.info(f"No expansion rule for category: {category}")
        return []
    
    # Analyze time window
    time_window = analyze_time_window(main_activity)
    
    # Get main activity location
    main_location = main_activity.get("location")
    if not main_location:
        logger.warning(f"Main activity '{main_activity['name']}' has no location")
        return []
    
    # Generate candidates
    candidates = []
    for service in expansion_rule["services"]:
        # Evaluate relevance based on user profile
        relevance_score = evaluate_relevance(service, customer_info)
        
        if relevance_score < 0.5:  # Skip low-relevance services
            continue
        
        candidate = {
            "name": service["name"],
            "type": "extended",
            "category": category,
            "priority": service["priority"],
            "duration_hours": service["duration_hours"],
            "location_type": service["type"],
            "search_query": f"{service['type']} near {main_location.get('name', '')}",
            "search_center": {
                "latitude": main_location.get("latitude"),
                "longitude": main_location.get("longitude")
            },
            "radius_km": expansion_rule["radius_km"],
            "relevance_score": relevance_score,
            "expansion_date": time_window["expansion_date"],
            "parent_activity": main_activity["name"],
            "dependencies": [main_activity["name"]]  # Depends on main activity
        }
        
        candidates.append(candidate)
    
    # Sort by relevance score
    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    logger.info(f"Generated {len(candidates)} expansion candidates for '{main_activity['name']}'")
    return candidates


def evaluate_relevance(service: Dict[str, Any], customer_info: Dict[str, Any]) -> float:
    """
    Evaluate relevance of a service based on customer profile.
    
    Args:
        service: Service information
        customer_info: Customer profile
        
    Returns:
        Relevance score (0.0 to 1.0)
    """
    base_score = 0.7  # Base relevance
    
    # Adjust based on family size
    family_size = customer_info.get("family_size", 1)
    if service["type"] in ["supermarket", "pharmacy"] and family_size > 1:
        base_score += 0.15
    
    # Adjust based on budget
    budget = customer_info.get("budget", 50000)
    if service["type"] in ["gym", "cafe"] and budget > 60000:
        base_score += 0.1
    
    # Adjust based on transportation preference
    transport_pref = customer_info.get("transportation_preference", "public")
    if service["type"] == "transit_station" and transport_pref == "public":
        base_score += 0.2
    
    # Priority adjustment
    if service["priority"] == "P1":
        base_score += 0.1
    elif service["priority"] == "P3":
        base_score -= 0.1
    
    return min(1.0, max(0.0, base_score))


def expand_all_activities(
    main_activities: List[Dict[str, Any]],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Expand all main activities with nearby services.
    
    Args:
        main_activities: List of main activities
        customer_info: Customer profile
        
    Returns:
        List of all expansion candidates
    """
    all_candidates = []
    
    for activity in main_activities:
        if activity.get("type") == "core":
            candidates = generate_expansion_candidates(activity, customer_info)
            all_candidates.extend(candidates)
    
    logger.info(f"Total expansion candidates: {len(all_candidates)}")
    return all_candidates


def filter_and_deduplicate(
    expansion_candidates: List[Dict[str, Any]],
    max_per_day: int = 3
) -> List[Dict[str, Any]]:
    """
    Filter and deduplicate expansion candidates.
    
    Args:
        expansion_candidates: List of expansion candidates
        max_per_day: Maximum expansions per day
        
    Returns:
        Filtered list of expansion activities
    """
    # Group by date
    by_date = {}
    for candidate in expansion_candidates:
        date = candidate["expansion_date"]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(candidate)
    
    # Filter top N per day
    filtered = []
    for date, candidates in by_date.items():
        # Sort by relevance and take top N
        top_candidates = sorted(candidates, key=lambda x: x["relevance_score"], reverse=True)[:max_per_day]
        filtered.extend(top_candidates)
    
    logger.info(f"Filtered to {len(filtered)} expansion activities")
    return filtered
