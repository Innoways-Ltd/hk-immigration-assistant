"""
Order API Client
用于查询客户订单信息的API客户端
"""
import os
import json
import logging
from typing import Optional, Dict, Any
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderAPIClient:
    """订单API客户端"""
    
    def __init__(self):
        """初始化API客户端"""
        self.api_base_url = os.getenv("ORDER_API_BASE_URL", "https://n8n.a4apple.cn/webhook/customer-summary")
        self.api_key = os.getenv("ORDER_API_KEY", "")
        self.timeout = 30.0
    
    async def get_order_summary(self, order_number: str) -> Optional[Dict[str, Any]]:
        """
        根据订单号获取订单摘要信息
        
        Args:
            order_number: 订单号
            
        Returns:
            订单摘要信息，包含客户基本信息和行程安排
            如果订单不存在或查询失败，返回None
        """
        try:
            logger.info(f"Querying order summary for order: {order_number}")
            
            # 调用实际API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base_url}?id={order_number}",
                    headers={
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully retrieved order summary for: {order_number}")
                    return data
                elif response.status_code == 404:
                    logger.warning(f"Order not found: {order_number}")
                    # 如果API返回404，尝试使用模拟数据
                    return self._get_mock_order_summary(order_number)
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    # API错误时使用模拟数据
                    return self._get_mock_order_summary(order_number)
                
        except httpx.TimeoutException:
            logger.error(f"Timeout querying order: {order_number}")
            # 超时时使用模拟数据
            return self._get_mock_order_summary(order_number)
        except Exception as e:
            logger.error(f"Error querying order: {e}")
            # 其他错误时使用模拟数据
            return self._get_mock_order_summary(order_number)
    
    def _get_mock_order_summary(self, order_number: str) -> Optional[Dict[str, Any]]:
        """
        获取模拟订单数据（用于开发和演示）
        
        根据订单号返回不同的模拟数据
        """
        # 模拟不同的订单场景
        mock_orders = {
            "HK20250504001": {
                "order_number": "HK20250504001",
                "status": "confirmed",
                "customer_name": "张明",
                "destination_country": "Hong Kong",
                "destination_city": "Hong Kong",
                "arrival_date": "2025-05-04",
                "arrival_flight": "CX123",
                "office_address": "One Island East, Taikoo Place, Quarry Bay, Hong Kong",
                "housing_requirements": {
                    "budget": 35000,
                    "bedrooms": 2,
                    "preferred_areas": ["Quarry Bay", "Tai Koo", "Sai Wan Ho"]
                },
                "family_info": {
                    "family_size": 2,
                    "has_children": False,
                    "needs_car": False
                },
                "temporary_accommodation": {
                    "hotel_name": "Dorsett Wanchai",
                    "check_in_date": "2025-05-04",
                    "check_out_date": "2025-05-18",
                    "days": 14,
                    "address": "387-397 Queen's Road East, Wan Chai, Hong Kong"
                },
                "scheduled_activities": [
                    {
                        "type": "home_viewing",
                        "date": "2025-05-09",
                        "description": "Property viewing appointments"
                    },
                    {
                        "type": "bank_account",
                        "date": "2025-05-10",
                        "description": "Open bank account at HSBC"
                    },
                    {
                        "type": "identity_card",
                        "date": "2025-05-15",
                        "description": "Apply for Hong Kong ID card"
                    }
                ],
                "special_requirements": [
                    "Need help with Mandarin-Cantonese translation",
                    "Prefer vegetarian restaurants nearby"
                ],
                "notes": "Customer prefers quiet residential areas close to MTR"
            },
            "HK20250510002": {
                "order_number": "HK20250510002",
                "status": "confirmed",
                "customer_name": "李华",
                "destination_country": "Hong Kong",
                "destination_city": "Hong Kong",
                "arrival_date": "2025-05-10",
                "arrival_flight": "KA456",
                "office_address": "International Commerce Centre, West Kowloon, Hong Kong",
                "housing_requirements": {
                    "budget": 45000,
                    "bedrooms": 3,
                    "preferred_areas": ["Tsim Sha Tsui", "Jordan", "Yau Ma Tei"]
                },
                "family_info": {
                    "family_size": 4,
                    "has_children": True,
                    "children_ages": [6, 8],
                    "needs_car": True
                },
                "temporary_accommodation": {
                    "hotel_name": "Sheraton Hong Kong Hotel & Towers",
                    "check_in_date": "2025-05-10",
                    "check_out_date": "2025-06-09",
                    "days": 30,
                    "address": "20 Nathan Road, Tsim Sha Tsui, Kowloon, Hong Kong"
                },
                "scheduled_activities": [
                    {
                        "type": "home_viewing",
                        "date": "2025-05-15",
                        "description": "Property viewing - family apartments"
                    },
                    {
                        "type": "school_visit",
                        "date": "2025-05-20",
                        "description": "Visit international schools"
                    },
                    {
                        "type": "bank_account",
                        "date": "2025-05-12",
                        "description": "Open family bank account"
                    }
                ],
                "special_requirements": [
                    "Need parking space",
                    "Proximity to international schools important",
                    "Pet-friendly housing required (small dog)"
                ],
                "notes": "Family relocation, priority on children's education"
            }
        }
        
        # 返回对应的模拟数据，如果订单号不存在则返回None
        order_data = mock_orders.get(order_number)
        
        if order_data:
            logger.info(f"Found mock order data for: {order_number}")
            return order_data
        else:
            logger.warning(f"No mock data found for order: {order_number}")
            return None


def parse_summary_text(summary_text: str) -> Dict[str, Any]:
    """
    Parse the summary text from API and extract structured information
    
    Args:
        summary_text: The raw summary text from API
        
    Returns:
        Structured order data dictionary
    """
    import re
    
    order_data = {}
    
    # Extract arrival date
    arrival_match = re.search(r'Arrival Date.*?:?\s*(\d+(?:st|nd|rd|th)?\s+\w+\s+\d{4})', summary_text, re.IGNORECASE)
    if arrival_match:
        order_data["arrival_date"] = arrival_match.group(1)
    
    # Extract temporary accommodation days
    temp_accom_match = re.search(r'Temporary accommodation:\s*(\d+)\s*days?', summary_text, re.IGNORECASE)
    if temp_accom_match:
        order_data["temporary_accommodation_days"] = int(temp_accom_match.group(1))
    
    # Extract budget
    budget_match = re.search(r'Budget:\s*HKD?\s*([0-9,]+)', summary_text, re.IGNORECASE)
    if budget_match:
        order_data["housing_budget"] = int(budget_match.group(1).replace(',', ''))
    
    # Extract bedrooms
    bedroom_match = re.search(r'(\d+)\s*bedroom', summary_text, re.IGNORECASE)
    if bedroom_match:
        order_data["bedrooms"] = int(bedroom_match.group(1))
    
    # Extract preferred areas
    areas_match = re.search(r'Property areas?:\s*([^\n]+)', summary_text, re.IGNORECASE)
    if areas_match:
        areas_text = areas_match.group(1)
        order_data["preferred_areas"] = [area.strip() for area in re.split(r',|;', areas_text) if area.strip()]
    
    # Extract office location
    office_match = re.search(r'Office Location:\s*([^\n]+)', summary_text, re.IGNORECASE)
    if office_match:
        order_data["office_address"] = office_match.group(1).strip()
    
    # Extract family size
    family_match = re.search(r'Family Size:\s*(\d+)\s*adult', summary_text, re.IGNORECASE)
    if family_match:
        order_data["family_size"] = int(family_match.group(1))
    
    # Extract scheduled dates for activities
    home_viewing_match = re.search(r'Home viewing.*?(\d+(?:st|nd|rd|th)?\s+\w+\s+\d{4})', summary_text, re.IGNORECASE)
    if home_viewing_match:
        if "scheduled_activities" not in order_data:
            order_data["scheduled_activities"] = []
        order_data["scheduled_activities"].append({
            "type": "home_viewing",
            "date": home_viewing_match.group(1)
        })
    
    bank_match = re.search(r'Bank account.*?(\d+(?:st|nd|rd|th)?\s+\w+\s+\d{4})', summary_text, re.IGNORECASE)
    if bank_match:
        if "scheduled_activities" not in order_data:
            order_data["scheduled_activities"] = []
        order_data["scheduled_activities"].append({
            "type": "bank_account",
            "date": bank_match.group(1)
        })
    
    return order_data


def extract_customer_info_from_order(order_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    从订单摘要中提取客户信息，转换为AgentState的customer_info格式
    
    Args:
        order_summary: 订单摘要数据（可能包含summary文本字段或结构化数据）
        
    Returns:
        customer_info格式的字典
    """
    customer_info = {}
    
    # 如果API返回的是summary文本格式，先解析它
    if "summary" in order_summary and isinstance(order_summary["summary"], str):
        logger.info("Parsing summary text from API response")
        parsed_data = parse_summary_text(order_summary["summary"])
        # 合并解析的数据到order_summary
        order_summary = {**order_summary, **parsed_data}
    
    # 基本信息
    if "customer_name" in order_summary:
        customer_info["name"] = order_summary["customer_name"]
    
    if "destination_country" in order_summary:
        customer_info["destination_country"] = order_summary["destination_country"]
    
    if "destination_city" in order_summary:
        customer_info["destination_city"] = order_summary["destination_city"]
    
    if "arrival_date" in order_summary:
        customer_info["arrival_date"] = order_summary["arrival_date"]
    
    if "office_address" in order_summary:
        customer_info["office_address"] = order_summary["office_address"]
    
    # 住房需求
    housing_req = order_summary.get("housing_requirements", {})
    if housing_req.get("budget"):
        customer_info["housing_budget"] = housing_req["budget"]
    
    if housing_req.get("bedrooms"):
        customer_info["bedrooms"] = housing_req["bedrooms"]
    
    if housing_req.get("preferred_areas"):
        customer_info["preferred_areas"] = housing_req["preferred_areas"]
    
    # 家庭信息
    family_info = order_summary.get("family_info", {})
    if family_info.get("family_size"):
        customer_info["family_size"] = family_info["family_size"]
    
    if "has_children" in family_info:
        customer_info["has_children"] = family_info["has_children"]
    
    if "needs_car" in family_info:
        customer_info["needs_car"] = family_info["needs_car"]
    
    # 临时住宿
    temp_accom = order_summary.get("temporary_accommodation", {})
    if temp_accom.get("days"):
        customer_info["temporary_accommodation_days"] = temp_accom["days"]
    
    # 预定活动日期
    scheduled_activities = order_summary.get("scheduled_activities", [])
    if scheduled_activities:
        preferred_dates = {}
        for activity in scheduled_activities:
            activity_type = activity.get("type")
            activity_date = activity.get("date")
            if activity_type and activity_date:
                preferred_dates[activity_type] = activity_date
        
        if preferred_dates:
            customer_info["preferred_dates"] = preferred_dates
    
    return customer_info


def format_order_summary_for_display(order_summary: Dict[str, Any]) -> str:
    """
    格式化订单摘要用于显示给用户
    
    Args:
        order_summary: 订单摘要数据（可能包含summary文本字段）
        
    Returns:
        格式化的字符串
    """
    # 如果有summary文本，解析它以获取结构化数据
    if "summary" in order_summary and isinstance(order_summary["summary"], str):
        parsed_data = parse_summary_text(order_summary["summary"])
        order_summary = {**order_summary, **parsed_data}
    
    lines = []
    
    lines.append(f"📋 **Order Information Retrieved Successfully**")
    
    if order_summary.get('arrival_date'):
        lines.append(f"✈️ **Arrival Date:** {order_summary['arrival_date']}")
    
    if order_summary.get('office_address'):
        lines.append(f"🏢 **Office Location:** {order_summary['office_address']}")
    
    # 临时住宿
    if order_summary.get("temporary_accommodation_days"):
        lines.append(f"🏨 **Temporary Accommodation:** {order_summary['temporary_accommodation_days']} days")
    
    # 住房需求
    if order_summary.get("housing_budget"):
        lines.append(f"\n🏠 **Housing Requirements:**")
        lines.append(f"   - Budget: HKD {order_summary['housing_budget']:,}/month")
    
    if order_summary.get("bedrooms"):
        lines.append(f"   - Bedrooms: {order_summary['bedrooms']}")
    
    if order_summary.get("preferred_areas"):
        areas = ", ".join(order_summary["preferred_areas"])
        lines.append(f"   - Preferred Areas: {areas}")
    
    # 家庭信息
    if order_summary.get("family_size"):
        lines.append(f"\n👨‍👩‍👧‍👦 **Family Size:** {order_summary['family_size']} adult(s)")
    
    # 已安排的活动
    scheduled_activities = order_summary.get("scheduled_activities", [])
    if scheduled_activities:
        lines.append(f"\n📅 **Scheduled Activities:**")
        for activity in scheduled_activities:
            activity_type = activity.get('type', '').replace('_', ' ').title()
            lines.append(f"   - {activity.get('date', 'TBD')}: {activity_type}")
    
    return "\n".join(lines)


# 创建全局API客户端实例
_api_client = None

def get_order_api_client() -> OrderAPIClient:
    """获取订单API客户端单例"""
    global _api_client
    if _api_client is None:
        _api_client = OrderAPIClient()
    return _api_client
