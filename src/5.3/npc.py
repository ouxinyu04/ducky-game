import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from config import IMAGES_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class NPC:
    def __init__(self, x, y, npc_type):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.npc_type = npc_type
        self.image = None
        image_path = os.path.join(IMAGES_DIR, f"{npc_type}.png")
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load NPC image {image_path}: {e}")

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y, self.width, self.height))