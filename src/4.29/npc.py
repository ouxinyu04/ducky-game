import pygame
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, PINK
from config import ASSETS_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class NPC:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.color = PINK
        self.charm_requirement = 10
        # 加载美女鸭子图片
        image_path = os.path.join(ASSETS_DIR, "lady_duck.png")
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load lady_duck.png: {e}")
        else:
            logging.warning(f"lady_duck.png not found at {image_path}. Using fallback pink rectangle.")

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))