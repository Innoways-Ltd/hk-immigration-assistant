"""
Comprehensive Task Generator for Immigration Settlement
Generates a complete 30-day settlement plan with essential tasks across 4 phases
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from langchain_openai import AzureChatOpenAI
from immigration.state import CustomerInfo
from immigration.geocoding_service import get_geocoding_service
from immigration.activity_expander import expand_all_activities, filter_and_deduplicate
from immigration.task_optimizer import balance_task_load, validate_dependencies, calculate_plan_summary, generate_plan_explanation

logger = logging.getLogger(__name__)

# Essential tasks knowledge base organized by phases
ESSENTIAL_TASKS_TEMPLATE = {
    "phase_1_arrival": {
        "name": "Arrival & Settlement",
        "days": "1-3",
        "tasks": [
            {
                "name": "Airport Pickup / Transportation",
                "priority": "P0",
                "day_offset": 0,
                "category": "transportation",
                "dependencies": [],
                "description": "Arrange transportation from airport to temporary accommodation",
                "duration_hours": 2
            },
            {
                "name": "Get Local SIM Card",
                "priority": "P0",
                "day_offset": 0,
                "category": "communication",
                "dependencies": [],
                "description": "Purchase and activate local phone number (essential for all future activities)",
                "duration_hours": 1,
                "location_type": "mobile_phone_shop"
            },
            {
                "name": "Check-in to Temporary Accommodation",
                "priority": "P0",
                "day_offset": 0,
                "category": "accommodation",
                "dependencies": ["Airport Pickup / Transportation"],
                "description": "Settle into temporary housing",
                "duration_hours": 1
            },
            {
                "name": "Buy Essential Supplies",
                "priority": "P0",
                "day_offset": 0,
                "category": "shopping",
                "dependencies": ["Check-in to Temporary Accommodation"],
                "description": "Purchase food, toiletries, and basic necessities",
                "duration_hours": 2,
                "location_type": "supermarket"
            },
            {
                "name": "Find Nearby Convenience Store",
                "priority": "P0",
                "day_offset": 0,
                "category": "orientation",
                "dependencies": ["Check-in to Temporary Accommodation"],
                "description": "Locate 24-hour convenience store near accommodation for emergency needs",
                "duration_hours": 0.5,
                "location_type": "convenience_store"
            },
            {
                "name": "Locate Nearby Pharmacy",
                "priority": "P0",
                "day_offset": 0,
                "category": "healthcare",
                "dependencies": ["Check-in to Temporary Accommodation"],
                "description": "Find local pharmacy for medical supplies and basic medications",
                "duration_hours": 0.5,
                "location_type": "pharmacy"
            },
            {
                "name": "Find Nearby Restaurants",
                "priority": "P0",
                "day_offset": 0,
                "category": "food",
                "dependencies": ["Check-in to Temporary Accommodation"],
                "description": "Discover restaurants and food options near accommodation",
                "duration_hours": 1,
                "location_type": "restaurant"
            },
            {
                "name": "Locate ATM and Bank",
                "priority": "P0",
                "day_offset": 0,
                "category": "finance",
                "dependencies": ["Check-in to Temporary Accommodation"],
                "description": "Find nearby ATM for cash withdrawal and bank location",
                "duration_hours": 0.5,
                "location_type": "atm"
            },
            {
                "name": "Explore Neighborhood",
                "priority": "P1",
                "day_offset": 1,
                "category": "orientation",
                "dependencies": ["Check-in to Temporary Accommodation"],
                "description": "Familiarize with nearby supermarkets, convenience stores, restaurants, and pharmacies",
                "duration_hours": 3
            },
            {
                "name": "Learn Public Transportation",
                "priority": "P1",
                "day_offset": 1,
                "category": "transportation",
                "dependencies": ["Check-in to Temporary Accommodation"],
                "description": "Understand metro/bus routes and purchase transportation card",
                "duration_hours": 2,
                "location_type": "transit_station"
            },
            {
                "name": "Visit Office Location",
                "priority": "P1",
                "day_offset": 2,
                "category": "work",
                "dependencies": ["Learn Public Transportation"],
                "description": "Visit workplace and plan commute route",
                "duration_hours": 2
            },
            {
                "name": "Explore Office Area",
                "priority": "P1",
                "day_offset": 2,
                "category": "orientation",
                "dependencies": ["Visit Office Location"],
                "description": "Discover nearby restaurants, banks, and convenience stores around office",
                "duration_hours": 2
            }
        ]
    },
    "phase_2_legal": {
        "name": "Legal & Administrative",
        "days": "4-10",
        "tasks": [
            {
                "name": "Property Viewing",
                "priority": "P1",
                "day_offset": 5,
                "category": "housing",
                "dependencies": ["Learn Public Transportation"],
                "description": "View potential rental properties",
                "duration_hours": 4,
                "user_customizable": True
            },
            {
                "name": "Bank Account Opening",
                "priority": "P1",
                "day_offset": 6,
                "category": "finance",
                "dependencies": ["Get Local SIM Card"],
                "description": "Open local bank account (bring passport, visa, address proof, phone number)",
                "duration_hours": 2,
                "location_type": "bank",
                "user_customizable": True
            },
            {
                "name": "Sign Rental Contract",
                "priority": "P1",
                "day_offset": 8,
                "category": "housing",
                "dependencies": ["Property Viewing", "Bank Account Opening"],
                "description": "Sign lease agreement and pay deposit",
                "duration_hours": 2
            },
            {
                "name": "Apply for Tax ID / Social Security Number",
                "priority": "P1",
                "day_offset": 7,
                "category": "legal",
                "dependencies": ["Bank Account Opening"],
                "description": "Register for tax identification and social security",
                "duration_hours": 3,
                "location_type": "government_office"
            },
            {
                "name": "Apply for Resident ID / Visa Extension",
                "priority": "P1",
                "day_offset": 9,
                "category": "legal",
                "dependencies": ["Sign Rental Contract"],
                "description": "Apply for resident identification card or visa extension",
                "duration_hours": 3,
                "location_type": "government_office"
            }
        ]
    },
    "phase_3_lifestyle": {
        "name": "Lifestyle Setup",
        "days": "11-20",
        "tasks": [
            {
                "name": "Set Up Utilities (Water, Electricity, Gas)",
                "priority": "P2",
                "day_offset": 11,
                "category": "housing",
                "dependencies": ["Sign Rental Contract", "Bank Account Opening"],
                "description": "Activate utility services for new residence",
                "duration_hours": 2
            },
            {
                "name": "Set Up Internet & TV",
                "priority": "P2",
                "day_offset": 12,
                "category": "housing",
                "dependencies": ["Sign Rental Contract"],
                "description": "Install internet and television services",
                "duration_hours": 2,
                "location_type": "electronics_store"
            },
            {
                "name": "Purchase Furniture & Appliances",
                "priority": "P2",
                "day_offset": 13,
                "category": "shopping",
                "dependencies": ["Sign Rental Contract"],
                "description": "Buy essential furniture and household appliances",
                "duration_hours": 4,
                "location_type": "furniture_store"
            },
            {
                "name": "Register for Health Insurance",
                "priority": "P2",
                "day_offset": 14,
                "category": "healthcare",
                "dependencies": ["Apply for Resident ID / Visa Extension", "Bank Account Opening"],
                "description": "Enroll in local health insurance program",
                "duration_hours": 2,
                "location_type": "hospital"
            },
            {
                "name": "Find Family Doctor / Clinic",
                "priority": "P2",
                "day_offset": 16,
                "category": "healthcare",
                "dependencies": ["Register for Health Insurance"],
                "description": "Locate and register with a local healthcare provider",
                "duration_hours": 2,
                "location_type": "doctor"
            },
            {
                "name": "Get Long-term Transportation Card",
                "priority": "P3",
                "day_offset": 15,
                "category": "transportation",
                "dependencies": ["Apply for Resident ID / Visa Extension"],
                "description": "Apply for monthly or annual transit pass",
                "duration_hours": 1,
                "location_type": "transit_station"
            },
            {
                "name": "Get Long-term Mobile Plan",
                "priority": "P3",
                "day_offset": 16,
                "category": "communication",
                "dependencies": ["Bank Account Opening", "Sign Rental Contract"],
                "description": "Switch from temporary SIM to long-term mobile contract",
                "duration_hours": 1,
                "location_type": "mobile_phone_shop"
            },
            {
                "name": "Explore Shopping Malls",
                "priority": "P3",
                "day_offset": 18,
                "category": "shopping",
                "dependencies": ["Learn Public Transportation"],
                "description": "Visit major shopping centers and retail areas",
                "duration_hours": 3,
                "location_type": "shopping_mall"
            },
            {
                "name": "Discover Local Markets",
                "priority": "P3",
                "day_offset": 19,
                "category": "shopping",
                "dependencies": ["Learn Public Transportation"],
                "description": "Explore local markets and grocery stores",
                "duration_hours": 2,
                "location_type": "supermarket"
            }
        ]
    },
    "phase_4_integration": {
        "name": "Community Integration",
        "days": "21-30",
        "tasks": [
            {
                "name": "Visit Cultural Landmarks",
                "priority": "P4",
                "day_offset": 21,
                "category": "culture",
                "dependencies": ["Learn Public Transportation"],
                "description": "Explore major cultural sites and attractions",
                "duration_hours": 4,
                "location_type": "tourist_attraction"
            },
            {
                "name": "Explore Local Cuisine",
                "priority": "P4",
                "day_offset": 24,
                "category": "culture",
                "dependencies": ["Explore Neighborhood"],
                "description": "Try local restaurants and traditional dishes",
                "duration_hours": 3,
                "location_type": "restaurant"
            },
            {
                "name": "Attend Community Events",
                "priority": "P4",
                "day_offset": 26,
                "category": "social",
                "dependencies": ["Explore Neighborhood"],
                "description": "Participate in local community activities or meetups",
                "duration_hours": 3
            },
            {
                "name": "Join Interest Groups / Clubs",
                "priority": "P4",
                "day_offset": 28,
                "category": "social",
                "dependencies": ["Explore Neighborhood"],
                "description": "Connect with hobby groups or social clubs",
                "duration_hours": 2
            },
            {
                "name": "Apply for Driver's License (if needed)",
                "priority": "P3",
                "day_offset": 25,
                "category": "legal",
                "dependencies": ["Apply for Resident ID / Visa Extension"],
                "description": "Convert or apply for local driving license",
                "duration_hours": 3,
                "location_type": "government_office",
                "conditional": "needs_car"
            },
            {
                "name": "Learn Local Laws & Customs",
                "priority": "P4",
                "day_offset": 29,
                "category": "culture",
                "dependencies": [],
                "description": "Understand local regulations and cultural norms",
                "duration_hours": 2,
                "location_type": "library"
            }
        ]
    }
}


async def generate_comprehensive_tasks(
    messages: List[Dict[str, Any]],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate comprehensive 30-day settlement plan.
    
    Strategy:
    1. Extract user-mentioned activities and preferred dates
    2. Generate essential tasks based on knowledge base
    3. Merge and deduplicate (user preferences take priority)
    4. Apply smart scheduling with dependency resolution
    5. Generate detailed descriptions for each task
    6. Geocode task locations
    
    Args:
        messages: Conversation history
        customer_info: Customer information
        
    Returns:
        List of comprehensive tasks with dates and locations
    """
    try:
        logger.info("Starting comprehensive task generation")
        
        # Step 1: Extract user activities
        user_activities = await extract_user_activities(messages, customer_info)
        logger.info(f"Extracted {len(user_activities)} user activities")
        
        # Step 2: Geocode user activities FIRST (needed for expansion)
        geocoded_user_activities = await geocode_user_activities(user_activities, customer_info)
        logger.info(f"Geocoded {len(geocoded_user_activities)} user activities")
        for activity in geocoded_user_activities:
            logger.info(f"User activity: {activity.get('name')} - day_offset={activity.get('day_offset')}, date={activity.get('date')}")
        
        # Step 3: Expand user activities with nearby services (now they have locations!)
        expansion_candidates = expand_all_activities(geocoded_user_activities, customer_info)
        filtered_expansions = filter_and_deduplicate(expansion_candidates, max_per_day=3)
        logger.info(f"Generated {len(filtered_expansions)} expansion activities")
        for expansion in filtered_expansions[:5]:  # Log first 5
            logger.info(f"Expansion: {expansion.get('name')} - day_offset={expansion.get('day_offset')}, parent={expansion.get('parent_activity')}")
        
        # Step 4: Generate essential tasks
        essential_tasks = generate_essential_tasks(customer_info)
        logger.info(f"Generated {len(essential_tasks)} essential tasks")
        
        # Step 5: Merge tasks (geocoded user activities + expansions + essential tasks)
        # Mark activity types
        for task in geocoded_user_activities:
            task["activity_type"] = "core"
        for task in filtered_expansions:
            task["activity_type"] = "extended"
        for task in essential_tasks:
            task["activity_type"] = "essential"
        
        merged_tasks = merge_tasks(geocoded_user_activities + filtered_expansions, essential_tasks)
        logger.info(f"Merged into {len(merged_tasks)} total tasks")
        
        # Step 6: Smart scheduling with dependencies
        scheduled_tasks = schedule_tasks_with_dependencies(
            merged_tasks,
            customer_info.get("arrival_date", datetime.now().strftime("%Y-%m-%d"))
        )
        logger.info(f"Scheduled {len(scheduled_tasks)} tasks")
        
        # Step 6.5: Load balancing (max 5 tasks per day)
        balanced_tasks = balance_task_load(
            scheduled_tasks,
            max_tasks_per_day=5,
            arrival_date=customer_info.get("arrival_date")
        )
        logger.info(f"Balanced to {len(balanced_tasks)} tasks")
        
        # Validate dependencies
        if not validate_dependencies(balanced_tasks):
            logger.error("Dependency validation failed, using unbalanced tasks")
            balanced_tasks = scheduled_tasks
        
        # Step 7: Generate detailed descriptions
        detailed_tasks = await generate_task_details_batch(balanced_tasks, customer_info)
        logger.info(f"Generated details for {len(detailed_tasks)} tasks")
        
        # Step 8: Geocode expansion and essential tasks (user activities already geocoded)
        geocoded_tasks = await geocode_remaining_tasks(detailed_tasks, customer_info)
        logger.info(f"Geocoded all tasks")
        
        # Step 9: Convert to SettlementTask format
        formatted_tasks = convert_to_settlement_task_format(geocoded_tasks, customer_info.get("arrival_date", datetime.now().strftime("%Y-%m-%d")))
        logger.info(f"Formatted {len(formatted_tasks)} tasks")
        
        # Step 10: Calculate plan summary
        summary = calculate_plan_summary(geocoded_tasks)
        logger.info(f"Plan summary: {summary}")
        
        # Log explanation for user
        explanation = generate_plan_explanation(summary)
        logger.info(f"Plan explanation: {explanation}")
        
        return formatted_tasks
        
    except Exception as e:
        logger.error(f"Error generating comprehensive tasks: {e}")
        # Fallback to basic essential tasks
        essential = generate_essential_tasks(customer_info)
        scheduled = schedule_tasks_with_dependencies(essential, customer_info.get("arrival_date", datetime.now().strftime("%Y-%m-%d")))
        return convert_to_settlement_task_format(scheduled, customer_info.get("arrival_date", datetime.now().strftime("%Y-%m-%d")))


async def extract_user_activities(
    messages: List[Dict[str, Any]],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Extract activities mentioned by user in conversation."""
    try:
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            temperature=0,
            streaming=False
        )
        
        conversation_text = "\n".join([
            f"{getattr(msg, 'type', 'user')}: {getattr(msg, 'content', '')}"
            for msg in messages[-10:]  # Last 10 messages
        ])
        
        prompt = f"""Analyze this conversation and extract any activities or tasks the user explicitly mentioned.

Conversation:
{conversation_text}

Customer Info:
- Arrival Date: {customer_info.get('arrival_date', 'Not specified')}
- Preferred Dates: {json.dumps(customer_info.get('preferred_dates') or {})}

Extract ONLY activities that the user explicitly mentioned. Return as JSON array:
[
  {{
    "name": "Activity name",
    "preferred_date": "YYYY-MM-DD" or null,
    "category": "housing/finance/legal/shopping/culture/social/healthcare/transportation",
    "user_mentioned": true
  }}
]

If no specific activities mentioned, return empty array: []
"""
        
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        activities = json.loads(content)
        
        # Add type, date, and day_offset fields for expansion logic
        arrival_date = datetime.strptime(customer_info.get("arrival_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
        
        for activity in activities:
            activity["type"] = "core"  # User activities are core activities
            
            if activity.get("preferred_date"):
                activity["date"] = activity["preferred_date"]
            else:
                # Default to arrival date + 5 days if no date specified
                activity["date"] = (arrival_date + timedelta(days=5)).strftime("%Y-%m-%d")
            
            # Calculate day_offset from arrival_date
            activity_date = datetime.strptime(activity["date"], "%Y-%m-%d")
            activity["day_offset"] = (activity_date - arrival_date).days
            
            logger.info(f"User activity '{activity['name']}': date={activity['date']}, day_offset={activity['day_offset']}")
        
        return activities if isinstance(activities, list) else []
        
    except Exception as e:
        logger.error(f"Error extracting user activities: {e}")
        return []


def generate_essential_tasks(customer_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate essential tasks from knowledge base."""
    tasks = []
    
    for phase_key, phase_data in ESSENTIAL_TASKS_TEMPLATE.items():
        for task_template in phase_data["tasks"]:
            # Skip conditional tasks if condition not met
            if task_template.get("conditional") == "needs_car" and customer_info.get("transportation_preference") != "car":
                continue
            
            task = {
                "name": task_template["name"],
                "priority": task_template["priority"],
                "day_offset": task_template["day_offset"],
                "category": task_template["category"],
                "dependencies": task_template["dependencies"],
                "description": task_template["description"],
                "duration_hours": task_template.get("duration_hours", 2),
                "location_type": task_template.get("location_type"),
                "user_customizable": task_template.get("user_customizable", False),
                "user_mentioned": False,
                "phase": phase_data["name"]
            }
            tasks.append(task)
    
    return tasks


def merge_tasks(
    user_activities: List[Dict[str, Any]],
    essential_tasks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge user activities with essential tasks.
    User activities take priority and override matching essential tasks.
    """
    # Create a map of essential tasks by normalized name
    essential_map = {}
    for task in essential_tasks:
        normalized_name = normalize_task_name(task["name"])
        essential_map[normalized_name] = task
    
    # Process user activities
    merged = []
    for user_task in user_activities:
        normalized_name = normalize_task_name(user_task["name"])
        
        # If matches an essential task, merge them
        if normalized_name in essential_map:
            essential_task = essential_map[normalized_name]
            merged_task = {**essential_task, **user_task}
            merged_task["user_mentioned"] = True
            merged.append(merged_task)
            # Remove from essential map to avoid duplication
            del essential_map[normalized_name]
        else:
            # New user activity not in essential list
            merged.append({
                **user_task,
                "priority": "P1",  # User-mentioned tasks are high priority
                "user_mentioned": True,
                "dependencies": []
            })
    
    # Add remaining essential tasks
    for task in essential_map.values():
        merged.append(task)
    
    return merged


def normalize_task_name(name: str) -> str:
    """Normalize task name for comparison."""
    # Remove common variations
    normalized = name.lower()
    normalized = normalized.replace("property viewing", "home viewing")
    normalized = normalized.replace("house viewing", "home viewing")
    normalized = normalized.replace("open bank account", "bank account opening")
    normalized = normalized.replace("opening bank account", "bank account opening")
    return normalized.strip()


def schedule_tasks_with_dependencies(
    tasks: List[Dict[str, Any]],
    arrival_date: str
) -> List[Dict[str, Any]]:
    """
    Schedule tasks based on dependencies and priorities.
    Respects user-specified dates as highest priority.
    """
    try:
        arrival_dt = datetime.fromisoformat(arrival_date)
    except:
        arrival_dt = datetime.now()
    
    # Separate user-specified and flexible tasks
    user_specified = [t for t in tasks if t.get("preferred_date")]
    flexible = [t for t in tasks if not t.get("preferred_date")]
    
    # Schedule user-specified tasks first
    scheduled = []
    task_completion_dates = {}
    
    for task in user_specified:
        try:
            task_date = datetime.fromisoformat(task["preferred_date"])
            day_number = (task_date - arrival_dt).days + 1
            task["day"] = max(1, min(30, day_number))
            task["date"] = task_date.strftime("%Y-%m-%d")
            scheduled.append(task)
            task_completion_dates[task["name"]] = task["day"]
        except:
            flexible.append(task)  # If date parsing fails, treat as flexible
    
    # Schedule flexible tasks based on dependencies and day_offset
    for task in sorted(flexible, key=lambda t: (t.get("day_offset", 999), t.get("priority", "P9"))):
        # Calculate earliest possible day based on dependencies
        earliest_day = task.get("day_offset", 1)
        
        for dep_name in task.get("dependencies", []):
            if dep_name in task_completion_dates:
                # Must be after dependency completion
                earliest_day = max(earliest_day, task_completion_dates[dep_name] + 1)
        
        # Ensure within 30-day range
        task_day = max(1, min(30, earliest_day))
        task_date = arrival_dt + timedelta(days=task_day - 1)
        
        task["day"] = task_day
        task["date"] = task_date.strftime("%Y-%m-%d")
        scheduled.append(task)
        task_completion_dates[task["name"]] = task_day
    
    return sorted(scheduled, key=lambda t: t["day"])


async def generate_task_details_batch(
    tasks: List[Dict[str, Any]],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate detailed descriptions for all tasks."""
    # For now, use existing descriptions
    # Can be enhanced with LLM for personalization
    for task in tasks:
        if not task.get("description"):
            task["description"] = f"Complete {task['name']}"
        
        # Add location search query if location_type exists
        if task.get("location_type"):
            task["location_search"] = f"{task['location_type']} near {customer_info.get('destination_city', 'Hong Kong')}"
    
    return tasks


async def geocode_user_activities(
    user_activities: List[Dict[str, Any]],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Geocode user activities before expansion."""
    geocoding_service = get_geocoding_service()
    
    for activity in user_activities:
        # Generate location search query
        if activity.get("name"):
            # Try to extract location from activity name or use destination city
            location_query = f"{activity['name']} in {customer_info.get('destination_city', 'Hong Kong')}"
            
            try:
                location = await geocoding_service.geocode_address(
                    location_query,
                    customer_info.get("destination_city", "Hong Kong")
                )
                
                if location:
                    activity["location"] = {
                        "name": location.get("display_name", location_query),
                        "latitude": location["latitude"],
                        "longitude": location["longitude"]
                    }
                    logger.info(f"Geocoded user activity '{activity['name']}': {activity['location']['name']}")
            except Exception as e:
                logger.error(f"Error geocoding user activity {activity['name']}: {e}")
    
    return user_activities


async def geocode_remaining_tasks(
    tasks: List[Dict[str, Any]],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Geocode tasks that don't have location yet (expansion and essential tasks)."""
    geocoding_service = get_geocoding_service()
    
    for task in tasks:
        # Skip if already has location
        if task.get("location"):
            continue
        
        if task.get("location_search"):
            try:
                location = await geocoding_service.geocode_address(
                    task["location_search"],
                    customer_info.get("destination_city", "Hong Kong")
                )
                
                if location:
                    task["location"] = {
                        "name": location.get("display_name", task["location_search"]),
                        "latitude": location["latitude"],
                        "longitude": location["longitude"]
                    }
                    logger.info(f"Geocoded task '{task['name']}': {task['location']['name']}")
            except Exception as e:
                logger.error(f"Error geocoding task {task['name']}: {e}")
    
    return tasks


async def geocode_tasks_batch(
    tasks: List[Dict[str, Any]],
    customer_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Geocode all tasks with location information (legacy function, kept for compatibility)."""
    geocoding_service = get_geocoding_service()
    
    for task in tasks:
        if task.get("location_search"):
            try:
                location = await geocoding_service.geocode_address(
                    task["location_search"],
                    customer_info.get("destination_city", "Hong Kong")
                )
                
                if location:
                    task["location"] = {
                        "name": location.get("display_name", task["location_search"]),
                        "latitude": location["latitude"],
                        "longitude": location["longitude"]
                    }
            except Exception as e:
                logger.error(f"Error geocoding task {task['name']}: {e}")
    
    return tasks


def convert_to_settlement_task_format(tasks: List[Dict[str, Any]], arrival_date: str) -> List[Dict[str, Any]]:
    """Convert comprehensive tasks to SettlementTask format."""
    formatted_tasks = []
    
    for idx, task in enumerate(tasks, start=1):
        # Calculate date string
        try:
            arrival_dt = datetime.fromisoformat(arrival_date)
            task_date = arrival_dt + timedelta(days=task.get("day", 1) - 1)
            date_str = task_date.strftime("%b %d")
            day_range = f"Day {task['day']} ({date_str})"
        except:
            day_range = f"Day {task.get('day', 1)}"
        
        formatted_task = {
            "id": f"task_{idx:03d}",
            "title": task.get("name", "Task"),
            "description": task.get("description", ""),
            "day_range": day_range,
            "priority": "high" if task.get("priority", "P1").startswith("P0") or task.get("priority", "P1").startswith("P1") else "medium",
            "location": task.get("location"),
            "estimated_duration": f"{task.get('duration_hours', 2)} hours",
            "status": "pending",
            "category": task.get("category", "general")
        }
        
        formatted_tasks.append(formatted_task)
    
    return formatted_tasks
