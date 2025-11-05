"""
Smart Task Generator - LLM-driven task generation based on user conversation
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from immigration.state import TaskType
from immigration.geocoding_service import get_geocoding_service
import os

logger = logging.getLogger(__name__)

# Initialize LLM
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    temperature=0.7,
    streaming=False,
)


async def extract_activities_from_conversation(
    messages: List[Any],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Use LLM to analyze conversation and extract main activities mentioned by user.
    
    Args:
        messages: Conversation history
        customer_info: Customer information
        
    Returns:
        List of activities with their details
    """
    # Build conversation context
    conversation_text = "\n".join([
        f"{msg.type}: {msg.content}" 
        for msg in messages 
        if hasattr(msg, 'content') and msg.content
    ])
    
    # Get arrival date
    arrival_date = customer_info.get('arrival_date', 'Not specified')
    destination = f"{customer_info.get('destination_city', 'the destination city')}, {customer_info.get('destination_country', 'the country')}"
    
    # Build preferred dates info
    preferred_dates_info = ""
    if customer_info.get('preferred_dates'):
        preferred_dates_info = "\n\nUser's Preferred Dates:\n"
        for activity, date in customer_info['preferred_dates'].items():
            preferred_dates_info += f"- {activity}: {date}\n"
    
    system_prompt = f"""You are an expert immigration settlement planner. Analyze the user's conversation and extract all activities they mentioned or need for settling in {destination}.

**CRITICAL RULES:**
1. **PRESERVE USER INTENT**: Do NOT change, remove, or reinterpret activities the user explicitly mentioned
2. **RESPECT USER DATES**: If user specified a date for an activity, use that EXACT date
3. **ADD ESSENTIALS ONLY**: Only add legally required activities (e.g., resident ID, bank account) that user didn't mention
4. **BE SPECIFIC**: Extract specific details like locations, preferences, requirements

**User Information:**
- Arrival Date: {arrival_date}
- Destination: {destination}
- Office: {customer_info.get('office_address', 'Not specified')}
- Housing Budget: {customer_info.get('housing_budget', 'Not specified')}
- Bedrooms: {customer_info.get('bedrooms', 'Not specified')}
- Family: {customer_info.get('family_size', 'Not specified')} adults, {customer_info.get('has_children', False) and 'with children' or 'no children'}
- Temporary Accommodation: {customer_info.get('temporary_accommodation_days', 30)} days{preferred_dates_info}

**Output Format (JSON array):**
```json
[
  {{
    "activity_name": "Property Viewing",
    "source": "user_mentioned",  // "user_mentioned" or "essential_added"
    "priority": "high",  // "high", "medium", "low"
    "preferred_date": "2025-05-09",  // Use user's date if specified, otherwise null
    "day_number": 5,  // Calculate from arrival date if preferred_date is given
    "description": "View 2-bedroom apartments in Wan Chai and Sheung Wan areas",
    "estimated_duration": "3-4 hours",
    "documents_needed": ["Passport", "Employment letter", "Proof of income"],
    "location_hint": "Wan Chai, Hong Kong",  // For geocoding
    "dependencies": [],  // IDs of activities that must be done before this
    "notes": "User specifically requested May 9th"
  }}
]
```

**Analyze this conversation and extract activities:**
"""

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=conversation_text)
        ])
        
        # Extract JSON from response
        content = response.content
        
        # Find JSON array in the response
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            logger.error("No JSON array found in LLM response")
            return []
        
        json_str = content[start_idx:end_idx]
        activities = json.loads(json_str)
        
        logger.info(f"Extracted {len(activities)} activities from conversation")
        return activities
        
    except Exception as e:
        logger.error(f"Error extracting activities from conversation: {e}")
        return []


async def assign_smart_dates(
    activities: List[Dict[str, Any]],
    arrival_date: str
) -> List[Dict[str, Any]]:
    """
    Use LLM to intelligently assign dates to activities based on dependencies and priorities.
    
    Args:
        activities: List of activities extracted from conversation
        arrival_date: User's arrival date
        
    Returns:
        Activities with assigned dates
    """
    system_prompt = f"""You are an expert at scheduling immigration settlement activities.

**Task:** Assign specific day numbers to each activity based on:
1. **User's preferred dates** (MUST be respected - highest priority)
2. **Dependencies** (prerequisite activities must come first)
3. **Priorities** (high priority activities should be scheduled earlier)
4. **Logical flow** (related activities should be grouped)
5. **Realistic timing** (don't overload any single day)

**Arrival Date:** {arrival_date}

**Rules:**
- Day 1 is the arrival date
- If an activity has a preferred_date, calculate day_number and USE IT (don't change)
- Respect dependencies: dependent activities must come AFTER their prerequisites
- High priority activities should be in first 7 days
- Don't schedule more than 4-5 activities on the same day
- Leave buffer days between major activities

**Output Format (JSON array):**
Return the SAME activities with updated day_number and day_range fields:
```json
[
  {{
    "activity_name": "...",
    "day_number": 5,
    "day_range": "Day 5 (May 09)",
    "reason": "User specified May 9th for this activity"
    // ... keep all other fields
  }}
]
```

**Activities to schedule:**
"""

    try:
        activities_json = json.dumps(activities, indent=2)
        
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=activities_json)
        ])
        
        content = response.content
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            logger.error("No JSON array found in LLM response")
            return activities
        
        json_str = content[start_idx:end_idx]
        scheduled_activities = json.loads(json_str)
        
        logger.info(f"Assigned dates to {len(scheduled_activities)} activities")
        return scheduled_activities
        
    except Exception as e:
        logger.error(f"Error assigning dates: {e}")
        return activities


async def generate_task_details(
    activity: Dict[str, Any],
    customer_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate detailed task information for an activity.
    
    Args:
        activity: Activity extracted from conversation
        customer_info: Customer information
        
    Returns:
        Complete task dictionary
    """
    destination = f"{customer_info.get('destination_city', 'the city')}, {customer_info.get('destination_country', 'the country')}"
    
    system_prompt = f"""You are an expert at creating detailed settlement task descriptions.

**Task:** Create a comprehensive task description for this activity in {destination}.

**Customer Context:**
- Destination: {destination}
- Office: {customer_info.get('office_address', 'Not specified')}
- Housing needs: {customer_info.get('bedrooms', 'Not specified')} bedrooms, budget {customer_info.get('housing_budget', 'Not specified')}
- Family: {customer_info.get('family_size', 1)} adults

**Output Format (JSON):**
```json
{{
  "title": "Clear, concise task title",
  "description": "Detailed description with specific guidance for {destination}",
  "estimated_duration": "Realistic time estimate",
  "documents_needed": ["List", "of", "required", "documents"],
  "tips": "Helpful tips specific to {destination}",
  "location_search": "Specific location query for geocoding"
}}
```

**Activity to detail:**
"""

    try:
        activity_json = json.dumps(activity, indent=2)
        
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=activity_json)
        ])
        
        content = response.content
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            logger.error("No JSON object found in LLM response")
            return activity
        
        json_str = content[start_idx:end_idx]
        details = json.loads(json_str)
        
        # Merge with original activity
        task = {**activity, **details}
        return task
        
    except Exception as e:
        logger.error(f"Error generating task details: {e}")
        return activity


async def geocode_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Geocode a task's location.
    
    Args:
        task: Task dictionary with location_search field
        
    Returns:
        Task with geocoded location
    """
    if not task.get('location_search'):
        return task
    
    try:
        geocoding_service = get_geocoding_service()
        location = await geocoding_service.geocode_address(task['location_search'])
        
        if location:
            task['location'] = {
                'name': location.get('display_name', task['location_search']),
                'latitude': location['lat'],
                'longitude': location['lon'],
                'address': location.get('display_name', '')
            }
        else:
            task['location'] = None
            
    except Exception as e:
        logger.error(f"Error geocoding task location: {e}")
        task['location'] = None
    
    return task


async def generate_smart_tasks(
    messages: List[Any],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate settlement tasks intelligently based on user conversation.
    
    This is the main entry point for smart task generation.
    
    Args:
        messages: Conversation history
        customer_info: Customer information
        
    Returns:
        List of complete tasks with geocoded locations
    """
    logger.info("Starting smart task generation...")
    
    # Step 1: Extract activities from conversation
    activities = await extract_activities_from_conversation(messages, customer_info)
    
    if not activities:
        logger.warning("No activities extracted, falling back to default tasks")
        # TODO: Implement fallback to basic tasks
        return []
    
    # Step 2: Assign smart dates
    arrival_date = customer_info.get('arrival_date', datetime.now().strftime('%Y-%m-%d'))
    scheduled_activities = await assign_smart_dates(activities, arrival_date)
    
    # Step 3: Generate detailed task information (parallel)
    detail_tasks = [
        generate_task_details(activity, customer_info)
        for activity in scheduled_activities
    ]
    detailed_tasks = await asyncio.gather(*detail_tasks)
    
    # Step 4: Geocode all tasks (parallel)
    geocode_tasks = [geocode_task(task) for task in detailed_tasks]
    final_tasks = await asyncio.gather(*geocode_tasks)
    
    # Step 5: Add task IDs and format
    for idx, task in enumerate(final_tasks, start=1):
        task['id'] = f"task_{idx:03d}"
        task['status'] = 'pending'
        task['type'] = TaskType.CORE if task.get('source') == 'user_mentioned' else TaskType.EXTENDED
    
    logger.info(f"Generated {len(final_tasks)} smart tasks")
    return final_tasks
