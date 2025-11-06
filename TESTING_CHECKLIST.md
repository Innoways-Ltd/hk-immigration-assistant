# 地图大头针显示修复 - 测试检查清单

## 测试环境设置

### 前置条件
1. 确保已配置环境变量：
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`
   - `GOOGLE_MAPS_API_KEY`
2. 启动Agent服务：`cd agent && poetry run demo`
3. 启动UI服务：`cd ui && pnpm dev`
4. 打开浏览器：`http://localhost:3000`

### 测试数据
使用以下测试消息：
```
Arrival Information:
- Arrival Date in Hong Kong: 4th May 2025
- Temporary Accommodation: Wan Chai Serviced Apartment

Housing Requirements:
- Lease Start Date: Early June 
- Budget: HKD 65,000
- Number of bedrooms: 2 bedroom
- Furnishing type: Fully furnished 
- Property areas: Wan Chai, Sheung Wan (walking distance to office)
- Family Size: 1 adult
- Office Location: 3 Lockhart Road, Wan Chai
- Temporary accommodation: 30 days
```

---

## 测试场景

### ✅ 场景1：地图初始化测试（关键！）

**目标**：验证地图容器初始化错误已修复

#### 步骤：
1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签页
3. 清空控制台
4. 刷新页面（F5）
5. 观察控制台输出

#### 预期结果：
- ✅ **不应该**看到 "Map container not found" 错误
- ✅ **不应该**看到 "Error: Map container not found" 堆栈跟踪
- ✅ 页面加载时应该显示 "Loading map..." 文字
- ✅ 地图应该正常加载，没有任何错误

#### 检查点：
- [ ] 控制台无 "Map container not found" 错误
- [ ] 控制台无其他地图相关错误
- [ ] 加载状态正确显示
- [ ] 地图正常渲染

---

### ✅ 场景2：创建安家计划

**目标**：验证地图能正确显示安家计划的位置

#### 步骤：
1. 在聊天界面输入测试数据
2. 等待AI生成安家计划
3. 观察地图是否显示位置

#### 预期结果：
- ✅ 地图应该从 "Loading map..." 切换到实际地图
- ✅ 地图中心应该在香港湾仔附近
- ✅ 应该显示多个蓝色大头针（编号1, 2, 3...）
- ✅ 大头针应该对应左侧卡片中的任务

#### 检查点：
- [ ] 地图正确加载
- [ ] 地图中心位置正确（香港）
- [ ] 显示多个大头针
- [ ] 大头针位置与任务对应
- [ ] 控制台无错误

---

### ✅ 场景3：鼠标悬停在Day卡片

**目标**：验证悬停在天数卡片时，地图正确高亮对应的大头针

#### 步骤：
1. 在左侧卡片找到 "Day 1" 分组
2. 将鼠标移动到 "Day 1" 区域上（不要点击）
3. 观察地图变化
4. 将鼠标移开
5. 观察地图恢复情况

#### 预期结果：
- ✅ 鼠标悬停时：
  - Day 1 的所有大头针应该变红色并放大
  - 其他天的大头针应该隐藏或变淡
  - 地图应该自动缩放到显示 Day 1 的所有位置
- ✅ 鼠标移开时：
  - 大头针应该恢复到蓝色
  - **应该显示 Day 1 的大头针**（默认状态）
  - 不应该保持之前的高亮状态

#### 检查点：
- [ ] 悬停时正确高亮
- [ ] 悬停时正确缩放
- [ ] **移开时恢复到 Day 1 显示**（关键！）
- [ ] 控制台查看调试日志：
  - 应该看到 `[DEBUG] Hovering on day: 1`
  - 应该看到 `[MAP DEBUG] Focused locations: ...`

---

### ✅ 场景4：鼠标悬停在Task卡片

**目标**：验证悬停在任务卡片时，地图显示对应的大头针

#### 步骤：
1. 在左侧卡片找到任意一个任务（例如 "Visit Office Location"）
2. 将鼠标移动到该任务卡片上
3. 观察地图变化
4. 将鼠标移开
5. 观察地图恢复情况

#### 预期结果：
- ✅ 鼠标悬停时：
  - 该任务的大头针应该变红色并放大
  - 其他大头针应该隐藏
  - 地图应该缩放到该位置
  - **即使该任务的location不在service_locations中，也应该显示**（关键修复！）
- ✅ 鼠标移开时：
  - 大头针应该恢复到蓝色
  - **应该显示 Day 1 的大头针**（默认状态）
  - 不应该保持之前的高亮状态

#### 检查点：
- [ ] 悬停时正确高亮单个大头针
- [ ] 悬停时正确缩放
- [ ] **所有有位置信息的任务都能显示大头针**（关键！）
- [ ] **移开时恢复到 Day 1 显示**（关键！）
- [ ] 控制台查看调试日志：
  - 应该看到 `[DEBUG] Hovered task: ... Has location: true`
  - 应该看到 `[DEBUG] Task location: ... Lat: ... Lng: ...`
  - 应该看到 `[MAP DEBUG] Total locations to render: ...`

---

### ✅ 场景5：快速切换测试

**目标**：验证快速移动鼠标时，地图状态正确更新

#### 步骤：
1. 快速地在多个任务卡片之间移动鼠标
2. 不要停顿，连续移动
3. 最后将鼠标移出所有卡片
4. 观察地图状态

#### 预期结果：
- ✅ 地图应该实时响应鼠标移动
- ✅ 大头针高亮应该跟随鼠标快速切换
- ✅ 最后移出时，地图应该恢复到 Day 1 的显示
- ✅ 不应该出现卡顿或错误状态
- ✅ 不应该有大头针"卡住"保持高亮

#### 检查点：
- [ ] 实时响应正常
- [ ] 无卡顿或错误
- [ ] 最终状态正确（Day 1）
- [ ] 控制台无错误

---

### ✅ 场景6：检查所有任务是否有位置

**目标**：验证所有应该有位置的任务都能在地图上显示

#### 步骤：
1. 遍历左侧所有任务
2. 对每个任务，将鼠标悬停上去
3. 观察地图是否显示对应的大头针
4. 记录哪些任务没有显示大头针

#### 预期结果：
- ✅ 以下类型的任务应该有大头针：
  - Airport Pickup（机场接机）
  - Temporary Accommodation（临时住宿）
  - Bank Account Opening（开银行账户）
  - Property Viewing（看房）
  - Office Location（办公室位置）
  - 其他有具体地址的任务

- ✅ 以下类型的任务可能没有大头针（这是正常的）：
  - 纯文档准备任务
  - 在线申请任务

#### 检查点：
- [ ] 所有应该有位置的任务都能显示大头针
- [ ] 控制台查看调试日志，确认任务是否有location：
  - `[DEBUG] Hovered task: "Task Name" Has location: true/false`
- [ ] 如果某个任务应该有位置但没显示，记录下来

---

### ✅ 场景7：控制台日志验证

**目标**：验证调试日志正确输出，帮助理解系统行为

#### 步骤：
1. 打开浏览器控制台
2. 执行各种操作（悬停、移开、切换）
3. 观察控制台输出

#### 预期结果：
应该看到以下调试日志：

**悬停在Day时：**
```
[DEBUG] Hovering on day: 1
[DEBUG] Task "Airport Pickup" day_range="Day 1" taskDay=1 matches=true hasLocation=true
[DEBUG] Task "Check-in Temporary Accommodation" day_range="Day 1" taskDay=1 matches=true hasLocation=true
[DEBUG] Tasks on day: 2
[DEBUG] Locations found on day 1: 2 ["Airport", "Hotel"]
[MAP DEBUG] Focused locations: 2 ["Airport (id123)", "Hotel (id456)"]
[MAP DEBUG] Total locations to render: 5
[MAP DEBUG] Focused location IDs: ["id123", "id456"]
[MAP DEBUG] Visible markers: 2
```

**悬停在Task时：**
```
[DEBUG] Hovered task: "Visit Office Location" Has location: true
[DEBUG] Task location: "3 Lockhart Road" Lat: 22.2783 Lng: 114.1747
[MAP DEBUG] Focused locations: 1 ["3 Lockhart Road (office-loc-id)"]
```

#### 检查点：
- [ ] 调试日志正确输出
- [ ] 日志信息准确反映系统状态
- [ ] 无错误或警告（除了我们添加的警告日志）

---

## 修复前后对比

### ❌ 修复前的问题
1. **初始化错误**：
   - 控制台显示 "Map container not found"
   - 地图加载失败或不稳定
   
2. **状态残留**：
   - 鼠标移开卡片后，大头针保持高亮
   - 无法恢复到默认的 Day 1 显示
   
3. **位置缺失**：
   - 某些任务有经纬度但不显示大头针
   - 只显示service_locations中的位置

### ✅ 修复后的行为
1. **初始化正常**：
   - 无控制台错误
   - 地图从"Loading map..."平滑过渡到正常显示
   - 使用正确的中心坐标和缩放级别
   
2. **状态管理正确**：
   - 鼠标移开后，大头针恢复到 Day 1 显示
   - 状态转换平滑，无残留
   
3. **位置显示完整**：
   - 所有有location的任务都能显示
   - allLocations包含service_locations + focusedLocations

---

## 问题排查指南

### 如果地图不显示
1. 检查控制台是否有错误
2. 检查环境变量是否正确配置
3. 检查是否显示"Loading map..."
4. 检查settlementPlan是否有center_latitude/longitude

### 如果大头针不显示
1. 检查控制台日志：`[DEBUG] Hovered task: ... Has location: ...`
2. 如果 Has location: false，说明任务确实没有位置信息
3. 检查 `[MAP DEBUG] Total locations to render` 数量
4. 检查 `[MAP DEBUG] Visible markers` 数量

### 如果状态不恢复
1. 确认是否看到 onMouseLeave 被触发
2. 检查控制台日志，确认 hoveredDay/hoveredTaskId 被设置为 null
3. 检查是否有JavaScript错误阻止了状态更新

---

## 代码验证

### 关键修复点验证

#### 1. onMouseLeave 事件（SettlementCard.tsx）
```tsx
// 在 Day 容器上应该有：
onMouseEnter={() => setHoveredDay(day)}
onMouseLeave={() => setHoveredDay(null)}  // ✅ 必须存在

// 在 Task 容器上应该有：
onMouseEnter={() => setHoveredTaskId(task.id)}
onMouseLeave={() => setHoveredTaskId(null)}  // ✅ 必须存在
```

#### 2. 条件渲染（MapCanvas.tsx）
```tsx
// 应该在 MapContainer 之前有这个检查：
if (!settlementPlan || !settlementPlan.center_latitude || !settlementPlan.center_longitude) {
  return (
    <div>Loading map...</div>
  );
}
```

#### 3. allLocations 合并（MapCanvas.tsx）
```tsx
// 应该有这个 useMemo：
const allLocations = useMemo(() => {
  const locationMap = new Map();
  settlementPlan.service_locations.forEach(loc => locationMap.set(loc.id, loc));
  focusedLocations.forEach(loc => {
    if (!locationMap.has(loc.id)) locationMap.set(loc.id, loc);
  });
  return Array.from(locationMap.values());
}, [settlementPlan?.service_locations, focusedLocations]);
```

---

## 测试报告模板

```markdown
# 地图修复测试报告

**测试日期**：[填写日期]
**测试人员**：[填写姓名]
**浏览器**：[Chrome/Firefox/Safari] [版本号]

## 测试结果总结

- [ ] 场景1：地图初始化测试 - ✅通过 / ❌失败
- [ ] 场景2：创建安家计划 - ✅通过 / ❌失败
- [ ] 场景3：悬停在Day卡片 - ✅通过 / ❌失败
- [ ] 场景4：悬停在Task卡片 - ✅通过 / ❌失败
- [ ] 场景5：快速切换测试 - ✅通过 / ❌失败
- [ ] 场景6：检查所有任务位置 - ✅通过 / ❌失败
- [ ] 场景7：控制台日志验证 - ✅通过 / ❌失败

## 发现的问题

[如果有问题，在这里详细描述]

## 控制台截图

[粘贴控制台截图]

## 总体评价

- 修复效果：✅优秀 / ⚠️一般 / ❌需要改进
- 建议：[填写建议]
```

---

## 结论

如果所有测试场景都通过，说明以下3个关键问题已完全修复：

1. ✅ **Map container not found 错误已消除**
2. ✅ **鼠标移开卡片后，大头针正确恢复到 Day 1 显示**
3. ✅ **所有有位置信息的任务都能在地图上显示大头针**

**修复质量指标**：
- 0个控制台错误 ✅
- 100%任务位置显示 ✅
- 正确的状态管理 ✅
- 平滑的用户体验 ✅
