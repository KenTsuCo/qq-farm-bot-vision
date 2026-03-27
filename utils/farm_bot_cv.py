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
        self.now_scene = "home"     # 判断当前所在的场景
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
        self.friend_icon_frame = cv2.imread(r"assert\datasets\icons\friend_red.jpg")
        self.can_steal_frame = cv2.imread(r"assert\datasets\icons\can_steal.jpg")
        self.steal_all_frame = cv2.imread(r"assert\datasets\icons\steal_all.jpg")
        self.go_home_frame = cv2.imread(r"assert\datasets\icons\go_home.jpg")
        self.close_x_frame = cv2.imread(r"assert\datasets\icons\close_x.jpg")
        self.help_remove_bugs = cv2.imread(r"assert\datasets\icons\help_remove_bugs.jpg")
        self.help_remove_grass = cv2.imread(r"assert\datasets\icons\help_remove_grass.jpg")
        self.help_watering = cv2.imread(r"assert\datasets\icons\help_watering.jpg")

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

            # 优先处理自家农场事件
            if self.now_scene == "home":
                if self.process_self_farm(game_frame):
                    return
                else:
                    self.logger.info("家里已无可执行的任务，下一轮巡查将尝试查看其它好友家可执行的任务")
                    self.now_scene = "friend"
            else:       # 自家地里没事干的时候尝试去偷菜
                if self.process_friend_farm(game_frame):
                    return
                else:
                    self.logger.info("好友农场已无可执行的任务，下一轮巡查将回家查看是否有可执行的任务")
                    self.now_scene = "home"

            # self.logger.info("无可执行的任务，继续等待下一轮检查")
        else:
            self.logger.warning("未找到游戏窗口，请检查游戏是否开启并确保窗口在前台")



    def process_self_farm(self, game_frame):
        '''
        处理自家农场事件
        '''
        # 检测重连按钮
        if self.check_reconnect(game_frame):
            return True
        # 检测欢迎回来界面
        if self.check_welcome_back(game_frame):
            return True
        # 检测一键收获按钮
        if self.check_harvest_all(game_frame):
            return True
        # 检测单个收获按钮
        if self.check_harvest_one(game_frame):
            return True
        # 检测获得新种子页面
        if self.check_get_new_seed(game_frame):
            return True
        # 检测升级提示窗口
        if self.check_level_up(game_frame):
            return True
        # 检测一键浇水按钮
        if self.check_watering_all(game_frame):
            return True
        # 检测一键除草按钮
        if self.check_remove_all_grass(game_frame):
            return True
        
        return False

    def process_friend_farm(self, game_frame):
        '''
        处理好友农场事件
        '''
        # 检测好友按钮
        if self.check_friend_icon(game_frame):
            self.now_scene = "friend_list"
            return True
        if self.now_scene == "friend_list":     # 在好友列表界面
            # 检测可以偷的图标
            if self.check_steal_icon(game_frame):
                self.now_scene = "friend_farm"  # 在好友农场界面
                return True 
            # 检测可以帮忙除草的图标
            if self.check_help_remove_grass(game_frame):
                self.now_scene = "friend_farm"  # 在好友农场界面
                return True
            # 检测可以帮忙浇水的图标
            if self.check_help_watering(game_frame):
                self.now_scene = "friend_farm"  # 在好友农场界面
                return True
            # 检测可以帮忙除虫的图标
            if self.check_help_remove_bugs(game_frame):
                self.now_scene = "friend_farm"  # 在好友农场界面
                return True
            # 没有好友任务，点击X返回
            self.check_close_x_icon(game_frame)
            return False
        
        if self.now_scene == "friend_farm":
            # 检测一键偷取按钮
            if self.check_steal_all_icon(game_frame):
                return True
            # 检测单个收获按钮（四方格地无法一键偷取）
            if self.check_harvest_one(game_frame):
                return True
            # 检测是否能帮忙浇水
            if self.check_watering_all(game_frame):
                return True
            # 检测是否能帮忙除草
            if self.check_remove_all_grass(game_frame):
                return True
            # 检测是否能帮忙除虫
            if self.check_remove_all_bugs(game_frame):
                return True
            # 以上都没有则回家
            if self.check_go_home_icon(game_frame):
                self.now_scene = "home"
                return True

        return False


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

    def check_help_remove_bugs(self, game_frame):
        '''
        检查是否可以帮忙除虫
        Returns:
            bool: 是否可以帮忙除虫
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.help_remove_bugs, threshold=0.6)
        if match_result is not None:        # 可以帮忙除虫
            self.logger.info(f"检测到【可帮忙除虫】图标，准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将点击位置偏移到【拜访】区域
            center_x = match_result['center'][0]
            center_y = match_result['center'][1]
            pias_x = center_x + 181
            pias_y = center_y - 10
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate((pias_x,pias_y))
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【可帮忙除虫】图标, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_help_remove_grass(self, game_frame):
        '''
        检查是否可以帮忙除草
        Returns:
            bool: 是否可以帮忙除草
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.help_remove_grass, threshold=0.6)
        if match_result is not None:        # 可以帮忙除草
            self.logger.info(f"检测到【可帮忙除草】图标，准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将点击位置偏移到【拜访】区域
            center_x = match_result['center'][0]
            center_y = match_result['center'][1]
            pias_x = center_x + 181
            pias_y = center_y - 10
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate((pias_x,pias_y))
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【可帮忙除草】图标, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_help_watering(self, game_frame):
        '''
        检查是否可以帮忙浇水
        Returns:
            bool: 是否可以帮忙浇水
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.help_watering, threshold=0.6)
        if match_result is not None:        # 可以帮忙浇水
            self.logger.info(f"检测到【可帮忙浇水】图标，准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将点击位置偏移到【拜访】区域
            center_x = match_result['center'][0]
            center_y = match_result['center'][1]
            pias_x = center_x + 181
            pias_y = center_y - 10
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate((pias_x,pias_y))
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【可帮忙浇水】图标, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_close_x_icon(self, game_frame):
        '''
        检查是否点击了关闭按钮
        Returns:
            bool: 是否点击了关闭按钮
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.close_x_frame, threshold=0.5)
        if match_result is not None:        # 点击了关闭按钮
            self.logger.info(f"检测到【关闭】按钮，准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【关闭】按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False



    def check_go_home_icon(self, game_frame):
        '''
        检查是否有一键回家的图标
        Returns:
            bool: 是否有一键回家的图标
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.go_home_frame, threshold=0.5)
        if match_result is not None:        # 有一键回家图标
            self.logger.info(f"检测到【一键回家】图标，准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【一键回家】图标, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False


    def check_steal_all_icon(self, game_frame):
        '''
        检查是否有一键偷取的图标
        Returns:
            bool: 是否有一键偷取的图标
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.steal_all_frame, threshold=0.5)
        if match_result is not None:        # 有一键偷取图标
            self.logger.info(f"检测到【一键偷取】图标，准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【一键偷取】图标, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False


    def check_steal_icon(self, game_frame):
        '''
        检查是否有可以偷菜的图标
        Returns:
            bool: 是否点击了偷菜图标
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.can_steal_frame, threshold=0.6)
        if match_result is not None:        # 点击了偷菜图标
            self.logger.info(f"检测到【可以偷的图标】，准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将点击位置偏移到【拜访】区域
            center_x = match_result['center'][0]
            center_y = match_result['center'][1]
            pias_x = center_x + 181
            pias_y = center_y - 10
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate((pias_x, pias_y))
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【可以偷的图标】, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False

    def check_friend_icon(self, game_frame):
        '''
        检查是否点击了好友图标
        Returns:
            bool: 是否点击了好友图标
        '''
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.friend_icon_frame, threshold=0.47)
        if match_result is not None:        # 点击了好友图标
            self.logger.info(f"检测到【好友图标】，准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【好友图标】, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False


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
            self.now_scene = "home"     # 只有在自家地里才会弹出这个窗口
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
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.remove_all_bugs_frame, threshold=0.5)
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
        match_result, max_val, threshold = self.cv_match.match_template(game_frame, self.reconnect_frame, threshold=0.5)
        if match_result is not None:        # 有重新登录按钮
            self.logger.info(f"检测到【重新登录】按钮,准备点击, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            # 将局部坐标转换为屏幕坐标
            screen_center = self.convert_to_screen_coordinate(match_result['center'])   # 直接点击中间即可
            self.click_at_position(screen_center)
            return True
        else:
            self.logger.debug(f"未检测到【重新登录】按钮, 最高置信度：{max_val:.4f} (阈值：{threshold})")
            return False
        