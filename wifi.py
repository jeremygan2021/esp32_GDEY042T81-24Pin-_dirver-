import network
import time
from config import WIFI_SSID, WIFI_PASSWORD, WIFI_TIMEOUT

class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.connected = False
        
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
            
        print(f"正在连接到WiFi: {ssid}")
        self.wlan.connect(ssid, password)
        
        # 等待连接
        start_time = time.ticks_ms()
        while not self.wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                print("WiFi连接超时")
                self.connected = False
                return False
            time.sleep_ms(100)
            
        print("WiFi连接成功")
        print(f"IP地址: {self.wlan.ifconfig()[0]}")
        self.connected = True
        return True
        
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
        if not self.wlan.active():
            self.wlan.active(True)
            
        networks = self.wlan.scan()
        return networks
        
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