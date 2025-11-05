"""
The settlement node is responsible for creating and managing settlement plans.
"""

import json
import math
from typing import cast
from datetime import datetime, timedelta
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from langchain.tools import tool
from copilotkit.langgraph import copilotkit_emit_state, copilotkit_customize_config
from immigration.state import AgentState, SettlementPlan, SettlementTask
from immigration.task_generator import (
    generate_all_tasks_async,
    optimize_tasks_with_routing,
    extract_service_locations,
    calculate_plan_duration
)
from immigration.extended_task_generator import (
    generate_extended_tasks,
    merge_and_optimize_tasks
)
from immigration.plan_summarizer import generate_plan_summary

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

def calculate_plan_duration(customer_info: dict) -> int:
    """
    Calculate the optimal plan duration based on customer information.
    
    Args:
        customer_info: Customer information dictionary
        
    Returns:
        Number of days for the settlement plan
    """
    # Get temporary accommodation days
    temp_days = customer_info.get('temporary_accommodation_days')
    
    # If not specified, use default based on other factors
    if temp_days is None:
        # Default: 30 days for comprehensive settlement
        return 30
    
    # Plan should be at least as long as temporary accommodation
    # But also consider minimum time needed for essential tasks
    min_days = 14  # Minimum for HKID application (must be done within 30 days)
    
    # If temp accommodation is very short, extend plan for essential tasks
    if temp_days < min_days:
        return min_days
    
    # Otherwise, use temp accommodation days as base
    # Add buffer for tasks that extend beyond temp accommodation
    return temp_days + 7  # 7 days buffer for ongoing tasks

def format_day_range(start_day: int, end_day: int, arrival_date: str = None) -> str:
    """
    Format day range, optionally with actual dates.
    
    Args:
        start_day: Start day number
        end_day: End day number
        arrival_date: Optional arrival date string (YYYY-MM-DD)
        
    Returns:
        Formatted day range string
    """
    if start_day == end_day:
        day_str = f"Day {start_day}"
    else:
        day_str = f"Day {start_day}-{end_day}"
    
    # Add actual dates if arrival date is provided
    if arrival_date:
        try:
            arrival = datetime.strptime(arrival_date, "%Y-%m-%d")
            start_date = arrival + timedelta(days=start_day - 1)
            end_date = arrival + timedelta(days=end_day - 1)
            
            if start_day == end_day:
                date_str = start_date.strftime("%b %d")
            else:
                date_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
            
            return f"{day_str} ({date_str})"
        except:
            pass
    
    return day_str

def generate_arrival_tasks(customer_info: dict, task_id_start: int = 1) -> list[SettlementTask]:
    """Generate arrival and immediate settlement tasks (Day 1-3)."""
    
    arrival_date = customer_info.get('arrival_date')
    temp_days = customer_info.get('temporary_accommodation_days', 30)
    
    tasks = []
    task_id = task_id_start
    
    # Task 1: Airport Pickup
    tasks.append({
        "id": f"task_{task_id:03d}",
        "title": "Airport Pickup",
        "description": "Arrange pickup from Hong Kong International Airport to temporary accommodation",
        "day_range": format_day_range(1, 1, arrival_date),
        "priority": "high",
        "location": HKIA,
        "documents_needed": ["Passport", "Visa", "Flight itinerary"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": []
    })
    task_id += 1
    
    # Task 2: Check-in to Temporary Accommodation
    tasks.append({
        "id": f"task_{task_id:03d}",
        "title": "Check-in to Temporary Accommodation",
        "description": f"Check-in to hotel/serviced apartment for {temp_days} days",
        "day_range": format_day_range(1, 1, arrival_date),
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport", "Booking confirmation"],
        "estimated_duration": "30 minutes",
        "status": "pending",
        "dependencies": [f"task_{task_id-1:03d}"]
    })
    task_id += 1
    
    # Task 3: Purchase Octopus Card
    octopus_location = get_location_by_type("mtr_station", "central")
    tasks.append({
        "id": f"task_{task_id:03d}",
        "title": "Purchase Octopus Card",
        "description": "Buy Octopus card for public transportation at MTR station or convenience store",
        "day_range": format_day_range(1, 2, arrival_date),
        "priority": "high",
        "location": octopus_location,
        "documents_needed": [],
        "estimated_duration": "15 minutes",
        "status": "pending",
        "dependencies": []
    })
    task_id += 1
    
    # Task 4: Get Mobile SIM Card
    mobile_location = get_location_by_type("mobile_shop", "csl_central")
    tasks.append({
        "id": f"task_{task_id:03d}",
        "title": "Get Mobile SIM Card",
        "description": "Purchase local SIM card from CSL, 3HK, or China Mobile",
        "day_range": format_day_range(1, 2, arrival_date),
        "priority": "high",
        "location": mobile_location,
        "documents_needed": ["Passport"],
        "estimated_duration": "30 minutes",
        "status": "pending",
        "dependencies": []
    })
    
    return tasks

def generate_housing_tasks(customer_info: dict, task_id_start: int, plan_duration: int) -> list[SettlementTask]:
    """Generate housing-related tasks."""
    
    arrival_date = customer_info.get('arrival_date')
    tasks = []
    task_id = task_id_start
    
    # Adjust timing based on plan duration
    viewing_start = min(3, plan_duration - 4)
    viewing_end = min(5, plan_duration - 2)
    lease_start = min(5, plan_duration - 2)
    lease_end = min(7, plan_duration)
    
    # Task: Property Viewing
    tasks.append({
        "id": f"task_{task_id:03d}",
        "title": "Property Viewing - First Batch",
        "description": "View shortlisted properties in preferred areas",
        "day_range": format_day_range(viewing_start, viewing_end, arrival_date),
        "priority": "high",
        "location": None,
        "documents_needed": ["Passport", "Employment letter", "Proof of income"],
        "estimated_duration": "3-4 hours",
        "status": "pending",
        "dependencies": []
    })
    task_id += 1
    
    # Only add lease signing if plan is long enough
    if plan_duration >= 7:
        tasks.append({
            "id": f"task_{task_id:03d}",
            "title": "Sign Lease Agreement",
            "description": "Sign rental agreement and pay deposit",
            "day_range": format_day_range(lease_start, lease_end, arrival_date),
            "priority": "high",
            "location": None,
            "documents_needed": ["Passport", "Employment letter", "Bank statement", "Deposit payment"],
            "estimated_duration": "1-2 hours",
            "status": "pending",
            "dependencies": [f"task_{task_id-1:03d}"]
        })
        task_id += 1
        
        # Task: Setup Utilities (only if signing lease)
        if plan_duration >= 10:
            tasks.append({
                "id": f"task_{task_id:03d}",
                "title": "Setup Utilities",
                "description": "Arrange electricity, gas, water, and internet connection",
                "day_range": format_day_range(min(7, plan_duration-3), min(10, plan_duration), arrival_date),
                "priority": "medium",
                "location": None,
                "documents_needed": ["Lease agreement", "HKID (if available)"],
                "estimated_duration": "1-2 hours",
                "status": "pending",
                "dependencies": [f"task_{task_id-1:03d}"]
            })
    
    return tasks

def generate_identity_tasks(customer_info: dict, task_id_start: int, plan_duration: int) -> list[SettlementTask]:
    """Generate banking and identity-related tasks."""
    
    arrival_date = customer_info.get('arrival_date')
    tasks = []
    task_id = task_id_start
    
    # Task: Open Bank Account (can be done early)
    bank_start = min(3, plan_duration - 4)
    bank_end = min(7, plan_duration - 3)
    bank_location = get_location_by_type("bank", "hsbc_central")
    
    tasks.append({
        "id": f"task_{task_id:03d}",
        "title": "Open Bank Account",
        "description": "Open bank account at HSBC, Standard Chartered, or Bank of China",
        "day_range": format_day_range(bank_start, bank_end, arrival_date),
        "priority": "high",
        "location": bank_location,
        "documents_needed": ["Passport", "Proof of address", "Employment letter"],
        "estimated_duration": "1-2 hours",
        "status": "pending",
        "dependencies": []
    })
    task_id += 1
    
    # Task: Apply for HKID (must be done within 30 days, but usually after settling)
    if plan_duration >= 10:
        hkid_start = min(7, plan_duration - 7)
        hkid_end = min(14, plan_duration - 2)
        
        hkid_location = get_location_by_type("government")
        tasks.append({
            "id": f"task_{task_id:03d}",
            "title": "Apply for Hong Kong Identity Card",
            "description": "Register for HKID at Immigration Department within 30 days of arrival",
            "day_range": format_day_range(hkid_start, hkid_end, arrival_date),
            "priority": "high",
            "location": hkid_location,
            "documents_needed": ["Passport", "Visa", "Proof of address", "Employment letter"],
            "estimated_duration": "2-3 hours",
            "status": "pending",
            "dependencies": []
        })
        task_id += 1
        
        # Task: Register for Tax (only if plan is long enough)
        if plan_duration >= 21:
            tasks.append({
                "id": f"task_{task_id:03d}",
                "title": "Register for Tax",
                "description": "Register with Inland Revenue Department for tax purposes",
                "day_range": format_day_range(14, min(21, plan_duration), arrival_date),
                "priority": "medium",
                "location": None,
                "documents_needed": ["Passport", "HKID", "Employment contract"],
                "estimated_duration": "1-2 hours",
                "status": "pending",
                "dependencies": [f"task_{task_id-1:03d}"]
            })
    
    return tasks

def generate_daily_life_tasks(customer_info: dict, task_id_start: int, plan_duration: int) -> list[SettlementTask]:
    """Generate daily life and work-related tasks."""
    
    arrival_date = customer_info.get('arrival_date')
    tasks = []
    task_id = task_id_start
    
    # Task: Visit Office Location
    if plan_duration >= 7:
        office_start = min(5, plan_duration - 5)
        office_end = min(10, plan_duration - 2)
        
        tasks.append({
            "id": f"task_{task_id:03d}",
            "title": "Visit Office Location",
            "description": "Familiarize with office location and commute route",
            "day_range": format_day_range(office_start, office_end, arrival_date),
            "priority": "medium",
            "location": None,
            "documents_needed": [],
            "estimated_duration": "2-3 hours",
            "status": "pending",
            "dependencies": []
        })
        task_id += 1
    
    # Task: Explore Neighborhood (ongoing task)
    if plan_duration >= 10:
        explore_start = min(7, plan_duration - 7)
        
        tasks.append({
            "id": f"task_{task_id:03d}",
            "title": "Explore Neighborhood",
            "description": "Find nearby supermarkets, restaurants, gyms, and essential services",
            "day_range": format_day_range(explore_start, plan_duration, arrival_date),
            "priority": "low",
            "location": None,
            "documents_needed": [],
            "estimated_duration": "Ongoing",
            "status": "pending",
            "dependencies": []
        })
        task_id += 1
    
    # Task: Register with Family Doctor
    if plan_duration >= 21:
        doctor_start = min(14, plan_duration - 7)
        
        tasks.append({
            "id": f"task_{task_id:03d}",
            "title": "Register with Family Doctor",
            "description": "Find and register with a general practitioner",
            "day_range": format_day_range(doctor_start, plan_duration, arrival_date),
            "priority": "medium",
            "location": None,
            "documents_needed": ["HKID", "Insurance card"],
            "estimated_duration": "1 hour",
            "status": "pending",
            "dependencies": []
        })
    
    return tasks

def generate_optional_tasks(customer_info: dict, task_id_start: int, plan_duration: int) -> list[SettlementTask]:
    """Generate optional tasks based on customer needs."""
    
    arrival_date = customer_info.get('arrival_date')
    tasks = []
    task_id = task_id_start
    
    # Add driving license if needed
    if customer_info.get("needs_car") and plan_duration >= 21:
        tasks.append({
            "id": f"task_{task_id:03d}",
            "title": "Apply for Hong Kong Driving License",
            "description": "Convert foreign driving license or apply for new license",
            "day_range": format_day_range(14, min(28, plan_duration), arrival_date),
            "priority": "medium",
            "location": None,
            "documents_needed": ["Passport", "HKID", "Foreign driving license", "Proof of address"],
            "estimated_duration": "2-3 hours",
            "status": "pending",
            "dependencies": []
        })
        task_id += 1
    
    # Add school registration if has children
    if customer_info.get("has_children") and plan_duration >= 7:
        school_start = min(5, plan_duration - 5)
        school_end = min(14, plan_duration)
        
        tasks.append({
            "id": f"task_{task_id:03d}",
            "title": "Register Children for School",
            "description": "Enroll children in international or local school",
            "day_range": format_day_range(school_start, school_end, arrival_date),
            "priority": "high",
            "location": None,
            "documents_needed": ["Passport", "Birth certificate", "Previous school records", "Proof of address"],
            "estimated_duration": "2-3 hours",
            "status": "pending",
            "dependencies": []
        })
    
    return tasks

def generate_default_tasks(customer_info: dict, office_coords: tuple = None) -> list[SettlementTask]:
    """
    Generate settlement tasks dynamically based on customer information.
    
    Args:
        customer_info: Customer information dictionary
        office_coords: Optional office coordinates tuple (lat, lng)
        
    Returns:
        List of settlement tasks tailored to customer needs
    """
    
    # Calculate plan duration based on customer info
    plan_duration = calculate_plan_duration(customer_info)
    
    tasks = []
    task_id = 1
    
    # Phase 1: Arrival & Immediate Settlement (always included)
    arrival_tasks = generate_arrival_tasks(customer_info, task_id)
    tasks.extend(arrival_tasks)
    task_id += len(arrival_tasks)
    
    # Phase 2: Housing (if plan is long enough)
    if plan_duration >= 5:
        housing_tasks = generate_housing_tasks(customer_info, task_id, plan_duration)
        tasks.extend(housing_tasks)
        task_id += len(housing_tasks)
    
    # Phase 3: Banking & Identity (if plan is long enough)
    if plan_duration >= 7:
        identity_tasks = generate_identity_tasks(customer_info, task_id, plan_duration)
        tasks.extend(identity_tasks)
        task_id += len(identity_tasks)
    
    # Phase 4: Daily Life (if plan is long enough)
    if plan_duration >= 10:
        daily_tasks = generate_daily_life_tasks(customer_info, task_id, plan_duration)
        tasks.extend(daily_tasks)
        task_id += len(daily_tasks)
    
    # Optional tasks based on customer needs
    optional_tasks = generate_optional_tasks(customer_info, task_id, plan_duration)
    tasks.extend(optional_tasks)
    
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
        
        # Calculate plan duration
        plan_duration = calculate_plan_duration(customer_info)
        
        # Phase 1: Generate core tasks with geocoding
        core_tasks = await generate_all_tasks_async(customer_info)
        
        # Phase 2: Generate extended (AI-suggested) tasks around core tasks
        extended_tasks = await generate_extended_tasks(core_tasks, customer_info, max_per_task=2)
        
        # Phase 3: Merge core and extended tasks
        all_tasks = await merge_and_optimize_tasks(core_tasks, extended_tasks)
        
        # Phase 4: Optimize task order using real routing API
        office_coords = customer_info.get("office_coordinates", (22.2770, 114.1720))
        optimized_tasks = await optimize_tasks_with_routing(all_tasks, office_coords)
        
        # Extract service locations from tasks
        service_locations = extract_service_locations(optimized_tasks)
        
        plan: SettlementPlan = {
            "id": "plan_001",
            "customer_name": customer_name,
            "center_latitude": office_coords[0],
            "center_longitude": office_coords[1],
            "zoom": 14,
            "tasks": optimized_tasks,
            "properties": [],
            "service_locations": service_locations
        }
        
        # Phase 5: Generate summary from FINALIZED plan (ensures consistency)
        # This MUST happen after all optimizations are complete
        plan_summary = await generate_plan_summary(plan, customer_info)
        plan["summary"] = plan_summary  # Store summary in plan
        
        state["settlement_plan"] = plan
        state["planning_progress"].append({
            "plan": plan,
            "done": True
        })
        
        await copilotkit_emit_state(config, state)
        
        # Add ToolMessage for the tool call
        state["messages"].append(ToolMessage(
            tool_call_id=tool_call["id"],
            content=f"Created {plan_duration}-day settlement plan with {len(optimized_tasks)} tasks for {customer_name}"
        ))
        
        # Add AIMessage with the plan summary for user visibility
        state["messages"].append(AIMessage(
            content=plan_summary
        ))
    
    state["planning_progress"] = []
    await copilotkit_emit_state(config, state)
    
    return state

async def perform_settlement_node(state: AgentState, config: RunnableConfig):
    """
    Perform the settlement plan operations (add/update/complete tasks).
    """
    return state
