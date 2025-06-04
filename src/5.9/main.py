import pygame
import sys
from duck import Duck
from game_state import GameState
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("鸭子冒险游戏")
font = pygame.font.SysFont("SimHei", 32)

# 游戏状态
game_state = None
menu_active = True

# 按钮区域
start_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, 200, 100)

def draw_menu():
    screen.fill(WHITE)
    pygame.draw.rect(screen, (0, 255, 0), start_button)
    text = font.render("开始游戏", True, BLACK)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 20))
    pygame.display.flip()

running = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and menu_active:
            if start_button.collidepoint(event.pos):
                # 初始化游戏状态
                duck = Duck(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                game_state = GameState(duck)
                menu_active = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    if menu_active:
        draw_menu()
    else:
        if game_state is None:
            continue  # 防止 game_state 未初始化
        keys = pygame.key.get_pressed()
        game_state.update(screen, keys, events)
        pygame.display.flip()

pygame.quit()
sys.exit()