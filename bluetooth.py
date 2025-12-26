import ubluetooth
import json
import time
import micropython
import network
from machine import Timer

class BLEManager:
    def __init__(self, name="ESP32-Epaper"):
        # 1. 强制关闭WiFi (STA和AP模式)，避免电源冲突和射频干扰
        try:
            wlan_sta = network.WLAN(network.STA_IF)
            wlan_ap = network.WLAN(network.AP_IF)
            if wlan_sta.active() or wlan_ap.active():
                print("正在关闭WiFi以启动蓝牙...")
                wlan_sta.active(False)
                wlan_ap.active(False)
                time.sleep_ms(500)
        except Exception as e:
            print(f"关闭WiFi时出错 (非致命): {e}")

        self.ble = ubluetooth.BLE()
        # 先关闭再开启，确保重置
        self.ble.active(False)
        time.sleep_ms(200)
        self.ble.active(True)
        print("BLE 硬件已激活")
        
        self.ble.irq(self.ble_irq)
        self.conn_handle = None
        self.name = name
        
        # 定义UUID
        # Nordic UART Service (NUS)
        self.NUS_UUID = ubluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
        self.RX_UUID = ubluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E") # Write
        self.TX_UUID = ubluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E") # Notify
        
        self.rx_handle = None
        self.tx_handle = None
        
        self._register_services()
        self._advertise()
        
        self.rx_buffer = b""
        
    def _register_services(self):
        # 注册服务
        # RX: Write, TX: Notify
        nus_service = (
            self.NUS_UUID,
            (
                (self.RX_UUID, ubluetooth.FLAG_WRITE | ubluetooth.FLAG_WRITE_NO_RESPONSE),
                (self.TX_UUID, ubluetooth.FLAG_NOTIFY | ubluetooth.FLAG_READ),
            ),
        )
        
        ((self.rx_handle, self.tx_handle),) = self.ble.gatts_register_services((nus_service,))
        
    def _advertise(self):
        # 广播数据
        name = bytes(self.name, 'UTF-8')
        # 0x02: Flags, 0x01: LE General Discoverable Mode
        # 0x09: Complete Local Name
        adv_data = bytearray(b'\x02\x01\x06') + bytearray((len(name) + 1, 0x09)) + name
        
        try:
            # 100ms interval (100000us)
            self.ble.gap_advertise(100000, adv_data)
            print(f"蓝牙正在广播: {self.name}")
        except Exception as e:
            print(f"蓝牙广播启动失败: {e}")

    def ble_irq(self, event, data):
        # 处理蓝牙事件
        if event == 1: # _IRQ_CENTRAL_CONNECT
            self.conn_handle, _, _ = data
            print(f"蓝牙已连接, handle: {self.conn_handle}")
            self.ble.gap_advertise(None) # 停止广播
        
        elif event == 2: # _IRQ_CENTRAL_DISCONNECT
            conn_handle, _, _ = data
            print(f"蓝牙已断开, handle: {conn_handle}")
            self.conn_handle = None
            # 使用 schedule 调度重新广播，避免在中断中出错
            micropython.schedule(self._restart_advertise, None)
            
        elif event == 3: # _IRQ_GATTS_WRITE
            conn_handle, value_handle = data
            if conn_handle == self.conn_handle and value_handle == self.rx_handle:
                # 读取接收到的数据
                try:
                    received_data = self.ble.gatts_read(self.rx_handle)
                    self.rx_buffer += received_data
                    # 调度数据处理
                    micropython.schedule(self._process_data, received_data)
                except Exception as e:
                    print(f"读取数据失败: {e}")

    def _restart_advertise(self, _):
        """调度执行的重新广播函数"""
        print("准备重新开始广播...")
        time.sleep_ms(100) # 稍微等待一下
        self._advertise()

    def _process_data(self, data):
        # 处理接收到的数据
        try:
            text = data.decode('utf-8').strip()
            print(f"收到数据: {text}")
            
            # 尝试解析JSON
            try:
                payload = json.loads(text)
                self._handle_json(payload)
            except ValueError:
                print("收到非JSON数据")
                
        except Exception as e:
            print(f"数据处理错误: {e}")

    def _handle_json(self, payload):
        # 处理JSON数据
        if 'ssid' in payload and 'password' in payload:
            print("检测到WiFi配置")
            self.save_wifi_config(payload['ssid'], payload['password'])
            self.send("WiFi config received")
        else:
            print("检测到普通JSON数据")
            self.save_json_data(payload)
            self.send("JSON data received")

    def save_wifi_config(self, ssid, password):
        # 保存WiFi配置到文件
        config = {'ssid': ssid, 'password': password}
        try:
            with open('wifi_config.json', 'w') as f:
                json.dump(config, f)
            print("WiFi配置已保存到 wifi_config.json")
        except Exception as e:
            print(f"保存WiFi配置失败: {e}")

    def save_json_data(self, data):
        # 保存通用JSON数据
        try:
            with open('received_data.json', 'w') as f:
                json.dump(data, f)
            print("数据已保存到 received_data.json")
        except Exception as e:
            print(f"保存数据失败: {e}")

    def send(self, data):
        # 发送数据给手机
        if self.conn_handle:
            try:
                self.ble.gatts_notify(self.conn_handle, self.tx_handle, data)
            except Exception as e:
                print(f"发送失败: {e}")

    def scan(self, duration_ms=5000):
        """扫描周围的蓝牙设备"""
        print(f"开始扫描蓝牙设备 ({duration_ms}ms)...")
        
        found_devices = set()
        
        def _scan_callback(event, data):
            if event == 5: # _IRQ_SCAN_RESULT
                addr_type, addr, adv_type, rssi, adv_data = data
                # 将MAC地址转换为可读字符串
                addr_hex = ':'.join(['{:02x}'.format(b) for b in addr])
                
                if addr_hex not in found_devices:
                    found_devices.add(addr_hex)
                    
                    # 尝试解析设备名称
                    name = "Unknown"
                    i = 0
                    while i < len(adv_data):
                        if i + 1 >= len(adv_data): break
                        length = adv_data[i]
                        if length == 0: break
                        
                        type = adv_data[i + 1]
                        # 0x08: Shortened Local Name, 0x09: Complete Local Name
                        if type == 0x08 or type == 0x09:
                            try:
                                name = adv_data[i+2 : i+1+length].decode('utf-8')
                            except:
                                pass
                            break
                        i += 1 + length
                    
                    print(f"发现设备: MAC={addr_hex}, RSSI={rssi}dBm, Name={name}")

        try:
            # 停止广播以便进行扫描
            self.ble.gap_advertise(None)
            
            # 开始扫描 (duration=0 means indefinite, manually stopped)
            # active=True means active scanning (request scan response)
            self.ble.gap_scan(duration_ms, 30000, 30000, True) 
            
            # 注册回调
            # 注意：这里会覆盖之前的IRQ回调，扫描结束后需要恢复
            original_irq = self.ble.irq(None) # 获取不到之前的callback，只能重新绑定
            self.ble.irq(_scan_callback)
            
            # 等待扫描完成
            time.sleep_ms(duration_ms)
            
            # 停止扫描
            self.ble.gap_scan(None)
            print(f"扫描完成，共发现 {len(found_devices)} 个设备")
            
        except Exception as e:
            print(f"扫描出错: {e}")
        finally:
            # 恢复原来的IRQ处理并重新开始广播
            self.ble.irq(self.ble_irq)
            self._advertise()

# 全局单例
ble_manager = BLEManager()

if __name__ == "__main__":
    print("蓝牙服务已启动...")
    
    # 启动时先扫描一次，证明蓝牙硬件工作正常
    ble_manager.scan(5000)
    
    print("保持运行中，等待连接...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("用户停止")

