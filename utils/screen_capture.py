import dxcam
import win32gui
import screeninfo
import cv2
# from PIL import Image


class ScreenCapture:
    def __init__(self, window_title):
        self.window_title = window_title
        self.camera = None
        self.current_monitor_idx = None
        self.window_rect = None  # 存储窗口位置 (left, top, right, bottom)
    
    def __del__(self):
        """析构函数，释放 camera 资源"""
        if hasattr(self, 'camera') and self.camera is not None:
            del self.camera
    
    def _find_window_by_title(self, window_title):
        return win32gui.FindWindow(None, window_title)
    
    def _capture_window_dxcam(self, hwnd):
        """使用 dxcam 截取窗口（自动选择正确显示器）"""
        if not hwnd or not win32gui.IsWindow(hwnd):
            raise ValueError("无效的窗口句柄")
        # 获取窗口位置
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            raise ValueError("窗口尺寸无效")
        
        # 保存窗口位置信息
        self.window_rect = (left, top, right, bottom)
        
        # 获取窗口中心点（用于判断属于哪个显示器）
        center_x = left + width // 2
        center_y = top + height // 2
        
        # 获取所有显示器信息
        monitors = screeninfo.get_monitors()
        target_monitor = None
        for i, monitor in enumerate(monitors):
            # 检查窗口中心点是否在显示器区域内
            if (monitor.x <= center_x <= monitor.x + monitor.width and
                monitor.y <= center_y <= monitor.y + monitor.height):
                target_monitor = monitor
                target_idx = i
                break
        if not target_monitor:
            # raise RuntimeError("窗口不在任何显示器上")
            return None
        
        # 创建对应显示器的 dxcam 实例
        if self.camera is None or self.current_monitor_idx != target_idx:
            if self.camera is not None:
                # 释放旧的 camera
                del self.camera
            self.camera = dxcam.create(output_idx=target_idx)
            self.current_monitor_idx = target_idx
        
        
        region_relative = (
            left - target_monitor.x,
            top - target_monitor.y,
            right - target_monitor.x,
            bottom - target_monitor.y
        )
        frame = self.camera.grab(region=region_relative)
        if frame is None:
            # raise RuntimeError("dxcam 截图失败")
            return None
        # img = Image.fromarray(frame)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        return frame_bgr

    def get_window_frame(self):
        hwnd = self._find_window_by_title('QQ经典农场')
        if hwnd:
            frame = self._capture_window_dxcam(hwnd)
            return frame
        else:
            return None
    
    def get_window_position(self):
        """获取窗口左上角在屏幕上的坐标"""
        if self.window_rect:
            return (self.window_rect[0], self.window_rect[1])
        hwnd = self._find_window_by_title(self.window_title)
        if hwnd:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            self.window_rect = (left, top, right, bottom)
            return (left, top)
        return None

    def check_window_exist(self):
        if self._find_window_by_title(self.window_title) == 0:
            return False
        else:
            return True

if __name__ == '__main__':
    sc = ScreenCapture('QQ经典农场')
    frame_bgr = sc.get_window_frame()
    cv2.imshow('frame', frame_bgr)

