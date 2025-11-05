"""
Plan Summarizer - Generates human-readable summary from finalized settlement plan
This ensures the summary is always based on the final, optimized plan.
"""
from typing import Dict, List
from datetime import datetime, timedelta
from .state import SettlementPlan, SettlementTask, CustomerInfo
import os
from langchain_openai import AzureChatOpenAI


def extract_key_dates_from_plan(plan: SettlementPlan) -> Dict[str, str]:
    """
    Extract key dates from the finalized plan.
    
    Returns:
        Dictionary mapping task types to their actual dates
    """
    key_dates = {}
    
    if not plan or not plan.get("tasks"):
        return key_dates
    
    arrival_date_str = None
    # Try to get arrival date from first task
    for task in plan["tasks"]:
        if "arrival" in task.get("title", "").lower() or "airport" in task.get("title", "").lower():
            day_range = task.get("day_range", "")
            if "(" in day_range:
                date_part = day_range.split("(")[1].split(")")[0]
                arrival_date_str = date_part
                break
    
    # Parse arrival date if found
    arrival_date = None
    if arrival_date_str:
        try:
            # Try different date formats
            for fmt in ["%b %d", "%B %d", "%Y-%m-%d"]:
                try:
                    arrival_date = datetime.strptime(arrival_date_str, fmt)
                    # If year not specified, assume current year
                    if arrival_date.year == 1900:
                        arrival_date = arrival_date.replace(year=datetime.now().year)
                    break
                except:
                    continue
        except:
            pass
    
    # Extract key task dates
    for task in plan["tasks"]:
        title_lower = task.get("title", "").lower()
        day_range = task.get("day_range", "")
        
        # Extract date from day_range
        task_date = None
        if "(" in day_range and ")" in day_range:
            date_part = day_range.split("(")[1].split(")")[0]
            if arrival_date:
                try:
                    # Extract day number
                    day_part = day_range.split("(")[0].strip()
                    if "Day" in day_part:
                        day_num = int(day_part.replace("Day", "").strip().split("-")[0])
                        task_date = arrival_date + timedelta(days=day_num - 1)
                except:
                    pass
        
        # Map task types to dates
        if "property" in title_lower or "housing" in title_lower or "viewing" in title_lower:
            if task_date:
                key_dates["property_viewing"] = task_date.strftime("%Y年%m月%d日")
            elif day_range:
                key_dates["property_viewing"] = day_range
                
        elif "bank" in title_lower:
            if task_date:
                key_dates["bank_account"] = task_date.strftime("%Y年%m月%d日")
            elif day_range:
                key_dates["bank_account"] = day_range
                
        elif "hkid" in title_lower or "identity" in title_lower:
            if task_date:
                key_dates["hkid"] = task_date.strftime("%Y年%m月%d日")
            elif day_range:
                key_dates["hkid"] = day_range
    
    return key_dates


async def generate_plan_summary(plan: SettlementPlan, customer_info: CustomerInfo) -> str:
    """
    Generate a human-readable summary from the finalized settlement plan.
    
    This function is called AFTER the plan has been fully optimized,
    ensuring the summary reflects the actual final dates and tasks.
    
    Args:
        plan: The finalized, optimized settlement plan
        customer_info: Customer information for context
        
    Returns:
        A natural language summary of the plan
    """
    if not plan or not plan.get("tasks"):
        return "尚未创建安家计划。"
    
    # Extract key information
    key_dates = extract_key_dates_from_plan(plan)
    total_tasks = len(plan["tasks"])
    core_tasks = [t for t in plan["tasks"] if t.get("task_type") == "core"]
    extended_tasks = [t for t in plan["tasks"] if t.get("task_type") == "extended"]
    
    # Calculate plan duration
    arrival_date_str = customer_info.get("arrival_date")
    temp_days = customer_info.get("temporary_accommodation_days", 30)
    
    # Build summary using LLM for better natural language
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        temperature=0.7,
        max_tokens=800,
        streaming=True,
    )
    
    # Prepare task summary
    task_summary_parts = []
    for task in plan["tasks"][:10]:  # First 10 tasks
        task_summary_parts.append(f"- {task.get('title')}: {task.get('day_range')}")
    
    # Build detailed task list with exact dates from the plan
    all_tasks_with_dates = []
    for task in plan["tasks"]:
        all_tasks_with_dates.append(
            f"- {task.get('title')}: {task.get('day_range')} (优先级: {task.get('priority', 'medium')})"
        )
    
    summary_prompt = f"""
基于以下**最终确定**的安家计划，生成一段自然、友好的中文摘要。

**重要提示：摘要中提到的所有日期必须与下面列出的任务日期完全一致，不要自行推算或修改日期。**

**客户信息：**
- 姓名: {plan.get('customer_name', '客户')}
- 到达日期: {arrival_date_str or '待定'}
- 临时住宿天数: {temp_days}天

**完整任务列表（按实际执行顺序）：**
{chr(10).join(all_tasks_with_dates)}

**任务统计：**
- 总任务数: {total_tasks}项
- 核心任务: {len(core_tasks)}项  
- 推荐任务: {len(extended_tasks)}项

请生成一段摘要，要求：
1. **严格使用上述任务列表中的日期**，不要自行计算或推测日期
2. 提及临时住宿安排（{temp_days}天）
3. 如果任务列表中有"房屋参观"或"Property"相关任务，使用其确切日期
4. 如果任务列表中有"银行"或"Bank"相关任务，使用其确切日期  
5. 如果任务列表中有"居民身份证"或"identity card"相关任务，使用其确切日期
6. 简要提及其他重要任务（如交通卡、手机卡、探索社区等）
7. 使用友好、自然的中文语言
8. 保持简洁，重点突出时间节点和优先级高的任务

**示例格式：**
"您的30天安家计划已准备就绪！从5月4日抵达开始，您将在临时住所居住30天。

关键时间线：
- 上门看房服务：定于 Day 3-5 (5月9日) 进行
- 银行账户开立：预计于 Day 7 (5月10日) 进行
- 申请居民身份证：安排在 Day 7-10 进行

此外，计划还包括交通卡办理、手机服务设置、探索社区等便利任务，帮助您快速融入当地生活。"
"""
    
    try:
        response = await llm.ainvoke(summary_prompt)
        summary = response.content
        return summary
    except Exception as e:
        # Fallback to template-based summary if LLM fails
        return _generate_fallback_summary(plan, customer_info, key_dates)


def _generate_fallback_summary(
    plan: SettlementPlan,
    customer_info: CustomerInfo,
    key_dates: Dict[str, str]
) -> str:
    """
    Generate a fallback summary using templates if LLM is unavailable.
    """
    arrival_date_str = customer_info.get("arrival_date", "")
    temp_days = customer_info.get("temporary_accommodation_days", 30)
    
    summary_parts = []
    
    # Temporary accommodation
    if arrival_date_str and temp_days:
        try:
            arrival = datetime.fromisoformat(arrival_date_str)
            end_date = arrival + timedelta(days=temp_days)
            summary_parts.append(
                f"**临时住宿 (Temporary Accommodation):** "
                f"您将从{arrival.strftime('%Y年%m月%d日')}起在湾仔的一间服务式公寓居住{temp_days}天。"
            )
        except:
            summary_parts.append(
                f"**临时住宿 (Temporary Accommodation):** "
                f"您将在一间服务式公寓居住{temp_days}天。"
            )
    
    # Property viewing - use actual date from plan
    if "property_viewing" in key_dates:
        summary_parts.append(
            f"**房屋参观服务 (Property Visit Service):** "
            f"定于{key_dates['property_viewing']}举行。房产经纪人将提前确定参观名单并与您分享以供审核。"
        )
    else:
        summary_parts.append(
            "**房屋参观服务 (Property Visit Service):** "
            "房产经纪人将提前确定参观名单并与您分享以供审核。"
        )
    
    # Bank account - use actual date from plan
    if "bank_account" in key_dates:
        summary_parts.append(
            f"**银行账户开立 (Bank Account Opening):** "
            f"暂定于{key_dates['bank_account']}进行。我们将提供协助，帮助您在合适的银行开立账户。"
        )
    else:
        summary_parts.append(
            "**银行账户开立 (Bank Account Opening):** "
            "我们将提供协助，帮助您在合适的银行开立账户。"
        )
    
    # Lease start date
    if arrival_date_str and temp_days:
        try:
            arrival = datetime.fromisoformat(arrival_date_str)
            lease_start = arrival + timedelta(days=temp_days)
            summary_parts.append(
                f"**房屋租赁开始日期 (Property Lease Start Date):** "
                f"{lease_start.strftime('%Y年%m月')}初,与您的临时住宿期结束日期一致。租赁期限为1年或2年。"
            )
        except:
            pass
    
    # Additional services
    summary_parts.extend([
        "**交通指南 (Transportation Guide):** "
        "指导如何高效地使用公共交通工具和游览香港，尤其是在湾仔和上环附近。",
        "**靠近办公室 (Near Office):** "
        "住房选择主要集中在步行可达或短途通勤至湾仔骆克道3号的区域。",
        "**日常生活必需品 (Daily Necessities):** "
        "湾仔和上环附近超市、餐馆和其他生活必需品的建议。",
        "**移动服务设置 (Mobile Service Setup):** "
        "协助选择和设置手机套餐。",
        "**水电煤气等公用设施安装 (Utilities Installation):** "
        "协助您安排永久住所的水电煤气等公用设施(电力、水、互联网)。",
        "**入门指南 (Getting Started Guide):** "
        "如何在香港出行、了解当地风俗以及如何融入这座充满活力的城市生活。"
    ])
    
    summary_parts.append(
        "\n如果您需要更具体的细节,或者想调整任何任务或时间安排,请告诉我!"
    )
    
    return "\n".join(summary_parts)

