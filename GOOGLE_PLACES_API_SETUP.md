# Google Places API (New) 设置指南

## 问题说明

当前系统遇到以下错误：
```
googlemaps.exceptions.ApiError: REQUEST_DENIED (You’re calling a legacy API, which is not enabled for your project. To get newer features and more functionality, switch to the Places API (New) or Routes API. Learn more: https://developers.google.com/maps/legacy#LegacyApiNotActivatedMapError)
```

## 解决方案

### 1. 启用 Google Places API (New)

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 选择你的项目 (项目ID: `382538074521`)
3. 导航到 "APIs & Services" > "Library"
4. 搜索 "Places API (New)"
5. 点击 "Enable" 启用该API

### 2. 验证API密钥权限

确保你的API密钥有以下权限：
- Places API (New)
- Geocoding API (可选，用于地址解析)

### 3. 等待生效

API启用后可能需要几分钟到24小时才能在全球生效。

## 当前临时解决方案

系统已实现智能fallback机制：

### ✅ 已实现的功能
- **自动检测API状态**：检测403错误并自动fallback
- **Mock数据支持**：提供香港主要区域的预定义POI数据
- **无缝切换**：API可用时使用真实数据，不可用时使用mock数据

### 📊 支持的POI类型
- 🏦 **银行**: Hang Seng Bank, HSBC, Bank of China
- 🛒 **超市**: Wellcome, ParknShop
- ☕ **咖啡店**: Starbucks, Pacific Coffee
- 🍽️ **餐厅**: Din Tai Fung, Yung Kee
- 🏢 **公寓**: Pacific Place, The Harbourview

### 🔧 测试验证

```bash
# 在项目根目录运行
docker-compose exec agent python -c "
from immigration.search import test_google_places_api
test_google_places_api()
"
```

## 启用API后的优势

启用Google Places API (New)后，你将获得：

- ✅ **实时准确数据**：最新的POI信息和评分
- ✅ **完整地址信息**：精确的地理坐标和地址
- ✅ **丰富元数据**：营业时间、联系方式等
- ✅ **全球覆盖**：不仅仅是香港地区

## 故障排除

### 如果仍然遇到403错误：
1. 检查API密钥是否正确
2. 确认Places API (New)已启用
3. 检查API配额是否充足
4. 等待24小时让更改生效

### 如果遇到其他错误：
- 系统会自动fallback到mock数据
- 查看容器日志了解详细错误信息

## 开发环境说明

在开发环境中，即使没有启用Google Places API，系统也能正常工作：
- 搜索功能使用mock数据
- 所有UI组件正常显示
- 用户体验不受影响

## 生产环境建议

在生产环境中，强烈建议启用Google Places API (New)以提供最佳用户体验。
