# weapon.py 修改图片处理部分
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
            "sword": {"attack_power": (4, 6), "color": RED, "image": "Weapon 1.png"},  # 注意这里改成了有空格的文件名
            "axe": {"attack_power": (3, 5), "color": GREEN, "image": "Weapon 2.png"},
            "dagger": {"attack_power": (2, 4), "color": BLUE, "image": "Weapon 3.png"},
            "bow": {"attack_power": (3, 5), "color": YELLOW, "image": "Weapon 4.png"},
            "staff": {"attack_power": (2, 4), "color": PURPLE, "image": "Weapon 5.png"},
            "spear": {"attack_power": (3, 5), "color": CYAN, "image": "Weapon 6.png"},
            "hammer": {"attack_power": (4, 6), "color": ORANGE, "image": "Weapon 7.png"},
            "shield": {"attack_power": (1, 3), "color": WHITE, "image": "Weapon 8.png"}
        }

        stats = weapon_stats.get(weapon_type, {"attack_power": (2, 2), "color": BLUE, "image": None})

        # 根据图片名称设置战力
        image_name = stats["image"]
        if image_name and "Weapon" in image_name:
            try:
                # 从Weapon X.png提取X作为战力
                power_num = int(image_name.split(" ")[1].split(".")[0])
                self.attack_power = power_num
                logging.info(f"Set weapon power based on image name: {power_num}")
            except Exception as e:
                logging.error(f"Failed to parse weapon power from image name: {e}")
                self.attack_power = random.randint(*stats["attack_power"])
        else:
            self.attack_power = random.randint(*stats["attack_power"])

        self.color = stats["color"]
        self.image = None

        # 尝试直接加载图片
        if image_name:
            image_path = os.path.join(ASSETS_DIR, image_name)
            logging.info(f"尝试加载武器图片: {image_path}")

            if os.path.exists(image_path):
                try:
                    self.image = pygame.image.load(image_path)
                    self.image = pygame.transform.scale(self.image, (self.width, self.height))
                    logging.info(f"成功加载武器图片: {image_name}")
                except pygame.error as e:
                    logging.error(f"Failed to load {image_name}: {e}")
            else:
                logging.warning(f"图片文件未找到: {image_path}")

                # 如果原始名称不存在，尝试替代方案
                alt_image_name = f"weapon_{power_num}.png"  # 尝试无空格版本
                alt_image_path = os.path.join(ASSETS_DIR, alt_image_name)
                logging.info(f"尝试替代路径: {alt_image_path}")

                if os.path.exists(alt_image_path):
                    try:
                        self.image = pygame.image.load(alt_image_path)
                        self.image = pygame.transform.scale(self.image, (self.width, self.height))
                        logging.info(f"成功加载替代武器图片: {alt_image_name}")
                    except pygame.error as e:
                        logging.error(f"Failed to load alternate {alt_image_name}: {e}")

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
        y = random.randint(100, 520)
        weapon_type = random.choice(weapon_types)
        weapon = Weapon(x, y, weapon_type)
        logging.info(f"Created weapon: {weapon_type}, attack_power={weapon.attack_power}")
        weapons.append(weapon)
    return weapons