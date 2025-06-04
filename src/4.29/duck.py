import pygame
import random
import os
import logging
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
        self.predict_risk = False
        self.hp = 100
        self.max_hp = 100
        self.is_alive = True
        # 加载鸭子图片
        image_path = os.path.join(ASSETS_DIR, "duck.png")
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load duck.png: {e}")
        else:
            logging.warning(f"duck.png not found at {image_path}. Using fallback orange rectangle.")

    def rect(self):
        """返回鸭子的边界框，用于碰撞检测"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if self.is_alive:
            if self.image:
                screen.blit(self.image, (self.x, self.y))
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
        base_power = self.attack_power + sum(partner.attack_power for partner in self.partners if partner.is_alive)
        return base_power

    def interact(self, npc, screen, font):
        if self.charm >= npc.charm_requirement:
            result = "Success: Charmed the duck lady!"
        else:
            dice = random.randint(1, 6)
            if dice >= 4:
                result = f"Dice: {dice} - Success: Charmed the duck lady!"
            else:
                result = f"Dice: {dice} - Failed to charm the duck lady."
        text = font.render(result, True, BLACK)
        screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)

    def predict(self, game_state, screen, font):
        if game_state.level % 5 == 0 and not game_state.in_battle:
            self.predict_risk = True
            text = font.render("Warning: Trap ahead in battle!", True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
            pygame.display.flip()
            pygame.time.wait(2000)

    def recover_after_battle(self):
        self.hp = self.max_hp
        self.is_alive = True
        for partner in self.partners:
            partner.hp = partner.max_hp
            partner.is_alive = True
        print("Duck and partners recovered after battle.")

# 调试：确认 Duck 类定义完成
print("Duck class defined.")