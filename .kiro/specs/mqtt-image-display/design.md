# Design Document - MQTT Image Display

## Overview

本设计文档描述了ESP32 MicroPython墨水屏项目的MQTT图片显示功能（RUN_MODE = 4）的技术实现方案。该功能通过MQTT协议实现设备与服务器之间的实时通信，支持服务器主动推送图片更新指令，设备接收指令后下载并显示二进制图片数据。

系统采用事件驱动架构，通过MQTT订阅/发布模式实现低延迟的内容更新。设备启动时通过HTTP REST API获取初始配置（bootstrap），然后建立MQTT长连接等待服务器推送更新。

## Architecture

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        ESP32 Device                          │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   boot.py    │───▶│mqtt_display  │───▶│  epaper4in2  │  │
│  │  (RUN_MODE=4)│    │    .py       │    │   driver     │  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘  │
│                              │                                │
│                              ▼                                │
│                      ┌──────────────┐                        │
│                      │  wifi.py     │                        │
│                      │  (WiFi Mgr)  │                        │
│                      └──────────────┘                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ WiFi
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                      Backend Server                           │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  FastAPI     │    │  MQTT Broker │    │  PostgreSQL  │  │
│  │  REST API    │    │  (Paho-MQTT) │    │   Database   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │           │
│         └────────────────────┴────────────────────┘           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 通信流程

1. **启动阶段**：
   - 设备连接WiFi
   - 调用HTTP GET `/api/devices/{device_id}/bootstrap` 获取当前版本
   - 建立MQTT连接到broker
   - 订阅主题 `devices/{device_id}/updates`

2. **等待更新阶段**：
   - 设备保持MQTT连接，等待消息
   - 定期发送心跳保持连接活跃

3. **接收更新阶段**：
   - 服务器通过MQTT推送更新消息
   - 消息包含新版本号和其他元数据
   - 设备解析消息并触发下载流程

4. **下载显示阶段**：
   - 设备通过HTTP GET `/api/devices/{device_id}/content/{version}` 下载图片
   - 验证图片数据大小（15000字节）
   - 加载到帧缓冲区并显示
   - 更新本地版本号

## Components and Interfaces

### 1. MQTTDisplayApp 类

主应用类，负责协调所有组件和管理应用生命周期。

```python
class MQTTDisplayApp:
    def __init__(self):
        """初始化应用组件"""
        # 初始化墨水屏驱动
        # 初始化WiFi管理器
        # 初始化MQTT客户端
        # 创建帧缓冲区
        
    def run(self):
        """主运行循环"""
        # 1. 连接WiFi
        # 2. Bootstrap获取初始版本
        # 3. 连接MQTT
        # 4. 进入消息循环
        
    def connect_wifi(self) -> bool:
        """连接WiFi网络"""
        
    def bootstrap(self) -> dict:
        """从服务器获取初始配置"""
        
    def connect_mqtt(self) -> bool:
        """连接MQTT服务器"""
        
    def on_message(self, topic, msg):
        """MQTT消息回调"""
        
    def download_image(self, version: str) -> bytearray:
        """下载指定版本的图片数据"""
        
    def display_image(self, image_data: bytearray):
        """在墨水屏上显示图片"""
        
    def display_status(self, message: str):
        """在墨水屏上显示状态信息"""
        
    def handle_error(self, error: Exception):
        """处理错误并显示错误信息"""
```

### 2. MQTT客户端接口

使用MicroPython的`umqtt.simple`或`umqtt.robust`库。

```python
from umqtt.simple import MQTTClient

# 创建MQTT客户端
client = MQTTClient(
    client_id=device_id,
    server=mqtt_server,
    port=mqtt_port,
    user=mqtt_user,
    password=mqtt_password
)

# 设置回调
client.set_callback(on_message_callback)

# 连接
client.connect()

# 订阅主题
client.subscribe(topic)

# 检查消息（非阻塞）
client.check_msg()

# 等待消息（阻塞）
client.wait_msg()
```

### 3. HTTP客户端接口

使用MicroPython的`urequests`库。

```python
import urequests

# Bootstrap API
response = urequests.get(
    f"{api_base_url}/api/devices/{device_id}/bootstrap"
)
data = response.json()
current_version = data['current_version']

# 下载图片
response = urequests.get(
    f"{api_base_url}/api/devices/{device_id}/content/{version}"
)
image_data = response.content
```

### 4. 配置管理

在`config.py`中添加MQTT和设备相关配置：

```python
# 设备配置
DEVICE_ID = None  # 如果为None，则使用MAC地址生成

# API服务器配置
API_SERVER = "http://192.168.1.100:9999"

# MQTT配置
MQTT_SERVER = "192.168.1.100"
MQTT_PORT = 1883
MQTT_USER = None  # 可选
MQTT_PASSWORD = None  # 可选
MQTT_KEEPALIVE = 60  # 秒
```

## Data Models

### 1. Bootstrap响应

```json
{
  "device_id": "esp32_aabbccddeeff",
  "current_version": "v1.0.0",
  "mqtt_config": {
    "server": "192.168.1.100",
    "port": 1883,
    "topic": "devices/esp32_aabbccddeeff/updates"
  }
}
```

### 2. MQTT更新消息

```json
{
  "type": "update",
  "version": "v1.0.1",
  "timestamp": "2025-11-26T10:30:00Z",
  "force": false
}
```

### 3. 图片数据格式

- 格式：原始二进制数据
- 大小：15000字节（400 × 300 ÷ 8）
- 编码：MONO_HMSB（每个字节代表8个像素，高位在前）
- 颜色：0=黑色，1=白色

### 4. 设备状态

```python
class DeviceState:
    INITIALIZING = "initializing"
    CONNECTING_WIFI = "connecting_wifi"
    BOOTSTRAPPING = "bootstrapping"
    CONNECTING_MQTT = "connecting_mqtt"
    READY = "ready"
    DOWNLOADING = "downloading"
    DISPLAYING = "displaying"
    ERROR = "error"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Configuration parameters are used correctly
*For any* valid MQTT server address and port in config.py, the device should use these exact values when establishing the MQTT connection
**Validates: Requirements 1.4**

### Property 2: Version storage consistency
*For any* valid version string returned by the bootstrap API, the device should store it in a local variable and be able to retrieve the same value
**Validates: Requirements 2.2**

### Property 3: Version display consistency
*For any* version string retrieved from bootstrap or after image display, the device should display it on the e-ink screen
**Validates: Requirements 2.4**

### Property 4: MQTT message parsing robustness
*For any* valid MQTT message with proper JSON structure, the device should successfully parse it and extract the message type
**Validates: Requirements 3.2**

### Property 5: Invalid message handling
*For any* invalid or malformed MQTT message, the device should log an error but continue running without crashing
**Validates: Requirements 3.4**

### Property 6: MQTT topic construction
*For any* valid device_id string, the device should construct the MQTT subscription topic as "devices/{device_id}/updates"
**Validates: Requirements 3.5**

### Property 7: API endpoint construction
*For any* valid device_id and version string, the device should construct the download URL as "{api_base}/api/devices/{device_id}/content/{version}"
**Validates: Requirements 4.2**

### Property 8: Image data size validation
*For any* downloaded binary data, the device should verify that its size equals exactly 15000 bytes before attempting to display it
**Validates: Requirements 4.3**

### Property 9: Invalid image data rejection
*For any* binary data with size not equal to 15000 bytes, the device should reject it and not attempt to display it
**Validates: Requirements 4.4**

### Property 10: Image data loading
*For any* valid 15000-byte binary image data, the device should successfully load it into the frame buffer
**Validates: Requirements 5.1**

### Property 11: Version update after display
*For any* version string associated with successfully displayed image, the device should update its local current_version variable to that value
**Validates: Requirements 5.5**

### Property 12: Exception recovery
*For any* caught exception during operation, the device should display an error message and attempt to continue running rather than crashing
**Validates: Requirements 6.5**

### Property 13: Configuration reading
*For any* valid config.py file with MQTT parameters, the device should successfully read and use those parameters
**Validates: Requirements 7.1**

### Property 14: Default value handling
*For any* missing configuration parameter, the device should use a reasonable default value and continue operation
**Validates: Requirements 7.2**

### Property 15: API URL construction from config
*For any* valid API server address in config, the device should construct complete API endpoint URLs using that base address
**Validates: Requirements 7.4**

### Property 16: Error message display
*For any* error that occurs during operation, the device should display an error message on the e-ink screen that includes the error type
**Validates: Requirements 8.5**

## Error Handling

### Error Categories

1. **Network Errors**
   - WiFi connection failure
   - MQTT connection failure
   - HTTP request timeout
   - Network disconnection during operation

2. **Data Errors**
   - Invalid JSON in MQTT message
   - Invalid image data size
   - Corrupted image data
   - Missing required fields in API response

3. **Resource Errors**
   - Memory allocation failure
   - Frame buffer creation failure
   - E-ink display initialization failure

4. **Configuration Errors**
   - Missing configuration file
   - Invalid configuration format
   - Missing required configuration parameters

### Error Handling Strategy

```python
class ErrorHandler:
    def __init__(self, display_app):
        self.display_app = display_app
        self.error_count = {}
        self.max_retries = 3
        
    def handle_error(self, error_type: str, error: Exception, retry_func=None):
        """统一错误处理"""
        # 记录错误
        print(f"Error [{error_type}]: {str(error)}")
        
        # 更新错误计数
        if error_type not in self.error_count:
            self.error_count[error_type] = 0
        self.error_count[error_type] += 1
        
        # 显示错误信息
        self.display_app.display_status(f"Error: {error_type}")
        
        # 决定是否重试
        if retry_func and self.error_count[error_type] < self.max_retries:
            print(f"Retrying... (attempt {self.error_count[error_type] + 1})")
            return retry_func()
        elif self.error_count[error_type] >= self.max_retries:
            print(f"Max retries reached for {error_type}")
            self.display_app.display_status(f"Fatal: {error_type}")
            return None
        
        return None
```

### 错误恢复机制

1. **WiFi断开恢复**：
   - 检测到WiFi断开后，等待5秒
   - 尝试重新连接，最多3次
   - 如果失败，显示持久错误信息

2. **MQTT断开恢复**：
   - 检测到MQTT断开后，等待3秒
   - 尝试重新连接，最多3次
   - 如果失败，尝试重新建立WiFi连接

3. **下载失败恢复**：
   - HTTP请求超时设置为30秒
   - 下载失败后，保持当前显示内容
   - 等待下一次MQTT更新消息

4. **内存不足处理**：
   - 捕获内存分配异常
   - 尝试垃圾回收：`gc.collect()`
   - 如果仍然失败，跳过本次更新

## Testing Strategy

### Unit Testing

由于MicroPython环境的限制，单元测试将在开发机器上使用标准Python进行模拟测试：

1. **配置解析测试**：
   - 测试从config.py读取各种配置参数
   - 测试缺失参数时的默认值处理
   - 测试无效配置的错误处理

2. **URL构建测试**：
   - 测试MQTT主题构建逻辑
   - 测试API端点URL构建逻辑
   - 测试各种device_id和version的组合

3. **消息解析测试**：
   - 测试有效MQTT消息的解析
   - 测试无效JSON的错误处理
   - 测试缺失字段的处理

4. **数据验证测试**：
   - 测试15000字节图片数据的验证通过
   - 测试其他大小数据的验证失败
   - 测试空数据的处理

### Property-Based Testing

使用Hypothesis库（在开发环境）进行属性测试：

**测试库**：Hypothesis (Python)

**配置**：每个属性测试运行最少100次迭代

**标记格式**：每个属性测试必须使用注释标记对应的设计文档属性
- 格式：`# Feature: mqtt-image-display, Property {number}: {property_text}`

**属性测试用例**：

1. **Property 1测试**：配置参数使用正确性
   - 生成随机的服务器地址和端口
   - 验证MQTT客户端使用这些参数

2. **Property 6测试**：MQTT主题构建
   - 生成随机的device_id字符串
   - 验证构建的主题格式正确

3. **Property 7测试**：API端点构建
   - 生成随机的device_id和version
   - 验证构建的URL格式正确

4. **Property 8测试**：图片数据大小验证
   - 生成各种大小的二进制数据
   - 验证只有15000字节的数据通过验证

5. **Property 9测试**：无效图片数据拒绝
   - 生成非15000字节的二进制数据
   - 验证数据被正确拒绝

6. **Property 12测试**：异常恢复
   - 模拟各种异常情况
   - 验证系统不会崩溃并能继续运行

### Integration Testing

在实际ESP32硬件上进行集成测试：

1. **完整流程测试**：
   - 启动设备 → WiFi连接 → Bootstrap → MQTT连接 → 接收消息 → 下载图片 → 显示图片

2. **网络断开恢复测试**：
   - 在运行过程中断开WiFi
   - 验证设备能够自动重连

3. **服务器不可用测试**：
   - 关闭MQTT broker
   - 验证设备的错误处理和重连逻辑

4. **多次更新测试**：
   - 连续推送多个版本的图片
   - 验证设备能够正确处理每次更新

### Manual Testing

1. **显示质量测试**：
   - 验证图片显示清晰，无残影
   - 验证全局刷新和局部刷新的效果

2. **状态信息测试**：
   - 验证各个阶段的状态信息显示正确
   - 验证错误信息显示清晰易懂

3. **长时间运行测试**：
   - 设备连续运行24小时
   - 验证内存泄漏和稳定性

## Implementation Notes

### 1. MQTT库选择

MicroPython有两个MQTT库选项：
- `umqtt.simple`：简单实现，适合基本使用
- `umqtt.robust`：增强版本，包含自动重连功能

**推荐使用`umqtt.robust`**，因为它提供了更好的错误处理和自动重连功能。

### 2. 内存管理

ESP32的内存有限，需要注意：
- 及时释放不再使用的对象
- 在分配大内存前调用`gc.collect()`
- 避免创建过多的临时对象
- 重用帧缓冲区，不要每次都重新创建

### 3. 非阻塞设计

为了保持系统响应性：
- 使用`client.check_msg()`而不是`client.wait_msg()`
- 在主循环中定期检查消息
- 下载大文件时显示进度信息
- 避免长时间阻塞操作

### 4. 设备ID生成

如果config中未配置DEVICE_ID，使用MAC地址生成：

```python
import network
import ubinascii

def get_device_id():
    if hasattr(config, 'DEVICE_ID') and config.DEVICE_ID:
        return config.DEVICE_ID
    
    # 使用MAC地址生成设备ID
    wlan = network.WLAN(network.STA_IF)
    mac = ubinascii.hexlify(wlan.config('mac')).decode()
    return f"esp32_{mac}"
```

### 5. 图片数据处理

图片数据格式需要与墨水屏驱动兼容：
- 服务器端使用Pillow预处理图片
- 转换为400x300像素，黑白模式
- 使用MONO_HMSB编码
- 输出15000字节的原始二进制数据

### 6. 状态显示优化

为了提供良好的用户体验：
- 使用简洁清晰的状态消息
- 错误信息包含错误类型和简短描述
- 使用图标或符号增强可读性
- 避免频繁刷新屏幕（消耗电量）

### 7. 配置文件扩展

在`config.py`中添加以下配置：

```python
# 设备配置
DEVICE_ID = None  # 留空则自动生成

# API服务器配置
API_SERVER = "http://192.168.1.100:9999"

# MQTT配置
MQTT_SERVER = "192.168.1.100"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None
MQTT_KEEPALIVE = 60

# 重连配置
MAX_WIFI_RETRIES = 3
MAX_MQTT_RETRIES = 3
RETRY_DELAY = 5  # 秒

# 下载配置
HTTP_TIMEOUT = 30  # 秒
```

## Performance Considerations

### 1. 启动时间

- WiFi连接：2-5秒
- Bootstrap API调用：1-2秒
- MQTT连接：1-2秒
- 总启动时间：约5-10秒

### 2. 图片更新时间

- MQTT消息接收：<1秒
- 图片下载（15KB）：1-3秒（取决于网络速度）
- 图片显示：2-5秒（取决于刷新模式）
- 总更新时间：约5-10秒

### 3. 功耗优化

- 使用MQTT保持连接，避免频繁重连
- 图片显示完成后，墨水屏不消耗功耗
- 考虑实现深度睡眠模式（未来扩展）

### 4. 网络带宽

- MQTT消息：<1KB
- 图片数据：15KB
- 总带宽需求：低，适合家庭WiFi网络

## Security Considerations

### 1. MQTT认证

- 支持用户名/密码认证
- 建议在生产环境启用认证
- 考虑使用TLS加密（如果ESP32性能允许）

### 2. API访问控制

- 设备ID作为访问凭证
- 服务器端验证设备ID的有效性
- 考虑实现设备注册和授权机制

### 3. 数据验证

- 验证下载的图片数据大小
- 验证MQTT消息的JSON格式
- 防止恶意数据导致设备崩溃

### 4. 网络安全

- 使用WPA2加密的WiFi网络
- 避免在代码中硬编码敏感信息
- 考虑使用HTTPS和MQTTS（加密版本）

## Future Enhancements

1. **OTA固件更新**：通过MQTT推送固件更新
2. **深度睡眠模式**：在不活动时进入低功耗模式
3. **本地图片缓存**：缓存最近的图片，减少下载
4. **多图片轮播**：支持显示多张图片的轮播
5. **传感器集成**：显示温度、湿度等传感器数据
6. **触摸按钮**：添加物理按钮进行交互
7. **Web配置界面**：通过Web界面配置WiFi和MQTT参数
8. **日志上报**：将设备日志上报到服务器
