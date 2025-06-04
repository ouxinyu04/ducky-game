import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WEAPON_ATTACK_BOOST
from config import IMAGES_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR, encoding='utf-8')

class Partner:
    def __init__(self, x, y, index):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.index = index
        self.attack_power = 5
        self.hp = 50
        self.max_hp = 50
        self.is_alive = True
        self.held_weapon = None
        self.collected = False  # 添加 collected 属性
        self.image = None
        image_path = os.path.join(IMAGES_DIR, "partner.png")
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"加载 partner.png 失败: {e}")

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.rect(screen, (0, 0, 255), (self.x, self.y, self.width, self.height))

    def equip_weapon(self, weapon):
        if not self.held_weapon:
            self.held_weapon = weapon
            self.attack_power += WEAPON_ATTACK_BOOST
            logging.info(f"伙伴 {self.index} 装备了武器")

    def unequip_weapon(self):
        if self.held_weapon:
            self.attack_power -= WEAPON_ATTACK_BOOST
            self.held_weapon = None
            logging.info(f"伙伴 {self.index} 卸下了武器")

def create_partners(num_partners):
    partners = []
    for i in range(num_partners):
        x = random.randint(0, SCREEN_WIDTH - 30)
        y = random.randint(0, SCREEN_HEIGHT - 30)
        partners.append(Partner(x, y, i + 1))
    return partners