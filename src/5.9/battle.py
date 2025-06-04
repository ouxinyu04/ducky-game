import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BOSS_LEVEL
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

def handle_battle(duck, enemies, keys, screen, font, level, selected_partners, selected_weapons):
    try:
        if not enemies:
            logging.error("No enemies provided for battle")
            return True, False

        enemy = enemies[0]
        BOSS_REQUIRED_POWER = 30 if level == BOSS_LEVEL else 100

        # 加载背景图
        background_image = None
        background_path = os.path.join(ASSETS_DIR, "battle_background.png")
        if os.path.exists(background_path):
            try:
                background_image = pygame.image.load(background_path)
                background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except pygame.error as e:
                logging.error(f"Failed to load battle_background.png: {e}")
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((255, 255, 255))  # 纯白背景

        # 定义角色位置（九宫格比例，无边框）
        grid_size = 100
        grid_positions = [
            (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 3 - 50),      # BOSS（上中）
            (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 50),      # 鸭子（中中）
            (SCREEN_WIDTH // 2 - 150, 2 * SCREEN_HEIGHT // 3 - 50), # 伙伴1（下左）
            (SCREEN_WIDTH // 2 - 50, 2 * SCREEN_HEIGHT // 3 - 50),  # 伙伴2（下中）
            (SCREEN_WIDTH // 2 + 50, 2 * SCREEN_HEIGHT // 3 - 50),  # 伙伴3（下右）
        ]

        # 绘制 BOSS
        if enemy.image:
            screen.blit(pygame.transform.scale(enemy.image, (grid_size, grid_size)), grid_positions[0])
        else:
            pygame.draw.rect(screen, enemy.color, (grid_positions[0][0], grid_positions[0][1], grid_size, grid_size))

        # 绘制鸭子
        if duck.png_image:
            screen.blit(pygame.transform.scale(duck.png_image, (grid_size, grid_size)), grid_positions[1])
        else:
            pygame.draw.rect(screen, duck.color, (grid_positions[1][0], grid_positions[1][1], grid_size, grid_size))

        # 绘制伙伴
        for i, partner in enumerate(selected_partners[:3]):
            pos = grid_positions[2 + i]
            if partner.image:
                screen.blit(pygame.transform.scale(partner.image, (grid_size, grid_size)), pos)
            else:
                pygame.draw.rect(screen, partner.color, (pos[0], pos[1], grid_size, grid_size))

        # 战力比较
        total_power = duck.get_total_power()
        logging.info(f"Player power: {total_power}, BOSS required power: {BOSS_REQUIRED_POWER}")

        if total_power >= BOSS_REQUIRED_POWER:
            text = font.render("战力足够，BOSS 战胜利！", True, (0, 0, 0))
            screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 200))
            pygame.display.flip()
            pygame.time.wait(2000)
            duck.take_battle_loss()
            return True, True
        else:
            text = font.render("战力不足，BOSS 战失败！", True, (0, 0, 0))
            screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 200))
            pygame.display.flip()
            pygame.time.wait(2000)
            logging.info("Battle failed due to insufficient power")
            return True, False

    except Exception as e:
        logging.error(f"Battle handling failed: {e}")
        return True, False