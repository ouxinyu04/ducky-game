# duck.py (导入修正版)
import pygame
import random
import os
import logging
import traceback
from PIL import Image
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, ORANGE, BLACK, MAX_PARTNERS, HP_LOSS_PER_BATTLE
from weapon import Weapon
from partner import Partner
from enemy import Enemy
# 移除导入 from npc import NPC，改为在需要时动态导入
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)


class Duck:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 80
        self.speed = 0.8
        self.color = ORANGE
        self.weapons = []
        self.partners = []
        self.attack_power = 10
        self.charm = 5
        self.reputation = 0
        self.is_alive = True
        self.buffs = []
        self.lucky_buff_active = False

        # 图像加载
        self.png_image = None
        png_path = os.path.join(ASSETS_DIR, "duck.png")
        if os.path.exists(png_path):
            try:
                self.png_image = pygame.image.load(png_path)
                self.png_image = pygame.transform.scale(self.png_image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load duck.png: {e}")
        self.gif_frames = []
        self.current_frame = 0
        self.frame_time = 100
        self.last_frame_update = 0
        gif_path = os.path.join(ASSETS_DIR, "duck.gif")
        if os.path.exists(gif_path):
            try:
                gif = Image.open(gif_path)
                for frame in range(gif.n_frames):
                    gif.seek(frame)
                    frame_image = gif.convert("RGBA")

                    # 创建带透明度的pygame surface
                    pygame_image = pygame.Surface(frame_image.size, pygame.SRCALPHA)
                    pygame_image = pygame.image.fromstring(frame_image.tobytes(), frame_image.size, frame_image.mode)

                    # 确保surface支持透明度
                    pygame_image = pygame_image.convert_alpha()

                    # 缩放时保持透明度
                    scaled_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    pygame.transform.scale(pygame_image, (self.width, self.height), scaled_surface)
                    self.gif_frames.append(scaled_surface)
            except Exception as e:
                logging.error(f"Failed to load duck.gif: {e}")
        if not self.gif_frames:
            self.gif_frames = [self.png_image] if self.png_image else [pygame.Surface((self.width, self.height))]

        # 骰子相关属性
        self.dice_images = {}
        for i in range(1, 7):
            dice_path = os.path.join(ASSETS_DIR, f"dice_{i}.png")
            if os.path.exists(dice_path):
                try:
                    dice_image = pygame.image.load(dice_path)
                    self.dice_images[i] = pygame.transform.scale(dice_image, (30, 30))
                except pygame.error as e:
                    logging.error(f"Failed to load dice_{i}.png: {e}")
        self.dice_state = None
        self.dice_result = None
        self.dice_animation_start = 0
        self.dice_animation_duration = 1000
        self.dice_display_time = 3000
        self.dice_current_number = 1
        self.success_threshold = 0
        self.interaction_result = None
        self.interaction_completed = False
        self.challenge_type = None
        self.e_pressed = False

    # duck.py 中 interact 方法排版优化
    def interact(self, target, screen, font, game_state, events):
        try:
            # 需要时动态导入NPC
            from npc import NPC

            current_time = pygame.time.get_ticks()
            if self.interaction_completed and self.interaction_result is not None:
                logging.info(f"Interaction completed: {self.interaction_result}")
                return True

            lucky_bonus = 2 if self.lucky_buff_active else 0
            if self.lucky_buff_active:
                self.lucky_buff_active = False
                self.buffs.remove("幸运 BUFF")
                logging.info("Lucky BUFF consumed")

            # 初始化挑战信息
            if self.dice_state is None:
                self.interaction_completed = False
                if isinstance(target, NPC):
                    self.challenge_type = "魅力"
                    self.success_threshold = max(1, target.charm_requirement - self.charm)
                elif isinstance(target, dict) and target["type"] == "trap":
                    self.challenge_type = "智慧"
                    self.success_threshold = 4
                elif isinstance(target, Enemy) and target.is_special:
                    self.challenge_type = "勇气"
                    self.success_threshold = 4
                self.dice_state = "showing_condition"
                logging.info(f"Starting interaction: type={self.challenge_type}, threshold={self.success_threshold}")

            if self.dice_state in ["showing_condition", "animating", "showing_result"]:
                # 绘制暗色背景
                dark_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                dark_background.set_alpha(150)
                dark_background.fill((0, 0, 0))
                screen.blit(dark_background, (0, 0))

            if self.dice_state == "showing_condition":
                background = pygame.Surface((400, 180))  # 增加高度以容纳更多信息
                background.set_alpha(200)
                background.fill((255, 255, 255))
                screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 90))

                # 标题 - 居中
                title_text = font.render(f"{self.challenge_type}挑战", True, BLACK)
                title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 65))
                screen.blit(title_text, title_rect)

                # 分隔线
                pygame.draw.line(screen, BLACK,
                                 (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 40),
                                 (SCREEN_WIDTH // 2 + 180, SCREEN_HEIGHT // 2 - 40), 1)

                # 成功条件 - 左对齐
                condition_text = font.render(f"成功条件:", True, BLACK)
                screen.blit(condition_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 30))

                detail_text = font.render(f"需要掷出 {self.success_threshold} 或更高点数", True, BLACK)
                screen.blit(detail_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))

                # 加成信息 - 左对齐
                bonus_text = "无"
                if lucky_bonus > 0:
                    bonus_text = f"+{lucky_bonus} (幸运BUFF)"

                bonus_label = font.render(f"骰子加成:", True, BLACK)
                bonus_value = font.render(bonus_text, True, (0, 128, 0) if lucky_bonus > 0 else BLACK)
                screen.blit(bonus_label, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 30))
                screen.blit(bonus_value, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 30))

                # 操作提示 - 底部居中
                prompt = font.render("按 E 键掷骰子", True, BLACK)
                prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
                screen.blit(prompt, prompt_rect)

                # 检查键盘事件
                for event in events:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                        self.dice_state = "animating"
                        self.dice_animation_start = current_time
                        self.dice_result = random.randint(1, 6) + lucky_bonus
                        logging.info(f"E key pressed, dice rolled: {self.dice_result}")
                        self.e_pressed = True
                        break
                return False

            if self.dice_state == "animating":
                if current_time - self.dice_animation_start < self.dice_animation_duration:
                    background = pygame.Surface((400, 180))
                    background.set_alpha(200)
                    background.fill((255, 255, 255))
                    screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 90))

                    # 标题
                    title_text = font.render(f"{self.challenge_type}挑战", True, BLACK)
                    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 65))
                    screen.blit(title_text, title_rect)

                    # 分隔线
                    pygame.draw.line(screen, BLACK,
                                     (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 40),
                                     (SCREEN_WIDTH // 2 + 180, SCREEN_HEIGHT // 2 - 40), 1)

                    # 成功条件
                    condition_text = font.render(f"成功条件: 需要 ≥ {self.success_threshold}", True, BLACK)
                    screen.blit(condition_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 30))

                    # 显示骰子动画
                    if (current_time - self.dice_animation_start) % 100 < 50:
                        self.dice_current_number = random.randint(1, 6)

                    # 居中显示骰子
                    if self.dice_current_number in self.dice_images:
                        dice_img = self.dice_images[self.dice_current_number]
                        dice_rect = dice_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
                        screen.blit(dice_img, dice_rect)
                    else:
                        dice_text = font.render(f"骰子: {self.dice_current_number}", True, BLACK)
                        dice_rect = dice_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
                        screen.blit(dice_text, dice_rect)

                    # 底部提示
                    rolling_text = font.render("正在掷骰子...", True, BLACK)
                    rolling_rect = rolling_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
                    screen.blit(rolling_text, rolling_rect)
                    return False
                else:
                    self.dice_state = "showing_result"
                    self.dice_animation_start = current_time
                    self.dice_current_number = self.dice_result
                    if self.dice_result >= self.success_threshold:
                        self.interaction_result = f"成功：{self.challenge_type}挑战通过！"
                    else:
                        self.interaction_result = f"失败：{self.challenge_type}挑战未通过。"
                    logging.info(f"Dice result: {self.dice_result}, Interaction result: {self.interaction_result}")

            if self.dice_state == "showing_result":
                if current_time - self.dice_animation_start < self.dice_display_time:
                    background = pygame.Surface((400, 180))
                    background.set_alpha(200)
                    background.fill((255, 255, 255))
                    screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 90))

                    # 标题
                    title_text = font.render(f"{self.challenge_type}挑战", True, BLACK)
                    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 65))
                    screen.blit(title_text, title_rect)

                    # 分隔线
                    pygame.draw.line(screen, BLACK,
                                     (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 40),
                                     (SCREEN_WIDTH // 2 + 180, SCREEN_HEIGHT // 2 - 40), 1)

                    # 成功条件
                    condition_text = font.render(f"成功条件: 需要 ≥ {self.success_threshold}", True, BLACK)
                    screen.blit(condition_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 30))

                    # 显示骰子结果
                    result_text = font.render(f"掷出点数: {self.dice_result}", True, BLACK)
                    screen.blit(result_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))

                    # 居中显示骰子图像
                    if self.dice_result in self.dice_images:
                        dice_img = self.dice_images[self.dice_result]
                        dice_rect = dice_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
                        screen.blit(dice_img, dice_rect)

                    # 显示挑战结果
                    outcome_color = (0, 200, 0) if self.dice_result >= self.success_threshold else (200, 0, 0)
                    outcome_text = font.render(self.interaction_result, True, outcome_color)
                    outcome_rect = outcome_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                    screen.blit(outcome_text, outcome_rect)
                    return False
                else:
                    self.dice_state = None
                    self.dice_result = None
                    self.success_threshold = 0
                    success = self.interaction_result and self.interaction_result.startswith("成功")
                    self.interaction_result = None
                    if success:
                        game_state.handle_interaction_success(target)
                    logging.info(f"Interaction ended, success: {success}")
                    logging.error(traceback.format_exc())
                    self.dice_state = None
                    self.interaction_result = None
                    self.e_pressed = False
                    if "critical" in str(e).lower():
                        self.interaction_completed = True
                        return True
                    return False


            return False
        except Exception as e:
            logging.error(f"交互失败: {e}")
            self.interaction_completed = True
            self.e_pressed = False
            self.interaction_result = "交互失败"
            return True

    # 其他方法...
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if self.is_alive:
            if self.gif_frames:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_frame_update >= self.frame_time:
                    self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                    self.last_frame_update = current_time
                screen.blit(self.gif_frames[self.current_frame], (self.x, self.y))
            elif self.png_image:
                screen.blit(self.png_image, (self.x, self.y))
            else:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def move(self, keys):
        if keys[pygame.K_a] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_d] and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed
        if keys[pygame.K_w] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_s] and self.y < SCREEN_HEIGHT - self.height:
            self.y += self.speed

    def collect(self, item):
        if isinstance(item, Weapon):
            self.weapons.append(item)
            self.attack_power += item.attack_power
            print(f"获得武器！攻击力 +{item.attack_power}，总攻击力：{self.attack_power}")
            return True
        elif isinstance(item, Partner):
            # MAX_PARTNERS 已修改为允许收集无限伙伴
            self.partners.append(item)
            print(f"伙伴加入！总伙伴数：{len(self.partners)}")
            return True
        return False

    def get_total_power(self):
        base_power = self.attack_power + sum(
            partner.get_total_power(self.buffs) for partner in self.partners if partner.is_alive)
        logging.info(f"Total power calculated: {base_power}")
        return base_power

    def take_battle_loss(self):
        for partner in self.partners:
            if partner.is_alive:
                partner_loss = int(partner.max_hp * HP_LOSS_PER_BATTLE)
                partner.hp = max(1, partner.hp - partner_loss)
                print(f"伙伴 {partner.index} 受到伤害！")

    def recover(self):
        for partner in self.partners:
            if partner.is_alive:
                partner.hp = partner.max_hp
        print("鸭子和伙伴 HP 完全恢复！")

    def add_buff(self, buff):
        if buff == "勇敢 BUFF" and "勇敢 BUFF" not in self.buffs:
            self.attack_power += 15
            self.buffs.append("勇敢 BUFF")
            print("获得勇敢 BUFF：战力 +15")
            logging.info("Brave BUFF added, attack_power +15")
        elif buff == "幸运 BUFF" and "幸运 BUFF" not in self.buffs:
            self.buffs.append("幸运 BUFF")
            self.lucky_buff_active = True
            print("获得幸运 BUFF：骰子点数 +2")
            logging.info("Lucky BUFF added")
        elif buff == "魅力 BUFF" and "魅力 BUFF" not in self.buffs:
            self.charm += 15
            self.buffs.append("魅力 BUFF")
            print("获得魅力 BUFF：魅力 +15")
            logging.info("Charm BUFF added")
        elif buff == "恢复 HP" and "恢复 HP" not in self.buffs:
            self.recover()
            self.buffs.append("恢复 HP")
            print("获得恢复 HP：伙伴HP 完全恢复")
            logging.info("Recover HP BUFF added")
        else:
            print(f"BUFF {buff} 已存在或无效")
            logging.warning(f"Attempted to add duplicate or invalid BUFF: {buff}")