# Requirements Document

## Introduction

本文档定义了ESP32 MicroPython墨水屏项目的MQTT图片显示功能需求。该功能允许ESP32设备通过MQTT协议连接到后端服务器，接收并显示服务器推送的二进制图片数据。这是对现有WiFi显示功能的扩展，提供了更实时、更高效的图片推送机制。

## Glossary

- **ESP32**: 运行MicroPython的微控制器设备
- **墨水屏 (E-ink Display)**: 电子墨水显示屏，型号为GDEQ042T81，分辨率400x300像素
- **MQTT**: 轻量级消息队列遥测传输协议，用于设备与服务器之间的通信
- **设备 (Device)**: 指ESP32硬件及其运行的MicroPython程序
- **服务器 (Server)**: 基于FastAPI的后端服务，管理设备和内容
- **二进制图片数据 (Binary Image Data)**: 经过预处理的墨水屏兼容格式图片数据
- **帧缓冲区 (Frame Buffer)**: 用于存储图片数据的内存缓冲区
- **RUN_MODE**: 设备运行模式选择器，用于切换不同的应用功能
- **Bootstrap**: 设备启动时从服务器获取初始配置和当前版本信息的过程

## Requirements

### Requirement 1

**User Story:** 作为设备开发者，我希望能够配置设备通过MQTT连接到服务器，以便实现实时的图片推送功能。

#### Acceptance Criteria

1. WHEN RUN_MODE设置为4 THEN 设备 SHALL 初始化MQTT客户端并连接到配置的MQTT服务器
2. WHEN MQTT连接建立前 THEN 设备 SHALL 首先建立WiFi连接
3. WHEN MQTT连接失败 THEN 设备 SHALL 在墨水屏上显示错误信息并尝试重新连接
4. WHERE 配置文件中定义了MQTT服务器地址和端口 THEN 设备 SHALL 使用这些配置参数进行连接
5. WHEN MQTT连接成功 THEN 设备 SHALL 在墨水屏上显示连接成功的状态信息

### Requirement 2

**User Story:** 作为设备开发者，我希望设备能够在启动时从服务器获取当前版本信息，以便确定是否需要更新显示内容。

#### Acceptance Criteria

1. WHEN 设备启动且WiFi连接成功后 THEN 设备 SHALL 调用bootstrap API获取当前内容版本
2. WHEN bootstrap API返回版本信息 THEN 设备 SHALL 将版本号存储在本地变量中
3. WHEN bootstrap API调用失败 THEN 设备 SHALL 在墨水屏上显示错误信息并继续等待MQTT消息
4. WHEN 获取到版本信息 THEN 设备 SHALL 在墨水屏上显示当前版本号

### Requirement 3

**User Story:** 作为设备开发者，我希望设备能够订阅MQTT主题并接收服务器推送的更新指令，以便及时获取新的图片内容。

#### Acceptance Criteria

1. WHEN MQTT连接建立后 THEN 设备 SHALL 订阅设备专属的MQTT主题
2. WHEN 收到MQTT消息 THEN 设备 SHALL 解析消息内容以确定消息类型
3. WHEN 消息类型为更新指令 THEN 设备 SHALL 提取新版本号并触发内容下载流程
4. WHEN 收到无效的MQTT消息 THEN 设备 SHALL 记录错误信息但不中断运行
5. WHERE MQTT主题格式为 "devices/{device_id}/updates" THEN 设备 SHALL 使用设备唯一ID构建订阅主题

### Requirement 4

**User Story:** 作为设备开发者，我希望设备能够从服务器下载二进制图片数据，以便在墨水屏上显示新内容。

#### Acceptance Criteria

1. WHEN 收到更新指令后 THEN 设备 SHALL 通过HTTP GET请求下载指定版本的图片数据
2. WHEN 下载图片数据时 THEN 设备 SHALL 使用API端点 "/api/devices/{device_id}/content/{version}"
3. WHEN 图片数据下载成功 THEN 设备 SHALL 验证数据大小是否符合墨水屏规格（400x300像素，15000字节）
4. WHEN 图片数据大小不正确 THEN 设备 SHALL 拒绝显示并记录错误信息
5. WHEN 下载失败 THEN 设备 SHALL 在墨水屏上显示错误信息并保持当前显示内容

### Requirement 5

**User Story:** 作为设备开发者，我希望设备能够将下载的二进制图片数据显示在墨水屏上，以便用户看到最新的内容。

#### Acceptance Criteria

1. WHEN 图片数据验证通过后 THEN 设备 SHALL 将二进制数据加载到帧缓冲区
2. WHEN 帧缓冲区准备完成后 THEN 设备 SHALL 调用墨水屏驱动的display_frame方法显示图片
3. WHEN 首次显示图片时 THEN 设备 SHALL 使用全局刷新模式以确保显示质量
4. WHEN 后续更新图片时 THEN 设备 SHALL 根据刷新计数器决定使用局部刷新或全局刷新
5. WHEN 图片显示完成后 THEN 设备 SHALL 更新本地存储的当前版本号

### Requirement 6

**User Story:** 作为设备开发者，我希望设备能够处理网络异常和错误情况，以便系统具有良好的健壮性。

#### Acceptance Criteria

1. WHEN WiFi连接断开 THEN 设备 SHALL 尝试重新连接WiFi并在墨水屏上显示重连状态
2. WHEN MQTT连接断开 THEN 设备 SHALL 尝试重新连接MQTT服务器
3. WHEN 连续重连失败超过3次 THEN 设备 SHALL 在墨水屏上显示持久错误信息
4. WHEN 内存不足无法分配帧缓冲区 THEN 设备 SHALL 显示内存错误信息并跳过本次更新
5. WHEN 发生未捕获的异常 THEN 设备 SHALL 捕获异常、显示错误信息并尝试恢复运行

### Requirement 7

**User Story:** 作为设备开发者，我希望能够在config.py中配置MQTT和设备相关参数，以便灵活部署到不同环境。

#### Acceptance Criteria

1. WHERE config.py文件存在 THEN 设备 SHALL 从该文件读取MQTT服务器地址、端口和设备ID
2. WHEN 配置参数缺失 THEN 设备 SHALL 使用合理的默认值并在墨水屏上显示警告信息
3. WHEN 设备ID未配置 THEN 设备 SHALL 生成基于MAC地址的唯一设备ID
4. WHERE 配置了API服务器地址 THEN 设备 SHALL 使用该地址构建完整的API端点URL
5. WHEN 配置文件格式错误 THEN 设备 SHALL 显示配置错误信息并停止运行

### Requirement 8

**User Story:** 作为设备用户，我希望在墨水屏上看到清晰的状态信息，以便了解设备当前的运行状态。

#### Acceptance Criteria

1. WHEN 设备启动时 THEN 墨水屏 SHALL 显示"正在启动..."的提示信息
2. WHEN WiFi连接过程中 THEN 墨水屏 SHALL 显示"正在连接WiFi..."的状态信息
3. WHEN MQTT连接过程中 THEN 墨水屏 SHALL 显示"正在连接MQTT服务器..."的状态信息
4. WHEN 下载图片时 THEN 墨水屏 SHALL 显示"正在下载图片..."的进度信息
5. WHEN 发生错误时 THEN 墨水屏 SHALL 显示具体的错误类型和简短描述
