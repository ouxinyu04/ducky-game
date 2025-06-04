import pygame
import random
import os
import logging
from PIL import Image
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, ORANGE, BLACK, MAX_PARTNERS, HP_LOSS_PER_BATTLE
from weapon import Weapon
from partner import Partner
from enemy import Enemy
from npc import NPC
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class Duck:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.speed = 0.67
        self.color = ORANGE
        self.weapons = []
        self.partners = []
        self.attack_power = 10
        self.charm = 5
        self.reputation = 0
        self.hp = 100
        self.max_hp = 100
        self.is_alive = True
        self.buffs = []
        self.lucky_buff_active = False
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
                    pygame_image = pygame.image.fromstring(frame_image.tobytes(), frame_image.size, frame_image.mode)
                    pygame_image = pygame.transform.scale(pygame_image, (self.width, self.height))
                    self.gif_frames.append(pygame_image)
            except Exception as e:
                logging.error(f"Failed to load duck.gif: {e}")
        if not self.gif_frames:
            self.gif_frames = [self.png_image] if self.png_image else [pygame.Surface((self.width, self.height))]
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
            if len(self.partners) < MAX_PARTNERS:
                self.partners.append(item)
                print(f"伙伴加入！总伙伴数：{len(self.partners)}")
                return True
            else:
                print("队伍已满！")
                return False
        return False

    def get_total_power(self):
        base_power = self.attack_power + sum(partner.attack_power for partner in self.partners if partner.is_alive)
        logging.info(f"Total power calculated: {base_power}")
        return base_power

    def take_battle_loss(self):
        loss = int(self.max_hp * HP_LOSS_PER_BATTLE)
        self.hp = max(1, self.hp - loss)
        print(f"鸭子损失 {loss} HP，剩余 HP：{self.hp}")
        for partner in self.partners:
            if partner.is_alive:
                partner_loss = int(partner.max_hp * HP_LOSS_PER_BATTLE)
                partner.hp = max(1, partner.hp - partner_loss)
                print(f"伙伴 {partner.index} 损失 {partner_loss} HP，剩余 HP：{partner.hp}")

    def recover(self):
        self.hp = self.max_hp
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
            print("获得恢复 HP：HP 完全恢复")
            logging.info("Recover HP BUFF added")
        else:
            print(f"BUFF {buff} 已存在或无效")
            logging.warning(f"Attempted to add duplicate or invalid BUFF: {buff}")

    def interact(self, target, screen, font, game_state, events):
        try:
            current_time = pygame.time.get_ticks()
            if self.interaction_completed:
                logging.info(f"Interaction completed: {self.interaction_result}")
                return True

            lucky_bonus = 2 if self.lucky_buff_active else 0
            if self.lucky_buff_active:
                self.lucky_buff_active = False
                self.buffs.remove("幸运 BUFF")
                logging.info("Lucky BUFF consumed")

            if self.dice_state in ["showing_condition", "animating", "showing_result"]:
                game_state.handle_exploration(screen, pygame.key.get_pressed(), [])
                dark_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                dark_background.set_alpha(150)
                dark_background.fill((0, 0, 0))
                screen.blit(dark_background, (0, 0))

            if self.dice_state == "showing_condition":
                background = pygame.Surface((400, 100))
                background.set_alpha(200)
                background.fill((255, 255, 255))
                screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))
                text = font.render(f"{self.challenge_type}挑战：骰子 ≥ {self.success_threshold}", True, BLACK)
                screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 30))
                prompt = font.render("按 E 键掷骰子", True, BLACK)
                screen.blit(prompt, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 10))
                pygame.display.flip()
                for event in events:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_e and not self.e_pressed:
                        logging.info("E key pressed, starting dice animation")
                        self.dice_state = "animating"
                        self.dice_animation_start = current_time
                        self.dice_result = random.randint(1, 6) + lucky_bonus
                        logging.info(f"Dice rolled: {self.dice_result}")
                        self.e_pressed = True
                return False

            if self.dice_state == "animating":
                if current_time - self.dice_animation_start < self.dice_animation_duration:
                    if (current_time - self.dice_animation_start) % 100 < 50:
                        self.dice_current_number = random.randint(1, 6)
                    if self.dice_current_number in self.dice_images:
                        screen.blit(self.dice_images[self.dice_current_number], (SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2))
                    else:
                        text = font.render(f"骰子: {self.dice_current_number}", True, BLACK)
                        screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
                    pygame.display.flip()
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
                    if self.dice_result in self.dice_images:
                        screen.blit(self.dice_images[self.dice_result], (SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2))
                        result_text = font.render(f"点数: {self.dice_result}", True, BLACK)
                        screen.blit(result_text, (SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT // 2 - 30))
                        outcome_text = font.render(self.interaction_result, True, BLACK)
                        screen.blit(outcome_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40))
                    else:
                        text = font.render(f"骰子结果: {self.dice_result}", True, BLACK)
                        screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
                        outcome_text = font.render(self.interaction_result, True, BLACK)
                        screen.blit(outcome_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40))
                    pygame.display.flip()
                    return False
                else:
                    self.dice_state = None
                    self.dice_result = None
                    self.success_threshold = 0
                    success = self.interaction_result and self.interaction_result.startswith("成功")
                    self.interaction_result = None
                    self.interaction_completed = True
                    self.challenge_type = None
                    self.e_pressed = False
                    if success:
                        game_state.handle_interaction_success(target)
                    logging.info(f"Interaction ended, success: {success}")
                    return True

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
            return False
        except Exception as e:
            logging.error(f"交互失败: {e}")
            self.interaction_completed = True
            self.e_pressed = False
            self.interaction_result = "交互失败"
            return True