"""
Hong Kong Service Locations Database
Contains coordinates and information for common service locations
"""

# Hong Kong International Airport
HKIA = {
    "id": "loc_hkia",
    "name": "Hong Kong International Airport",
    "address": "1 Sky Plaza Road, Hong Kong International Airport, Lantau",
    "latitude": 22.3080,
    "longitude": 113.9185,
    "type": "airport"
}

# MTR Stations (major hubs)
MTR_STATIONS = {
    "central": {
        "id": "loc_mtr_central",
        "name": "Central MTR Station",
        "address": "Central, Hong Kong Island",
        "latitude": 22.2813,
        "longitude": 114.1580,
        "type": "mtr_station"
    },
    "admiralty": {
        "id": "loc_mtr_admiralty",
        "name": "Admiralty MTR Station",
        "address": "Admiralty, Hong Kong Island",
        "latitude": 22.2796,
        "longitude": 114.1652,
        "type": "mtr_station"
    },
    "wan_chai": {
        "id": "loc_mtr_wan_chai",
        "name": "Wan Chai MTR Station",
        "address": "Wan Chai, Hong Kong Island",
        "latitude": 22.2770,
        "longitude": 114.1720,
        "type": "mtr_station"
    },
    "causeway_bay": {
        "id": "loc_mtr_causeway_bay",
        "name": "Causeway Bay MTR Station",
        "address": "Causeway Bay, Hong Kong Island",
        "latitude": 22.2800,
        "longitude": 114.1850,
        "type": "mtr_station"
    },
    "tsim_sha_tsui": {
        "id": "loc_mtr_tst",
        "name": "Tsim Sha Tsui MTR Station",
        "address": "Tsim Sha Tsui, Kowloon",
        "latitude": 22.2976,
        "longitude": 114.1722,
        "type": "mtr_station"
    },
    "mong_kok": {
        "id": "loc_mtr_mong_kok",
        "name": "Mong Kok MTR Station",
        "address": "Mong Kok, Kowloon",
        "latitude": 22.3193,
        "longitude": 114.1694,
        "type": "mtr_station"
    }
}

# Banks
BANKS = {
    "hsbc_central": {
        "id": "loc_hsbc_central",
        "name": "HSBC Main Building",
        "address": "1 Queen's Road Central, Central",
        "latitude": 22.2810,
        "longitude": 114.1590,
        "type": "bank"
    },
    "hsbc_wan_chai": {
        "id": "loc_hsbc_wan_chai",
        "name": "HSBC Wan Chai",
        "address": "Wan Chai Road, Wan Chai",
        "latitude": 22.2765,
        "longitude": 114.1725,
        "type": "bank"
    },
    "standard_chartered_central": {
        "id": "loc_sc_central",
        "name": "Standard Chartered Central",
        "address": "4-4A Des Voeux Road Central, Central",
        "latitude": 22.2820,
        "longitude": 114.1575,
        "type": "bank"
    },
    "boc_central": {
        "id": "loc_boc_central",
        "name": "Bank of China Tower",
        "address": "1 Garden Road, Central",
        "latitude": 22.2788,
        "longitude": 114.1615,
        "type": "bank"
    }
}

# Mobile Operators
MOBILE_SHOPS = {
    "csl_central": {
        "id": "loc_csl_central",
        "name": "CSL Store - Central",
        "address": "IFC Mall, Central",
        "latitude": 22.2850,
        "longitude": 114.1580,
        "type": "mobile_shop"
    },
    "3hk_causeway_bay": {
        "id": "loc_3hk_cwb",
        "name": "3HK Store - Causeway Bay",
        "address": "Times Square, Causeway Bay",
        "latitude": 22.2780,
        "longitude": 114.1825,
        "type": "mobile_shop"
    },
    "china_mobile_wan_chai": {
        "id": "loc_cm_wan_chai",
        "name": "China Mobile - Wan Chai",
        "address": "Wan Chai Road, Wan Chai",
        "latitude": 22.2770,
        "longitude": 114.1730,
        "type": "mobile_shop"
    }
}

# Government Offices
GOVERNMENT_OFFICES = {
    "immigration_wan_chai": {
        "id": "loc_immd_wan_chai",
        "name": "Immigration Tower",
        "address": "7 Gloucester Road, Wan Chai",
        "latitude": 22.2790,
        "longitude": 114.1725,
        "type": "government"
    },
    "immigration_tsim_sha_tsui": {
        "id": "loc_immd_tst",
        "name": "Immigration Department - TST",
        "address": "5/F, Immigration Tower, Tsim Sha Tsui",
        "latitude": 22.2976,
        "longitude": 114.1722,
        "type": "government"
    }
}

# Convenience Stores (for Octopus Card)
CONVENIENCE_STORES = {
    "7eleven_central": {
        "id": "loc_7e_central",
        "name": "7-Eleven - Central",
        "address": "Des Voeux Road Central, Central",
        "latitude": 22.2825,
        "longitude": 114.1570,
        "type": "convenience_store"
    },
    "circle_k_wan_chai": {
        "id": "loc_ck_wan_chai",
        "name": "Circle K - Wan Chai",
        "address": "Hennessy Road, Wan Chai",
        "latitude": 22.2775,
        "longitude": 114.1715,
        "type": "convenience_store"
    }
}

# Shopping Areas (for general shopping)
SHOPPING_AREAS = {
    "times_square": {
        "id": "loc_times_square",
        "name": "Times Square",
        "address": "1 Matheson Street, Causeway Bay",
        "latitude": 22.2780,
        "longitude": 114.1825,
        "type": "shopping"
    },
    "ifc_mall": {
        "id": "loc_ifc",
        "name": "IFC Mall",
        "address": "8 Finance Street, Central",
        "latitude": 22.2850,
        "longitude": 114.1580,
        "type": "shopping"
    }
}

def get_location_by_type(location_type: str, preferred_area: str = None):
    """
    Get a location by type, optionally filtering by preferred area.
    
    Args:
        location_type: Type of location (bank, mobile_shop, mtr_station, etc.)
        preferred_area: Preferred area name (central, wan_chai, causeway_bay, etc.)
        
    Returns:
        Location dictionary or None
    """
    if location_type == "airport":
        return HKIA
    
    if location_type == "bank":
        if preferred_area and preferred_area.lower() in BANKS:
            return BANKS[preferred_area.lower()]
        return BANKS["hsbc_central"]
    
    if location_type == "mobile_shop":
        if preferred_area and preferred_area.lower() in MOBILE_SHOPS:
            return MOBILE_SHOPS[preferred_area.lower()]
        return MOBILE_SHOPS["csl_central"]
    
    if location_type == "mtr_station":
        if preferred_area and preferred_area.lower() in MTR_STATIONS:
            return MTR_STATIONS[preferred_area.lower()]
        return MTR_STATIONS["central"]
    
    if location_type == "government":
        return GOVERNMENT_OFFICES["immigration_wan_chai"]
    
    if location_type == "convenience_store":
        if preferred_area and preferred_area.lower() in CONVENIENCE_STORES:
            return CONVENIENCE_STORES[preferred_area.lower()]
        return CONVENIENCE_STORES["7eleven_central"]
    
    if location_type == "shopping":
        return SHOPPING_AREAS["times_square"]
    
    return None

def find_nearest_location(target_lat: float, target_lng: float, location_type: str):
    """
    Find the nearest location of a given type to target coordinates.
    
    Args:
        target_lat: Target latitude
        target_lng: Target longitude
        location_type: Type of location to search for
        
    Returns:
        Nearest location dictionary
    """
    import math
    
    def distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    # Get all locations of the specified type
    locations = []
    
    if location_type == "bank":
        locations = list(BANKS.values())
    elif location_type == "mobile_shop":
        locations = list(MOBILE_SHOPS.values())
    elif location_type == "mtr_station":
        locations = list(MTR_STATIONS.values())
    elif location_type == "government":
        locations = list(GOVERNMENT_OFFICES.values())
    elif location_type == "convenience_store":
        locations = list(CONVENIENCE_STORES.values())
    elif location_type == "shopping":
        locations = list(SHOPPING_AREAS.values())
    elif location_type == "airport":
        return HKIA
    
    if not locations:
        return None
    
    # Find nearest
    nearest = min(locations, key=lambda loc: distance(
        target_lat, target_lng,
        loc["latitude"], loc["longitude"]
    ))
    
    return nearest
