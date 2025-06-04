# npc.py (修正版)
import pygame
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, PINK, GREEN, BLUE
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)


class NPC:
    def __init__(self, x, y, npc_type="lady_duck"):
        self.x = x
        self.y = y
        self.width = 60  # 增大尺寸以适应动画
        self.height = 60
        self.npc_type = npc_type

        # 初始化动画属性
        self.gif_frames = []
        self.current_frame = 0
        self.frame_time = 200  # 每帧200毫秒
        self.last_frame_update = 0

        # 设置NPC属性
        if npc_type == "lady_duck":
            self.color = PINK
            self.charm_requirement = 10
            self.image_name = "lady_duck.png"
        elif npc_type == "broccoli_general":
            self.color = GREEN
            self.charm_requirement = 15
            self.image_name = "broccoli_general.png"
        elif npc_type == "human_child":
            self.color = BLUE
            self.charm_requirement = 8
            self.image_name = "human_child.png"
        # 支持动画类型的NPC
        elif npc_type == "duck_friend_animation":
            self.color = PINK
            self.charm_requirement = 8
            self.image_name = "duck_friend_animation.gif"
        elif npc_type == "bat_animation":
            self.color = (128, 0, 128)  # 紫色
            self.charm_requirement = 12
            self.image_name = "bat_animation.gif"
        elif npc_type == "good_boy_animation":
            self.color = BLUE
            self.charm_requirement = 10
            self.image_name = "good_boy_animation.gif"
        elif npc_type == "lady_duck_animation":
            self.color = PINK
            self.charm_requirement = 10
            self.image_name = "chicken_animation.gif"
        elif npc_type == "mushroom_animation":
            self.color = GREEN
            self.charm_requirement = 15
            self.image_name = "mushroom_animation.gif"
        elif npc_type == "chicken_animation":
            self.color = (255, 165, 0)  # 橙色
            self.charm_requirement = 8
            self.image_name = "chicken_animation.gif"
        else:
            # 默认值
            self.color = PINK
            self.charm_requirement = 10
            self.image_name = "lady_duck.png"

        # 加载图像或动画
        self.image = None
        if self.image_name.endswith('.gif'):
            # 加载GIF动画
            self.load_gif_animation()
        else:
            # 加载静态图像
            image_path = os.path.join(ASSETS_DIR, self.image_name)
            if os.path.exists(image_path):
                try:
                    self.image = pygame.image.load(image_path)
                    self.image = pygame.transform.scale(self.image, (self.width, self.height))
                except pygame.error as e:
                    logging.error(f"Failed to load {self.image_name}: {e}")

    def load_gif_animation(self):
        """加载GIF动画"""
        try:
            from animation_utils import load_animation_frames
            self.gif_frames, _ = load_animation_frames(self.image_name, target_size=(self.width, self.height))
            if self.gif_frames:
                logging.info(f"Loaded NPC animation {self.image_name} with {len(self.gif_frames)} frames")
            else:
                logging.warning(f"Failed to load NPC animation {self.image_name}")
        except Exception as e:
            logging.error(f"Error loading NPC animation {self.image_name}: {e}")
            self.gif_frames = []

    def draw(self, screen):
        # 如果有动画帧，播放动画
        if self.gif_frames:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_frame_update >= self.frame_time:
                self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                self.last_frame_update = current_time

            # 绘制当前动画帧
            screen.blit(self.gif_frames[self.current_frame], (self.x, self.y))
        elif self.image:
            # 绘制静态图像
            screen.blit(self.image, (self.x, self.y))
        else:
            # 绘制颜色方块作为备用
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def convert_to_partner(self, partner_index):
        """将NPC转换为伙伴"""
        # 延迟导入避免循环引用
        from partner import Partner

        partner = Partner(self.x, self.y, partner_index, is_special=True, npc_type=self.npc_type)
        partner.collected = True

        # 复制NPC的图像和动画到伙伴对象
        if self.gif_frames:
            # 复制动画帧
            partner.gif_frames = self.gif_frames.copy()
            partner.current_frame = 0
            partner.frame_time = self.frame_time
            partner.last_frame_update = 0
        elif self.image:
            # 复制静态图像
            partner.image = self.image

        return partner