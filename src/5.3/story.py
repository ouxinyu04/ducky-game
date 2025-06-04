import pygame
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class StoryEvent:
    def __init__(self):
        self.active = False
        self.events = []

    def trigger(self, duck, screen, font):
        pass

    def handle_choice(self, choice, duck):
        pass

    def reset(self):
        self.active = False