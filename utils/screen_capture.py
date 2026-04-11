import ctypes

import cv2
import dxcam
import numpy as np
import screeninfo
import win32gui
import win32ui


PW_RENDERFULLCONTENT = 0x00000002


class ScreenCapture:
    def __init__(self, window_title):
        self.window_title = window_title
        self.camera = None
        self.current_monitor_idx = None
        self.window_rect = None

    def __del__(self):
        """析构函数，释放 camera 资源"""
        if hasattr(self, "camera") and self.camera is not None:
            del self.camera

    def _find_window_by_title(self, window_title):
        return win32gui.FindWindow(None, window_title)

    def _get_window_rect(self, hwnd):
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            raise ValueError("窗口尺寸无效")
        self.window_rect = (left, top, right, bottom)
        return left, top, right, bottom, width, height

    def _capture_window_printwindow(self, hwnd):
        """优先使用 PrintWindow 后台抓取窗口内容，避免被其他窗口遮挡。"""
        if not hwnd or not win32gui.IsWindow(hwnd):
            raise ValueError("无效的窗口句柄")
        if win32gui.IsIconic(hwnd):
            return None

        left, top, right, bottom, width, height = self._get_window_rect(hwnd)

        hwnd_dc = None
        mfc_dc = None
        save_dc = None
        save_bitmap = None
        try:
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)

            result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)
            if result != 1:
                result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 0)
            if result != 1:
                return None

            bmp_info = save_bitmap.GetInfo()
            bmp_bytes = save_bitmap.GetBitmapBits(True)
            frame = np.frombuffer(bmp_bytes, dtype=np.uint8)
            frame = frame.reshape((bmp_info["bmHeight"], bmp_info["bmWidth"], 4))
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        finally:
            if save_bitmap is not None:
                win32gui.DeleteObject(save_bitmap.GetHandle())
            if save_dc is not None:
                save_dc.DeleteDC()
            if mfc_dc is not None:
                mfc_dc.DeleteDC()
            if hwnd_dc is not None:
                win32gui.ReleaseDC(hwnd, hwnd_dc)

    def _capture_window_dxcam(self, hwnd):
        """使用 dxcam 截取当前屏幕上的窗口区域，作为后台抓取失败时的回退方案。"""
        if not hwnd or not win32gui.IsWindow(hwnd):
            raise ValueError("无效的窗口句柄")

        left, top, right, bottom, width, height = self._get_window_rect(hwnd)

        center_x = left + width // 2
        center_y = top + height // 2

        monitors = screeninfo.get_monitors()
        target_monitor = None
        target_idx = None
        for i, monitor in enumerate(monitors):
            if (
                monitor.x <= center_x <= monitor.x + monitor.width
                and monitor.y <= center_y <= monitor.y + monitor.height
            ):
                target_monitor = monitor
                target_idx = i
                break
        if not target_monitor:
            return None

        if self.camera is None or self.current_monitor_idx != target_idx:
            if self.camera is not None:
                del self.camera
            self.camera = dxcam.create(output_idx=target_idx)
            self.current_monitor_idx = target_idx

        region_relative = (
            left - target_monitor.x,
            top - target_monitor.y,
            right - target_monitor.x,
            bottom - target_monitor.y,
        )
        frame = self.camera.grab(region=region_relative)
        if frame is None:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def get_window_frame(self):
        hwnd = self._find_window_by_title(self.window_title)
        if not hwnd:
            return None

        frame = self._capture_window_printwindow(hwnd)
        if frame is not None:
            return frame
        return self._capture_window_dxcam(hwnd)

    def get_window_position(self):
        """获取窗口左上角在屏幕上的坐标"""
        if self.window_rect:
            return (self.window_rect[0], self.window_rect[1])
        hwnd = self._find_window_by_title(self.window_title)
        if hwnd:
            left, top, right, bottom, _, _ = self._get_window_rect(hwnd)
            return (left, top)
        return None

    def check_window_exist(self):
        return self._find_window_by_title(self.window_title) != 0


if __name__ == "__main__":
    sc = ScreenCapture("QQ经典农场")
    frame_bgr = sc.get_window_frame()
    if frame_bgr is not None:
        cv2.imshow("frame", frame_bgr)
        cv2.waitKey(0)
