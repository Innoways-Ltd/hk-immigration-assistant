# 智能核心任务生成器 - 功能总结

## 🎯 核心目标

实现智能核心任务扩展生成器，**只为主要活动当天生成扩展活动**，未提到的日期不安排任何活动。

---

## ✨ 主要功能

### 1. 智能活动扩展逻辑

```
对每个主要活动（Core Task）：
├─ 分析时间窗口（当天或次日）
├─ 扩展活动依赖性（根据主要活动安排其他）
│  └─ 例如：去税务局之前必须先申请银行卡
├─ 查找附近服务（半径2km）
├─ 评估生活便利性（基于用户画像）
├─ 生成扩展活动候选列表
└─ 过滤和排序（相关性评分）
```

### 2. 活动依赖关系管理

系统内置了活动依赖关系图：

| 活动 | 依赖 | 原因 |
|------|------|------|
| 税务登记 | 银行账户 | Tax registration requires a local bank account for payments |
| 租房合同 | 银行账户 + 居民身份证 | Rental contracts require proof of identity and bank account |
| 水电设置 | 租房合同 | Utility services require proof of residence |
| 手机合约 | 居民身份证 | Mobile contracts require local ID verification |
| 驾照转换 | 居民身份证 | Driver's license conversion requires local resident ID |
| 健康保险 | 身份证 + 银行账户 | Health insurance enrollment requires ID and bank account |

### 3. 生活便利性评估

基于以下因素计算综合得分（0-1分制）：

#### A. 距离因子（越近越好，2km内）
- **500m内** → 0.4分
- **1km内** → 0.3分
- **2km内** → 0.2分
- **超过2km** → 0.1分

#### B. 用户画像匹配度
- **有孩子**：
  - 学校、游乐场、儿科诊所 → +0.2分
- **预算较低（<20,000 HKD）**：
  - 超市、便利店、市场 → +0.2分
- **预算较高（>40,000 HKD）**：
  - 高档餐厅、健身房、SPA → +0.2分
- **远程办公**：
  - 咖啡厅、共享办公空间 → +0.2分

#### C. 服务类型基础重要性
| 服务类型 | 得分 |
|---------|------|
| 超市 | 0.3 |
| 药店 | 0.25 |
| 诊所 | 0.25 |
| 银行 | 0.2 |
| 便利店 | 0.2 |
| 餐厅 | 0.15 |
| 咖啡厅 | 0.1 |
| 健身房 | 0.1 |
| 其他 | 0.05 |

#### D. 综合评分公式

```
最终得分 = 基础相关性 × 0.4 + 便利性得分 × 0.6
```

### 4. 智能去重机制

- **去重键**：`(service_type, district)` 元组
- **规则**：同一天内，同一区域的相同服务类型只推荐一次
- **效果**：避免重复推荐（例如：同一天推荐多个咖啡厅）

---

## 📂 文件结构

```
agent/immigration/
├── smart_core_task_generator.py     [NEW] 智能核心任务生成器
│   │
│   ├── ACTIVITY_DEPENDENCIES          活动依赖关系定义
│   ├── TASK_TYPE_MAPPING              任务类型映射
│   │
│   ├── SmartTaskAnalyzer              分析器类
│   │   ├── __init__()                 初始化（解析到达日期）
│   │   ├── analyze_time_window()      分析任务时间窗口
│   │   ├── analyze_dependencies()     分析任务依赖关系
│   │   ├── assess_lifestyle_convenience() 评估生活便利性
│   │   └── _calculate_distance()      计算地理距离
│   │
│   └── SmartCoreTaskGenerator         生成器类
│       ├── __init__()                 初始化分析器
│       ├── generate_extended_activities_for_core_tasks() 主函数
│       ├── _extract_district()        提取区域名称
│       ├── _create_extended_task()    创建扩展任务
│       └── _estimate_duration()       估算任务时长
│
└── comprehensive_task_generator.py  [MODIFIED] 主任务生成器
    ├── [imports] 新增导入
    │   ├── from smart_core_task_generator import generate_smart_extended_tasks
    │   ├── from core_tasks_generator import generate_core_tasks
    │   └── from state import TaskType
    │
    ├── generate_comprehensive_tasks() [MODIFIED] 主函数
    │   └── 集成智能生成器逻辑
    │
    └── convert_core_tasks_format()    [NEW] 格式转换函数
        └── 将 SettlementTask 转换为内部格式
```

---

## 🎯 核心逻辑改进

### Before（旧逻辑）

❌ **为所有日期生成活动**（包括没有主要任务的日期）
❌ **缺少依赖关系检查**
❌ **没有基于用户画像的便利性评估**
❌ **可能推荐重复服务**

### After（新逻辑）

✅ **只为主要活动当天生成扩展活动**
✅ **分析并遵守活动依赖关系**
✅ **基于用户画像智能评估便利性**
✅ **2km半径内查找附近服务**
✅ **智能去重和排序**
✅ **综合评分排序推荐**

---

## 📊 示例效果

### 场景1：开银行账户

假设用户在 **Day 10** 有"开银行账户"的主要任务：

```
Day 10 (Nov 17):
  ✓ [主要] 开银行账户 @ 中环 (Core Task)
  ✓ [扩展] 附近超市 @ 距离500m (自动添加，综合得分: 0.9)
  ✓ [扩展] 附近药店 @ 距离800m (自动添加，综合得分: 0.8)
  ✓ [扩展] 附近餐厅 @ 距离1.2km (自动添加，综合得分: 0.6)

Day 11-13 (Nov 18-20):
  (没有主要任务，因此不添加任何扩展活动)

Day 14 (Nov 21):
  ✓ [主要] 申请居民身份证 @ 湾仔 (Core Task)
  ✓ [扩展] 附近便利店 @ 距离300m (自动添加)
  ✓ [扩展] 附近咖啡厅 @ 距离600m (自动添加)
```

### 场景2：依赖关系管理

```
Day 7:
  ✓ [主要] 申请居民身份证 @ 湾仔
  
Day 10:
  ✓ [主要] 开银行账户 @ 中环
  ℹ️  依赖检查通过：已有居民身份证

Day 14:
  ✓ [主要] 税务登记 @ 中环
  ℹ️  依赖检查通过：已有银行账户
```

如果顺序不对：

```
Day 7:
  ⚠️  [主要] 税务登记 @ 中环
  ❌ 依赖检查失败：需要先开银行账户
  → 系统建议：请先完成"开银行账户"任务
```

### 场景3：用户画像匹配

**用户A：预算较低的家庭**
- 预算：15,000 HKD/月
- 有孩子：是

```
Day 10 附近推荐：
  1. 本地超市（得分: 0.95）← 距离近 + 预算友好
  2. 社区游乐场（得分: 0.88）← 有孩子 + 免费
  3. 平价餐厅（得分: 0.72）← 预算友好
```

**用户B：高预算的专业人士**
- 预算：50,000 HKD/月
- 远程办公：是

```
Day 10 附近推荐：
  1. 精品咖啡厅（得分: 0.93）← 远程办公适合
  2. 高档餐厅（得分: 0.85）← 预算匹配
  3. 精品健身房（得分: 0.78）← 生活品质
```

---

## 🔧 技术实现细节

### 1. 时间窗口分析

```python
def analyze_time_window(self, task: SettlementTask) -> Tuple[int, Optional[datetime]]:
    """
    分析任务的时间窗口
    
    输入: "Day 10 (Nov 17)"
    输出: (10, datetime(2025, 11, 17))
    
    输入: "Day 3-5"
    输出: (3, datetime(2025, 11, 10))  # 取开始日期
    """
```

### 2. 依赖关系分析

```python
def analyze_dependencies(
    self, 
    task: SettlementTask,
    completed_task_types: Set[str]
) -> Tuple[bool, List[str], Optional[str]]:
    """
    分析任务依赖关系
    
    Returns:
        (is_ready, missing_dependencies, reason)
        
    Example:
        task = "税务登记"
        completed = {"resident_id"}  # 只有身份证
        
        返回: (False, ["bank_account"], "Tax registration requires...")
    """
```

### 3. 地理距离计算

使用 **Haversine公式** 计算地球表面两点间的距离：

```python
def _calculate_distance(self, lat1, lon1, lat2, lon2) -> float:
    """
    计算两点之间的距离（km）
    
    使用 Haversine 公式:
    a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
    c = 2 ⋅ atan2(√a, √(1−a))
    d = R ⋅ c
    
    其中 R = 6371 km（地球平均半径）
    """
```

### 4. 评分算法

```python
def assess_lifestyle_convenience(
    self,
    service: Dict[str, Any],
    task_location: Dict[str, Any]
) -> float:
    """
    评估生活便利性得分（0-1）
    
    计算流程:
    1. 距离因子（0.1-0.4分）
    2. 用户画像匹配（0-0.2分）
    3. 服务类型重要性（0.05-0.3分）
    
    最终: min(总分, 1.0)
    """
```

### 5. 去重策略

```python
# 跟踪已生成的活动
generated_activities: Dict[int, Set[Tuple[str, str]]] = {}
# key: day_num
# value: set of (service_type, district) tuples

# 检查是否重复
activity_key = (service_type, district)
if activity_key in generated_activities[day_num]:
    continue  # 跳过重复活动
```

---

## 🎉 预期效果

### 用户体验改进

✅ **计划更精简**：只显示有意义的日子，不会有"空白日期"
✅ **逻辑更清晰**：扩展活动都围绕主要任务展开
✅ **推荐更准确**：基于用户画像，推荐更符合需求
✅ **避免重复**：不会推荐大量相似服务

### 系统优势

✅ **智能化**：自动分析依赖关系和时间窗口
✅ **个性化**：基于用户画像定制推荐
✅ **可扩展**：易于添加新的依赖关系和服务类型
✅ **可维护**：代码结构清晰，职责分离

---

## 🚀 使用方式

### 在代码中集成

```python
from immigration.smart_core_task_generator import generate_smart_extended_tasks
from immigration.core_tasks_generator import generate_core_tasks

# 1. 生成核心任务
core_tasks = generate_core_tasks(customer_info)

# 2. 为核心任务生成智能扩展活动
extended_tasks = await generate_smart_extended_tasks(
    core_tasks,
    customer_info,
    max_per_task=3  # 每个核心任务最多3个扩展活动
)

# 3. 合并任务
all_tasks = core_tasks + extended_tasks
```

### 配置参数

```python
# 在 smart_core_task_generator.py 中可以调整：

# 距离阈值
DISTANCE_THRESHOLDS = {
    "very_close": 0.5,  # 500m
    "close": 1.0,       # 1km
    "nearby": 2.0       # 2km
}

# 评分权重
SCORE_WEIGHTS = {
    "base_relevance": 0.4,
    "convenience": 0.6
}

# 每个核心任务的最大扩展数
MAX_ACTIVITIES_PER_TASK = 3
```

---

## 📝 总结

本次实现完全满足了需求：

1. ✅ **只为主要活动当天生成扩展活动**
2. ✅ **未提到的日期不安排任何活动**
3. ✅ **分析活动依赖关系**
4. ✅ **查找2km半径内的附近服务**
5. ✅ **基于用户画像评估便利性**
6. ✅ **生成、过滤和排序扩展活动**

系统现在可以更智能地生成安家计划，只在有主要任务的日子安排相关活动，避免不必要的日程安排，提供更好的用户体验。

---

**提交信息**: 11e47f5 - feat: 实现智能核心任务生成器，只为主要活动当天生成扩展活动

**Pull Request**: https://github.com/Innoways-Ltd/hk-immigration-assistant/pull/3
