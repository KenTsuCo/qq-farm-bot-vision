import cv2
import keyboard
import time
import pyautogui
import logging
from utils.cv_match import cvMatch
from utils.screen_capture import ScreenCapture


class FarmBotCV:
    def __init__(self, check_interval = 3, debug_mode = False):
        self.logger = logging.getLogger(__name__)
        if debug_mode == True:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.check_interval = check_interval
        self.running = True
        self.pause_status = False
        self.screen_capture = ScreenCapture("QQ经典农场")
        self.cv_match = cvMatch()
        
        # 加载匹配图片资源
        self.welcome_back_frame = cv2.imread(r"assert\datasets\icons\welcome_back.jpg")
        self.harvest_all_frame = cv2.imread(r"assert\datasets\icons\harvest_all.jpg")
        self.harvest_one_frame = cv2.imread(r"assert\datasets\icons\harvest_one.jpg")
        self.get_new_seed_frame = cv2.imread(r"assert\datasets\icons\get_new_seed.jpg")
        self.level_up_frame = cv2.imread(r"assert\datasets\icons\level_up.jpg")
        self.watering_all_frame = cv2.imread(r"assert\datasets\icons\watering_all.jpg")
        self.remove_all_grass_frame = cv2.imread(r"assert\datasets\icons\remove_all_grass.jpg")
        self.remove_all_bugs_frame = cv2.imread(r"assert\datasets\icons\remove_all_bugs.jpg")
        self.reconnect_frame = cv2.imread(r"assert\datasets\icons\reconnect.jpg")

        self.logger.info("机器人初始化完成,准备开始巡检")
        
    def start(self):
        # 注册退出热键
        keyboard.add_hotkey('ctrl+s', self.stop)
        keyboard.add_hotkey('p', self.pause)

        while self.running:
            # 主循环逻辑
            if not self.pause_status:
                self.logger.info("======================开始新的一轮检查======================")
                self.run_cycle()
                self.logger.info(f"======================本轮巡查完毕======================")
            time.sleep(self.check_interval)
            
    def pause(self):
        if self.pause_status == False:
            self.logger.info("接收到暂停信号，机器人暂时停止处理")
            self.pause_status = True
        else:
            self.logger.info("接收到恢复信号，机器人继续处理")
            self.pause_status = False

    def stop(self):
        self.logger.info("接收到停止信号，机器人已停止退出")
        self.running = False
    

    def run_cycle(self):
        # 循环处理事件
        if self.screen_capture.check_window_exist():
            self.logger.info("正在获取游戏画面")
            game_frame = self.screen_capture.get_window_frame()     # 获取游戏画面
            if game_frame is None:
                self.logger.error(f"游戏画面截取失败，请检查游戏是否开启并确保窗口在前台")
                return
            self.logger.info("游戏画面获取成功,开始处理")
            # 检测重连按钮
            if self.check_reconnect(game_frame):
                return
            # 检测欢迎回来界面
            if self.check_welcome_back(game_frame):
                return
            # 检测一键收获按钮
            if self.check_harvest_all(game_frame):
                return
            # 检测单个收获按钮
            if self.check_harvest_one(game_frame):
                return
            # 检测获得新种子页面
            if self.check_get_new_seed(game_frame):
                return
            # 检测升级提示窗口
            if self.check_level_up(game_frame):
                return
            # 检测一键浇水按钮
            if self.check_watering_all(game_frame):
                return
            # 检测一键除草按钮
            if self.check_remove_all_grass(game_frame):
                return
            self.logger.info("无可执行的任务，继续等待下一轮检查")
        else:
            self.logger.warning("未找到游戏窗口，请检查游戏是否开启并确保窗口在前台")

    def convert_to_screen_coordinate(self, local_coord):
        '''
        将截图内的局部坐标转换为屏幕绝对坐标
        
        Args:
            local_coord: 局部坐标 (x, y)
        
        Returns:
            tuple: 屏幕绝对坐标 (screen_x, screen_y)
        '''
        window_pos = self.screen_capture.get_window_position()
        if window_pos is None:
            raise RuntimeError("无法获取窗口位置")
        
        screen_x = window_pos[0] + local_coord[0]
        screen_y = window_pos[1] + local_coord[1]
        
        return (screen_x, screen_y)
    
    def click_at_position(self, screen_coord, duration=0.1):
        '''
        在指定屏幕坐标位置执行鼠标点击
        
        Args:
            screen_coord: 屏幕绝对坐标 (x, y)
            duration: 鼠标按下持续时间，默认 0.1 秒
        '''
        pyautogui.click(screen_coord[0], screen_coord[1], duration=duration)
        self.logger.info(f"已模拟点击坐标：{screen_coord}")

    def check_welcome_back(self, game_frame):
        '''
        检查是否弹欢迎回来的窗口
        
        Returns:
            bool: 是否检测到并处理了欢迎弹窗
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.welcome_back_frame, threshold=0.65)
        if match_result is not None:        # 有欢迎回来界面
            self.logger.info(f"检测到【欢迎回来】界面，准备点击 X 按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            center_x = match_result['center'][0]
            center_y = match_result['center'][1]
            # 因截图是上方一条，因此右上角X位置要加上偏移
            pias_x = center_x + 185     # 往右偏大概185pxs
            pias_y = center_y - 16      # 往上偏大概16px
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate((pias_x, pias_y))
            # 点击屏幕坐标
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【欢迎回来】界面, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_harvest_all(self, game_frame):
        '''
        检查是否有一键收获的按钮
        Returns:
            bool: 是否有一键收获的按钮
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.harvest_all_frame)
        if match_result is not None:        # 有一键收获按钮
            self.logger.info(f"检测到【一键收获】按钮,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【一键收获】按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_harvest_one(self, game_frame):
        '''
        检查是否有单个收获按钮
        部分四方格无法一键收获,需要使用单个收获按钮
        Returns:
            bool: 检查是否有单个收获按钮
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.harvest_one_frame)
        if match_result is not None:        # 有单个收获按钮
            self.logger.info(f"检测到【单个收获】按钮,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【单个收获】按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_get_new_seed(self, game_frame):
        '''
        检查是否有获取新种子的提示窗口，有就点击一下关闭
        Returns:
            bool: 是否有获取新种子的按钮
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.get_new_seed_frame)
        if match_result is not None:        # 有获取新种子的按钮
            self.logger.info(f"检测到【获得新种子】的提示窗口,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【获得新种子】的提示窗口, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False
        
    def check_level_up(self, game_frame):
        '''
        检查是否升级提示窗口
        Returns:
            bool: 是否有升级提示窗口
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.level_up_frame, threshold=0.6)
        if match_result is not None:        # 有升级提示窗口
            self.logger.info(f"检测到【升级提示】窗口,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            # 点击位置要往下偏移一些
            screen_center = (screen_center[0], screen_center[1] + 500)
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【升级提示】窗口, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_watering_all(self, game_frame):
        '''
        检查是否有一键浇水按钮
        Returns:
            bool: 是否有一键浇水按钮
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.watering_all_frame)
        if match_result is not None:        # 有一键浇水按钮
            self.logger.info(f"检测到【一键浇水】按钮,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【一键浇水】按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False
        
    def check_remove_all_grass(self, game_frame):
        '''
        检查是否有一键除草按钮
        Returns:
            bool: 是否有一键除草按钮
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.remove_all_grass_frame)
        if match_result is not None:        # 有一键除草按钮
            self.logger.info(f"检测到【一键除草】按钮,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【一键除草】按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False
    
    def check_remove_all_bugs(self, game_frame):
        '''
        检查是否有一键除虫按钮
        Returns:
            bool: 是否有一键除虫按钮
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.remove_all_bugs_frame)
        if match_result is not None:        # 有一键除虫按钮
            self.logger.info(f"检测到【一键除虫】按钮,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【一键除虫】按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_reconnect(self, game_frame):
        '''
        检查是否有重新登录按钮
        Returns:
            bool: 是否有重新登录按钮
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.reconnect_frame)
        if match_result is not None:        # 有重新登录按钮
            self.logger.info(f"检测到【重新登录】按钮,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【重新登录】按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False
        