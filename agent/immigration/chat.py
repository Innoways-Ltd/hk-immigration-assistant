"""Chat node for the immigration settlement assistant"""
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

llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    temperature=0.7,
    max_tokens=1600,
)

tools = [
    save_customer_info,
    search_service_locations,
    search_properties,
    create_settlement_plan,
    add_settlement_task,
    update_settlement_task,
    complete_settlement_task,
]

async def chat_node(state: AgentState, config: RunnableConfig):
    """Handle chat operations for immigration settlement"""
    
    llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
    
    customer_info = state.get("customer_info", {})
    settlement_plan = state.get("settlement_plan")
    
    system_message = f"""
    You are a helpful Hong Kong immigration settlement assistant. Your role is to help new immigrants 
    settle into Hong Kong by creating a personalized settlement plan.

    **Your Process:**
    
    1. **Collect Information**:
       - IMPORTANT: Allow customers to provide ALL information in one message
       - Extract information from their summary/description automatically
       - Information needed:
         * Customer's name
         * Arrival date in Hong Kong
         * Office address (where they will work)
         * Housing: budget (HKD), preferred areas, number of bedrooms
         * Family size and whether they have children
         * Whether they need a car
         * Temporary accommodation days
       
       - Use save_customer_info tool to save ALL extracted information at once
       - Only ask follow-up questions if critical information is missing
    
    2. **Create Settlement Plan** (once you have basic info):
       - Call create_settlement_plan immediately after collecting information
       - Generate a comprehensive 30-day settlement plan
       - Plan includes: airport pickup, temporary accommodation, SIM card, property viewing,
         bank account, HKID application, tax registration, etc.
    
    3. **Search for Services** (as needed):
       - Use search_service_locations to find banks, mobile shops, government offices
       - Use search_properties to find rental properties matching requirements
    
    4. **Provide Guidance**:
       - Explain the settlement plan
       - Provide tips about living in Hong Kong
       - Answer questions
    
    **Current Customer Information:**
    {json.dumps(customer_info, indent=2)}
    
    **Current Settlement Plan:**
    {json.dumps(settlement_plan, indent=2) if settlement_plan else "Not created yet"}
    
    **Guidelines:**
    - Extract ALL information from customer's first message if possible
    - DO NOT ask multiple questions - let customers provide information naturally
    - Be friendly, professional, and encouraging
    - Provide specific, actionable advice
    - Consider Hong Kong context (Octopus card, HKID, tax system)
    - Create the plan as soon as you have: name, arrival date, office address, housing budget
    """

    response = await llm_with_tools.ainvoke(
        [
            SystemMessage(content=system_message),
            *state["messages"]
        ],
        config=config,
    )

    ai_message = cast(AIMessage, response)

    # Handle save_customer_info tool call
    if ai_message.tool_calls:
        tool_call = ai_message.tool_calls[0]
        if tool_call["name"] == "save_customer_info":
            # Update customer_info in state
            updates = tool_call["args"]
            for key, value in updates.items():
                if value is not None:
                    customer_info[key] = value
            
            return {
                "messages": [ai_message, ToolMessage(
                    tool_call_id=tool_call["id"],
                    content="Customer information updated successfully"
                )],
                "customer_info": customer_info
            }

    return {
        "messages": [response],
        "customer_info": customer_info,
        "settlement_plan": settlement_plan
    }
