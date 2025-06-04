import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLUE, RED, GREEN, YELLOW, PURPLE, CYAN, ORANGE, WHITE
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class Weapon:
    def __init__(self, x, y, weapon_type):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.weapon_type = weapon_type
        self.collected = False
        # 武器类型、战力范围、颜色和图片映射
        weapon_stats = {
            "sword": {"attack_power": (4, 6), "color": RED, "image": "weapon_1.png"},
            "axe": {"attack_power": (3, 5), "color": GREEN, "image": "weapon_2.png"},
            "dagger": {"attack_power": (2, 4), "color": BLUE, "image": "weapon_3.png"},
            "bow": {"attack_power": (3, 5), "color": YELLOW, "image": "weapon_4.png"},
            "staff": {"attack_power": (2, 4), "color": PURPLE, "image": "weapon_5.png"},
            "spear": {"attack_power": (3, 5), "color": CYAN, "image": "weapon_6.png"},
            "hammer": {"attack_power": (4, 6), "color": ORANGE, "image": "weapon_7.png"},
            "shield": {"attack_power": (1, 3), "color": WHITE, "image": "weapon_8.png"}
        }
        stats = weapon_stats.get(weapon_type, {"attack_power": (2, 2), "color": BLUE, "image": None})
        self.attack_power = random.randint(*stats["attack_power"])
        self.color = stats["color"]
        self.image = None
        if stats["image"]:
            image_path = os.path.join(ASSETS_DIR, stats["image"])
            if os.path.exists(image_path):
                try:
                    self.image = pygame.image.load(image_path)
                    self.image = pygame.transform.scale(self.image, (self.width, self.height))
                except pygame.error as e:
                    logging.error(f"Failed to load {stats['image']}: {e}")
            else:
                logging.warning(f"Image file {stats['image']} not found, using default color")
        logging.info(f"Initialized weapon: {weapon_type}, attack_power={self.attack_power}")

    def draw(self, screen):
        if not self.collected:
            if self.image:
                screen.blit(self.image, (self.x, self.y))
            else:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

def create_weapons(num_weapons):
    weapons = []
    weapon_types = ["sword", "axe", "dagger", "bow", "staff", "spear", "hammer", "shield"]
    for _ in range(num_weapons):
        x = random.randint(0, SCREEN_WIDTH - 20)
        y = random.randint(0, SCREEN_HEIGHT - 20)
        weapon_type = random.choice(weapon_types)
        weapon = Weapon(x, y, weapon_type)
        logging.info(f"Created weapon: {weapon_type}, attack_power={weapon.attack_power}")
        weapons.append(weapon)
    return weapons