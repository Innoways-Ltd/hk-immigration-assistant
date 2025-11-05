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
def save_customer_info(
    name: str = None,
    arrival_date: str = None,
    office_address: str = None,
    housing_budget: int = None,
    preferred_areas: list = None,
    bedrooms: int = None,
    family_size: int = None,
    has_children: bool = False,
    needs_car: bool = False,
    temporary_accommodation_days: int = None
):
    """
    Save customer information collected from the conversation.
    Call this tool whenever you learn new information about the customer.
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
)

tools = [
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
    return all(customer_info.get(field) for field in required_fields)

async def chat_node(state: AgentState, config: RunnableConfig):
    """Handle chat operations for immigration settlement"""
    
    llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    
    customer_info = state.get("customer_info", {})
    settlement_plan = state.get("settlement_plan")
    info_confirmed = state.get("info_confirmed", False)
    
    # Determine conversation stage
    has_min_info = has_minimum_info(customer_info)
    
    if not has_min_info:
        # Stage 1: Collecting information - BE PROACTIVE AND HELPFUL
        system_message = f"""
You are an experienced Hong Kong immigration settlement assistant with deep knowledge of the city.
Your role is to help new immigrants settle smoothly by understanding their needs and creating a personalized plan.

**Current Stage: Information Collection & Guidance**

**Your Personality:**
- Warm, friendly, and conversational (not robotic)
- Proactive in offering suggestions and insights
- Knowledgeable about Hong Kong districts, transportation, and lifestyle
- Ask thoughtful follow-up questions to better understand their needs

**Information needed:**
- Customer's name
- Arrival date in Hong Kong
- Office address (where they will work)
- Housing needs (budget, bedrooms, preferred areas)
- Family situation (size, children, pets)
- Transportation needs (car or public transport)
- **Temporary accommodation days** (CRITICAL: how many days they need temporary housing)

**Current Customer Information:**
{json.dumps(customer_info, indent=2) if customer_info else "No information collected yet"}

**Instructions:**
1. **Extract information** from the customer's message and use save_customer_info tool
2. **Be proactive and helpful:**
   - If they mention their office location, suggest nearby residential areas with good commute
   - If they mention budget, give context (e.g., "HKD 30,000 can get you a nice 1-bedroom in Causeway Bay")
   - If they're unsure about areas, ask about their priorities (quiet vs vibrant, proximity to MTR, etc.)
   - If they don't mention temporary accommodation, explain why it's important and suggest typical durations
3. **Ask intelligent follow-up questions:**
   - "Your office is in Central - would you prefer living nearby for a short commute, or in a quieter area like Mid-Levels?"
   - "Since you're arriving with family, have you considered proximity to international schools?"
   - "Will you be using public transportation or do you need parking space?"
4. **Guide them naturally** - don't just collect data, help them think through their needs
5. **Use conversational language** - avoid robotic phrases like "I have collected the following information"

**Example of good interaction:**
User: "I'm moving to Hong Kong next month, office is in Admiralty."
You: "Welcome! Admiralty is a great central location. For housing, you have several excellent options nearby:
- **Wan Chai/Causeway Bay**: Vibrant area, 5-10 min commute, lots of dining and shopping
- **Mid-Levels**: Quieter, more expat-friendly, 15 min commute
- **Quarry Bay/Tai Koo**: More affordable, 15-20 min via MTR

What's your budget range and how many bedrooms do you need? Also, will you be moving alone or with family?"

DO NOT create the settlement plan yet - focus on understanding their needs deeply.
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
You are a helpful Hong Kong immigration settlement assistant.

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

Based on your office in Central and preference for Sheung Wan, you'll have an excellent 10-minute commute via MTR. The area is also great for dining and has a nice mix of local and expat-friendly spots.

Is there anything else you'd like me to know before we create your personalized settlement plan? For example, any specific apartment features you need, or particular services you want nearby?"
"""
    else:
        # Stage 3: Plan creation and assistance
        system_message = f"""
You are a helpful Hong Kong immigration settlement assistant.

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
4. **After creating the plan**:
   - Explain the key highlights (duration, number of tasks, priorities)
   - Point out any important deadlines or time-sensitive tasks
   - Offer to answer questions or make adjustments
5. **Be helpful with the plan**:
   - If they ask about specific tasks, provide detailed information
   - If they want to modify the plan, use update_settlement_task or add_settlement_task
   - If they need location recommendations, use search_service_locations or search_properties
6. **Maintain conversational tone** - you're their helpful guide, not a robot

**Example after plan creation:**
"I've created your 14-day settlement plan with 11 essential tasks! Here are the highlights:

📍 **Day 1**: Airport pickup, check-in, and getting your Octopus card and SIM card
🏠 **Days 3-5**: Property viewings in Causeway Bay
🏦 **Day 7**: Opening your bank account
📋 **Day 10**: Applying for your HKID card

The plan is optimized based on your 5-day temporary accommodation, so we've front-loaded the housing search. You can see all tasks on the left, and click on any task to see it highlighted on the map.

Would you like me to explain any specific task in detail, or would you like to make any adjustments?"
"""
    
    messages = [SystemMessage(content=system_message)] + state["messages"]
    
    response = await llm_with_tools.ainvoke(messages, config)
    
    # Handle tool calls
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        
        # Handle save_customer_info
        if tool_name == "save_customer_info":
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
