"""
POI Search Service with Multiple Backends
Supports Overpass API with caching and fallback options
"""
import os
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)

# Global rate limiter for Overpass API
_last_request_time = 0
MIN_REQUEST_INTERVAL = 1.0  # Minimum 1 second between requests


async def _rate_limit_wait():
    """
    Global rate limiter to ensure minimum interval between Overpass API requests.
    """
    global _last_request_time
    current_time = time.time()
    time_since_last_request = current_time - _last_request_time

    if time_since_last_request < MIN_REQUEST_INTERVAL:
        wait_time = MIN_REQUEST_INTERVAL - time_since_last_request
        logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before next request")
        await asyncio.sleep(wait_time)

    _last_request_time = time.time()


# Service type mapping to Overpass tags
SERVICE_TAG_MAPPING = {
    "supermarket": {"shop": "supermarket"},
    "convenience_store": {"shop": "convenience"},
    "pharmacy": {"amenity": "pharmacy"},
    "restaurant": {"amenity": "restaurant"},
    "cafe": {"amenity": "cafe"},
    "bakery": {"shop": "bakery"},
    "gym": {"leisure": "fitness_centre"},
    "clinic": {"amenity": "clinic"},
    "bank": {"amenity": "bank"},
    "atm": {"amenity": "atm"},
    "mall": {"shop": "mall"},
    "market": {"amenity": "marketplace"},
}


async def search_nearby_pois_overpass(
    lat: float,
    lon: float,
    radius_m: int = 2000,
    service_types: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for nearby POIs using Overpass API with optimized error handling.

    Args:
        lat: Latitude
        lon: Longitude
        radius_m: Search radius in meters (default 2000m = 2km)
        service_types: List of service types to search for
        limit: Maximum number of results per service type

    Returns:
        List of POI dictionaries
    """
    if not service_types:
        service_types = ["supermarket", "convenience_store", "pharmacy", "cafe", "restaurant"]

    all_pois = []
    consecutive_failures = 0
    max_consecutive_failures = 3

    for service_type in service_types:
        tags = SERVICE_TAG_MAPPING.get(service_type)
        if not tags:
            continue

        try:
            pois = await _query_overpass(lat, lon, radius_m, tags, limit)

            if pois:  # Only add if we got results
                # Add service type to each POI
                for poi in pois:
                    poi["service_type"] = service_type

                all_pois.extend(pois)
                consecutive_failures = 0  # Reset failure counter on success
            else:
                consecutive_failures += 1

            # Rate limiting: increase wait time after failures, more conservative
            wait_time = 1.0 if consecutive_failures == 0 else min(1.0 * (2 ** consecutive_failures), 5.0)
            await asyncio.sleep(wait_time)

            # If too many consecutive failures, add a longer break
            if consecutive_failures >= max_consecutive_failures:
                logger.warning(f"Too many consecutive failures ({consecutive_failures}), taking longer break")
                await asyncio.sleep(10.0)  # Increased from 5.0 to 10.0
                consecutive_failures = 0  # Reset after long break

        except Exception as e:
            logger.error(f"Error querying Overpass for {service_type}: {e}")
            consecutive_failures += 1
            continue

    return all_pois


# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Cache for POI data to reduce API calls
_poi_cache = {}
CACHE_TTL = 3600  # 1 hour cache


def _get_cache_key(lat: float, lon: float, radius_m: int, service_types: List[str]) -> str:
    """Generate cache key for POI requests."""
    return f"{round(lat, 3)}_{round(lon, 3)}_{radius_m}_{'_'.join(sorted(service_types))}"


def _is_cache_valid(cache_entry: Dict) -> bool:
    """Check if cache entry is still valid."""
    return time.time() - cache_entry.get('timestamp', 0) < CACHE_TTL


def _get_cached_pois(cache_key: str) -> Optional[List[Dict[str, Any]]]:
    """Get POI data from cache if valid."""
    if cache_key in _poi_cache and _is_cache_valid(_poi_cache[cache_key]):
        logger.debug(f"Using cached POI data for {cache_key}")
        return _poi_cache[cache_key]['data']
    return None


def _cache_pois(cache_key: str, pois: List[Dict[str, Any]]):
    """Cache POI data."""
    _poi_cache[cache_key] = {
        'data': pois,
        'timestamp': time.time()
    }
    logger.debug(f"Cached {len(pois)} POI entries for {cache_key}")


def _google_places_nearby_search(lat: float, lon: float, service_type: str, radius_m: int = 2000, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for nearby places using Google Places API (New).

    Args:
        lat: Latitude
        lon: Longitude
        service_type: Type of service to search for
        radius_m: Search radius in meters
        max_results: Maximum number of results

    Returns:
        List of POI dictionaries
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.error("GOOGLE_MAPS_API_KEY not configured")
        return []

    # Map service types to Google Places types
    places_type_mapping = {
        "supermarket": "supermarket",
        "convenience_store": "convenience_store",
        "pharmacy": "pharmacy",
        "restaurant": "restaurant",
        "cafe": "cafe",
        "bakery": "bakery",
        "gym": "gym",
        "clinic": "hospital",
        "bank": "bank",
        "atm": "atm",
        "mall": "shopping_mall",
        "market": "market"
    }

    places_type = places_type_mapping.get(service_type, service_type)

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.types"
    }

    data = {
        "includedTypes": [places_type],
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon
                },
                "radius": radius_m
            }
        },
        "maxResultCount": max_results
    }

    try:
        import requests
        response = requests.post(GOOGLE_PLACES_NEARBY_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()

        result = response.json()
        places = result.get("places", [])

        # Convert to our POI format
        pois = []
        for place in places:
            poi = {
                "id": place.get("id", ""),
                "name": place.get("displayName", {}).get("text", ""),
                "address": place.get("formattedAddress", ""),
                "latitude": place.get("location", {}).get("latitude", 0),
                "longitude": place.get("location", {}).get("longitude", 0),
                "rating": place.get("rating", 4.0),
                "type": places_type,
                "service_type": service_type,
                "description": f"{place.get('displayName', {}).get('text', '')} in Hong Kong"
            }
            pois.append(poi)

        return pois

    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            logger.error("Google Places API access denied. Check API key and Places API enablement.")
            logger.error("Enable Places API at: https://console.developers.google.com/apis/api/places.googleapis.com")
        else:
            logger.error(f"Google Places API HTTP error: {e}")
        return []
    except Exception as e:
        logger.error(f"Google Places API error: {e}")
        return []


# Predefined POI data for Hong Kong major areas (fallback when API fails)
HK_PREDEFINED_POIS = {
    "central": [
        {"name": "IFC Mall", "type": "mall", "service_type": "mall", "latitude": 22.2849, "longitude": 114.1581},
        {"name": "Pacific Place", "type": "mall", "service_type": "mall", "latitude": 22.2775, "longitude": 114.1667},
        {"name": "Times Square", "type": "mall", "service_type": "mall", "latitude": 22.2782, "longitude": 114.1822},
        {"name": "Wellcome Supermarket", "type": "supermarket", "service_type": "supermarket", "latitude": 22.2819, "longitude": 114.1556},
        {"name": "Starbucks IFC", "type": "cafe", "service_type": "cafe", "latitude": 22.2850, "longitude": 114.1580},
        {"name": "Pret A Manger", "type": "cafe", "service_type": "cafe", "latitude": 22.2820, "longitude": 114.1550},
        {"name": "Yung Kee Restaurant", "type": "restaurant", "service_type": "restaurant", "latitude": 22.2826, "longitude": 114.1554},
        {"name": "Din Tai Fung", "type": "restaurant", "service_type": "restaurant", "latitude": 22.2781, "longitude": 114.1675},
        {"name": "Watsons Pharmacy", "type": "pharmacy", "service_type": "pharmacy", "latitude": 22.2815, "longitude": 114.1550},
        {"name": "Hang Seng Bank", "type": "bank", "service_type": "bank", "latitude": 22.2828, "longitude": 114.1558}
    ],
    "wan_chai": [
        {"name": "Times Square", "type": "mall", "service_type": "mall", "latitude": 22.2782, "longitude": 114.1822},
        {"name": "Wellcome", "type": "supermarket", "service_type": "supermarket", "latitude": 22.2771, "longitude": 114.1700},
        {"name": "Pacific Coffee", "type": "cafe", "service_type": "cafe", "latitude": 22.2784, "longitude": 114.1705},
        {"name": "Starbucks", "type": "cafe", "service_type": "cafe", "latitude": 22.2790, "longitude": 114.1726},
        {"name": "Shanghai Restaurant", "type": "restaurant", "service_type": "restaurant", "latitude": 22.2788, "longitude": 114.1730},
        {"name": "Watsons", "type": "pharmacy", "service_type": "pharmacy", "latitude": 22.2775, "longitude": 114.1720},
        {"name": "ATM", "type": "atm", "service_type": "atm", "latitude": 22.2778, "longitude": 114.1725}
    ],
    "causeway_bay": [
        {"name": "Times Square", "type": "mall", "service_type": "mall", "latitude": 22.2782, "longitude": 114.1822},
        {"name": "Sogo", "type": "mall", "service_type": "mall", "latitude": 22.2780, "longitude": 114.1810},
        {"name": "Park Lane", "type": "mall", "service_type": "mall", "latitude": 22.2795, "longitude": 114.1880},
        {"name": "Wellcome", "type": "supermarket", "service_type": "supermarket", "latitude": 22.2800, "longitude": 114.1850},
        {"name": "Starbucks", "type": "cafe", "service_type": "cafe", "latitude": 22.2789, "longitude": 114.1826},
        {"name": "Pacific Coffee", "type": "cafe", "service_type": "cafe", "latitude": 22.2800, "longitude": 114.1830},
        {"name": "Joy Hing Roasted Goose", "type": "restaurant", "service_type": "restaurant", "latitude": 22.2792, "longitude": 114.1828},
        {"name": "Watsons", "type": "pharmacy", "service_type": "pharmacy", "latitude": 22.2795, "longitude": 114.1820}
    ]
}


def _get_nearest_predefined_pois(lat: float, lon: float, service_types: List[str], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get predefined POI data for Hong Kong areas as fallback.
    """
    # Determine which area we're in (simplified logic)
    if 22.275 <= lat <= 22.290 and 114.150 <= lon <= 114.175:
        area = "central"
    elif 22.275 <= lat <= 22.285 and 114.165 <= lon <= 114.185:
        area = "wan_chai"
    elif 22.275 <= lat <= 22.285 and 114.175 <= lon <= 114.195:
        area = "causeway_bay"
    else:
        # Default to central if location doesn't match known areas
        area = "central"

    pois = HK_PREDEFINED_POIS.get(area, [])
    filtered_pois = [poi for poi in pois if poi.get("service_type") in service_types]

    # Add missing fields for compatibility
    for poi in filtered_pois:
        if "id" not in poi:
            poi["id"] = f"predefined_{area}_{poi['name'].lower().replace(' ', '_')}"
        if "address" not in poi:
            poi["address"] = f"{poi['name']}, {area.title().replace('_', ' ')}, Hong Kong"
        if "description" not in poi:
            poi["description"] = f"{poi['name']} in {area.title().replace('_', ' ')}"
        if "rating" not in poi:
            poi["rating"] = 4.0

    return filtered_pois[:limit]


async def search_nearby_pois_cached(
    lat: float,
    lon: float,
    radius_m: int = 2000,
    service_types: Optional[List[str]] = None,
    limit: int = 10,
    use_cache: bool = True,
    use_fallback: bool = True
) -> List[Dict[str, Any]]:
    """
    Search for nearby POIs using Google Places API with caching and fallback options.

    Args:
        lat: Latitude
        lon: Longitude
        radius_m: Search radius in meters
        service_types: List of service types to search for
        limit: Maximum number of results per service type
        use_cache: Whether to use caching
        use_fallback: Whether to use predefined data as fallback

    Returns:
        List of POI dictionaries
    """
    if not service_types:
        service_types = ["supermarket", "convenience_store", "pharmacy", "cafe", "restaurant"]

    cache_key = _get_cache_key(lat, lon, radius_m, service_types)

    # Try cache first
    if use_cache:
        cached_result = _get_cached_pois(cache_key)
        if cached_result:
            return cached_result

    # Try Google Places API calls
    all_pois = []
    consecutive_failures = 0
    max_consecutive_failures = 3

    for service_type in service_types:
        try:
            # Use Google Places API for each service type
            pois = _google_places_nearby_search(lat, lon, service_type, radius_m, limit)

            if pois:
                all_pois.extend(pois)
                consecutive_failures = 0
            else:
                consecutive_failures += 1

            # Rate limiting between service types
            import asyncio
            await asyncio.sleep(0.5)

            # If too many consecutive failures, break
            if consecutive_failures >= max_consecutive_failures:
                logger.warning(f"Too many consecutive failures ({consecutive_failures}), stopping API calls")
                break

        except Exception as e:
            logger.error(f"Error searching for {service_type}: {e}")
            consecutive_failures += 1
            continue

    # If we got some results from Google Places API, cache and return them
    if all_pois:
        if use_cache:
            _cache_pois(cache_key, all_pois)
        return all_pois

    # If Google Places API failed completely, use fallback predefined data
    logger.warning("Google Places API calls failed, using fallback data")
    if use_fallback:
        fallback_pois = _get_nearest_predefined_pois(lat, lon, service_types, limit * len(service_types))

        if use_cache and fallback_pois:
            _cache_pois(cache_key, fallback_pois)

        return fallback_pois

    return []


async def _query_overpass(
    lat: float,
    lon: float,
    radius_m: int,
    tags: Dict[str, str],
    limit: int
) -> List[Dict[str, Any]]:
    """
    Query Overpass API for specific tags with retry mechanism for 504 errors.
    """
    # Build tag filter
    tag_filters = []
    for key, value in tags.items():
        tag_filters.append(f'["{key}"="{value}"]')
    tag_filter_str = "".join(tag_filters)

    # Build Overpass query - reduce timeout to avoid 504
    query = f"""
    [out:json][timeout:15];
    (
      node{tag_filter_str}(around:{radius_m},{lat},{lon});
      way{tag_filter_str}(around:{radius_m},{lat},{lon});
    );
    out center {limit};
    """

    url = "https://overpass-api.de/api/interpreter"

    # Apply global rate limiting before making requests
    await _rate_limit_wait()

    # Retry mechanism for rate limiting and timeout errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data={"data": query},
                    headers={"User-Agent": "HK-Immigration-Assistant/1.0"},
                    timeout=aiohttp.ClientTimeout(total=20)  # Reduced total timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        elements = data.get("elements", [])

                        pois = []
                        for elem in elements:
                            poi = _parse_overpass_element(elem)
                            if poi:
                                pois.append(poi)

                        return pois
                    elif response.status == 504:
                        # 504 Gateway Timeout - retry with exponential backoff
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # 1s, 2s, 4s
                            logger.warning(f"Overpass API 504 timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error("Overpass API 504 timeout after all retries")
                            return []
                    elif response.status == 429:
                        # 429 Too Many Requests - wait longer before retry
                        if attempt < max_retries - 1:
                            wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                            logger.warning(f"Overpass API 429 rate limited, waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error("Overpass API 429 rate limited after all retries")
                            return []
                    else:
                        logger.error(f"Overpass API error: {response.status}")
                        return []

        except asyncio.TimeoutError:
            # Client timeout - retry with exponential backoff
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Overpass API client timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                continue
            else:
                logger.error("Overpass API client timeout after all retries")
                return []
        except Exception as e:
            logger.error(f"Overpass API exception: {e}")
            return []

    return []


def _parse_overpass_element(elem: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse an Overpass API element into our POI format.
    """
    tags = elem.get("tags", {})
    
    # Get name
    name = tags.get("name") or tags.get("name:en") or tags.get("brand") or "Unnamed"
    
    # Get coordinates
    if elem.get("lat") and elem.get("lon"):
        lat = float(elem["lat"])
        lon = float(elem["lon"])
    elif elem.get("center"):
        lat = float(elem["center"]["lat"])
        lon = float(elem["center"]["lon"])
    else:
        return None
    
    # Build address from tags
    address_parts = []
    if tags.get("addr:housenumber"):
        address_parts.append(tags["addr:housenumber"])
    if tags.get("addr:street"):
        address_parts.append(tags["addr:street"])
    if tags.get("addr:district"):
        address_parts.append(tags["addr:district"])
    
    address = ", ".join(address_parts) if address_parts else name
    
    return {
        "id": f"osm_{elem.get('type', 'node')}_{elem.get('id', 0)}",
        "name": name,
        "address": address,
        "latitude": lat,
        "longitude": lon,
        "rating": 4.0,  # Default rating
        "type": tags.get("amenity") or tags.get("shop") or "unknown",
        "description": f"{name} in Hong Kong"
    }


async def test_overpass_search():
    """Test function"""
    # Test near Wan Chai office
    lat = 22.2770
    lon = 114.1720

    print("Testing Overpass API search near Wan Chai...")
    pois = await search_nearby_pois_overpass(
        lat, lon,
        radius_m=1000,
        service_types=["supermarket", "cafe", "restaurant"],
        limit=5
    )

    print(f"Found {len(pois)} POIs:")
    for poi in pois:
        print(f"  - {poi['name']} ({poi['service_type']}) at ({poi['latitude']}, {poi['longitude']})")


async def test_cached_search():
    """Test cached POI search with fallback."""
    # Test near Central
    lat = 22.2849
    lon = 114.1581

    print("\nTesting cached POI search with fallback...")

    # First call - should use API or fallback
    print("First call (should fetch data):")
    pois1 = await search_nearby_pois_cached(
        lat, lon,
        radius_m=1000,
        service_types=["supermarket", "cafe", "restaurant"],
        limit=5,
        use_cache=True,
        use_fallback=True
    )
    print(f"Found {len(pois1)} POIs")

    # Second call - should use cache
    print("Second call (should use cache):")
    pois2 = await search_nearby_pois_cached(
        lat, lon,
        radius_m=1000,
        service_types=["supermarket", "cafe", "restaurant"],
        limit=5,
        use_cache=True,
        use_fallback=True
    )
    print(f"Found {len(pois2)} POIs (cached)")

    # Test fallback data
    print("Testing fallback data (Causeway Bay):")
    fallback_pois = await search_nearby_pois_cached(
        22.2789, 114.1826,  # Causeway Bay coordinates
        radius_m=1000,
        service_types=["mall", "cafe"],
        limit=3,
        use_cache=False,  # Disable cache to force fallback
        use_fallback=True
    )
    print(f"Found {len(fallback_pois)} fallback POIs:")
    for poi in fallback_pois:
        print(f"  - {poi['name']} ({poi.get('service_type', 'unknown')})")


if __name__ == "__main__":
    asyncio.run(test_overpass_search())
    asyncio.run(test_cached_search())
