import network
import time
from config import WIFI_SSID, WIFI_PASSWORD, WIFI_TIMEOUT

class WiFiManager:
    def __init__(self):
        try:
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
            time.sleep_ms(500)  # 等待WiFi模块完全初始化
            self.connected = False
        except Exception as e:
            print(f"WiFi初始化失败: {e}")
            # 尝试重新初始化
            try:
                time.sleep_ms(1000)
                self.wlan = network.WLAN(network.STA_IF)
                self.wlan.active(True)
                time.sleep_ms(500)
                self.connected = False
            except Exception as e2:
                print(f"WiFi重新初始化失败: {e2}")
                raise
        
    def connect(self, ssid=None, password=None, timeout=None):
        """连接到WiFi网络
        
        参数:
            ssid: WiFi名称，如果为None则使用config.py中的配置
            password: WiFi密码，如果为None则使用config.py中的配置
            timeout: 连接超时时间(毫秒)，如果为None则使用config.py中的配置
            
        返回:
            bool: 连接是否成功
        """
        ssid = ssid or WIFI_SSID
        password = password or WIFI_PASSWORD
        timeout = timeout or WIFI_TIMEOUT
        
        if not ssid or not password:
            print("错误: WiFi SSID或密码未设置")
            return False
            
        # 如果已经连接到同一网络，直接返回成功
        if self.wlan.isconnected() and self.wlan.config('ssid') == ssid:
            self.connected = True
            return True
            
        # 断开当前连接
        if self.wlan.isconnected():
            self.wlan.disconnect()
            
        # 重置WiFi模块以解决内部错误
        try:
            self.wlan.active(False)
            time.sleep_ms(100)
            self.wlan.active(True)
            time.sleep_ms(500)  # 等待WiFi模块完全初始化
        except Exception as e:
            print(f"WiFi模块重置失败: {e}")
            # 尝试重新创建WLAN对象
            try:
                self.wlan = network.WLAN(network.STA_IF)
                self.wlan.active(True)
                time.sleep_ms(500)
            except Exception as e2:
                print(f"重新创建WLAN对象失败: {e2}")
                return False
            
        print(f"正在连接到WiFi: {ssid}")
        
        # 尝试连接，最多重试3次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.wlan.connect(ssid, password)
                
                # 等待连接
                start_time = time.ticks_ms()
                while not self.wlan.isconnected():
                    if time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                        print(f"WiFi连接超时 (尝试 {attempt + 1}/{max_retries})")
                        break
                    time.sleep_ms(100)
                
                if self.wlan.isconnected():
                    print("WiFi连接成功")
                    print(f"IP地址: {self.wlan.ifconfig()[0]}")
                    self.connected = True
                    return True
                    
            except OSError as e:
                print(f"WiFi连接错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # 重置WiFi模块并重试
                    try:
                        self.wlan.active(False)
                        time.sleep_ms(200)
                        self.wlan.active(True)
                        time.sleep_ms(500)
                    except:
                        try:
                            self.wlan = network.WLAN(network.STA_IF)
                            self.wlan.active(True)
                            time.sleep_ms(500)
                        except Exception as e2:
                            print(f"重试时重新创建WLAN对象失败: {e2}")
                            return False
                else:
                    print("所有连接尝试均失败")
                    
        self.connected = False
        return False
        
    def disconnect(self):
        """断开WiFi连接"""
        if self.wlan.isconnected():
            self.wlan.disconnect()
            self.connected = False
            print("WiFi已断开")
            
    def is_connected(self):
        """检查WiFi连接状态
        
        返回:
            bool: 是否已连接
        """
        return self.wlan.isconnected() and self.connected
        
    def get_ip(self):
        """获取当前IP地址
        
        返回:
            str: IP地址，如果未连接则返回None
        """
        if self.is_connected():
            return self.wlan.ifconfig()[0]
        return None
        
    def get_network_info(self):
        """获取网络信息
        
        返回:
            tuple: (IP, 子网掩码, 网关, DNS)，如果未连接则返回None
        """
        if self.is_connected():
            return self.wlan.ifconfig()
        return None
        
    def scan_networks(self):
        """扫描可用的WiFi网络
        
        返回:
            list: 包含网络信息的列表，每个元素为(SSID, BSSID, 通道, RSSI, 安全模式, 隐藏)的元组
        """
        try:
            if not self.wlan.active():
                self.wlan.active(True)
                time.sleep_ms(200)
                
            networks = self.wlan.scan()
            return networks
        except Exception as e:
            print(f"WiFi网络扫描失败: {e}")
            # 尝试重置WiFi模块
            try:
                self.wlan.active(False)
                time.sleep_ms(200)
                self.wlan.active(True)
                time.sleep_ms(500)
                networks = self.wlan.scan()
                return networks
            except Exception as e2:
                print(f"重试WiFi网络扫描失败: {e2}")
                return []  # 返回空列表而不是None，避免调用方需要额外检查
        
    def get_signal_strength(self):
        """获取当前连接的信号强度(RSSI)
        
        返回:
            int: RSSI值，如果未连接则返回None
        """
        if not self.is_connected():
            return None
            
        try:
            # 尝试直接获取RSSI
            # 在某些MicroPython实现中，可以直接获取RSSI
            rssi = self.wlan.status('rssi')
            if rssi is not None:
                return rssi
        except:
            pass
            
        # 如果直接获取失败，尝试通过扫描网络查找
        try:
            # 获取当前连接的SSID
            current_ssid = self.wlan.config('ssid')
            if isinstance(current_ssid, bytes):
                current_ssid = current_ssid.decode('utf-8')
            
            # 扫描网络并查找当前连接的RSSI
            networks = self.scan_networks()
            for network in networks:
                ssid = network[0].decode('utf-8') if isinstance(network[0], bytes) else network[0]
                if ssid == current_ssid:  # SSID匹配
                    return network[3]  # RSSI值
        except:
            pass
            
        # 如果都失败了，返回一个默认值
        return -60  # 默认中等信号强度

# 创建全局WiFi管理器实例
wifi_manager = WiFiManager()