import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, RED
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class Weapon:
    def __init__(self, x, y, weapon_type):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.color = RED
        self.collected = False
        self.weapon_type = weapon_type
        image_path = os.path.join(ASSETS_DIR, f"Weapon {weapon_type}.png")
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load Weapon {weapon_type}.png: {e}")

    def draw(self, screen):
        if not self.collected:
            if self.image:
                screen.blit(self.image, (self.x, self.y))
            else:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

def create_weapons(num):
    return [Weapon(random.randint(0, SCREEN_WIDTH - 20), random.randint(0, SCREEN_HEIGHT - 20), random.randint(1, 8)) for _ in range(num)]