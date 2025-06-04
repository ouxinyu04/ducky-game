import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WEAPON_ATTACK_BOOST
from config import IMAGES_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class Weapon:
    def __init__(self, x, y, weapon_type):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.weapon_type = weapon_type
        self.collected = False
        self.image = None
        image_path = os.path.join(IMAGES_DIR, f"weapon_{weapon_type}.png")
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load weapon_{weapon_type}.png: {e}")

    def draw(self, screen):
        if self.image and not self.collected:
            screen.blit(self.image, (self.x, self.y))
        elif not self.collected:
            pygame.draw.rect(screen, (128, 128, 128), (self.x, self.y, self.width, self.height))

def create_weapons(num_weapons):
    weapons = []
    for _ in range(num_weapons):
        x = random.randint(0, SCREEN_WIDTH - 20)
        y = random.randint(0, SCREEN_HEIGHT - 20)
        weapon_type = random.randint(1, 8)
        weapons.append(Weapon(x, y, weapon_type))
    return weapons