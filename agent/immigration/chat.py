import os
import json
from immigration.state import AgentState
from langchain_core.messages import SystemMessage
from langchain_openai import AzureChatOpenAI
from immigration.search import search_service_locations, search_properties
from immigration.settlement import create_settlement_plan, add_settlement_task, update_settlement_task, complete_settlement_task
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from typing import cast
from langchain_core.tools import tool

@tool
async def fetch_order_summary(order_number: str) -> str:
    """
    Fetch customer order summary from the order system using order number.
    Call this tool when user provides their order number to retrieve their booking information.
    
    Args:
        order_number: The customer's order number (e.g., "HK20250504001", "file1234")
    
    Returns:
        A formatted summary of the customer's order information
    """
    api_client = get_order_api_client()
    order_data = await api_client.get_order_summary(order_number)
    
    if order_data:
        return format_order_summary_for_display(order_data)
    else:
        return f"Order {order_number} not found in the system. Please check the order number and try again."

@tool
def save_customer_info(
    name: str = None,
    destination_country: str = None,
    destination_city: str = None,
    arrival_date: str = None,
    office_address: str = None,
    housing_budget: int = None,
    preferred_areas: list = None,
    bedrooms: int = None,
    family_size: int = None,
    has_children: bool = False,
    needs_car: bool = False,
    temporary_accommodation_days: int = None,
    preferred_dates: dict = None,
    order_number: str = None
):
    """
    Save customer information collected from the conversation or from order system.
    Call this tool whenever you learn new information about the customer.
    
    Args:
        order_number: Customer's order number for reference
        preferred_dates: Dictionary of task-specific preferred dates.
            Keys should be task types (e.g., "home_viewing", "bank_account", "identity_card").
            Values should be dates in YYYY-MM-DD format.
            Example: {"home_viewing": "2025-05-09", "bank_account": "2025-05-10"}
    """
    return "Customer information saved"

@tool
def confirm_customer_info():
    """
    Mark that the customer has confirmed their information.
    Call this tool after the customer explicitly confirms the information summary.
    """
    return "Customer information confirmed"

llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    temperature=0.7,
    max_tokens=1600,
    streaming=True,
)

tools = [
    fetch_order_summary,
    save_customer_info,
    confirm_customer_info,
    search_service_locations,
    search_properties,
    create_settlement_plan,
    add_settlement_task,
    update_settlement_task,
    complete_settlement_task,
]

def format_customer_info_summary(customer_info: dict) -> str:
    """Format customer information as a readable summary."""
    summary_parts = []
    
    if customer_info.get("name"):
        summary_parts.append(f"**Name:** {customer_info['name']}")
    
    if customer_info.get("destination_country") or customer_info.get("destination_city"):
        dest_parts = []
        if customer_info.get("destination_city"):
            dest_parts.append(customer_info['destination_city'])
        if customer_info.get("destination_country"):
            dest_parts.append(customer_info['destination_country'])
        summary_parts.append(f"**Destination:** {', '.join(dest_parts)}")
    
    if customer_info.get("arrival_date"):
        summary_parts.append(f"**Arrival Date:** {customer_info['arrival_date']}")
    
    if customer_info.get("office_address"):
        summary_parts.append(f"**Office Address:** {customer_info['office_address']}")
    
    if customer_info.get("housing_budget"):
        summary_parts.append(f"**Housing Budget:** HKD {customer_info['housing_budget']:,}/month")
    
    if customer_info.get("bedrooms"):
        summary_parts.append(f"**Bedrooms Required:** {customer_info['bedrooms']}")
    
    if customer_info.get("preferred_areas"):
        areas = ", ".join(customer_info['preferred_areas'])
        summary_parts.append(f"**Preferred Areas:** {areas}")
    
    if customer_info.get("family_size"):
        summary_parts.append(f"**Family Size:** {customer_info['family_size']} adult(s)")
        if customer_info.get("has_children"):
            summary_parts.append(f"**Children:** Yes")
        else:
            summary_parts.append(f"**Children:** No children or pets")
    
    if customer_info.get("needs_car"):
        summary_parts.append(f"**Transportation:** Need car")
    
    if customer_info.get("temporary_accommodation_days"):
        summary_parts.append(f"**Temporary Accommodation Duration:** {customer_info['temporary_accommodation_days']} days")
    
    return "\n".join(summary_parts)

def has_minimum_info(customer_info: dict) -> bool:
    """Check if we have minimum required information."""
    required_fields = ["name", "arrival_date", "office_address", "temporary_accommodation_days"]
    has_destination = customer_info.get("destination_country") or customer_info.get("destination_city")
    return has_destination and all(customer_info.get(field) for field in required_fields)

async def chat_node(state: AgentState, config: RunnableConfig):
    """Handle chat operations for immigration settlement"""
    
    llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    
    customer_info = state.get("customer_info", {})
    settlement_plan = state.get("settlement_plan")
    info_confirmed = state.get("info_confirmed", False)
    
    # Determine conversation stage
    has_order_number = customer_info.get("order_number") is not None
    has_min_info = has_minimum_info(customer_info)
    
    if not has_order_number:
        # Stage 0: Welcome and ask for order number
        system_message = f"""
You are a warm and professional immigration settlement assistant.

**Current Stage: Welcome & Order Number Collection**

**Your Task:**
1. **Warmly welcome the user** - introduce yourself as their immigration assistant
2. **Ask for their order number** - explain that you need it to retrieve their booking information
3. **Be friendly and reassuring** - make them feel comfortable

**Instructions:**
- Keep it simple and welcoming
- Don't ask for any other information yet
- Once they provide an order number, use the fetch_order_summary tool to retrieve their information
- Use conversational, friendly language

**Example Opening:**
"Hello! 👋 I'm your immigration settlement assistant. I'm here to help make your move smooth and stress-free.

To get started, could you please share your order number? This will allow me to pull up your booking details and create a personalized settlement plan for you."

**Current Customer Information:**
{json.dumps(customer_info, indent=2) if customer_info else "No information collected yet"}
"""
    elif not has_min_info:
        # Stage 1: Collecting information - BE PROACTIVE AND HELPFUL
        system_message = f"""
You are an experienced immigration settlement assistant with deep knowledge of various destinations.
Your role is to help new immigrants settle smoothly by understanding their needs and creating a personalized plan.

**Current Stage: Information Review & Additional Requirements**

**Your Personality:**
- Warm, friendly, and conversational (not robotic)
- Proactive in offering suggestions and insights
- Knowledgeable about local districts, transportation, and lifestyle in various destinations
- Ask thoughtful follow-up questions to better understand their needs

**Current Customer Information:**
{json.dumps(customer_info, indent=2) if customer_info else "Order information has been retrieved"}

**Your Task:**
1. **Review the information** retrieved from the order system
2. **Summarize key details** in a friendly way (arrival date, accommodation, scheduled activities)
3. **Ask if there are any additional requirements or changes** they'd like to make
4. **Be helpful with suggestions:**
   - If they mention specific needs, offer relevant advice
   - If they want to change dates, use save_customer_info to update
   - If they have special requests, make note of them

**Instructions:**
1. **Present the order summary** in a friendly, conversational way
2. **Highlight key information:**
   - Arrival date and temporary accommodation duration
   - Already scheduled activities (if any)
   - Housing preferences
3. **Ask about additional requirements:**
   - "Do you have any additional requirements or preferences I should know about?"
   - "Would you like to adjust any of the scheduled dates?"
   - "Is there anything specific you'd like me to focus on in your settlement plan?"
4. **Use save_customer_info** to update any new information
5. **Once they confirm or finish adding requirements**, ask if they're ready to create the settlement plan

**Example Interaction:**
"Great! I've retrieved your booking information. Here's what I have:

📋 You're arriving on [Date] and will stay at [Hotel] for [X] days
🏢 Your office is located in [Location]
🏠 You're looking for [bedroom] housing in [areas]
📅 You have activities scheduled: [list activities with dates]

Do you have any additional requirements, or would you like to adjust any of these details? I'm here to make sure your settlement plan perfectly matches your needs!"

DO NOT create the settlement plan yet - wait for user confirmation.
"""
    elif not info_confirmed:
        # Stage 2: Confirmation with insights
        info_summary = format_customer_info_summary(customer_info)
        
        # Generate insights based on collected info
        insights = []
        if customer_info.get("office_address") and customer_info.get("preferred_areas"):
            insights.append("✨ Based on your office location and preferred areas, I can help you find properties with optimal commute times.")
        
        if customer_info.get("temporary_accommodation_days"):
            days = customer_info["temporary_accommodation_days"]
            if days <= 7:
                insights.append(f"⚡ With only {days} days of temporary accommodation, we'll prioritize urgent tasks like housing search in your plan.")
            elif days >= 30:
                insights.append(f"📅 With {days} days of temporary stay, we can create a more relaxed timeline for your settlement.")
        
        insights_text = "\n".join(insights) if insights else ""
        
        system_message = f"""
You are a helpful immigration settlement assistant.

**Current Stage: Information Confirmation & Insights**

You have collected the following information:

{info_summary}

{insights_text}

**Your task:**
1. **Present the summary** in a friendly, conversational way
2. **Offer insights or suggestions** based on their information (show you understand their situation)
3. **Ask if they want to add anything** - be specific about what might be helpful:
   - "Would you like me to note any specific requirements for your apartment (e.g., pet-friendly, gym, parking)?"
   - "Do you have any dietary restrictions I should consider when suggesting areas with good restaurants?"
   - "Are there any specific services or amenities you'll need nearby?"
4. **Wait for confirmation** before calling confirm_customer_info tool
5. **If they confirm** (say "yes", "correct", "looks good", etc.), call confirm_customer_info
6. **If they add info or make changes**, use save_customer_info to update

**Instructions:**
- Be warm and personal, not robotic
- Show that you understand their situation
- Offer helpful suggestions or insights
- Make them feel confident about the next steps

**Example:**
"Perfect! Let me confirm what I have:
[summary]

Based on your office location and preferred areas, you'll have good commute options. The area should have nice amenities and services for your needs.

Is there anything else you'd like me to know before we create your personalized settlement plan? For example, any specific apartment features you need, or particular services you want nearby?"
"""
    else:
        # Stage 3: Plan creation and assistance
        system_message = f"""
You are a helpful immigration settlement assistant.

**Current Stage: Plan Creation & Ongoing Assistance**

The customer has confirmed their information.

**Confirmed Customer Information:**
{json.dumps(customer_info, indent=2)}

**Current Settlement Plan:**
{json.dumps(settlement_plan, indent=2) if settlement_plan else "Not created yet"}

**Instructions:**
1. **After confirmation**, acknowledge warmly and ask if they'd like to create the plan now
   - Example: "Great! I'm ready to create your personalized settlement plan. Should I go ahead and generate it for you?"
2. **Wait for explicit request** before calling create_settlement_plan
3. **Keywords indicating they want the plan**: "yes", "create", "generate", "make", "start", "go ahead", "please", "show me"
4. **IMPORTANT: When user requests plan creation**, IMMEDIATELY respond with an acknowledgment message BEFORE calling create_settlement_plan:
   - Example: "Perfect! I'm now creating your personalized settlement plan. This will take a moment as I'm gathering information about locations, optimizing routes, and organizing tasks. Please wait..."
   - Then call create_settlement_plan
5. **After creating the plan**:
   - Explain the key highlights (duration, number of tasks, priorities)
   - Point out any important deadlines or time-sensitive tasks
   - Offer to answer questions or make adjustments
5. **Be helpful with the plan**:
   - If they ask about specific tasks, provide detailed information
   - If they want to modify the plan, use update_settlement_task or add_settlement_task
   - If they need location recommendations, use search_service_locations or search_properties
6. **Maintain conversational tone** - you're their helpful guide, not a robot

"""
    
    messages = [SystemMessage(content=system_message)] + state["messages"]
    
    response = await llm_with_tools.ainvoke(messages, config)
    
    # Handle tool calls
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        
        # Handle fetch_order_summary
        if tool_name == "fetch_order_summary":
            order_number = tool_call["args"]["order_number"]
            
            # Call the actual tool
            api_client = get_order_api_client()
            order_data = await api_client.get_order_summary(order_number)
            
            if order_data:
                # Extract customer info from order (using AI)
                extracted_info = await extract_customer_info_from_order(order_data)
                extracted_info["order_number"] = order_number
                
                # Format for display (using AI)
                formatted_summary = await format_order_summary_for_display(order_data)
                
                tool_message = ToolMessage(
                    content=formatted_summary,
                    tool_call_id=tool_call["id"]
                )
                
                return {
                    "messages": [response, tool_message],
                    "customer_info": extracted_info
                }
            else:
                tool_message = ToolMessage(
                    content=f"Order {order_number} not found in the system. Please check the order number and try again.",
                    tool_call_id=tool_call["id"]
                )
                
                return {
                    "messages": [response, tool_message],
                }
        
        # Handle save_customer_info
        elif tool_name == "save_customer_info":
            args = tool_call["args"]
            # Update customer_info with new data
            updated_info = customer_info.copy()
            for key, value in args.items():
                if value is not None:
                    updated_info[key] = value
            
            tool_message = ToolMessage(
                content="Customer information saved successfully",
                tool_call_id=tool_call["id"]
            )
            
            return {
                "messages": [response, tool_message],
                "customer_info": updated_info
            }
        
        # Handle confirm_customer_info
        elif tool_name == "confirm_customer_info":
            tool_message = ToolMessage(
                content="Customer information confirmed",
                tool_call_id=tool_call["id"]
            )
            
            return {
                "messages": [response, tool_message],
                "info_confirmed": True
            }
        
        # For other tools, just return the response and let routing handle it
        else:
            return {
                "messages": [response],
            }
    
    return {"messages": [response]}
