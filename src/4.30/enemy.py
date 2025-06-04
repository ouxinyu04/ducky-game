import pygame
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, RED
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class Enemy:
    def __init__(self, x, y, enemy_type="human", is_boss=False):
        self.x = x
        self.y = y
        self.width = 50 if is_boss else 30
        self.height = 50 if is_boss else 30
        self.enemy_type = enemy_type
        self.is_boss = is_boss
        if enemy_type == "human":
            self.hp = 80
            self.attack_power = 12
        elif enemy_type == "traitor_duck":
            self.hp = 60
            self.attack_power = 10
        elif enemy_type == "soul":
            self.hp = 50
            self.attack_power = 8
        elif enemy_type == "ingredient":
            self.hp = 40
            self.attack_power = 6
        if is_boss:
            self.hp *= 5
            self.attack_power *= 2
        self.max_hp = self.hp
        self.is_alive = True
        # 加载敌人图片
        image_name = "boss_human.png" if is_boss else f"{enemy_type}.png"
        image_path = os.path.join(ASSETS_DIR, image_name)
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load {image_name}: {e}")
        else:
            logging.warning(f"{image_name} not found at {image_path}. Using fallback red rectangle.")

    def draw(self, screen):
        if self.is_alive:
            if self.image:
                screen.blit(self.image, (self.x, self.y))
            else:
                pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))

    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            self.is_alive = False