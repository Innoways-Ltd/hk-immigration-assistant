"""
AI-powered extraction of housing details from free-form conversation text.
"""
import os
import logging
from typing import Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# Initialize LLM with deterministic settings for extraction
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    temperature=0,  # Deterministic extraction
    max_tokens=500,
)

async def extract_housing_details_from_text(
    conversation_text: str,
    office_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract housing requirements from free-form conversation text using AI.
    
    This function is called when user mentions housing needs without explicit budget/bedrooms.
    It uses AI to infer reasonable defaults based on context.
    
    Args:
        conversation_text: Raw text from user conversation
            Example: "我12月15日去找房子希望离办公室近一点"
        office_address: Office address for context (if available)
    
    Returns:
        Dictionary with extracted housing details:
        {
            "housing_budget": int (monthly budget) or None,
            "bedrooms": int or None,
            "preferred_areas": list of area names or None
        }
    """
    
    system_prompt = """You are a housing requirements extraction specialist.

Your task is to analyze user conversation text and extract housing requirements.
If explicit details are not mentioned, infer REASONABLE DEFAULTS based on context.

EXTRACTION RULES:
1. **housing_budget**: Monthly housing budget in local currency
   - If not mentioned, return null (we'll use system defaults later)
   - Common indicators: "预算", "budget", "租金", "rent", price mentions
   
2. **bedrooms**: Number of bedrooms needed
   - If not mentioned but user mentions "找房子" or "home_viewing", assume 2 bedrooms as reasonable default
   - Single person: 1 bedroom
   - Family/couple: 2-3 bedrooms
   
3. **preferred_areas**: List of preferred areas/districts
   - If user mentions "离办公室近" (close to office), extract this as preference
   - Include any specific area names mentioned
   - If office address is provided, include "near_office" as a preference

OUTPUT FORMAT (JSON):
{
  "housing_budget": <number or null>,
  "bedrooms": <number or null>,
  "preferred_areas": [<list of strings or null>]
}

IMPORTANT:
- Output ONLY valid JSON, no additional text
- Use null for missing values
- Be conservative with assumptions
- When user says "找房子" without details, assume they need at least 1-2 bedrooms

EXAMPLES:

Input: "我12月15日去找房子希望离办公室近一点"
Context: office_address = "鸿隆世纪广场"
Output: {"housing_budget": null, "bedrooms": 2, "preferred_areas": ["near_office"]}

Input: "需要租一个两室的房子，预算15000"
Context: office_address = null
Output: {"housing_budget": 15000, "bedrooms": 2, "preferred_areas": null}

Input: "找个一居室，最好在市中心"
Context: office_address = null
Output: {"housing_budget": null, "bedrooms": 1, "preferred_areas": ["市中心"]}

Input: "I need a place to live close to my office"
Context: office_address = "Central Plaza"
Output: {"housing_budget": null, "bedrooms": 1, "preferred_areas": ["near_office"]}
"""

    user_message = f"""Conversation text: "{conversation_text}"
Office address: {office_address if office_address else "Not provided"}

Extract housing requirements from the conversation text."""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        logger.info(f"Extracting housing details from text: {conversation_text}")
        response = await llm.ainvoke(messages)
        result_text = response.content.strip()
        
        # Parse JSON response
        import json
        housing_details = json.loads(result_text)
        
        # Validate and clean the response
        cleaned_details = {}
        
        if housing_details.get("housing_budget") and isinstance(housing_details["housing_budget"], (int, float)):
            cleaned_details["housing_budget"] = int(housing_details["housing_budget"])
        
        if housing_details.get("bedrooms") and isinstance(housing_details["bedrooms"], (int, float)):
            cleaned_details["bedrooms"] = int(housing_details["bedrooms"])
        
        if housing_details.get("preferred_areas") and isinstance(housing_details["preferred_areas"], list):
            cleaned_details["preferred_areas"] = [str(area) for area in housing_details["preferred_areas"]]
        
        logger.info(f"Successfully extracted housing details: {cleaned_details}")
        return cleaned_details
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {result_text}. Error: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error extracting housing details with AI: {e}")
        return {}
