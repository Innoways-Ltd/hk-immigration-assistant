# 订单查询对话流程实现方案

## 📋 需求概述

修改Agent对话逻辑，实现新的交互流程：

1. **欢迎开场** - 询问订单号
2. **订单查询** - 使用API获取客户信息
3. **信息提取** - 从订单中提取行程关键信息
4. **信息确认** - 引导用户确认或补充信息
5. **创建计划** - 开始生成安家行程安排

## ✅ 已完成（第1步）

### 1. 订单API基础设施 (`order_api.py`)

**OrderAPIClient 类：**
- `get_order_summary(order_number)` - 查询订单信息
- 支持真实API和模拟数据
- 环境变量配置：
  - `ORDER_API_BASE_URL` - API地址
  - `ORDER_API_KEY` - API密钥

**辅助函数：**
- `extract_customer_info_from_order()` - 转换订单数据为agent格式
- `format_order_summary_for_display()` - 格式化订单信息用于展示
- `get_order_api_client()` - 获取客户端单例

**模拟订单数据：**

#### 订单1: HK20250504001
```json
{
  "customer_name": "张明",
  "arrival_date": "2025-05-04",
  "office_address": "One Island East, Taikoo Place, Quarry Bay",
  "temporary_accommodation": {
    "hotel_name": "Dorsett Wanchai",
    "days": 14
  },
  "scheduled_activities": [
    {"type": "home_viewing", "date": "2025-05-09"},
    {"type": "bank_account", "date": "2025-05-10"},
    {"type": "identity_card", "date": "2025-05-15"}
  ]
}
```

#### 订单2: HK20250510002
```json
{
  "customer_name": "李华",
  "arrival_date": "2025-05-10",
  "office_address": "International Commerce Centre, West Kowloon",
  "family_info": {
    "family_size": 4,
    "has_children": true,
    "children_ages": [6, 8],
    "needs_car": true
  },
  "temporary_accommodation": {
    "hotel_name": "Sheraton Hong Kong Hotel & Towers",
    "days": 30
  }
}
```

### 2. 状态扩展 (`state.py`)

**新增字段：**
- `order_number: Optional[str]` - 订单号
- `order_summary: Optional[Dict]` - 订单摘要
- `conversation_stage: Optional[str]` - 对话阶段标识

**对话阶段定义：**
1. `greeting` - 欢迎并询问订单号
2. `order_lookup` - 查询订单中
3. `info_review` - 展示订单信息，询问是否有更新
4. `info_confirmation` - 确认最终信息
5. `plan_creation` - 创建计划
6. `assistance` - 计划后的持续辅助

## 🚧 待实现（第2步）

### 1. 更新 `chat.py`

需要完全重写 `chat_node` 函数以实现新的对话流程。

#### Stage 1: Greeting（欢迎阶段）

**触发条件：**
- `not order_number and not customer_info.get("name")`

**System Message：**
```python
system_message = """
您是一位专业的移民安家助手。

**当前阶段：欢迎用户**

**您的任务：**
1. 热情友好地欢迎用户
2. 介绍自己是他们的移民安家助手
3. 询问用户的订单号
4. 解释订单号的作用（用于获取他们的行程安排）

**示例：**
"您好！我是您的专属移民安家助手 🌟

很高兴能帮助您规划香港的安家事宜。为了给您提供最准确的服务，我需要查询您的订单信息。

请问您能告诉我您的订单号吗？订单号通常以'HK'开头，例如：HK20250504001"

**工具使用：**
- 当用户提供订单号时，立即调用 query_order(order_number) 工具
"""
```

#### Stage 2: Order Lookup（订单查询）

**触发条件：**
- `order_number and not order_summary`

**处理逻辑：**
```python
if tool_name == "query_order":
    order_num = tool_call["args"]["order_number"]
    api_client = get_order_api_client()
    order_summary = await api_client.get_order_summary(order_num)
    
    if order_summary:
        # 提取客户信息
        extracted_info = extract_customer_info_from_order(order_summary)
        
        tool_message = ToolMessage(
            content="订单查询成功！",
            tool_call_id=tool_call["id"]
        )
        
        return {
            "messages": [response, tool_message],
            "order_number": order_num,
            "order_summary": order_summary,
            "customer_info": extracted_info,
            "conversation_stage": "info_review"
        }
    else:
        # 订单未找到
        tool_message = ToolMessage(
            content=f"抱歉，未找到订单号 {order_num}。请检查订单号是否正确。",
            tool_call_id=tool_call["id"]
        )
        
        return {
            "messages": [response, tool_message],
            "conversation_stage": "greeting"  # 回到欢迎阶段
        }
```

#### Stage 3: Info Review（信息审核）

**触发条件：**
- `order_summary and not info_confirmed`

**System Message：**
```python
order_display = format_order_summary_for_display(order_summary)

system_message = f"""
您是一位专业的移民安家助手。

**当前阶段：信息确认**

**已获取的订单信息：**

{order_display}

**您的任务：**
1. 友好地展示上述订单信息
2. 询问用户是否有任何需要更新或补充的信息
   - 特殊要求（如饮食偏好、宠物、健身房等）
   - 额外的日期安排
   - 任何其他偏好
3. 如果用户提供新信息，使用 save_customer_info 工具保存
4. 当用户确认信息无误或已完成更新时，调用 confirm_customer_info 工具

**示例开场：**
"太好了！我已经获取到您的订单信息：

[展示格式化的订单信息]

请您确认一下这些信息是否准确？另外，您是否有任何特殊要求或偏好需要告诉我？

例如：
- 对住房的特殊要求（如需要健身房、宠物友好等）
- 饮食偏好或限制
- 其他需要我注意的事项"
"""
```

#### Stage 4: Plan Creation（创建计划）

**触发条件：**
- `info_confirmed and not settlement_plan`

**System Message：**
```python
system_message = """
您是一位专业的移民安家助手。

**当前阶段：创建安家计划**

**已确认的客户信息：**
{customer_info_summary}

**您的任务：**
1. 告诉用户信息已确认，准备创建个性化安家计划
2. 询问用户是否现在创建计划
3. 当用户确认时，调用 create_settlement_plan(customer_name) 工具

**示例：**
"完美！✅ 我已经确认了您的所有信息。

现在我可以为您创建个性化的安家计划了。这个计划将包括：
- 📅 基于您指定日期的核心活动安排
- 🏘️ 智能推荐的便利服务（如附近的超市、餐厅等）
- 🗺️ 优化的路线规划
- ⏰ 合理的时间分配

需要我现在为您生成安家计划吗？"
"""
```

### 2. 添加工具到 `chat.py`

```python
@tool
async def query_order(order_number: str) -> str:
    """
    Query customer order information by order number.
    
    Args:
        order_number: Customer's order number (e.g., "HK20250504001")
    
    Returns:
        Success or error message
    """
    return f"Querying order: {order_number}"

# Add to tools list
tools = [
    query_order,  # 新增
    save_customer_info,
    confirm_customer_info,
    ...
]
```

### 3. 更新路由逻辑 (`agent.py`)

不需要修改，现有的路由逻辑已足够：
```python
def route(state: AgentState):
    # ...
    if tool_name in ["save_customer_info", "confirm_customer_info", "query_order"]:
        return "chat_node"
    # ...
```

## 🎯 实现优先级

1. **高优先级（必需）：**
   - ✅ 订单API基础设施
   - ⏳ 重写chat_node函数实现新流程
   - ⏳ 添加query_order工具
   - ⏳ 工具调用处理逻辑

2. **中优先级（重要）：**
   - ⏳ 错误处理（订单未找到、API失败等）
   - ⏳ 用户体验优化（加载提示、友好消息）
   - ⏳ 日志记录

3. **低优先级（可选）：**
   - 真实API集成
   - 更多模拟订单数据
   - 订单缓存机制

## 📝 测试计划

### 测试用例1：正常流程（订单HK20250504001）

**输入序列：**
1. 用户："你好"
2. Agent："欢迎...请提供订单号"
3. 用户："HK20250504001"
4. Agent："已获取订单信息...{显示订单}...是否需要补充？"
5. 用户："没有了"
6. Agent："信息已确认...是否创建计划？"
7. 用户："好的"
8. Agent：开始创建计划...

**预期结果：**
- 成功查询订单
- 显示完整订单信息
- 提取3个预定活动日期
- 生成包含Day 1, Day 5, Day 6, Day 11的计划

### 测试用例2：订单未找到

**输入序列：**
1. 用户："HK99999999"
2. Agent："未找到订单...请检查"

**预期结果：**
- 友好的错误提示
- 返回欢迎阶段重新询问

### 测试用例3：用户补充信息

**输入序列：**
1. 用户："HK20250504001"
2. Agent：显示订单信息
3. 用户："我需要宠物友好的房子，还有我吃素"
4. Agent：保存信息并确认
5. 用户："确认"
6. Agent：创建计划（考虑素食餐厅）

**预期结果：**
- 成功保存补充信息
- 扩展活动推荐素食餐厅

## 🔧 环境变量配置

```bash
# .env 文件
ORDER_API_BASE_URL=https://api.example.com  # 真实API地址
ORDER_API_KEY=your_api_key_here             # API密钥

# 如果不配置，将使用模拟数据
```

## 📚 参考文档

- `agent/immigration/order_api.py` - API客户端实现
- `agent/immigration/state.py` - 状态定义
- `agent/immigration/chat.py` - 对话节点（待更新）

## ⚠️ 注意事项

1. **订单号格式：** 当前模拟数据使用 `HK{YYYYMMDD}{序号}` 格式
2. **异步处理：** query_order 必须是异步函数
3. **错误处理：** 优雅处理API超时和失败
4. **用户体验：** 查询过程中显示"查询中..."提示
5. **数据转换：** 确保订单数据正确映射到customer_info格式

## 🎉 完成标志

- [ ] chat_node函数重写完成
- [ ] query_order工具集成
- [ ] 所有对话阶段实现
- [ ] 错误处理完善
- [ ] 测试用例通过
- [ ] 文档更新
- [ ] 代码提交并推送

---

**当前状态：** WIP - 已完成基础设施（第1步），等待实现对话流程（第2步）

**最后更新：** 2025-11-10
