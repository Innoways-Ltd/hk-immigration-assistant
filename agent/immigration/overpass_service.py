"""
Overpass API Service for POI Search
More reliable than Nominatim for finding nearby amenities
"""
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


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
    Search for nearby POIs using Overpass API.
    
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
    
    for service_type in service_types:
        tags = SERVICE_TAG_MAPPING.get(service_type)
        if not tags:
            continue
        
        try:
            pois = await _query_overpass(lat, lon, radius_m, tags, limit)
            
            # Add service type to each POI
            for poi in pois:
                poi["service_type"] = service_type
            
            all_pois.extend(pois)
            
            # Rate limiting: wait 0.5s between requests
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error querying Overpass for {service_type}: {e}")
            continue
    
    return all_pois


async def _query_overpass(
    lat: float,
    lon: float,
    radius_m: int,
    tags: Dict[str, str],
    limit: int
) -> List[Dict[str, Any]]:
    """
    Query Overpass API for specific tags.
    """
    # Build tag filter
    tag_filters = []
    for key, value in tags.items():
        tag_filters.append(f'["{key}"="{value}"]')
    tag_filter_str = "".join(tag_filters)
    
    # Build Overpass query
    query = f"""
    [out:json][timeout:25];
    (
      node{tag_filter_str}(around:{radius_m},{lat},{lon});
      way{tag_filter_str}(around:{radius_m},{lat},{lon});
    );
    out center {limit};
    """
    
    url = "https://overpass-api.de/api/interpreter"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data={"data": query},
                headers={"User-Agent": "HK-Immigration-Assistant/1.0"},
                timeout=aiohttp.ClientTimeout(total=30)
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
                else:
                    logger.error(f"Overpass API error: {response.status}")
                    return []
                    
    except asyncio.TimeoutError:
        logger.error("Overpass API timeout")
        return []
    except Exception as e:
        logger.error(f"Overpass API exception: {e}")
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


if __name__ == "__main__":
    asyncio.run(test_overpass_search())
