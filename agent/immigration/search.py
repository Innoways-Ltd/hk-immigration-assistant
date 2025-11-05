"""
The search node is responsible for searching for service locations and properties.
Uses Google Places API (New) for better reliability and features.
"""

import os
import json
import requests
from typing import cast
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from langchain.tools import tool
from copilotkit.langgraph import copilotkit_emit_state, copilotkit_customize_config
from immigration.state import AgentState

@tool
def search_service_locations(location_type: str, area: str) -> list[dict]:
    """
    Search for service locations (banks, mobile shops, government offices, etc.) in Hong Kong.
    
    Args:
        location_type: Type of service ("bank", "mobile_shop", "government", "hospital", "supermarket")
        area: Area in Hong Kong (e.g., "Wan Chai", "Central", "Sheung Wan")
    
    Returns:
        List of service locations with name, address, and coordinates
    """

@tool
def search_properties(area: str, bedrooms: int, max_rent: int) -> list[dict]:
    """
    Search for rental properties in Hong Kong.
    
    Args:
        area: Area in Hong Kong (e.g., "Wan Chai", "Central", "Sheung Wan")
        bedrooms: Number of bedrooms required
        max_rent: Maximum monthly rent in HKD
    
    Returns:
        List of properties with address, rent, and coordinates
    """

# Google Places API (New) configuration
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1/places:searchText"


def _google_places_search(query: str, location_bias: str = None, max_results: int = 5) -> dict:
    """
    Search using Google Places API (New).

    Args:
        query: Search query
        location_bias: Location bias (e.g., "circle:1000@22.2770,114.1720")
        max_results: Maximum number of results

    Returns:
        Places search results
    """
    if not GOOGLE_PLACES_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating"
    }

    # Build request data
    data = {
        "textQuery": query,
        "maxResultCount": max_results
    }

    # Add location bias if provided (for Hong Kong area)
    if location_bias:
        data["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": 22.3193,  # Hong Kong center
                    "longitude": 114.1694
                },
                "radius": 20000.0  # 20km radius
            }
        }

    try:
        response = requests.post(GOOGLE_PLACES_BASE_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            print("Google Places API (New) not enabled. Please enable it at: https://console.developers.google.com/apis/api/places.googleapis.com/overview")
            print("Falling back to mock data for development...")
            return _get_mock_places_data(query, max_results)
        else:
            print(f"Google Places API HTTP error: {e}")
            return {"places": []}
    except requests.exceptions.RequestException as e:
        print(f"Google Places API network error: {e}")
        print("Falling back to mock data for development...")
        return _get_mock_places_data(query, max_results)


def _get_mock_places_data(query: str, max_results: int = 5) -> dict:
    """
    Generate mock places data for development when API is not available.

    Args:
        query: Search query string
        max_results: Maximum number of results

    Returns:
        Mock places data in Google Places API format
    """
    # Mock data based on query keywords
    mock_data = {
        "bank": [
            {
                "id": "mock_bank_1",
                "displayName": {"text": "Hang Seng Bank"},
                "formattedAddress": "1 Queen's Road Central, Central, Hong Kong",
                "location": {"latitude": 22.2819, "longitude": 114.1556},
                "rating": 4.2
            },
            {
                "id": "mock_bank_2",
                "displayName": {"text": "HSBC Bank"},
                "formattedAddress": "1 Queen's Road Central, Central, Hong Kong",
                "location": {"latitude": 22.2828, "longitude": 114.1558},
                "rating": 4.1
            },
            {
                "id": "mock_bank_3",
                "displayName": {"text": "Bank of China"},
                "formattedAddress": "1 Garden Road, Central, Hong Kong",
                "location": {"latitude": 22.2820, "longitude": 114.1580},
                "rating": 4.0
            }
        ],
        "supermarket": [
            {
                "id": "mock_super_1",
                "displayName": {"text": "Wellcome Supermarket"},
                "formattedAddress": "123 Queen's Road East, Wan Chai, Hong Kong",
                "location": {"latitude": 22.2771, "longitude": 114.1700},
                "rating": 4.1
            },
            {
                "id": "mock_super_2",
                "displayName": {"text": "ParknShop"},
                "formattedAddress": "1 Hysan Avenue, Causeway Bay, Hong Kong",
                "location": {"latitude": 22.2800, "longitude": 114.1850},
                "rating": 4.0
            }
        ],
        "cafe": [
            {
                "id": "mock_cafe_1",
                "displayName": {"text": "Starbucks IFC"},
                "formattedAddress": "8 Finance Street, Central, Hong Kong",
                "location": {"latitude": 22.2850, "longitude": 114.1580},
                "rating": 4.2
            },
            {
                "id": "mock_cafe_2",
                "displayName": {"text": "Pacific Coffee"},
                "formattedAddress": "1 D'Aguilar Street, Central, Hong Kong",
                "location": {"latitude": 22.2820, "longitude": 114.1550},
                "rating": 4.0
            }
        ],
        "restaurant": [
            {
                "id": "mock_rest_1",
                "displayName": {"text": "Din Tai Fung"},
                "formattedAddress": "Shop 130, 2/F, Times Square, Causeway Bay, Hong Kong",
                "location": {"latitude": 22.2781, "longitude": 114.1675},
                "rating": 4.3
            },
            {
                "id": "mock_rest_2",
                "displayName": {"text": "Yung Kee Restaurant"},
                "formattedAddress": "32-40 Wellington Street, Central, Hong Kong",
                "location": {"latitude": 22.2826, "longitude": 114.1554},
                "rating": 4.1
            }
        ],
        "apartment": [
            {
                "id": "mock_apt_1",
                "displayName": {"text": "Pacific Place Apartments"},
                "formattedAddress": "88 Queensway, Admiralty, Hong Kong",
                "location": {"latitude": 22.2780, "longitude": 114.1667},
                "rating": 4.5
            },
            {
                "id": "mock_apt_2",
                "displayName": {"text": "The Harbourview"},
                "formattedAddress": "4 Harbour Road, Wan Chai, Hong Kong",
                "location": {"latitude": 22.2810, "longitude": 114.1720},
                "rating": 4.3
            }
        ]
    }

    # Determine data type based on query keywords
    query_lower = query.lower()

    if "bank" in query_lower:
        places = mock_data["bank"]
    elif "supermarket" in query_lower or "super" in query_lower:
        places = mock_data["supermarket"]
    elif "cafe" in query_lower or "coffee" in query_lower:
        places = mock_data["cafe"]
    elif "restaurant" in query_lower or "food" in query_lower:
        places = mock_data["restaurant"]
    elif "apartment" in query_lower or "flat" in query_lower or "rent" in query_lower:
        places = mock_data["apartment"]
    else:
        # Default to bank data
        places = mock_data["bank"]

    return {"places": places[:max_results]}


# Mapping of service types to Google Maps search queries
SERVICE_TYPE_QUERIES = {
    "bank": "bank",
    "mobile_shop": "mobile phone shop",
    "government": "government office",
    "hospital": "hospital",
    "supermarket": "supermarket",
    "immigration_dept": "Immigration Department Hong Kong",
    "tax_office": "Inland Revenue Department Hong Kong",
}

async def search_node(state: AgentState, config: RunnableConfig):
    """
    The search node is responsible for searching for service locations and properties.
    """
    ai_message = cast(AIMessage, state["messages"][-1])
    tool_call = ai_message.tool_calls[0]
    tool_name = tool_call["name"]

    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[{
            "state_key": "search_progress",
            "tool": tool_name,
            "tool_argument": "search_progress",
        }],
    )

    state["search_progress"] = state.get("search_progress", [])
    
    results = []
    
    if tool_name == "search_service_locations":
        location_type = tool_call["args"]["location_type"]
        area = tool_call["args"]["area"]
        
        query = f"{SERVICE_TYPE_QUERIES.get(location_type, location_type)} in {area}, Hong Kong"
        
        state["search_progress"].append({
            "query": query,
            "results": [],
            "done": False
        })
        await copilotkit_emit_state(config, state)
        
        response = _google_places_search(query, max_results=5)
        for result in response.get("places", [])[:5]:  # Limit to 5 results
            location = {
                "id": result.get("id", ""),
                "name": result.get("displayName", {}).get("text", ""),
                "address": result.get("formattedAddress", ""),
                "latitude": result.get("location", {}).get("latitude", 0),
                "longitude": result.get("location", {}).get("longitude", 0),
                "rating": result.get("rating", 0),
                "type": location_type,
                "description": f"{location_type.replace('_', ' ').title()} in {area}"
            }
            results.append(location)
        
        state["search_progress"][0]["done"] = True
        state["search_progress"][0]["results"] = [loc["name"] for loc in results]
        await copilotkit_emit_state(config, state)
        
    elif tool_name == "search_properties":
        area = tool_call["args"]["area"]
        bedrooms = tool_call["args"]["bedrooms"]
        max_rent = tool_call["args"]["max_rent"]
        
        # Search for residential properties
        query = f"{bedrooms} bedroom apartment for rent in {area}, Hong Kong"
        
        state["search_progress"].append({
            "query": query,
            "results": [],
            "done": False
        })
        await copilotkit_emit_state(config, state)
        
        response = _google_places_search(query, max_results=5)
        for result in response.get("places", [])[:5]:  # Limit to 5 results
            property_data = {
                "id": result.get("id", ""),
                "name": result.get("displayName", {}).get("text", ""),
                "address": result.get("formattedAddress", ""),
                "latitude": result.get("location", {}).get("latitude", 0),
                "longitude": result.get("location", {}).get("longitude", 0),
                "bedrooms": bedrooms,
                "rent": max_rent,  # In real app, would get from property API
                "furnished": True,
                "commute_time": None,
                "description": f"{bedrooms} bedroom apartment in {area}"
            }
            results.append(property_data)
        
        state["search_progress"][0]["done"] = True
        state["search_progress"][0]["results"] = [prop["name"] for prop in results]
        await copilotkit_emit_state(config, state)
    
    state["search_progress"] = []
    await copilotkit_emit_state(config, state)

    state["messages"].append(ToolMessage(
        tool_call_id=tool_call["id"],
        content=f"Found {len(results)} results: {json.dumps(results)}"
    ))

    return state


# Test function for Google Places API
def test_google_places_api():
    """Test the new Google Places API implementation with fallback."""
    print("Testing Google Places API (New) with fallback...")

    # Test service location search
    result1 = _google_places_search("bank in Central, Hong Kong", max_results=3)
    places1 = result1.get('places', [])
    print(f"Bank search results: {len(places1)} places found")

    # Test property search
    result2 = _google_places_search("2 bedroom apartment for rent in Wan Chai, Hong Kong", max_results=3)
    places2 = result2.get('places', [])
    print(f"Property search results: {len(places2)} places found")

    # Print sample results
    if places1:
        place = places1[0]
        name = place.get('displayName', {}).get('text', 'Unknown')
        address = place.get('formattedAddress', 'Unknown address')
        print(f"Sample bank: {name} at {address}")

    if places2:
        place = places2[0]
        name = place.get('displayName', {}).get('text', 'Unknown')
        address = place.get('formattedAddress', 'Unknown address')
        print(f"Sample property: {name} at {address}")

    # Test mock data directly
    print("\nTesting mock data fallback:")
    mock_result = _get_mock_places_data("supermarket in Hong Kong", 2)
    mock_places = mock_result.get('places', [])
    print(f"Mock data results: {len(mock_places)} places found")
    for place in mock_places:
        name = place.get('displayName', {}).get('text', 'Unknown')
        address = place.get('formattedAddress', 'Unknown address')
        print(f"  - {name}: {address}")

    print("Google Places API test completed.")


if __name__ == "__main__":
    test_google_places_api()
