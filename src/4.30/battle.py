import pygame
import random
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

def handle_battle(duck, enemies, keys, screen, font):
    try:
        enemies = [enemy for enemy in enemies if enemy.is_alive]
        if not enemies:
            print("战斗胜利！")
            return True, True

        alive_partners = [partner for partner in duck.partners if partner.is_alive]
        if not duck.is_alive and not alive_partners:
            print("队伍全灭，战斗失败！")
            return True, False

        screen.fill(WHITE)

        # 绘制我方（左侧）
        # 主人公
        duck_x = 50
        duck_y = SCREEN_HEIGHT // 2 - duck.height // 2
        if duck.png_image:
            screen.blit(duck.png_image, (duck_x, duck_y))
        else:
            pygame.draw.rect(screen, duck.color, (duck_x, duck_y, duck.width, duck.height))
        # 主人公的武器
        if duck.held_weapon and duck.held_weapon.image:
            screen.blit(pygame.transform.scale(duck.held_weapon.image, (20, 20)), (duck_x + duck.width + 10, duck_y + 10))
        # 主人公 HP
        duck_hp_text = font.render(f"HP: {duck.hp}/{duck.max_hp}", True, BLACK)
        screen.blit(duck_hp_text, (duck_x, duck_y - 30))

        # 伙伴
        for i, partner in enumerate(alive_partners):
            partner_x = 150 + i * 50
            partner_y = SCREEN_HEIGHT // 2 - partner.height // 2
            if partner.image:
                screen.blit(partner.image, (partner_x, partner_y))
            else:
                pygame.draw.rect(screen, partner.color, (partner_x, partner_y, partner.width, partner.height))
            # 伙伴的武器
            if partner.held_weapon and partner.held_weapon.image:
                screen.blit(pygame.transform.scale(partner.held_weapon.image, (20, 20)), (partner_x + partner.width + 10, partner_y + 5))
            # 伙伴 HP
            partner_hp_text = font.render(f"HP: {partner.hp}/{partner.max_hp}", True, BLACK)
            screen.blit(partner_hp_text, (partner_x, partner_y - 30))

        # 绘制敌方（右侧）
        for enemy in enemies:
            # BOSS 图片放大两倍
            enemy_width = 80 if enemy.is_boss else enemy.width
            enemy_height = 80 if enemy.is_boss else enemy.height
            if enemy.image:
                scaled_image = pygame.transform.scale(enemy.image, (enemy_width, enemy_height))
                enemy_x = SCREEN_WIDTH - 100 - enemy_width
                enemy_y = SCREEN_HEIGHT // 2 - enemy_height // 2
                screen.blit(scaled_image, (enemy_x, enemy_y))
            else:
                pygame.draw.rect(screen, (255, 0, 0), (enemy_x, enemy_y, enemy_width, enemy_height))
            # 敌方 HP
            enemy_hp_text = font.render(f"HP: {enemy.hp}/{enemy.max_hp}", True, BLACK)
            screen.blit(enemy_hp_text, (enemy_x, enemy_y - 30))

        # 战斗逻辑
        if keys[pygame.K_SPACE]:
            total_power = duck.get_total_power()
            for enemy in enemies:
                damage = max(1, total_power - random.randint(0, 5))
                enemy.take_damage(damage)
                print(f"对敌方造成 {damage} 点伤害！敌方剩余 HP: {enemy.hp}")

            enemies = [enemy for enemy in enemies if enemy.is_alive]
            if not enemies:
                print("战斗胜利！")
                return True, True

            for enemy in enemies:
                damage = max(1, enemy.attack_power - random.randint(0, 5))
                if alive_partners:
                    target = random.choice(alive_partners + [duck] if duck.is_alive else alive_partners)
                    if target == duck:
                        duck.hp = max(0, duck.hp - damage)
                        print(f"鸭子受到 {damage} 点伤害！剩余 HP: {duck.hp}")
                        if duck.hp == 0:
                            duck.is_alive = False
                    else:
                        target.hp = max(0, target.hp - damage)
                        print(f"伙伴 {target.index} 受到 {damage} 点伤害！剩余 HP: {target.hp}")
                        if target.hp == 0:
                            target.is_alive = False
                else:
                    if duck.is_alive:
                        duck.hp = max(0, duck.hp - damage)
                        print(f"鸭子受到 {damage} 点伤害！剩余 HP: {duck.hp}")
                        if duck.hp == 0:
                            duck.is_alive = False

            alive_partners = [partner for partner in duck.partners if partner.is_alive]
            if not duck.is_alive and not alive_partners:
                print("队伍全灭，战斗失败！")
                return True, False

        return False, False
    except Exception as e:
        logging.error(f"Battle error: {e}")
        return True, False