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
    extract_service_locations
)
from immigration.core_tasks_generator import generate_core_tasks
from immigration.smart_core_task_generator import generate_smart_extended_tasks
from immigration.plan_summarizer import generate_plan_summary

@tool
def create_settlement_plan(customer_name: str) -> dict:
    """
    Create a settlement plan for a new immigrant to Hong Kong.
    This will generate tasks based on customer-specified dates only.
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

# All task generation functions removed - we now use generate_core_tasks from core_tasks_generator.py
# which only generates tasks for user-specified dates in preferred_dates

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
        
        # Generate core tasks ONLY for user-specified dates in preferred_dates
        # No default timeline, no 30-day plan, only what user explicitly requested
        core_tasks = generate_core_tasks(customer_info)
        
        # Generate smart extended activities around core tasks
        # This provides better immigration experience by suggesting convenient services
        # on the same day as main activities (e.g., find supermarket after home viewing)
        extended_tasks = await generate_smart_extended_tasks(
            core_tasks,
            customer_info,
            max_per_task=3  # Maximum 3 extended activities per core task
        )
        
        # Combine core tasks with extended activities
        optimized_tasks = core_tasks + extended_tasks
        
        # Get office coordinates for map centering
        office_coords = customer_info.get("office_coordinates", (22.2770, 114.1720))
        
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
        
        # Generate summary from FINALIZED plan
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
            content=f"Created settlement plan with {len(optimized_tasks)} tasks for {customer_name} based on your specified dates"
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
