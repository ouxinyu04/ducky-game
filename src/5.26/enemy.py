# enemy.py
import pygame
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, RED
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)


class Enemy:
    def __init__(self, x, y, enemy_type="human", is_boss=False, is_special=False):
        self.x = x
        self.y = y
        self.width = 50 if is_boss else 30
        self.height = 50 if is_boss else 30
        self.enemy_type = enemy_type
        self.is_boss = is_boss
        self.is_special = is_special

        # 初始化HP属性
        self.hp = 250 if is_boss else 50
        self.max_hp = 250 if is_boss else 50

        if enemy_type == "human":
            self.attack_power = 12
        elif enemy_type == "traitor_duck":
            self.attack_power = 10
        elif enemy_type == "soul":
            self.attack_power = 8
        elif enemy_type == "ingredient":
            self.attack_power = 6
        if is_boss:
            self.attack_power = 50  # BOSS 固定战力
        if is_special:
            self.attack_power = int(self.attack_power * 1.5)  # 特殊敌人战力增加 50%
        image_name = "boss_human.png" if is_boss else f"{enemy_type}.png"
        image_path = os.path.join(ASSETS_DIR, image_name)
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load {image_name}: {e}")

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))