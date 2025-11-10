"""
Smart Core Task Generator with Intelligent Activity Extension
智能核心任务生成器 - 基于主要活动智能扩展同日行程

核心逻辑：
1. 只为主要活动（Core Tasks）所在的日期生成扩展活动
2. 分析活动依赖关系（例如：去税务局前必须先有银行卡）
3. 基于主要活动位置查找附近服务（2km半径内）
4. 根据用户画像评估生活便利性
5. 生成、过滤和排序扩展活动候选列表
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import logging

from immigration.state import SettlementTask, TaskType, CustomerInfo
from immigration.nearby_services import find_extended_activities_for_task
from immigration.geocoding_service import get_geocoding_service

logger = logging.getLogger(__name__)


# 活动依赖关系定义
ACTIVITY_DEPENDENCIES = {
    "tax_registration": {
        "requires": ["bank_account"],  # 税务登记需要先有银行账户
        "reason": "Tax registration requires a local bank account for payments"
    },
    "rental_contract": {
        "requires": ["bank_account", "resident_id"],  # 租房合同需要银行账户和居民身份证
        "reason": "Rental contracts require proof of identity and bank account for deposits"
    },
    "utility_setup": {
        "requires": ["rental_contract"],  # 水电设置需要先有租房合同
        "reason": "Utility services require proof of residence"
    },
    "mobile_contract": {
        "requires": ["resident_id"],  # 手机合约需要居民身份证
        "reason": "Mobile contracts require local ID verification"
    },
    "driver_license": {
        "requires": ["resident_id"],  # 驾照需要居民身份证
        "reason": "Driver's license conversion requires local resident ID"
    },
    "health_insurance": {
        "requires": ["resident_id", "bank_account"],  # 健康保险需要身份证和银行账户
        "reason": "Health insurance enrollment requires ID and bank account for payments"
    }
}


# 核心任务类型映射（用于依赖分析）
TASK_TYPE_MAPPING = {
    "Open Bank Account": "bank_account",
    "Apply for Resident Identity Card": "resident_id",
    "Property Viewing": "property_search",
    "Sign Rental Contract": "rental_contract",
    "Tax Registration": "tax_registration",
    "Convert Driver's License": "driver_license",
    "Health Insurance": "health_insurance",
    "Utility Setup": "utility_setup",
    "Get Mobile SIM Card": "mobile_contract"
}


class SmartTaskAnalyzer:
    """智能任务分析器 - 分析时间窗口、依赖关系和生活便利性"""
    
    def __init__(self, customer_info: CustomerInfo):
        self.customer_info = customer_info
        self.arrival_date = self._parse_arrival_date()
    
    def _parse_arrival_date(self) -> Optional[datetime]:
        """解析到达日期"""
        if self.customer_info.get("arrival_date"):
            try:
                return datetime.strptime(
                    self.customer_info["arrival_date"], 
                    "%Y-%m-%d"
                )
            except:
                pass
        return None
    
    def analyze_time_window(
        self, 
        task: SettlementTask
    ) -> Tuple[int, Optional[datetime]]:
        """
        分析任务的时间窗口
        
        Returns:
            (day_number, actual_date) tuple
        """
        day_range = task.get("day_range", "")
        
        # 提取日期编号
        try:
            if "Day" in day_range:
                day_part = day_range.split("(")[0].strip()
                if "-" in day_part:
                    # "Day 1-3" -> 取开始日期
                    day_num = int(day_part.split("-")[0].replace("Day", "").strip())
                else:
                    # "Day 1"
                    day_num = int(day_part.replace("Day", "").strip())
                
                # 计算实际日期
                actual_date = None
                if self.arrival_date:
                    actual_date = self.arrival_date + timedelta(days=day_num - 1)
                
                return day_num, actual_date
        except Exception as e:
            logger.warning(f"Failed to parse day_range '{day_range}': {e}")
        
        return 1, self.arrival_date
    
    def analyze_dependencies(
        self, 
        task: SettlementTask,
        completed_task_types: Set[str]
    ) -> Tuple[bool, List[str], Optional[str]]:
        """
        分析任务依赖关系
        
        Args:
            task: 要分析的任务
            completed_task_types: 已完成的任务类型集合
        
        Returns:
            (is_ready, missing_dependencies, reason) tuple
            - is_ready: 是否满足所有依赖
            - missing_dependencies: 缺失的依赖列表
            - reason: 依赖说明
        """
        task_title = task.get("title", "")
        task_type = TASK_TYPE_MAPPING.get(task_title)
        
        if not task_type or task_type not in ACTIVITY_DEPENDENCIES:
            return True, [], None  # 没有依赖，可以直接执行
        
        dependency_info = ACTIVITY_DEPENDENCIES[task_type]
        required = set(dependency_info["requires"])
        missing = required - completed_task_types
        
        is_ready = len(missing) == 0
        reason = dependency_info["reason"] if not is_ready else None
        
        return is_ready, list(missing), reason
    
    def assess_lifestyle_convenience(
        self,
        service: Dict[str, Any],
        task_location: Dict[str, Any]
    ) -> float:
        """
        评估生活便利性得分（0-1）
        
        基于：
        1. 距离主要活动的远近
        2. 用户画像匹配度（年龄、家庭状况、预算等）
        3. 服务类型重要性
        """
        score = 0.0
        
        # 1. 距离因子（越近越好，2km内）
        distance = self._calculate_distance(
            service.get("latitude"),
            service.get("longitude"),
            task_location.get("latitude"),
            task_location.get("longitude")
        )
        
        if distance <= 0.5:  # 500m内
            score += 0.4
        elif distance <= 1.0:  # 1km内
            score += 0.3
        elif distance <= 2.0:  # 2km内
            score += 0.2
        else:
            score += 0.1
        
        # 2. 用户画像匹配度
        service_type = service.get("type", "")
        
        # 家庭状况
        if self.customer_info.get("has_children"):
            if service_type in ["school", "playground", "pediatric_clinic"]:
                score += 0.2
        
        # 预算敏感度
        budget = self.customer_info.get("housing_budget", 0)
        if budget < 20000:  # 预算较低
            if service_type in ["supermarket", "convenience_store", "market"]:
                score += 0.2
        elif budget > 40000:  # 预算较高
            if service_type in ["fine_dining", "gym", "spa"]:
                score += 0.2
        
        # 工作相关
        if self.customer_info.get("works_from_home"):
            if service_type in ["cafe", "coworking_space"]:
                score += 0.2
        
        # 3. 服务类型基础重要性
        essential_services = {
            "supermarket": 0.3,
            "pharmacy": 0.25,
            "clinic": 0.25,
            "bank": 0.2,
            "convenience_store": 0.2,
            "restaurant": 0.15,
            "cafe": 0.1,
            "gym": 0.1
        }
        
        score += essential_services.get(service_type, 0.05)
        
        return min(score, 1.0)  # 限制在0-1范围内
    
    def _calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """计算两点之间的距离（km）"""
        from math import radians, cos, sin, sqrt, atan2
        
        R = 6371  # 地球半径（km）
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c


class SmartCoreTaskGenerator:
    """智能核心任务生成器 - 只为主要活动当天生成扩展活动"""
    
    def __init__(self, customer_info: CustomerInfo):
        self.customer_info = customer_info
        self.analyzer = SmartTaskAnalyzer(customer_info)
    
    async def generate_extended_activities_for_core_tasks(
        self,
        core_tasks: List[SettlementTask],
        max_activities_per_task: int = 3
    ) -> List[SettlementTask]:
        """
        为核心任务生成扩展活动
        
        核心流程：
        1. 对每个核心任务：
           ├─ 分析时间窗口（提取day number和实际日期）
           ├─ 检查活动依赖性（是否满足前置条件）
           ├─ 查找附近服务（2km半径内）
           ├─ 评估生活便利性（基于用户画像）
           ├─ 生成扩展活动候选列表
           └─ 过滤和排序（相关性评分）
        
        2. 只为核心任务所在的日期生成活动
        3. 未提到的日期不安排任何活动
        4. 特殊处理Day 1（到达日）：显著减少扩展活动数量，避免让用户疲惫
        """
        all_extended_tasks = []
        task_counter = 1000
        
        # 跟踪已生成的活动（去重）
        generated_activities: Dict[int, Set[Tuple[str, str]]] = {}  # day -> set of (type, district)
        
        # 跟踪每天的核心任务数量和扩展活动配额
        daily_task_counts: Dict[int, int] = {}  # day -> core_task_count
        daily_extended_quota: Dict[int, int] = {}  # day -> remaining_extended_quota
        
        # 跟踪已完成的任务类型（用于依赖分析）
        completed_task_types: Set[str] = set()
        
        # First pass: 计算每天的核心任务数量
        for core_task in core_tasks:
            day_num, _ = self.analyzer.analyze_time_window(core_task)
            daily_task_counts[day_num] = daily_task_counts.get(day_num, 0) + 1
        
        # 设置每天的扩展活动配额
        for day_num, core_count in daily_task_counts.items():
            if day_num == 1:
                # Day 1（到达日）特殊处理：
                # - 如果有2个或更多核心任务（如机场接机+入住），则不添加扩展活动
                # - 如果只有1个核心任务，最多添加1个扩展活动
                if core_count >= 2:
                    daily_extended_quota[day_num] = 0
                    logger.info(f"Day 1 (Arrival Day) has {core_count} core tasks - no extended activities to avoid fatigue")
                else:
                    daily_extended_quota[day_num] = 1
                    logger.info(f"Day 1 (Arrival Day) - limited to 1 extended activity maximum")
            else:
                # 其他日期：每个核心任务最多max_activities_per_task个扩展活动
                daily_extended_quota[day_num] = core_count * max_activities_per_task
        
        # Second pass: 为每个核心任务生成扩展活动
        for core_task in core_tasks:
            # Step 1: 分析时间窗口
            day_num, actual_date = self.analyzer.analyze_time_window(core_task)
            
            # 检查该天是否还有扩展活动配额
            remaining_quota = daily_extended_quota.get(day_num, 0)
            if remaining_quota <= 0:
                logger.info(
                    f"Day {day_num} has reached its extended activity quota. "
                    f"Skipping extended activities for '{core_task.get('title')}'"
                )
                continue
            
            logger.info(
                f"Processing core task '{core_task.get('title')}' on Day {day_num} "
                f"(remaining quota: {remaining_quota})"
            )
            
            # Step 2: 检查任务依赖
            task_title = core_task.get("title", "")
            task_type = TASK_TYPE_MAPPING.get(task_title)
            
            is_ready, missing_deps, reason = self.analyzer.analyze_dependencies(
                core_task, 
                completed_task_types
            )
            
            if not is_ready:
                logger.warning(
                    f"Task '{task_title}' has unmet dependencies: {missing_deps}. "
                    f"Reason: {reason}"
                )
                # 可以选择跳过或调整任务顺序
                # 这里我们继续生成，但会在任务描述中添加依赖提示
            
            # 更新已完成任务类型（假设任务会按顺序完成）
            if task_type:
                completed_task_types.add(task_type)
            
            # Step 3: 查找附近服务（2km半径内）
            if not core_task.get("location"):
                logger.warning(f"Core task '{task_title}' has no location, skipping")
                continue
            
            # 跳过特殊位置类型（机场、中转站等）
            skip_location_types = ["airport", "transit", "station"]
            if core_task["location"].get("type") in skip_location_types:
                logger.info(f"Skipping core task at special location: {core_task['location'].get('type')}")
                continue
            
            try:
                # Step 4: 获取附近服务候选列表
                nearby_activities = await find_extended_activities_for_task(
                    core_task,
                    self.customer_info,
                    max_activities=max_activities_per_task * 3  # 获取更多候选用于筛选
                )
                
                # Step 5: 评估生活便利性并过滤
                scored_activities = []
                for service, base_score, reason in nearby_activities:
                    # 计算综合得分
                    convenience_score = self.analyzer.assess_lifestyle_convenience(
                        service,
                        core_task["location"]
                    )
                    
                    # 综合得分 = 基础相关性 * 0.4 + 便利性得分 * 0.6
                    final_score = base_score * 0.4 + convenience_score * 0.6
                    
                    scored_activities.append((service, final_score, reason))
                
                # Step 6: 排序（按相关性评分降序）
                scored_activities.sort(key=lambda x: x[1], reverse=True)
                
                # Step 7: 去重并生成扩展任务
                if day_num not in generated_activities:
                    generated_activities[day_num] = set()
                
                added_count = 0
                for service, score, reason in scored_activities:
                    # 检查是否达到该天的配额
                    if daily_extended_quota[day_num] <= 0:
                        logger.info(f"Day {day_num} quota exhausted, stopping extended activity generation")
                        break
                    
                    if added_count >= max_activities_per_task:
                        break
                    
                    # 去重检查
                    service_type = service.get("type", "unknown")
                    district = self._extract_district(service.get("address", ""))
                    activity_key = (service_type, district)
                    
                    if activity_key in generated_activities[day_num]:
                        continue  # 跳过重复活动
                    
                    # 生成扩展任务
                    extended_task = self._create_extended_task(
                        service=service,
                        reason=reason,
                        day_num=day_num,
                        actual_date=actual_date,
                        core_task=core_task,
                        relevance_score=score,
                        task_counter=task_counter
                    )
                    
                    if extended_task:
                        all_extended_tasks.append(extended_task)
                        generated_activities[day_num].add(activity_key)
                        daily_extended_quota[day_num] -= 1  # 减少配额
                        task_counter += 1
                        added_count += 1
                        
                        logger.info(
                            f"  → Generated extended activity: {extended_task['title']} "
                            f"(score: {score:.2f}, remaining quota: {daily_extended_quota[day_num]})"
                        )
            
            except Exception as e:
                logger.error(f"Error generating extended activities for '{task_title}': {e}")
                continue
        
        logger.info(
            f"Total extended activities generated: {len(all_extended_tasks)} "
            f"across {len(generated_activities)} days"
        )
        
        return all_extended_tasks
    
    def _extract_district(self, address: str) -> str:
        """从地址中提取区域名称"""
        districts = [
            "Wan Chai", "Central", "Admiralty", "Causeway Bay", "Sheung Wan",
            "Mid-Levels", "Quarry Bay", "Tai Koo", "Tsim Sha Tsui", "Mong Kok",
            "Yau Ma Tei", "Jordan", "Kowloon", "Sha Tin", "Tuen Mun"
        ]
        
        address_lower = address.lower()
        for district in districts:
            if district.lower() in address_lower:
                return district
        
        return "unknown"
    
    def _create_extended_task(
        self,
        service: Dict[str, Any],
        reason: str,
        day_num: int,
        actual_date: Optional[datetime],
        core_task: SettlementTask,
        relevance_score: float,
        task_counter: int
    ) -> Optional[SettlementTask]:
        """创建扩展任务"""
        
        # 格式化日期范围
        day_range = f"Day {day_num}"
        if actual_date:
            day_range += f" ({actual_date.strftime('%b %d')})"
        
        # 生成任务标题
        service_type = service.get("type", "").replace("_", " ").title()
        task_title = f"Visit {service.get('name', service_type)}"
        
        # 生成任务描述（包含推荐理由）
        description = f"{service.get('description', '')}. {reason}"
        
        # 创建位置对象
        location = {
            "id": service.get("id", f"ext_loc_{task_counter}"),
            "name": service.get("name", ""),
            "address": service.get("address", ""),
            "latitude": service["latitude"],
            "longitude": service["longitude"],
            "rating": service.get("rating"),
            "type": service.get("type", "extended_service"),
            "description": service.get("description", "")
        }
        
        # 估算时长
        duration = self._estimate_duration(service.get("type", ""))
        
        return {
            "id": str(uuid.uuid4()),
            "title": task_title,
            "description": description,
            "day_range": day_range,
            "priority": "low",  # 扩展任务优先级较低
            "task_type": TaskType.EXTENDED.value,
            "core_activity_id": core_task.get("id"),  # 关联到核心任务
            "relevance_score": round(relevance_score, 2),
            "recommendation_reason": reason,
            "location": location,
            "documents_needed": [],
            "estimated_duration": duration,
            "status": "pending",
            "dependencies": []
        }
    
    def _estimate_duration(self, service_type: str) -> str:
        """估算访问时长"""
        duration_map = {
            "supermarket": "30-45 minutes",
            "pharmacy": "15-20 minutes",
            "convenience_store": "10-15 minutes",
            "restaurant": "1-1.5 hours",
            "cafe": "30-45 minutes",
            "gym": "1-2 hours",
            "clinic": "30-60 minutes",
            "hospital": "1-3 hours",
            "mall": "1-2 hours",
            "market": "45-60 minutes",
            "bank": "30-45 minutes",
            "atm": "5-10 minutes",
            "school": "1-2 hours",
            "playground": "30-60 minutes",
        }
        
        return duration_map.get(service_type, "30 minutes")


async def generate_smart_extended_tasks(
    core_tasks: List[SettlementTask],
    customer_info: CustomerInfo,
    max_per_task: int = 3
) -> List[SettlementTask]:
    """
    智能生成扩展任务的主入口函数
    
    Args:
        core_tasks: 核心任务列表
        customer_info: 客户信息
        max_per_task: 每个核心任务最多生成多少个扩展活动
    
    Returns:
        扩展任务列表
    """
    generator = SmartCoreTaskGenerator(customer_info)
    return await generator.generate_extended_activities_for_core_tasks(
        core_tasks,
        max_activities_per_task=max_per_task
    )
