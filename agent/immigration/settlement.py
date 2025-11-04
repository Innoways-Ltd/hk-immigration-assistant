"""
The settlement node is responsible for creating and managing settlement plans.
"""

import json
from typing import cast
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from langchain.tools import tool
from copilotkit.langgraph import copilotkit_emit_state, copilotkit_customize_config
from immigration.state import AgentState, SettlementPlan, SettlementTask

@tool
def create_settlement_plan(customer_name: str) -> dict:
    """
    Create a comprehensive settlement plan for a new immigrant to Hong Kong.
    This will generate all necessary tasks based on customer information.
    """

@tool
def add_settlement_task(task: dict) -> dict:
    """
    Add a new task to the settlement plan.
    
    Args:
        task: Task details including title, description, day_range, priority, etc.
    """

@tool
def update_settlement_task(task_id: str, updates: dict) -> dict:
    """
    Update an existing settlement task.
    
    Args:
        task_id: ID of the task to update
        updates: Dictionary of fields to update
    """

@tool
def complete_settlement_task(task_id: str) -> dict:
    """
    Mark a settlement task as completed.
    
    Args:
        task_id: ID of the task to complete
    """

def generate_default_tasks(customer_info: dict, office_coords: tuple = None) -> list[SettlementTask]:
    """Generate default settlement tasks based on customer information."""
    
    tasks = []
    
    # Phase 1: Arrival & Temporary Settlement (Day 1-3)
    tasks.append({
        "id": "task_001",
        "title": "Airport Pickup",
        "description": "Arrange pickup from Hong Kong International Airport to temporary accommodation",
        "day_range": "Day 1",
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport", "Visa", "Flight itinerary"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": []
    })
    
    tasks.append({
        "id": "task_002",
        "title": "Check-in to Temporary Accommodation",
        "description": f"Check-in to hotel/serviced apartment for {customer_info.get('temporary_accommodation_days', 30)} days",
        "day_range": "Day 1",
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport", "Booking confirmation"],
        "estimated_duration": "30 minutes",
        "status": "pending",
        "dependencies": ["task_001"]
    })
    
    tasks.append({
        "id": "task_003",
        "title": "Purchase Octopus Card",
        "description": "Buy Octopus card for public transportation at MTR station or convenience store",
        "day_range": "Day 1-2",
        "priority": "high",
        "location": None,
        "documents_needed": [],
        "estimated_duration": "15 minutes",
        "status": "pending",
        "dependencies": []
    })
    
    tasks.append({
        "id": "task_004",
        "title": "Get Mobile SIM Card",
        "description": "Purchase local SIM card from CSL, 3HK, or China Mobile",
        "day_range": "Day 1-2",
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport"],
        "estimated_duration": "30 minutes",
        "status": "pending",
        "dependencies": []
    })
    
    # Phase 2: Housing (Day 3-7)
    tasks.append({
        "id": "task_005",
        "title": "Property Viewing - First Batch",
        "description": "View shortlisted properties in preferred areas",
        "day_range": "Day 3-5",
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport", "Employment letter", "Proof of income"],
        "estimated_duration": "3-4 hours",
        "status": "pending",
        "dependencies": []
    })
    
    tasks.append({
        "id": "task_006",
        "title": "Sign Lease Agreement",
        "description": "Sign rental agreement and pay deposit",
        "day_range": "Day 5-7",
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport", "Employment letter", "Bank statement", "Deposit payment"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": ["task_005"]
    })
    
    tasks.append({
        "id": "task_007",
        "title": "Setup Utilities",
        "description": "Arrange electricity, gas, water, and internet connection",
        "day_range": "Day 7-10",
        "priority": "medium",
        "location": None,
        "documents_needed": ["Lease agreement", "HKID (if available)"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": ["task_006"]
    })
    
    # Phase 3: Banking & Identity (Day 7-14)
    tasks.append({
        "id": "task_008",
        "title": "Open Bank Account",
        "description": "Open bank account at HSBC, Standard Chartered, or Bank of China",
        "day_range": "Day 7-10",
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport", "Proof of address", "Employment letter"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": []
    })
    
    tasks.append({
        "id": "task_009",
        "title": "Apply for Hong Kong Identity Card",
        "description": "Register for HKID at Immigration Department within 30 days of arrival",
        "day_range": "Day 10-14",
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport", "Visa", "Proof of address", "Employment letter"],
        "estimated_duration": "2-3 hours",
        "status": "pending",
        "dependencies": ["task_006"]
    })
    
    tasks.append({
        "id": "task_010",
        "title": "Register for Tax",
        "description": "Register with Inland Revenue Department for tax purposes",
        "day_range": "Day 14-21",
        "priority": "medium",
        "location": None,
        "documents_needed": ["Passport", "HKID", "Employment contract"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": ["task_009"]
    })
    
    # Phase 4: Work & Daily Life (Day 14-30)
    tasks.append({
        "id": "task_011",
        "title": "Visit Office Location",
        "description": "Familiarize with office location and commute route",
        "day_range": "Day 14-21",
        "priority": "medium",
        "location": None,
        "documents_needed": [],
        "estimated_duration": "2-3 hours",
        "status": "pending",
        "dependencies": []
    })
    
    tasks.append({
        "id": "task_012",
        "title": "Explore Neighborhood",
        "description": "Find nearby supermarkets, restaurants, gyms, and essential services",
        "day_range": "Day 14-30",
        "priority": "low",
        "location": None,
        "documents_needed": [],
        "estimated_duration": "Ongoing",
        "status": "pending",
        "dependencies": ["task_006"]
    })
    
    tasks.append({
        "id": "task_013",
        "title": "Register with Family Doctor",
        "description": "Find and register with a general practitioner",
        "day_range": "Day 21-30",
        "priority": "medium",
        "location": None,
        "documents_needed": ["HKID", "Insurance card"],
        "estimated_duration": "1 hour",
        "status": "pending",
        "dependencies": ["task_009"]
    })
    
    # Add driving license if needed
    if customer_info.get("needs_car"):
        tasks.append({
            "id": "task_014",
            "title": "Apply for Hong Kong Driving License",
            "description": "Convert foreign driving license or apply for new license",
            "day_range": "Day 21-30",
            "priority": "medium",
            "location": None,
            "documents_needed": ["Passport", "HKID", "Foreign driving license", "Proof of address"],
            "estimated_duration": "2-3 hours",
            "status": "pending",
            "dependencies": ["task_009"]
        })
    
    # Add school registration if has children
    if customer_info.get("has_children"):
        tasks.append({
            "id": "task_015",
            "title": "Register Children for School",
            "description": "Enroll children in international or local school",
            "day_range": "Day 7-14",
            "priority": "high",
            "location": None,
            "documents_needed": ["Passport", "Birth certificate", "Previous school records", "Proof of address"],
            "estimated_duration": "2-3 hours",
            "status": "pending",
            "dependencies": ["task_006"]
        })
    
    return tasks

async def settlement_node(state: AgentState, config: RunnableConfig):
    """
    The settlement node creates and manages settlement plans.
    """
    ai_message = cast(AIMessage, state["messages"][-1])
    tool_call = ai_message.tool_calls[0]
    tool_name = tool_call["name"]
    
    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[{
            "state_key": "planning_progress",
            "tool": tool_name,
            "tool_argument": "planning_progress",
        }],
    )
    
    state["planning_progress"] = state.get("planning_progress", [])
    
    if tool_name == "create_settlement_plan":
        customer_name = tool_call["args"]["customer_name"]
        customer_info = state.get("customer_info", {})
        
        # Generate default tasks
        tasks = generate_default_tasks(customer_info)
        
        # Create settlement plan
        office_coords = customer_info.get("office_coordinates", (22.2770, 114.1720))  # Default to Wan Chai
        
        plan: SettlementPlan = {
            "id": "plan_001",
            "customer_name": customer_name,
            "center_latitude": office_coords[0],
            "center_longitude": office_coords[1],
            "zoom": 14,
            "tasks": tasks,
            "properties": [],
            "service_locations": []
        }
        
        state["settlement_plan"] = plan
        state["planning_progress"].append({
            "plan": plan,
            "done": True
        })
        
        await copilotkit_emit_state(config, state)
        
        state["messages"].append(ToolMessage(
            tool_call_id=tool_call["id"],
            content=f"Created settlement plan with {len(tasks)} tasks for {customer_name}"
        ))
    
    state["planning_progress"] = []
    await copilotkit_emit_state(config, state)
    
    return state

async def perform_settlement_node(state: AgentState, config: RunnableConfig):
    """
    Perform the settlement plan operations (add/update/complete tasks).
    """
    return state
