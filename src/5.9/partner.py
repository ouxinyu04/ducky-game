import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, GREEN
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class Partner:
    def __init__(self, x, y, index):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.color = GREEN
        self.collected = False
        self.attack_power = 5
        self.hp = 50
        self.max_hp = 50
        self.is_alive = True
        self.index = index
        image_path = os.path.join(ASSETS_DIR, "partner.png")
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load partner.png: {e}")

    def draw(self, screen):
        if not self.collected and self.is_alive:
            if self.image:
                screen.blit(self.image, (self.x, self.y))
            else:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

def create_partners(num):
    return [Partner(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30), i + 1) for i in range(num)]