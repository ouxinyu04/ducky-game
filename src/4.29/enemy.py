import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, RED

class Enemy:
    def __init__(self, x, y, is_boss=False):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.hp = 100 if not is_boss else 500  # boss 有更高 HP
        self.max_hp = self.hp
        self.attack_power = 10 if not is_boss else 20  # boss 攻击力更高
        self.is_boss = is_boss
        self.is_alive = True

    def draw(self, screen):
        if self.is_alive:
            pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))

    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            self.is_alive = False