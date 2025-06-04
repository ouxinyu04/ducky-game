import pygame
import sys
from game_state import GameState

pygame.init()

screen = pygame.display.set_mode((1024, 768))
pygame.display.set_caption("Duck Escape")
clock = pygame.time.Clock()

game_state = GameState()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    game_state.update(screen, keys, pygame.event.get())
    pygame.display.flip()
    clock.tick(60)