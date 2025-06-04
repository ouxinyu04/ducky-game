import pygame
import random
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR, encoding='utf-8')

def handle_battle(duck, enemy, screen, font):
    try:
        screen.fill(WHITE)
        # 绘制我方（左侧）
        duck_x = 50
        duck_y = SCREEN_HEIGHT // 2 - duck.height // 2
        if duck.png_image:
            screen.blit(duck.png_image, (duck_x, duck_y))
        else:
            pygame.draw.rect(screen, duck.color, (duck_x, duck_y, duck.width, duck.height))
        if duck.held_weapon and duck.held_weapon.image:
            screen.blit(pygame.transform.scale(duck.held_weapon.image, (20, 20)), (duck_x + duck.width + 10, duck_y + 10))

        for i, partner in enumerate(duck.partners):
            partner_x = 150 + i * 50
            partner_y = SCREEN_HEIGHT // 2 - partner.height // 2
            if partner.image:
                screen.blit(partner.image, (partner_x, partner_y))
            else:
                pygame.draw.rect(screen, partner.color, (partner_x, partner_y, partner.width, partner.height))
            if partner.held_weapon and partner.held_weapon.image:
                screen.blit(pygame.transform.scale(partner.held_weapon.image, (20, 20)), (partner_x + partner.width + 10, partner_y + 5))

        # 绘制敌方（右侧）
        enemy_width = 80 if enemy.is_boss else enemy.width
        enemy_height = 80 if enemy.is_boss else enemy.height
        # 在所有分支之前定义 enemy_x 和 enemy_y
        enemy_x = SCREEN_WIDTH - 100 - enemy_width
        enemy_y = SCREEN_HEIGHT // 2 - enemy_height // 2
        if enemy.image:
            scaled_image = pygame.transform.scale(enemy.image, (enemy_width, enemy_height))
            screen.blit(scaled_image, (enemy_x, enemy_y))
        else:
            pygame.draw.rect(screen, (255, 0, 0), (enemy_x, enemy_y, enemy_width, enemy_height))

        prompt = font.render("按空格攻击", True, BLACK)
        screen.blit(prompt, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))

        keys = pygame.key.get_pressed()
        battle_ended = False
        victory = False
        if keys[pygame.K_SPACE]:
            total_power = duck.get_total_power()
            enemy_power = enemy.attack_power + random.randint(0, 5)
            if total_power >= enemy_power:
                battle_ended = True
                victory = True
            else:
                duck.hp = max(0, duck.hp - int(duck.max_hp * 0.1))
                for partner in duck.partners:
                    partner.hp = max(0, partner.hp - int(partner.max_hp * 0.1))
                if duck.hp == 0:
                    battle_ended = True
                    victory = False
                else:
                    battle_ended = True  # 即使失败也结束战斗
                    victory = False
        return battle_ended, victory
        return False, False
    except Exception as e:
        logging.error(f"战斗错误: {e}")
        return True, False