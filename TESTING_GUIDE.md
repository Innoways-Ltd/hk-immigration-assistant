# Testing Guide - Core/Extended Tasks Feature

## 快速启动

### 1. 启动后端服务

```bash
cd /home/ubuntu/hk-immigration-assistant/agent
python3.11 -c "from immigration.demo import main; main()" &
```

等待5秒后，验证后端已启动：
```bash
curl http://localhost:8000/docs
```

### 2. 启动前端服务

```bash
cd /home/ubuntu/hk-immigration-assistant/ui
pnpm dev &
```

等待10秒后，访问：
- 本地：http://localhost:3000
- 公开URL：https://3000-i2yig35w8uxyn2370v6hr-b6356d1f.manus-asia.computer

## 测试场景

### 场景1：基础核心任务生成

**测试步骤：**
1. 打开应用
2. 输入基本信息：
   ```
   Name: John Smith
   Arrival Date: 2024-11-10
   Office Address: Wan Chai, Hong Kong
   Temporary Accommodation Days: 7
   ```
3. 确认信息
4. 查看生成的计划

**预期结果：**
- 生成4-5个核心任务（⭐ 标记）
- 所有任务都是必需的（机场接机、临时住宿、SIM卡、银行账户）
- 每个任务都有地理位置信息
- 任务按天分组显示

### 场景2：扩展任务生成（单身专业人士）

**测试步骤：**
1. 输入信息：
   ```
   Name: Sarah Chen
   Arrival Date: 2024-11-10
   Office Address: Central, Hong Kong
   Temporary Accommodation Days: 14
   Housing Budget: 35000 HKD
   Preferred Areas: Central, Sheung Wan
   Has Children: No
   ```
2. 确认信息
3. 查看生成的计划

**预期结果：**
- 核心任务（⭐）：机场接机、临时住宿、看房、开银行账户、申请HKID
- 扩展任务（💡）：
  - 咖啡馆（工作场所）
  - 健身房（生活质量）
  - 高端超市或商场
- 每个扩展任务都有蓝色推荐理由卡片
- 推荐理由包含距离信息和相关性说明

### 场景3：扩展任务生成（有孩子的家庭）

**测试步骤：**
1. 输入信息：
   ```
   Name: David Wong
   Arrival Date: 2024-11-10
   Office Address: Quarry Bay, Hong Kong
   Temporary Accommodation Days: 21
   Housing Budget: 28000 HKD
   Preferred Areas: Quarry Bay, Tai Koo
   Has Children: Yes
   Family Size: 4
   ```
2. 确认信息
3. 查看生成的计划

**预期结果：**
- 核心任务（⭐）：包含学校注册任务
- 扩展任务（💡）：
  - 药店（家庭必需）
  - 儿童诊所（健康保障）
  - 家庭超市（日常采购）
  - 公园（儿童活动）
- 推荐理由针对家庭需求定制

## 功能验证清单

### ✅ 核心功能
- [ ] 核心任务生成（⭐ 图标）
- [ ] 扩展任务生成（💡 图标）
- [ ] 地理编码正常工作
- [ ] 路线优化正常工作
- [ ] 任务按天分组显示

### ✅ 扩展任务特性
- [ ] 扩展任务显示推荐理由
- [ ] 推荐理由包含距离信息
- [ ] 推荐理由包含相关性说明
- [ ] 扩展任务在相关核心任务附近
- [ ] 每个核心任务最多2个扩展任务

### ✅ UI/UX
- [ ] 核心任务和扩展任务视觉区分清晰
- [ ] 推荐理由卡片样式正确（蓝色背景）
- [ ] 任务卡片hover效果正常
- [ ] 地图标记正确显示
- [ ] 任务选择（checkbox）功能正常
- [ ] 发送邮件功能正常

### ✅ 相关性评分
- [ ] 距离因素：近的服务优先推荐
- [ ] 用户需求匹配：
  - 有孩子 → 药店、诊所、超市
  - 高预算 → 商场、健身房、咖啡馆
  - 低预算 → 市场、便利店
- [ ] 评分阈值：只显示评分≥0.6的服务

## 调试技巧

### 查看后端日志
```bash
# 如果后台运行
tail -f /home/ubuntu/hk-immigration-assistant/backend.log

# 如果前台运行
# 直接查看终端输出
```

### 查看前端日志
```bash
# 浏览器控制台
# F12 → Console
```

### 检查API调用
```bash
# 测试后端健康状态
curl http://localhost:8000/docs

# 测试前端
curl http://localhost:3000
```

### 常见问题

**问题1：后端无法启动**
```bash
# 检查端口占用
lsof -i :8000

# 杀掉占用进程
kill -9 <PID>

# 重新启动
cd /home/ubuntu/hk-immigration-assistant/agent
python3.11 -c "from immigration.demo import main; main()" &
```

**问题2：前端无法启动**
```bash
# 检查端口占用
lsof -i :3000

# 杀掉占用进程
kill -9 <PID>

# 重新启动
cd /home/ubuntu/hk-immigration-assistant/ui
pnpm dev &
```

**问题3：没有生成扩展任务**
- 检查核心任务是否有地理位置信息
- 检查Nominatim API是否正常响应
- 检查相关性评分是否≥0.6
- 查看后端日志中的错误信息

**问题4：推荐理由不显示**
- 检查 `task.task_type === "extended"`
- 检查 `task.recommendation_reason` 是否存在
- 检查前端类型定义是否正确

## 性能测试

### 测试生成速度
```bash
# 记录开始时间
time curl -X POST http://localhost:8000/copilotkit \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**预期性能：**
- 核心任务生成：2-5秒（包含地理编码）
- 扩展任务生成：3-8秒（包含附近服务搜索）
- 总计：5-13秒

### 测试API限制
- Nominatim：1请求/秒（已实现1.2秒间隔）
- OSRM：无严格限制
- Azure OpenAI：根据订阅计划

## 验收标准

### 必须通过的测试
1. ✅ 核心任务正确生成并标记为 `task_type="core"`
2. ✅ 扩展任务正确生成并标记为 `task_type="extended"`
3. ✅ 扩展任务显示推荐理由
4. ✅ 前端正确显示⭐和💡图标
5. ✅ 推荐理由卡片样式正确
6. ✅ 地理位置信息正确
7. ✅ 路线优化正常工作

### 可选的增强测试
1. 🔄 不同用户画像生成不同的扩展任务
2. 🔄 评分系统正确工作
3. 🔄 任务按距离排序
4. 🔄 每个核心任务最多2个扩展任务

## 测试报告模板

```markdown
## 测试报告

**测试日期：** 2024-11-05
**测试人员：** [Your Name]
**测试环境：** Manus Sandbox

### 测试场景1：基础核心任务生成
- 状态：✅ 通过 / ❌ 失败
- 备注：[描述]

### 测试场景2：扩展任务生成（单身专业人士）
- 状态：✅ 通过 / ❌ 失败
- 备注：[描述]

### 测试场景3：扩展任务生成（有孩子的家庭）
- 状态：✅ 通过 / ❌ 失败
- 备注：[描述]

### 发现的问题
1. [问题描述]
2. [问题描述]

### 建议改进
1. [改进建议]
2. [改进建议]
```

## 下一步

测试通过后，可以考虑：
1. 部署到生产环境
2. 集成Overpass API进行更精确的POI搜索
3. 添加用户反馈机制
4. 实现扩展任务的接受/拒绝功能
5. 增加更多服务类型
