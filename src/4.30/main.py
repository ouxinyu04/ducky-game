import pygame
import random
import sys

# 调试：确认 main.py 开始加载
print("Loading main.py...")

# 核心导入
from duck import Duck
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK
from weapon import create_weapons
from partner import create_partners
print("Attempting to import Enemy...")
from enemy import Enemy
print("Enemy imported successfully.")
from npc import NPC
from game_state import GameState, BattlePrepState

# 初始化 Pygame
pygame.init()

# 创建窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Duck Escape Game")

# 初始化游戏对象
duck = Duck(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
enemies = [Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)]  # 初始敌人，后续由 GameState 管理
game_state = GameState(duck, enemies)

# 字体
font = pygame.font.SysFont("SimHei", 24)

# 游戏主循环控制
clock = pygame.time.Clock()

# 游戏开始界面
start_screen = True
while start_screen:
    screen.fill(WHITE)
    title = font.render("鸭子逃脱 Duck Escape", True, BLACK)
    start_button = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 25, 120, 50)
    pygame.draw.rect(screen, (0, 120, 255), start_button)
    label = font.render("开始游戏", True, WHITE)
    screen.blit(title, (SCREEN_WIDTH // 2 - 100, 100))
    screen.blit(label, (SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 - 10))
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if start_button.collidepoint(event.pos):
                start_screen = False

running = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    try:
        screen.fill(WHITE)
        keys = pygame.key.get_pressed()
        game_state.update(screen, keys, events)

        if not game_state.in_battle and game_state.state != "battle_prep" and game_state.state != "buff_selection":
            duck.move(keys)

        # 绘制角色与对象
        duck.draw(screen)
        for weapon in game_state.weapons:
            weapon.draw(screen)
        for partner in game_state.partners:
            partner.draw(screen)
        for enemy in game_state.enemies:
            enemy.draw(screen)
        if game_state.npc:
            game_state.npc.draw(screen)

        # 绘制关卡信息
        level_text = font.render(f"Level: {game_state.level}", True, BLACK)
        screen.blit(level_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)
    except Exception as e:
        print(f"Error: {e}")
        pygame.quit()
        sys.exit()

pygame.quit()
sys.exit()