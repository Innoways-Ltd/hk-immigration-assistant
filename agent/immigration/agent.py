"""
Hong Kong Immigration Settlement Assistant Agent
This defines the workflow graph and entry point for the agent.
"""
from typing import cast
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from immigration.chat import chat_node
from immigration.search import search_node
from immigration.settlement import settlement_node, perform_settlement_node
from immigration.state import AgentState
from langgraph.checkpoint.memory import MemorySaver

def route(state: AgentState):
    """Route after the chat node based on tool calls."""
    messages = state.get("messages", [])
    if messages and isinstance(messages[-1], AIMessage):
        ai_message = cast(AIMessage, messages[-1])
        
        if ai_message.tool_calls:
            tool_name = ai_message.tool_calls[0]["name"]
            
            # Route to search node for location/property searches
            if tool_name in ["search_service_locations", "search_properties"]:
                return "search_node"
            
            # Route to settlement node for plan creation
            if tool_name in ["create_settlement_plan"]:
                return "settlement_node"
            
            # Route to perform_settlement_node for task operations
            if tool_name in ["add_settlement_task", "update_settlement_task", "complete_settlement_task"]:
                return "perform_settlement_node"
            
            # Stay in chat node for save_customer_info
            return "chat_node"
    
    if messages and isinstance(messages[-1], ToolMessage):
        return "chat_node"
    
    return END

# Build the graph
graph_builder = StateGraph(AgentState)

# Add nodes
graph_builder.add_node("chat_node", chat_node)
graph_builder.add_node("search_node", search_node)
graph_builder.add_node("settlement_node", settlement_node)
graph_builder.add_node("perform_settlement_node", perform_settlement_node)

# Add edges
graph_builder.add_conditional_edges(
    "chat_node", 
    route, 
    ["search_node", "settlement_node", "perform_settlement_node", "chat_node", END]
)

graph_builder.add_edge(START, "chat_node")
graph_builder.add_edge("search_node", "chat_node")
graph_builder.add_edge("settlement_node", "chat_node")
graph_builder.add_edge("perform_settlement_node", "chat_node")

# Compile the graph
graph = graph_builder.compile(
    interrupt_after=["settlement_node"],
    checkpointer=MemorySaver(),
)
