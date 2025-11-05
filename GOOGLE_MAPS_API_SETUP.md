# Google Maps API 设置指南

本文档介绍如何为香港移民助手应用设置Google Maps API服务。

## 概述

香港移民助手应用现在使用Google Maps API替换了所有之前的地图服务：

- **Overpass API** → **Google Places API (New)**
- **OSRM (Open Source Routing Machine)** → **Google Directions API & Distance Matrix API**
- **Nominatim (OpenStreetMap)** → **Google Geocoding API**

## 所需API服务

您需要在Google Cloud Console中启用以下API服务：

### 1. Places API (New)
- **API ID**: `places.googleapis.com`
- **用途**: 搜索附近的地点和服务（如超市、药店、银行等）
- **配额**: 每月6,000次免费请求

### 2. Directions API
- **API ID**: `directions-backend.googleapis.com`
- **用途**: 计算两点之间的路线和导航指示
- **配额**: 每月2,500次免费请求

### 3. Distance Matrix API
- **API ID**: `distancematrix.googleapis.com`
- **用途**: 计算多点之间的距离和时间矩阵，用于路线优化
- **配额**: 每月1,000次免费请求

### 4. Geocoding API
- **API ID**: `geocoding-backend.googleapis.com`
- **用途**: 将地址转换为坐标，反之亦然
- **配额**: 每月40,000次免费请求

## 设置步骤

### 步骤1: 创建Google Cloud项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 为项目启用结算功能（即使使用免费配额也需要）

### 步骤2: 启用API服务

1. 在Cloud Console中，转到"APIs & Services" > "Library"
2. 搜索并启用以下API：
   - Places API (New)
   - Directions API
   - Distance Matrix API
   - Geocoding API

### 步骤3: 创建API密钥

1. 转到"APIs & Services" > "Credentials"
2. 点击"Create credentials" > "API key"
3. 复制生成的API密钥

### 步骤4: 配置应用程序

在应用程序的`.env`文件中设置API密钥：

```bash
GOOGLE_MAPS_API_KEY=your_api_key_here
```

### 步骤5: 限制API密钥（推荐用于生产环境）

1. 在"APIs & Services" > "Credentials"中选择您的API密钥
2. 添加以下限制：
   - **应用程序限制**: 选择"HTTP referrers"并添加您的域名
   - **API限制**: 选择"Restrict key"并只选择上面提到的4个API

## 配额和定价

### 免费配额
- **Places API**: 6,000次/月
- **Directions API**: 2,500次/月
- **Distance Matrix API**: 1,000次/月
- **Geocoding API**: 40,000次/月

### 超出免费配额的定价
- Places API: $32/1,000次额外请求
- Directions API: $5/1,000次额外请求
- Distance Matrix API: $5/1,000次额外请求
- Geocoding API: $5/1,000次额外请求

## 故障排除

### 常见错误

#### 1. REQUEST_DENIED
```
Error: Places API error: REQUEST_DENIED
```
**原因**: API密钥无效或未启用Places API
**解决**: 检查API密钥是否正确，以及Places API是否已启用

#### 2. OVER_QUERY_LIMIT
```
Error: Google Places API error: OVER_QUERY_LIMIT
```
**原因**: 超出API配额限制
**解决**: 等待下个月重置，或升级到付费计划

#### 3. ZERO_RESULTS
```
Error: Google Geocoding API error: ZERO_RESULTS
```
**原因**: 无法找到指定的地址
**解决**: 检查地址格式，尝试更具体的地址

#### 4. INVALID_REQUEST
```
Error: Google Directions API error: INVALID_REQUEST
```
**原因**: 请求参数无效
**解决**: 检查坐标格式和旅行模式参数

### 调试技巧

1. **启用API日志**: 在Cloud Console中查看API请求日志
2. **测试API密钥**: 使用以下URL测试API密钥：
   ```
   https://maps.googleapis.com/maps/api/geocode/json?address=Hong+Kong&key=YOUR_API_KEY
   ```
3. **检查配额使用**: 在Cloud Console的"APIs & Services" > "Dashboard"中查看使用情况

## 开发环境设置

对于开发环境，如果您不想设置真实的Google Maps API，可以：

1. 保持API密钥为空（应用程序会使用预定义的模拟数据）
2. 或者设置一个无效的API密钥（应用程序会自动回退到模拟数据）

## 生产环境注意事项

1. **安全**: 始终使用受限的API密钥
2. **监控**: 设置配额警报以避免意外费用
3. **缓存**: 应用程序已实现缓存以减少API调用
4. **错误处理**: 应用程序包含完善的错误处理和回退机制

## 支持

如果您在设置过程中遇到问题，请：

1. 检查Google Cloud Console中的错误消息
2. 验证API密钥和配额
3. 查看应用程序日志中的详细错误信息
4. 参考Google Maps API官方文档：https://developers.google.com/maps
