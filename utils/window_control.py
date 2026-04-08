import ctypes
import time
from ctypes import wintypes

# Windows API 常量
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001

class WindowControl:
    """Windows 窗口后台控制类，支持后台静默点击"""
    
    def __init__(self, window_title):
        """
        初始化窗口控制器
        
        Args:
            window_title: 窗口标题
        """
        self.window_title = window_title
        self.hwnd = None
    
    def find_window(self):
        """
        查找窗口句柄
        
        Returns:
            bool: 是否找到窗口
        """
        try:
            self.hwnd = ctypes.windll.user32.FindWindowW(None, self.window_title)
            if self.hwnd:
                return True
            else:
                return False
        except Exception as e:
            print(f"查找窗口失败：{e}")
            return False
    
    def is_window_visible(self):
        """检查窗口是否可见"""
        if not self.hwnd:
            return False
        return ctypes.windll.user32.IsWindowVisible(self.hwnd)
    
    def get_window_rect(self):
        """
        获取窗口位置
        
        Returns:
            tuple: (left, top, right, bottom) 或 None
        """
        if not self.hwnd:
            return None
        
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        return (rect.left, rect.top, rect.right, rect.bottom)
    
    def click(self, x, y, duration=0.1):
        """
        在窗口内指定坐标执行后台点击（相对于窗口左上角）
        
        Args:
            x: 相对于窗口客户区的 x 坐标
            y: 相对于窗口客户区的 y 坐标
            duration: 点击持续时间（秒）
        
        Returns:
            bool: 是否点击成功
        """
        if not self.hwnd:
            if not self.find_window():
                print("未找到窗口")
                return False
        
        # 将屏幕坐标转换为窗口客户区坐标
        client_point = ctypes.wintypes.POINT(x, y)
        ctypes.windll.user32.ScreenToClient(self.hwnd, ctypes.byref(client_point))
        
        # 构造 LPARAM 参数 (x, y)
        lparam = (client_point.y << 16) | (client_point.x & 0xFFFF)
        
        # 发送鼠标按下消息
        ctypes.windll.user32.PostMessageW(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        time.sleep(duration / 2)
        
        # 发送鼠标释放消息
        ctypes.windll.user32.PostMessageW(self.hwnd, WM_LBUTTONUP, 0, lparam)
        
        return True
    
    def double_click(self, x, y, duration=0.1):
        """
        在窗口内指定坐标执行后台双击
        
        Args:
            x: 相对于窗口客户区的 x 坐标
            y: 相对于窗口客户区的 y 坐标
            duration: 每次点击的持续时间（秒）
        """
        self.click(x, y, duration)
        time.sleep(0.1)
        self.click(x, y, duration)