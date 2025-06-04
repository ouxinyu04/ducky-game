import pygame
import random
import os
import logging
from PIL import Image
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, ORANGE, BLACK, WEAPON_ATTACK_BOOST, MAX_PARTNERS
from weapon import Weapon
from partner import Partner
from config import IMAGES_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR, encoding='utf-8')

class Duck:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.speed = 5
        self.color = ORANGE
        self.weapons = []
        self.held_weapon = None
        self.partners = []
        self.attack_power = 10
        self.charm = 5
        self.reputation = 0
        self.hp = 100
        self.max_hp = 100
        self.is_alive = True
        self.is_moving = False
        # 加载图像
        self.png_image = None
        png_path = os.path.join(IMAGES_DIR, "duck.png")
        logging.info(f"尝试加载图片: {png_path}")
        if os.path.exists(png_path):
            try:
                self.png_image = pygame.image.load(png_path).convert_alpha()  # 确保透明度支持
                self.png_image = pygame.transform.scale(self.png_image, (self.width, self.height))
                logging.info(f"成功加载图片: {png_path}")
            except pygame.error as e:
                logging.error(f"加载 {png_path} 失败: {e}")
                self.png_image = None
        else:
            logging.error(f"文件不存在: {png_path}")
        self.gif_frames = []
        gif_path = os.path.join(IMAGES_DIR, "duck.gif")
        if os.path.exists(gif_path):
            try:
                gif = Image.open(gif_path)
                for frame in range(gif.n_frames):
                    gif.seek(frame)
                    frame_image = gif.convert("RGBA")
                    mode = frame_image.mode
                    size = frame_image.size
                    data = frame_image.tobytes()
                    pygame_image = pygame.image.fromstring(data, size, mode)
                    pygame_image = pygame.transform.scale(pygame_image, (self.width, self.height))
                    self.gif_frames.append(pygame_image)
            except Exception as e:
                logging.error(f"加载 duck.gif 失败: {e}")
        if not self.gif_frames:
            self.gif_frames = [self.png_image] if self.png_image else [pygame.Surface((self.width, self.height))]
        self.current_frame = 0
        self.frame_time = 100
        self.last_frame_update = 0
        # 加载骰子图片
        self.dice_images = {}
        for i in range(1, 7):
            dice_path = os.path.join(IMAGES_DIR, f"dice_{i}.png")
            if os.path.exists(dice_path):
                try:
                    dice_image = pygame.image.load(dice_path)
                    self.dice_images[i] = pygame.transform.scale(dice_image, (20, 20))
                except pygame.error as e:
                    logging.error(f"加载 dice_{i}.png 失败: {e}")
        # 骰子状态
        self.dice_state = None
        self.dice_result = None
        self.dice_animation_start = 0
        self.dice_animation_duration = 1000
        self.dice_display_time = 1000
        self.dice_current_number = 1
        self.success_threshold = 0
        self.interaction_result = None
        self.interaction_completed = False

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if self.is_alive:
            if self.is_moving and self.gif_frames:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_frame_update >= self.frame_time:
                    self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                    self.last_frame_update = current_time
                screen.blit(self.gif_frames[self.current_frame], (self.x, self.y))
            else:
                if self.png_image:
                    screen.blit(self.png_image, (self.x, self.y))
                else:
                    pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
                    # 添加加载失败提示
                    font = pygame.font.SysFont("SimHei", 20)
                    text = font.render("图片加载失败！", True, BLACK)
                    screen.blit(text, (self.x, self.y - 20))

    def move(self, keys):
        self.is_moving = False
        if keys[pygame.K_a] and self.x > 0:
            self.x -= self.speed
            self.is_moving = True
        if keys[pygame.K_d] and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed
            self.is_moving = True
        if keys[pygame.K_w] and self.y > 0:
            self.y -= self.speed
            self.is_moving = True
        if keys[pygame.K_s] and self.y < SCREEN_HEIGHT - self.height:
            self.y += self.speed
            self.is_moving = True

    def collect(self, item):
        if isinstance(item, Weapon):
            self.weapons.append(item)
            return True
        elif isinstance(item, Partner):
            if len(self.partners) < MAX_PARTNERS:
                self.partners.append(item)
                return True
            return False
        return False

    def equip_weapon(self, weapon):
        if weapon in self.weapons:
            self.held_weapon = weapon
            self.attack_power += WEAPON_ATTACK_BOOST

    def unequip_weapon(self):
        if self.held_weapon:
            self.attack_power -= WEAPON_ATTACK_BOOST
            self.held_weapon = None

    def get_total_power(self):
        return self.attack_power + sum(partner.attack_power for partner in self.partners if partner.is_alive)

    def interact(self, screen, font, keys, event_type=None):
        try:
            current_time = pygame.time.get_ticks()
            if self.interaction_completed:
                return True

            if self.dice_state == "showing_condition":
                background = pygame.Surface((400, 100))
                background.set_alpha(200)
                background.fill((255, 255, 255))
                screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))
                text = font.render(f"骰子点数超过 {self.success_threshold} 即为成功", True, BLACK)
                screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 30))
                prompt = font.render("按 E 键掷骰子", True, BLACK)
                screen.blit(prompt, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 10))
                pygame.display.flip()
                if keys[pygame.K_e]:
                    self.dice_state = "animating"
                    self.dice_animation_start = current_time
                return False

            if self.dice_state == "animating":
                if current_time - self.dice_animation_start < self.dice_animation_duration:
                    if (current_time - self.dice_animation_start) % 100 < 50:
                        self.dice_current_number = random.randint(1, 6)
                    if self.dice_current_number in self.dice_images:
                        screen.blit(self.dice_images[self.dice_current_number], (SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2))
                    else:
                        text = font.render(f"掷骰中: {self.dice_current_number}", True, BLACK)
                        screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
                    pygame.display.flip()
                    return False
                else:
                    self.dice_state = "showing_result"
                    self.dice_animation_start = current_time

            if self.dice_state == "showing_result":
                if current_time - self.dice_animation_start < self.dice_display_time:
                    if self.dice_result in self.dice_images:
                        screen.blit(self.dice_images[self.dice_result], (SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2))
                        result_text = font.render(self.interaction_result, True, BLACK)
                        screen.blit(result_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30))
                    else:
                        text = font.render(f"骰子结果: {self.dice_result}", True, BLACK)
                        screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
                        result_text = font.render(self.interaction_result, True, BLACK)
                        screen.blit(result_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30))
                    pygame.display.flip()
                    return False
                else:
                    self.dice_state = None
                    self.dice_result = None
                    self.success_threshold = 0
                    self.interaction_result = None
                    self.interaction_completed = True
                    return True
                # 添加额外的状态重置
                self.dice_animation_start = 0
                self.dice_current_number = 1

            self.interaction_result = ""  # 初始化为字符串，避免 None
            self.interaction_completed = False
            if event_type == "npc":
                self.success_threshold = max(1, 4)
                self.dice_result = random.randint(1, 6)
                if self.dice_result >= self.success_threshold:
                    self.interaction_result = "成功：说服了 NPC！"
                    self.charm += 5
                else:
                    self.interaction_result = "失败：NPC 不信任你！"
                self.dice_state = "showing_condition"

            elif event_type == "trap":
                self.success_threshold = max(1, 3)
                self.dice_result = random.randint(1, 6)
                if self.dice_result >= self.success_threshold:
                    self.interaction_result = "成功：拆除了陷阱！"
                else:
                    self.interaction_result = "失败：触发了陷阱！"
                self.dice_state = "showing_condition"
            elif event_type == "special_enemy":
                self.success_threshold = max(1, 5)
                self.dice_result = random.randint(1, 6)
                if self.dice_result >= self.success_threshold:
                    self.interaction_result = "成功：削弱了敌人攻击力！"
                else:
                    self.interaction_result = "失败：敌人攻击力未受影响！"
                self.dice_state = "showing_condition"
            return False
        except Exception as e:
            logging.error(f"交互错误: {e}")
            self.interaction_completed = True
            return True