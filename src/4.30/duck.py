import pygame
import random
import os
import logging
from PIL import Image
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, ORANGE, BLACK, WEAPON_ATTACK_BOOST, MAX_PARTNERS
from weapon import Weapon
from partner import Partner
from config import ASSETS_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

# 调试：确认 duck.py 被加载
print("Loading duck.py...")

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
        self.predict_risk = None
        self.hp = 100
        self.max_hp = 100
        self.is_alive = True
        self.is_moving = False
        # 加载 PNG 图像
        self.png_image = None
        png_path = os.path.join(ASSETS_DIR, "duck.png")
        if os.path.exists(png_path):
            try:
                self.png_image = pygame.image.load(png_path)
                self.png_image = pygame.transform.scale(self.png_image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load duck.png: {e}")
        else:
            logging.warning(f"duck.png not found at {png_path}. Using fallback orange rectangle.")
        # 加载 GIF 动画
        self.gif_frames = []
        self.current_frame = 0
        self.frame_time = 100  # 每帧 100ms
        self.last_frame_update = 0
        gif_path = os.path.join(ASSETS_DIR, "duck.gif")
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
                logging.error(f"Failed to load duck.gif: {e}")
        if not self.gif_frames:
            logging.warning(f"duck.gif not found or failed to load. Using duck.png.")
            self.gif_frames = [self.png_image] if self.png_image else [pygame.Surface((self.width, self.height))]
        # 加载骰子图片
        self.dice_images = {}
        for i in range(1, 7):
            dice_path = os.path.join(ASSETS_DIR, f"dice_{i}.png")
            if os.path.exists(dice_path):
                try:
                    dice_image = pygame.image.load(dice_path)
                    self.dice_images[i] = pygame.transform.scale(dice_image, (20, 20))
                except pygame.error as e:
                    logging.error(f"Failed to load dice_{i}.png: {e}")
            else:
                logging.warning(f"dice_{i}.png not found at {dice_path}. Using fallback text.")
        # 骰子动画状态
        self.dice_state = None  # "showing_condition", "animating", "showing_result", 或 None
        self.dice_result = None
        self.dice_animation_start = 0
        self.dice_animation_duration = 1000  # 1秒动画
        self.dice_display_time = 2000  # 结果显示2秒
        self.dice_current_number = 1  # 当前显示的骰子数字（用于动画）
        self.success_threshold = 0  # 成功所需的骰子点数
        self.interaction_result = None  # 存储交互结果
        self.interaction_completed = False  # 标记交互是否完成

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if self.is_alive:
            if self.is_moving and self.gif_frames:
                # 更新 GIF 帧
                current_time = pygame.time.get_ticks()
                if current_time - self.last_frame_update >= self.frame_time:
                    self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                    self.last_frame_update = current_time
                screen.blit(self.gif_frames[self.current_frame], (self.x, self.y))
            else:
                # 显示 PNG 或备用矩形
                if self.png_image:
                    screen.blit(self.png_image, (self.x, self.y))
                else:
                    pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

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
            print(f"Collected weapon! Total weapons: {len(self.weapons)}")
            return True
        elif isinstance(item, Partner):
            if len(self.partners) < MAX_PARTNERS:
                self.partners.append(item)
                print(f"Collected partner! Total partners: {len(self.partners)}")
                return True
            else:
                print("Team is full! Cannot add more partners.")
                return False
        return False

    def equip_weapon(self, weapon):
        if weapon in self.weapons:
            self.held_weapon = weapon
            self.attack_power += WEAPON_ATTACK_BOOST
            print(f"Duck equipped weapon {weapon.weapon_type}")

    def unequip_weapon(self):
        if self.held_weapon:
            self.attack_power -= WEAPON_ATTACK_BOOST
            self.held_weapon = None

    def get_total_power(self):
        base_power = self.attack_power + sum(partner.get_effective_power() for partner in self.partners if partner.is_alive)
        return base_power

    def interact(self, npc, screen, font, game_state, keys):
        try:
            current_time = pygame.time.get_ticks()
            # 如果交互已完成，直接返回
            if self.interaction_completed:
                return True

            # 显示成功条件
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

            # 处理骰子动画
            if self.dice_state == "animating":
                if current_time - self.dice_animation_start < self.dice_animation_duration:
                    # 每 100ms 更新一次骰子数字
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
                    # 动画结束，显示最终结果
                    self.dice_state = "showing_result"
                    self.dice_animation_start = current_time
            elif self.dice_state == "showing_result":
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
                    # 结束骰子显示，重置状态
                    self.dice_state = None
                    self.dice_result = None
                    self.success_threshold = 0
                    self.interaction_result = None
                    self.interaction_completed = True
                    if npc.story_trigger:
                        game_state.state = "story"
                    return True

            # 开始交互逻辑
            self.interaction_completed = False
            if self.charm >= npc.charm_requirement:
                self.interaction_result = f"Success: Charmed the {npc.npc_type}!"
                if npc.npc_type == "broccoli_general":
                    self.attack_power += 5
                elif npc.npc_type == "human_child":
                    self.reputation += 10
                if npc.story_trigger:
                    game_state.state = "story"
                text = font.render(self.interaction_result, True, BLACK)
                screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
                pygame.display.flip()
                pygame.time.wait(2000)
                self.interaction_completed = True
                return True
            else:
                self.dice_state = "showing_condition"
                self.success_threshold = max(1, npc.charm_requirement - self.charm)  # 至少需要 1 点
                self.dice_result = random.randint(1, 6)
                if self.dice_result >= self.success_threshold:
                    self.interaction_result = f"Success: Charmed the {npc.npc_type}!"
                    if npc.npc_type == "broccoli_general":
                        self.attack_power += 5
                    elif npc.npc_type == "human_child":
                        self.reputation += 10
                else:
                    self.interaction_result = f"Failed to charm the {npc.npc_type}."
                return False
        except Exception as e:
            logging.error(f"Failed to interact with NPC: {e}")
            text = font.render("交互失败！", True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(2000)
            self.interaction_completed = True
            return True

    def predict(self, game_state, screen, font):
        if game_state.level % 5 == 0 and not game_state.in_battle:
            risks = [
                ("战斗陷阱", "战斗中可能触发陷阱，造成额外伤害。1. 拆除陷阱 2. 加固掩体"),
                ("武器破坏", "武器可能被破坏，降低攻击力。1. 检查武器 2. 备用武器"),
                ("伙伴背叛", "一名伙伴可能心生怨气。1. 安抚伙伴 2. 隔离伙伴")
            ]
            risk_type, risk_text = random.choice(risks)
            self.predict_risk = risk_type
            text = font.render(risk_text, True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))
            pygame.display.flip()
            pygame.time.wait(2000)

    def recover_after_battle(self):
        self.hp = self.max_hp
        self.is_alive = True
        for partner in self.partners:
            partner.hp = partner.max_hp
            partner.hearts = 3
            partner.is_alive = True
        print("Duck and partners recovered after battle.")

# 调试：确认 Duck 类定义完成
print("Duck class defined.")