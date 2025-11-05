"""
Nearby Services Search and Relevance Scoring
"""
from typing import List, Dict, Optional, Tuple
from .state import ServiceLocation, SettlementTask, CustomerInfo
from .overpass_service import search_nearby_pois_overpass
import aiohttp
import asyncio
import math


# Service categories and their relevance to different core activities
SERVICE_CATEGORIES = {
    "arrival": ["convenience_store", "pharmacy", "supermarket", "restaurant"],
    "housing": ["real_estate", "furniture_store", "home_goods"],
    "identity": ["post_office", "photo_studio"],
    "banking": ["atm", "currency_exchange"],
    "transportation": ["car_rental", "bicycle_rental", "parking"],
    "daily_life": ["gym", "clinic", "laundry", "cafe", "bakery"],
    "shopping": ["mall", "market", "electronics_store"],
}


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


async def search_nearby_services(
    core_task: SettlementTask,
    radius_km: float = 2.0,
    categories: Optional[List[str]] = None
) -> List[ServiceLocation]:
    """
    Search for nearby services around a core task location using Overpass API.
    
    Args:
        core_task: The core task to search around
        radius_km: Search radius in kilometers
        categories: List of service categories to search for
        
    Returns:
        List of nearby service locations
    """
    if not core_task.get("location"):
        return []
    
    location = core_task["location"]
    lat, lon = location["latitude"], location["longitude"]
    
    if not categories:
        # Determine categories based on task title/description
        categories = _infer_relevant_categories(core_task)
    
    # Use Overpass API for POI search
    radius_m = int(radius_km * 1000)  # Convert km to meters
    services = await search_nearby_pois_overpass(
        lat, lon,
        radius_m=radius_m,
        service_types=categories,
        limit=5  # Limit per category
    )
    
    # Convert to our ServiceLocation format
    formatted_services = []
    for service in services:
        formatted_services.append({
            "id": service["id"],
            "name": service["name"],
            "address": service["address"],
            "latitude": service["latitude"],
            "longitude": service["longitude"],
            "rating": service.get("rating", 4.0),
            "type": service.get("service_type", service.get("type", "unknown")),
            "description": service.get("description", "")
        })
    
    # Remove duplicates and filter by distance
    formatted_services = _deduplicate_services(formatted_services)
    formatted_services = [s for s in formatted_services if calculate_distance_km(
        lat, lon, s["latitude"], s["longitude"]
    ) <= radius_km]
    
    return formatted_services


async def _search_category_nominatim(
    lat: float,
    lon: float,
    radius_km: float,
    category: str
) -> List[ServiceLocation]:
    """
    Search for a specific category using Nominatim.
    """
    # Map our categories to Nominatim amenity types
    amenity_mapping = {
        "convenience_store": "convenience",
        "pharmacy": "pharmacy",
        "supermarket": "supermarket",
        "restaurant": "restaurant",
        "post_office": "post_office",
        "photo_studio": "photo_studio",
        "gym": "gym",
        "clinic": "clinic",
        "laundry": "laundry",
        "cafe": "cafe",
        "bakery": "bakery",
        "atm": "atm",
        "mall": "mall",
        "market": "marketplace",
    }
    
    amenity = amenity_mapping.get(category, category)
    
    # Use Nominatim search with amenity filter
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "format": "json",
        "amenity": amenity,
        "lat": lat,
        "lon": lon,
        "bounded": 1,
        "limit": 10,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers={"User-Agent": "HK-Immigration-Assistant/1.0"}) as response:
                if response.status == 200:
                    data = await response.json()
                    services = []
                    
                    for item in data:
                        # Check if within radius
                        item_lat = float(item.get("lat", 0))
                        item_lon = float(item.get("lon", 0))
                        distance = calculate_distance_km(lat, lon, item_lat, item_lon)
                        
                        if distance <= radius_km:
                            services.append({
                                "id": item.get("place_id", ""),
                                "name": item.get("display_name", "").split(",")[0],
                                "address": item.get("display_name", ""),
                                "latitude": item_lat,
                                "longitude": item_lon,
                                "rating": 4.0,  # Default rating
                                "type": category,
                                "description": f"{category.replace('_', ' ').title()} near {item.get('display_name', '').split(',')[0]}"
                            })
                    
                    return services
    except Exception as e:
        print(f"Error searching nearby services: {e}")
    
    return []


def _infer_relevant_categories(task: SettlementTask) -> List[str]:
    """
    Infer relevant service categories based on task title and description.
    """
    title_lower = task["title"].lower()
    desc_lower = task["description"].lower()
    text = f"{title_lower} {desc_lower}"
    
    categories = []
    
    # Arrival tasks
    if "airport" in text or "arrival" in text or "check-in" in text:
        categories.extend(SERVICE_CATEGORIES["arrival"])
        categories.extend(SERVICE_CATEGORIES["daily_life"])
    
    # Housing tasks
    if "property" in text or "housing" in text or "apartment" in text:
        categories.extend(SERVICE_CATEGORIES["housing"])
        categories.extend(SERVICE_CATEGORIES["daily_life"])
    
    # Identity/banking tasks
    if "hkid" in text or "identity" in text:
        categories.extend(SERVICE_CATEGORIES["identity"])
    
    if "bank" in text:
        categories.extend(SERVICE_CATEGORIES["banking"])
        categories.extend(SERVICE_CATEGORIES["daily_life"])
    
    # Transportation tasks
    if "transport" in text or "car" in text or "license" in text:
        categories.extend(SERVICE_CATEGORIES["transportation"])
    
    # Default: daily life essentials
    if not categories:
        categories.extend(SERVICE_CATEGORIES["daily_life"])
    
    return list(set(categories))  # Remove duplicates


def _deduplicate_services(services: List[ServiceLocation]) -> List[ServiceLocation]:
    """
    Remove duplicate services based on name and location.
    """
    seen = set()
    unique = []
    
    for service in services:
        key = (service["name"], round(service["latitude"], 4), round(service["longitude"], 4))
        if key not in seen:
            seen.add(key)
            unique.append(service)
    
    return unique


def calculate_relevance_score(
    service: ServiceLocation,
    core_task: SettlementTask,
    customer_info: CustomerInfo
) -> float:
    """
    Calculate relevance score for an extended activity.
    Score is between 0 and 1, where 1 is most relevant.
    
    Factors:
    - Distance from core task (40% weight)
    - Time compatibility (30% weight)
    - User needs match (30% weight)
    
    Args:
        service: The service location
        core_task: The core task this service would extend
        customer_info: Customer information
        
    Returns:
        Relevance score (0-1)
    """
    score = 0.0
    
    if not core_task.get("location"):
        return 0.0
    
    core_location = core_task["location"]
    
    # 1. Distance factor (40% weight)
    distance_km = calculate_distance_km(
        core_location["latitude"],
        core_location["longitude"],
        service["latitude"],
        service["longitude"]
    )
    
    # Score decreases linearly from 1.0 at 0km to 0.0 at 2km
    distance_score = max(0, 1 - distance_km / 2.0)
    score += distance_score * 0.4
    
    # 2. Time compatibility (30% weight)
    # For now, assume all services are time-compatible
    # In future, can check opening hours, estimated duration, etc.
    time_score = 1.0
    score += time_score * 0.3
    
    # 3. User needs match (30% weight)
    need_score = _calculate_need_match(service, customer_info)
    score += need_score * 0.3
    
    return round(score, 2)


def _calculate_need_match(service: ServiceLocation, customer_info: CustomerInfo) -> float:
    """
    Calculate how well a service matches user needs.
    """
    service_type = service["type"]
    score = 0.5  # Base score
    
    # Family with children
    if customer_info.get("has_children"):
        if service_type in ["pharmacy", "clinic", "supermarket", "park"]:
            score += 0.3
    
    # Needs car
    if customer_info.get("needs_car"):
        if service_type in ["car_rental", "parking", "gas_station"]:
            score += 0.4
    
    # Budget-conscious (lower budget)
    budget = customer_info.get("housing_budget", 0)
    if budget < 25000:  # Lower budget
        if service_type in ["market", "convenience_store"]:
            score += 0.2
    else:  # Higher budget
        if service_type in ["mall", "gym", "cafe"]:
            score += 0.2
    
    # Always useful services
    if service_type in ["supermarket", "pharmacy", "atm", "convenience_store"]:
        score += 0.2
    
    return min(1.0, score)


def generate_recommendation_reason(
    service: ServiceLocation,
    core_task: SettlementTask,
    relevance_score: float
) -> str:
    """
    Generate a human-readable, unique reason for recommending this service.
    
    This function creates more specific and varied reasons to avoid
    repetitive recommendations (e.g., "就在湾仔附近，非常方便").
    """
    if not core_task.get("location"):
        return "Convenient location"
    
    core_location = core_task["location"]
    distance_km = calculate_distance_km(
        core_location["latitude"],
        core_location["longitude"],
        service["latitude"],
        service["longitude"]
    )
    
    service_type = service["type"].replace("_", " ").title()
    service_name = service.get("name", service_type)
    
    # Build more specific and varied reasons
    reasons = []
    
    # Distance-based description
    if distance_km < 0.3:
        distance_desc = "就在附近，步行几分钟即达"
        convenience = "非常适合在完成主要任务后顺道前往"
    elif distance_km < 0.5:
        distance_desc = "距离很近，步行约5-10分钟"
        convenience = "方便您在办理事务时稍作休息"
    elif distance_km < 1.0:
        distance_desc = f"距离约{int(distance_km * 1000)}米"
        convenience = "适合在完成主要任务后前往"
    else:
        distance_desc = f"距离约{distance_km:.1f}公里"
        convenience = "可以安排在行程中"
    
    # Service-specific highlights
    service_highlights = {
        "cafe": ["这家咖啡店环境舒适，适合短暂休息", "可以在这里稍作歇息，品尝香港本地特色饮品"],
        "restaurant": ["这里是品尝地道美食的好去处", "推荐在这里用餐，体验本地风味"],
        "supermarket": ["可以在这里采购日常用品", "适合购买生活必需品"],
        "pharmacy": ["可以在这里购买常用药品", "方便购买日常健康用品"],
        "gym": ["适合保持运动习惯", "可以在这里锻炼身体"],
        "park": ["适合放松和散步", "是休息和呼吸新鲜空气的好地方"],
    }
    
    highlight = service_highlights.get(service["type"], ["值得一去"])
    
    # Combine reasons with variety
    if service_name and service_name != service_type:
        reasons.append(f"{service_name} {distance_desc}")
    else:
        reasons.append(f"{service_type} {distance_desc}")
    
    reasons.append(convenience)
    
    # Add service-specific highlight (randomly select for variety)
    import random
    if highlight:
        reasons.append(random.choice(highlight))
    
    # Add relevance-based recommendation
    if relevance_score > 0.8:
        reasons.append("强烈推荐")
    elif relevance_score > 0.6:
        reasons.append("值得考虑")
    
    return "。".join(reasons) + "。"


async def find_extended_activities_for_task(
    core_task: SettlementTask,
    customer_info: CustomerInfo,
    max_activities: int = 3
) -> List[Tuple[ServiceLocation, float, str]]:
    """
    Find extended activities for a core task.
    
    Returns:
        List of (service, relevance_score, recommendation_reason) tuples
    """
    # Search nearby services
    nearby_services = await search_nearby_services(core_task, radius_km=2.0)
    
    if not nearby_services:
        return []
    
    # Calculate relevance scores
    scored_services = []
    for service in nearby_services:
        score = calculate_relevance_score(service, core_task, customer_info)
        if score >= 0.6:  # Threshold
            reason = generate_recommendation_reason(service, core_task, score)
            scored_services.append((service, score, reason))
    
    # Sort by score and return top N
    scored_services.sort(key=lambda x: x[1], reverse=True)
    return scored_services[:max_activities]
