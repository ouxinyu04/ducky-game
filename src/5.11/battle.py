import pygame
import random
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GREEN

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

def handle_battle(duck, enemies, keys, screen, font, level, selected_partners, selected_weapons, events):
    try:
        logging.info("Starting battle rendering")
        logging.info(f"Selected weapons: {[w.weapon_type for w in selected_weapons]}, Partners: {[p.index for p in selected_partners]}")
        if not enemies or not duck.is_alive:
            logging.info("Battle ended: no enemies or duck dead")
            return True, False

        boss = enemies[0]
        state = "roll_dice"
        player_dice = 0
        boss_dice = 0
        player_turn = False
        selected_attacker = None
        info_text = ""
        info_timer = 0
        dice_display_start = 0
        dice_display_duration = 2000

        weapon_power = sum(weapon.attack_power for weapon in selected_weapons)
        logging.info(f"Total weapon power: {weapon_power}")
        characters = [(duck, "鸭子")] + [(partner, f"伙伴 {partner.index}") for partner in selected_partners if partner.is_alive]

        while True:
            current_time = pygame.time.get_ticks()
            screen.fill(WHITE)

            boss_hp_ratio = boss.hp / boss.max_hp
            pygame.draw.rect(screen, RED, (SCREEN_WIDTH // 2 - 100, 20, 200, 20))
            pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH // 2 - 100, 20, 200 * boss_hp_ratio, 20))
            hp_text = font.render(f"BOSS HP: {boss.hp}/{boss.max_hp}", True, BLACK)
            screen.blit(hp_text, (SCREEN_WIDTH // 2 - 80, 50))

            boss.draw(screen)
            duck.draw(screen)
            for partner in selected_partners:
                if partner.is_alive:
                    partner.draw(screen)

            if state == "roll_dice":
                if not player_dice:
                    player_dice = random.randint(1, 6)
                    boss_dice = random.randint(1, 6)
                    dice_display_start = current_time
                    logging.info(f"Dice rolled: Player={player_dice}, Boss={boss_dice}")
                if current_time - dice_display_start < dice_display_duration:
                    text = font.render(f"玩家骰子: {player_dice}  BOSS骰子: {boss_dice}", True, BLACK)
                    screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 20))
                else:
                    player_turn = player_dice >= boss_dice
                    state = "player_turn" if player_turn else "boss_turn"
                    info_text = "玩家先手！" if player_turn else "BOSS先手！"
                    info_timer = 120
                    logging.info(f"Turn decided: {'Player' if player_turn else 'Boss'} first")

            elif state == "player_turn":
                for i, (char, name) in enumerate(characters):
                    if char.is_alive:
                        text = font.render(f"按 {i+1} 选择 {name} (战力: {get_character_power(char, weapon_power, selected_partners, duck.buffs)})", True, BLACK)
                        screen.blit(text, (50, 100 + i * 40))
                prompt = font.render("选择攻击角色", True, BLACK)
                screen.blit(prompt, (50, 100 + len(characters) * 40))
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                            index = event.key - pygame.K_1
                            if index < len(characters) and characters[index][0].is_alive:
                                selected_attacker = characters[index][0]
                                power = get_character_power(selected_attacker, weapon_power, selected_partners, duck.buffs)
                                boss.hp = max(0, boss.hp - power)
                                info_text = f"{characters[index][1]} 攻击，造成 {power} 伤害！"
                                info_timer = 120
                                state = "boss_turn"
                                logging.info(f"Player attack: {characters[index][1]}, Damage={power}, Boss HP={boss.hp}")
                                break

            elif state == "boss_turn":
                if info_timer <= 0:
                    alive_targets = [duck] + [p for p in selected_partners if p.is_alive]
                    if alive_targets:
                        target = random.choice(alive_targets)
                        target_name = "鸭子" if target == duck else f"伙伴 {target.index}"
                        target.hp = max(0, target.hp - boss.attack_power)
                        info_text = f"BOSS 攻击 {target_name}，造成 {boss.attack_power} 伤害！"
                        info_timer = 120
                        logging.info(f"Boss attack: {target_name}, Damage={boss.attack_power}, Target HP={target.hp}")
                    state = "roll_dice"
                    player_dice = 0
                    boss_dice = 0

            if info_timer > 0:
                background = pygame.Surface((400, 50))
                background.set_alpha(200)
                background.fill((255, 255, 255))
                screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 100))
                text = font.render(info_text, True, BLACK)
                screen.blit(text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 100))
                info_timer -= 1

            if boss.hp <= 0:
                logging.info("Battle ended: Boss defeated")
                return True, True
            if not duck.is_alive or duck.hp <= 0:
                logging.info("Battle ended: Duck defeated")
                return True, False

            pygame.display.flip()

    except Exception as e:
        logging.error(f"Battle error: {e}")
        return True, False

def get_character_power(character, weapon_power, selected_partners, duck_buffs):
    base_power = character.attack_power
    if selected_partners:
        weapon_share = weapon_power // (len(selected_partners) + 1)
    else:
        weapon_share = weapon_power
    buff_power = 15 if "勇敢 BUFF" in duck_buffs else 0
    total_power = base_power + weapon_share + buff_power
    return total_power