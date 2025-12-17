# Implementation Plan - MQTT Image Display

## 现状分析
- ✅ WiFi功能已实现 (wifi.py, WiFiManager类)
- ✅ 墨水屏驱动已实现 (epaper4in2.py)
- ✅ 配置文件存在 (config.py) - 需要添加MQTT参数
- ✅ Boot.py支持RUN_MODE切换
- ❌ MQTT功能尚未实现

## 实现任务

- [ ] 1. 扩展config.py以支持MQTT和设备参数
  - 添加DEVICE_ID配置（可选，默认使用MAC地址生成）
  - 添加API_SERVER配置（后端服务器地址）
  - 添加MQTT_SERVER、MQTT_PORT、MQTT_USER、MQTT_PASSWORD、MQTT_KEEPALIVE配置
  - 添加MAX_WIFI_RETRIES、MAX_MQTT_RETRIES、RETRY_DELAY配置
  - 添加HTTP_TIMEOUT配置
  - _Requirements: 1.4, 7.1, 7.4_

- [ ]* 1.1 编写配置参数使用的属性测试
  - **Property 1: Configuration parameters are used correctly**
  - **Property 13: Configuration reading**
  - **Validates: Requirements 1.4, 7.1**

- [ ]* 1.2 编写默认值处理的属性测试
  - **Property 14: Default value handling**
  - **Validates: Requirements 7.2**

- [ ] 2. 创建mqtt_display.py模块并实现辅助函数
  - 创建新文件mqtt_display.py
  - 实现get_device_id()函数：从config读取或基于MAC地址生成设备ID
  - 实现build_mqtt_topic(device_id)函数：构建MQTT订阅主题 "devices/{device_id}/updates"
  - 实现build_api_url(api_server, device_id, endpoint)函数：构建完整API URL
  - 实现parse_mqtt_message(msg)函数：解析MQTT JSON消息，提取type和version字段
  - 实现validate_image_data(data)函数：验证图片数据大小为15000字节
  - 添加模块级文档字符串
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 4.2, 4.3, 4.4, 7.3, 7.4_

- [ ]* 2.1 编写设备ID生成的单元测试
  - 测试配置了DEVICE_ID时返回配置值
  - 测试未配置时基于MAC地址生成
  - _Requirements: 7.3_

- [ ]* 2.2 编写MQTT主题构建的属性测试
  - **Property 6: MQTT topic construction**
  - **Validates: Requirements 3.5**

- [ ]* 2.3 编写API端点构建的属性测试
  - **Property 7: API endpoint construction**
  - **Property 15: API URL construction from config**
  - **Validates: Requirements 4.2, 7.4**

- [ ]* 2.4 编写MQTT消息解析的属性测试
  - **Property 4: MQTT message parsing robustness**
  - **Validates: Requirements 3.2**

- [ ]* 2.5 编写无效消息处理的属性测试
  - **Property 5: Invalid message handling**
  - **Validates: Requirements 3.4**

- [ ]* 2.6 编写图片数据验证的属性测试
  - **Property 8: Image data size validation**
  - **Property 9: Invalid image data rejection**
  - **Validates: Requirements 4.3, 4.4**

- [ ] 3. 实现MQTTDisplayApp类的基础结构
  - 在mqtt_display.py中创建MQTTDisplayApp类
  - 实现__init__方法：初始化墨水屏驱动、WiFi管理器、帧缓冲区、状态变量
  - 实现display_status(message)方法：在墨水屏上显示状态信息（参考wifi_display.py的实现）
  - 实现display_error(error_type, error_msg)方法：显示错误信息
  - 添加current_version、refresh_count等状态变量
  - _Requirements: 1.1, 1.2, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 3.1 编写错误消息显示的属性测试
  - **Property 16: Error message display**
  - **Validates: Requirements 8.5**

- [ ] 4. 实现Bootstrap功能
  - 在MQTTDisplayApp类中实现bootstrap()方法
  - 使用urequests.get()调用 {API_SERVER}/api/devices/{device_id}/bootstrap
  - 解析JSON响应，提取current_version字段
  - 处理HTTP错误和超时（使用HTTP_TIMEOUT配置）
  - 在墨水屏上显示获取到的版本号
  - 失败时显示错误但不中断程序
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 4.1 编写版本存储的属性测试
  - **Property 2: Version storage consistency**
  - **Validates: Requirements 2.2**

- [ ]* 4.2 编写版本显示的属性测试
  - **Property 3: Version display consistency**
  - **Validates: Requirements 2.4**

- [ ] 5. 实现图片下载和显示功能
  - 实现download_image(version)方法：通过HTTP GET下载图片数据
  - 使用build_api_url()构建下载URL: {API_SERVER}/api/devices/{device_id}/content/{version}
  - 设置HTTP_TIMEOUT超时
  - 使用validate_image_data()验证下载的数据
  - 实现display_image(image_data)方法：将数据加载到帧缓冲区并显示
  - 首次显示使用global_refresh=True
  - 后续根据refresh_count决定刷新模式（每5次局部刷新后执行一次全局刷新）
  - 显示成功后更新current_version
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 5.1 编写图片下载的单元测试
  - 测试成功下载的情况
  - 测试下载失败的错误处理
  - 测试超时处理
  - _Requirements: 4.1, 4.5_

- [ ]* 5.2 编写图片数据加载的属性测试
  - **Property 10: Image data loading**
  - **Validates: Requirements 5.1**

- [ ]* 5.3 编写版本更新的属性测试
  - **Property 11: Version update after display**
  - **Validates: Requirements 5.5**

- [ ] 6. 实现MQTT连接和消息处理
  - 导入umqtt.robust库
  - 实现connect_mqtt()方法：创建MQTTClient并连接到MQTT服务器
  - 使用config中的MQTT_SERVER、MQTT_PORT、MQTT_USER、MQTT_PASSWORD、MQTT_KEEPALIVE
  - 使用get_device_id()作为client_id
  - 订阅build_mqtt_topic()构建的主题
  - 实现on_message(topic, msg)回调函数
  - 在回调中使用parse_mqtt_message()解析消息
  - 当消息类型为"update"时，调用download_image()和display_image()
  - 处理连接失败，支持重试（使用MAX_MQTT_RETRIES和RETRY_DELAY）
  - _Requirements: 1.1, 1.3, 1.5, 3.1, 3.2, 3.3, 3.4, 6.2_

- [ ]* 6.1 编写MQTT连接的单元测试
  - 测试成功连接的情况
  - 测试连接失败的错误处理
  - 测试主题订阅
  - _Requirements: 1.1, 3.1_

- [ ]* 6.2 编写消息回调的单元测试
  - 测试更新消息的处理
  - 测试无效消息的处理
  - 测试消息触发的操作
  - _Requirements: 3.2, 3.3, 3.4_

- [ ] 7. 实现主运行循环和错误处理
  - 实现run()方法作为主入口
  - 步骤1: 显示"正在启动..."状态
  - 步骤2: 调用wifi.wifi_manager.connect()连接WiFi，失败时重试（MAX_WIFI_RETRIES）
  - 步骤3: 调用bootstrap()获取初始版本
  - 步骤4: 调用connect_mqtt()建立MQTT连接
  - 步骤5: 进入消息循环，使用client.check_msg()非阻塞检查消息
  - 在每个步骤显示相应的状态信息
  - 实现统一的异常处理：捕获所有异常，显示错误信息，尝试恢复
  - 添加gc.collect()调用进行内存管理
  - WiFi断开时自动重连
  - MQTT断开时自动重连
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 7.1 编写异常恢复的属性测试
  - **Property 12: Exception recovery**
  - **Validates: Requirements 6.5**

- [ ]* 7.2 编写主流程的集成测试
  - 测试完整的启动和运行流程
  - 测试WiFi断开恢复
  - 测试MQTT断开恢复
  - _Requirements: 6.1, 6.2_

- [ ]* 7.3 编写内存管理的单元测试
  - 测试内存不足时的错误处理
  - 测试垃圾回收的调用
  - _Requirements: 6.4_

- [ ] 8. 在boot.py中添加RUN_MODE=4支持
  - 在boot.py中添加elif RUN_MODE == 4:条件分支
  - 导入mqtt_display模块
  - 创建MQTTDisplayApp实例并调用run()方法
  - 添加try-except捕获异常并在墨水屏上显示错误
  - _Requirements: 1.1_

- [ ] 9. Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 10. 在实际硬件上进行端到端测试
  - 在ESP32设备上部署代码
  - 设置RUN_MODE=4并重启设备
  - 验证WiFi连接成功
  - 验证Bootstrap API调用成功
  - 验证MQTT连接成功
  - 通过后端发送MQTT更新消息
  - 验证设备接收消息并下载显示图片
  - 测试多次更新图片
  - 测试网络断开恢复
  - 验证墨水屏显示质量和刷新模式
  - _Requirements: 所有需求_

- [ ] 11. 编写使用文档
  - 在README.md或创建新文档说明RUN_MODE=4的使用方法
  - 列出config.py中需要配置的所有MQTT相关参数
  - 提供配置示例
  - 说明后端服务器的API要求（Bootstrap和Content端点）
  - 说明MQTT消息格式
  - 提供测试步骤和故障排除指南
  - _Requirements: 所有需求_
