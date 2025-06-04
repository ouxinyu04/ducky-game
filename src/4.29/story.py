import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK

class StoryEvent:
    def __init__(self):
        self.active = False
        self.options = ["Apologize", "Ignore"]
        self.choice = None

    def trigger(self, duck, screen, font):
        self.active = True
        text = font.render("Partner is jealous! Choose: 1. Apologize 2. Ignore", True, BLACK)
        screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)

    def handle_choice(self, choice, duck):
        self.choice = choice
        if choice == 1:
            print("Partner feels better. Charm +2")
            duck.charm += 2
        else:
            print("Partner leaves! Lost a partner.")
            if duck.partners:
                duck.partners.pop(0)
        self.active = False