"""
AI-powered extraction of housing details from free-form conversation text.
This module uses Azure OpenAI to intelligently extract housing requirements
from user messages when explicit parameters are not provided.
"""
import os
import logging
from typing import Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# Initialize LLM for extraction (low temperature for deterministic results)
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
    Use AI to extract housing details from free-form conversation text.
    
    Args:
        conversation_text: Raw text from user (e.g., "我12月15日去找房子希望离办公室近一点")
        office_address: Office address if available (helps with area suggestions)
    
    Returns:
        Dictionary with extracted housing details:
        {
            "housing_budget": int or None,
            "bedrooms": int or None,
            "preferred_areas": list or None,
            "notes": str  # Any additional context extracted
        }
    
    Examples:
        Input: "我12月15日去找房子希望离办公室近一点"
        Output: {"housing_budget": None, "bedrooms": 1, "preferred_areas": ["Near office"], "notes": "User wants proximity to office"}
        
        Input: "找一个两室一厅，预算3万左右，最好在市中心"
        Output: {"housing_budget": 30000, "bedrooms": 2, "preferred_areas": ["City Center"], "notes": "User wants 2-bedroom apartment"}
    """
    logger.info(f"Extracting housing details from text: {conversation_text}")
    
    system_prompt = """You are a housing requirements extraction assistant. Extract housing details from user messages.

**CRITICAL RULES:**
1. Output ONLY valid JSON with these fields: housing_budget (int or null), bedrooms (int or null), preferred_areas (list or null), notes (string)
2. If a field cannot be determined from the text, set it to null
3. Use reasonable defaults when appropriate:
   - If user mentions "找房子" (find house) without details, default to 1 bedroom
   - If user mentions "近办公室" (near office) without specific areas, use ["Near office"]
   - Budget should only be set if explicitly mentioned (numbers like "3万", "30000", "HKD 30000")
4. Be intelligent about Chinese text:
   - "两室" = 2 bedrooms, "一室" = 1 bedroom, "三室" = 3 bedrooms
   - "市中心" = City Center, "郊区" = Suburbs, "海边" = Waterfront
   - Budget amounts: "3万" = 30000, "五万" = 50000
5. Notes field should capture user's intent and preferences in English

**Examples:**

Input: "我12月15日去找房子希望离办公室近一点"
Output: {"housing_budget": null, "bedrooms": 1, "preferred_areas": ["Near office"], "notes": "User wants to find housing close to office"}

Input: "找一个两室一厅，预算3万左右，最好在市中心"
Output: {"housing_budget": 30000, "bedrooms": 2, "preferred_areas": ["City Center"], "notes": "User wants 2-bedroom apartment in city center with budget around HKD 30000"}

Input: "我想租房子"
Output: {"housing_budget": null, "bedrooms": 1, "preferred_areas": null, "notes": "User wants to rent housing, no specific requirements mentioned"}

Input: "need a place with 3 bedrooms, budget is HKD 50000 per month, prefer Wan Chai or Central"
Output: {"housing_budget": 50000, "bedrooms": 3, "preferred_areas": ["Wan Chai", "Central"], "notes": "User needs 3-bedroom apartment in Wan Chai or Central area with budget HKD 50000"}

**IMPORTANT:** Output ONLY the JSON object, no additional text or formatting."""
    
    context_info = ""
    if office_address:
        context_info = f"\n\n**Additional Context:**\nUser's office address: {office_address}\n(Use this to infer preferred areas if user mentions 'near office')"
    
    try:
        messages = [
            SystemMessage(content=system_prompt + context_info),
            HumanMessage(content=f"Extract housing details from this text:\n{conversation_text}")
        ]
        
        response = await llm.ainvoke(messages)
        result_text = response.content.strip()
        
        # Parse JSON response
        import json
        try:
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            housing_details = json.loads(result_text)
            
            # Validate structure
            required_keys = {"housing_budget", "bedrooms", "preferred_areas", "notes"}
            if not all(key in housing_details for key in required_keys):
                logger.error(f"AI returned incomplete JSON: {housing_details}")
                return _default_housing_details()
            
            logger.info(f"Successfully extracted housing details: {housing_details}")
            return housing_details
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}\nResponse: {result_text}")
            return _default_housing_details()
            
    except Exception as e:
        logger.error(f"Error extracting housing details with AI: {e}")
        return _default_housing_details()


def _default_housing_details() -> Dict[str, Any]:
    """
    Return default housing details when extraction fails.
    These defaults allow task generation to proceed.
    """
    return {
        "housing_budget": None,
        "bedrooms": 1,  # Default to 1 bedroom
        "preferred_areas": None,
        "notes": "Default values used due to extraction failure"
    }
