import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, GREEN, WEAPON_ATTACK_BOOST, FRONT_ROW_ATTACK_BOOST, BACK_ROW_ATTACK_BOOST
from config import ASSETS_DIR
from weapon import Weapon

# 设置日志
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
        self.hearts = 3
        self.is_alive = True
        self.position = "front"
        self.held_weapon = None
        self.index = index
        image_path = os.path.join(ASSETS_DIR, "partner.png")
        self.image = None
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except pygame.error as e:
                logging.error(f"Failed to load partner.png: {e}")
        else:
            logging.warning(f"partner.png not found at {image_path}. Using fallback green rectangle.")

    def draw(self, screen):
        if not self.collected and self.is_alive:
            if self.image:
                screen.blit(self.image, (self.x, self.y))
            else:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def equip_weapon(self, weapon):
        if self.held_weapon:
            self.unequip_weapon()
        self.held_weapon = weapon
        self.attack_power += WEAPON_ATTACK_BOOST
        print(f"Partner {self.index} equipped weapon {weapon.weapon_type}")

    def unequip_weapon(self):
        if self.held_weapon:
            self.attack_power -= WEAPON_ATTACK_BOOST
            self.held_weapon = None

    def get_effective_power(self):
        base_power = self.attack_power
        if self.position == "front":
            return base_power * FRONT_ROW_ATTACK_BOOST
        return base_power * BACK_ROW_ATTACK_BOOST

    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)
        if self.hp == 0 and self.hearts > 0:
            self.hearts -= 1
            self.hp = self.max_hp
            if self.hearts == 0:
                self.is_alive = False
                print(f"Partner {self.index} is defeated!")

def create_partners(num):
    return [Partner(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30), i + 1) for i in range(num)]