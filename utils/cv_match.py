import cv2

class cvMatch:
    def __init__(self):
        pass

    def match_template(self, full_capture_image, need_match_image, threshold=0.4):
        """
        在全局图片上匹配局部图片的位置
        
        Args:
            need_match_image: 局部图片（模板）路径
            full_capture_image: 全局图片
            threshold: 匹配置信度阈值，默认 0.4
        
        Returns:
            dict: 包含匹配结果的信息，包括坐标和置信度
                如果未找到匹配，返回 None
        """
        if need_match_image is None:
            print(f"错误：无法读取模板图片")
            return None
        
        if full_capture_image is None:
            print(f"错误：无法读取全局图片")
            return None
        
        # 获取模板尺寸
        template_height, template_width = need_match_image.shape[:2]
        
        # 执行模板匹配
        result = cv2.matchTemplate(full_capture_image, need_match_image, cv2.TM_CCOEFF_NORMED)
        
        # 获取最佳匹配位置和分数
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            # 找到匹配
            top_left = max_loc
            bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
            
            return {
                'top_left': top_left,
                'bottom_right': bottom_right,
                'confidence': float(max_val),
                'center': (
                    top_left[0] + template_width // 2,
                    top_left[1] + template_height // 2
                )
            } , max_val, threshold
        else:
            # print(f"未找到匹配，最高置信度：{max_val:.4f} (阈值：{threshold})")
            return None, max_val, threshold
