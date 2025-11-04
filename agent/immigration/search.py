"""
The search node is responsible for searching for service locations and properties.
"""

import os
import json
import googlemaps
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

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

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
        
        response = gmaps.places(query)
        for result in response.get("results", [])[:5]:  # Limit to 5 results
            location = {
                "id": result.get("place_id", ""),
                "name": result.get("name", ""),
                "address": result.get("formatted_address", ""),
                "latitude": result.get("geometry", {}).get("location", {}).get("lat", 0),
                "longitude": result.get("geometry", {}).get("location", {}).get("lng", 0),
                "rating": result.get("rating", 0),
                "type": location_type,
                "description": result.get("types", [])[0] if result.get("types") else ""
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
        
        response = gmaps.places(query)
        for result in response.get("results", [])[:5]:  # Limit to 5 results
            property_data = {
                "id": result.get("place_id", ""),
                "name": result.get("name", ""),
                "address": result.get("formatted_address", ""),
                "latitude": result.get("geometry", {}).get("location", {}).get("lat", 0),
                "longitude": result.get("geometry", {}).get("location", {}).get("lng", 0),
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
