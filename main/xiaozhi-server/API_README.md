# 广播消息API文档

## 概述

小智服务端现在提供了HTTP API接口，可以通过POST请求向连接的设备广播语音消息，无需登录认证。

## 接口地址

- **服务器默认端口**: 8003
- **广播消息接口**: `POST /api/broadcast`
- **服务器状态接口**: `GET /api/status`

## 接口详情

### 1. 广播消息接口

**接口地址**: `POST /api/broadcast`

**请求方式**: POST

**Content-Type**: `application/json` 或 `application/x-www-form-urlencoded`

**请求参数**:

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| text | string | 是 | 要广播的消息内容 |
| device_id | string | 否 | 指定设备ID，不提供则广播到所有设备 |

**JSON格式示例**:
```json
{
  "text": "现在是下午三点，请注意休息",
  "device_id": "可选的设备ID"
}
```

**表单格式示例**:
```
text=现在是下午三点，请注意休息
device_id=可选的设备ID
```

**响应格式**:

成功响应:
```json
{
  "status": "success",
  "message": "消息已广播到 2 个设备",
  "data": {
    "text": "现在是下午三点，请注意休息",
    "sent_count": 2,
    "total_connections": 3
  }
}
```

错误响应:
```json
{
  "status": "error",
  "message": "消息内容不能为空"
}
```

### 2. 服务器状态接口

**接口地址**: `GET /api/status`

**请求方式**: GET

**响应格式**:
```json
{
  "status": "success",
  "data": {
    "active_connections": 2,
    "devices": [
      {
        "device_id": "ESP32_001",
        "client_ip": "192.168.1.100",
        "session_id": "abc123"
      },
      {
        "device_id": "ESP32_002", 
        "client_ip": "192.168.1.101",
        "session_id": "def456"
      }
    ],
    "server_time": 1640995200.123
  }
}
```

## 使用示例

### 使用curl命令

1. **广播消息到所有设备**:
```bash
curl -X POST http://localhost:8003/api/broadcast \
  -H "Content-Type: application/json" \
  -d '{"text": "大家好，这是系统广播"}'
```

2. **发送消息到指定设备**:
```bash
curl -X POST http://localhost:8003/api/broadcast \
  -H "Content-Type: application/json" \
  -d '{"text": "您好，设备001", "device_id": "ESP32_001"}'
```

3. **使用表单数据**:
```bash
curl -X POST http://localhost:8003/api/broadcast \
  -d "text=这是表单格式的消息"
```

4. **获取服务器状态**:
```bash
curl -X GET http://localhost:8003/api/status
```

### 使用Python requests

```python
import requests

# 广播消息
response = requests.post(
    'http://localhost:8003/api/broadcast',
    json={'text': '现在是下午三点，请注意休息'}
)
print(response.json())

# 获取状态
status = requests.get('http://localhost:8003/api/status')
print(status.json())
```

### 使用JavaScript fetch

```javascript
// 广播消息
fetch('http://localhost:8003/api/broadcast', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: '现在是下午三点，请注意休息'
  })
})
.then(response => response.json())
.then(data => console.log(data));

// 获取状态
fetch('http://localhost:8003/api/status')
.then(response => response.json())
.then(data => console.log(data));
```

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误（如消息内容为空） |
| 404 | 指定的设备未找到 |
| 500 | 服务器内部错误 |

## 注意事项

1. **无需认证**: 该接口免登录，可直接调用
2. **消息内容**: 支持中文，会通过TTS转换为语音播报
3. **设备连接**: 只有连接到WebSocket的设备才能接收消息
4. **并发性**: 支持多个客户端同时调用
5. **CORS**: 支持跨域请求

## 应用场景

- 智能家居系统的语音通知
- 办公室广播系统
- 定时提醒服务
- 紧急通知广播
- 多媒体展示系统的语音导览

## 故障排除

1. **连接失败**: 检查服务器是否正在运行，端口是否正确
2. **无设备响应**: 检查设备是否已连接到WebSocket服务器
3. **消息不播报**: 检查设备的TTS配置是否正确
4. **CORS错误**: 接口已支持跨域，如仍有问题请检查浏览器设置
