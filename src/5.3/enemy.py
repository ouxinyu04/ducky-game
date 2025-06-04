import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from config import IMAGES_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class Enemy:
    def __init__(self, x, y, enemy_type, is_boss=False):
        self.x = x
        self.y = y
        self.width = 50 if is_boss else 30
        self.height = 50 if is_boss else 30
        self.attack_power = 10 if is_boss else 5
        self.hp = 50 if is_boss else 20
        self.max_hp = 50 if is_boss else 20
        self.is_alive = True
        self.is_boss = is_boss
        self.image = None
        image_path = os.path.join(IMAGES_DIR, "boss_human.png" if is_boss else random.choice(["human.png", "traitor_duck.png", "soul.png", "ingredient.png"]))
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load enemy image {image_path}: {e}")

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.width, self.height))