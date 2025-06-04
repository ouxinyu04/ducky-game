import pygame
import random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, FRONT_ROW_DAMAGE_TAKEN, BACK_ROW_DAMAGE_TAKEN
from partner import Partner


def handle_battle(duck, enemies, keys, screen, font):
    # 显示“开始战斗”和退出提示
    screen.fill((255, 255, 255))  # 清屏
    text = font.render("开始战斗", True, BLACK)
    prompt = font.render("点击窗口关闭按钮退出", True, BLACK)
    screen.blit(text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    screen.blit(prompt, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

    # 不执行任何战斗逻辑，等待玩家关闭窗口
    return False, True  # 返回 False 表示战斗未结束，True 表示鸭子存活