import pygame
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, PINK, GREEN, BLUE
from config import ASSETS_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class NPC:
    def __init__(self, x, y, npc_type="lady_duck"):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.npc_type = npc_type
        self.story_trigger = True  # 特殊NPC触发剧情
        if npc_type == "lady_duck":
            self.color = PINK
            self.charm_requirement = 10
            self.image_name = "lady_duck.png"
        elif npc_type == "broccoli_general":
            self.color = GREEN
            self.charm_requirement = 15
            self.image_name = "broccoli_general.png"
        elif npc_type == "human_child":
            self.color = BLUE
            self.charm_requirement = 8
            self.image_name = "human_child.png"
        image_path = os.path.join(ASSETS_DIR, self.image_name)
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load {self.image_name}: {e}")
        else:
            logging.warning(f"{self.image_name} not found at {image_path}. Using fallback rectangle.")

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))