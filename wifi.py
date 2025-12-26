import network
import time
import ntptime
import json
from machine import RTC
from config import WIFI_SSID, WIFI_PASSWORD, WIFI_TIMEOUT
try:
    from buzzer import system_buzzer
except ImportError:
    system_buzzer = None

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
        
    def _load_stored_config(self):
        """尝试从文件加载WiFi配置"""
        try:
            with open('wifi_config.json', 'r') as f:
                config = json.load(f)
                return config.get('ssid'), config.get('password')
        except:
            return None, None

    def connect(self, ssid=None, password=None, timeout=None):
        """连接到WiFi网络
        
        参数:
            ssid: WiFi名称，如果为None则尝试从wifi_config.json或config.py获取
            password: WiFi密码，如果为None则尝试从wifi_config.json或config.py获取
            timeout: 连接超时时间(毫秒)，如果为None则使用config.py中的配置
            
        返回:
            bool: 连接是否成功
        """
        # 1. 如果未提供参数，尝试从文件加载
        if not ssid or not password:
            stored_ssid, stored_pass = self._load_stored_config()
            if stored_ssid and stored_pass:
                ssid = ssid or stored_ssid
                password = password or stored_pass

        # 2. 如果仍未获取到，使用config.py中的默认配置
        ssid = ssid or WIFI_SSID
        password = password or WIFI_PASSWORD
        timeout = timeout or WIFI_TIMEOUT
        
        if not ssid or not password:

            print("错误: WiFi SSID或密码未设置")
            return False
            
        # 如果已经连接到同一网络，直接返回成功
        if self.wlan.isconnected() and self.wlan.config('ssid') == ssid:
            self.connected = True
            
            # 即使已经连接，也检查一下时间是否正确 (年份 < 2024 说明未同步)
            # 或者是每次连接都强制同步一次，确保准确
            try:
                if time.localtime()[0] < 2024:
                    print("时间未同步(2024年前)，尝试同步...")
                    self.sync_time()
            except:
                pass
                
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
                    
                    # 连接成功后同步时间
                    self.sync_time()
                    
                    if system_buzzer:
                        system_buzzer.play_wifi_connected()

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
        if system_buzzer:
            system_buzzer.play_wifi_fail()
        return False
        
    def sync_time(self):
        """同步网络时间"""
        print("正在同步网络时间...")
        
        # 尝试多个NTP服务器
        ntp_servers = ['ntp.aliyun.com', 'cn.pool.ntp.org', 'pool.ntp.org']
        
        for server in ntp_servers:
            try:
                print(f"尝试连接NTP服务器: {server}")
                ntptime.host = server
                ntptime.settime()
                
                # MicroPython的ntptime设置的是UTC时间
                # 我们需要加上时区偏移 (例如 UTC+8)
                # 获取当前UTC时间戳
                t = time.time()
                # 加上8小时的秒数 (8 * 3600 = 28800)
                t_local = t + 28800
                
                # 更新RTC
                tm = time.localtime(t_local)
                
                # RTC.datetime格式: (year, month, day, weekday, hour, minute, second, subseconds)
                RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
                
                print(f"时间同步成功: {tm[0]}-{tm[1]:02d}-{tm[2]:02d} {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}")
                return True
                
            except Exception as e:
                print(f"NTP服务器 {server} 同步失败: {e}")
                time.sleep_ms(1000) # 失败后稍作等待
        
        print("所有NTP服务器同步失败")
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