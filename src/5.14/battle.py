# battle.py 角色显示和交互优化版
import pygame
import random
import logging
import traceback
import os
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GREEN, BLUE
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

# 背景图片路径
BATTLE_BACKGROUND_PATH = os.path.join(ASSETS_DIR, "battle_background.png")


def distribute_weapon_power(selected_partners, selected_weapons, duck_buffs=None):
    """分配武器战力给伙伴"""
    try:
        if not selected_partners or not selected_weapons:
            return

        # 简单分配：每个伙伴分配到同等的武器战力加成
        weapon_power_per_partner = sum(w.attack_power for w in selected_weapons) / len(selected_partners)

        for partner in selected_partners:
            partner.weapon_power_bonus = weapon_power_per_partner
            logging.info(f"Partner {partner.index} received weapon bonus: {weapon_power_per_partner}")
    except Exception as e:
        logging.error(f"Error in distribute_weapon_power: {e}")
        logging.error(traceback.format_exc())


def get_total_team_power(partners, duck_buffs=None):
    """计算队伍总战力"""
    try:
        total_power = 0
        for partner in partners:
            if partner and partner.is_alive:
                try:
                    power = partner.get_total_power(duck_buffs)
                except:
                    power = partner.attack_power
                total_power += power
        return total_power
    except Exception as e:
        logging.error(f"Error calculating team power: {e}")
        return sum(p.attack_power for p in partners if p and p.is_alive)


# battle.py 角色选择修复部分
def handle_battle(duck, enemies, keys, screen, font, level, selected_partners, selected_weapons, events):
    try:
        logging.info("Starting battle rendering")
        logging.info(
            f"Selected weapons: {[w.weapon_type for w in selected_weapons if w]}, Partners: {[p.index for p in selected_partners if p]}")

        # 安全检查
        if not enemies:
            logging.error("Battle ended: no enemies provided")
            return True, False

        if not selected_partners:
            logging.error("Battle ended: no partners selected")
            return True, False

        # 再次安全检查所有对象都有有效实例
        valid_partners = [p for p in selected_partners if p and hasattr(p, 'is_alive') and p.is_alive]
        if not valid_partners:
            logging.error("No valid partners available for battle")
            return True, False

        # 记录详细信息用于调试
        logging.info(f"Duck info: {duck.__dict__ if duck else 'None'}")
        logging.info(f"Enemies info: {[e.__dict__ for e in enemies] if enemies else 'None'}")
        logging.info(
            f"Selected partners info: {[p.__dict__ for p in selected_partners if p] if selected_partners else 'None'}")

        # 加载背景图片
        background_image = None
        try:
            if os.path.exists(BATTLE_BACKGROUND_PATH):
                background_image = pygame.image.load(BATTLE_BACKGROUND_PATH)
                background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                logging.info(f"Battle background loaded successfully")
            else:
                logging.warning(f"Battle background image not found at: {BATTLE_BACKGROUND_PATH}")
        except Exception as e:
            logging.error(f"Error loading battle background: {e}")
            logging.error(traceback.format_exc())

        # 初始化BOSS
        boss = enemies[0]

        # 安全地初始化BOSS的HP
        if not hasattr(boss, 'hp') or boss.hp <= 0:
            boss.hp = 250
        if not hasattr(boss, 'max_hp') or boss.max_hp <= 0:
            boss.max_hp = 250

        logging.info(f"Boss initialized with HP: {boss.hp}/{boss.max_hp}")

        # 团队属性 - 新增
        team_hp = 15
        team_max_hp = 15
        team_mp = 30
        team_max_mp = 30

        # 初始化战斗状态变量
        state = "roll_dice"
        player_dice = 0
        boss_dice = 0
        player_turn = False
        selected_attacker = None
        selected_skill = None
        target_selection = False
        heal_target = None
        info_text = ""
        info_timer = 0
        dice_display_start = 0
        dice_display_duration = 2000
        battle_end = False  # 添加战斗结束标记
        battle_victory = False  # 添加战斗胜利标记

        # 技能按钮
        attack_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 250, 140, 60)
        heal_button = pygame.Rect(SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT - 250, 140, 60)

        # 计算队伍总战力
        team_power = get_total_team_power(selected_partners, duck.buffs)
        logging.info(f"Team total power: {team_power}")

        # 安全分配武器战力
        try:
            distribute_weapon_power(selected_partners, selected_weapons, duck.buffs)
        except Exception as e:
            logging.error(f"Error distributing weapon power: {e}")
            logging.error(traceback.format_exc())

        # 创建角色选择按钮区域 - 定位在窗口底部
        character_buttons = []
        character_y_offsets = []  # 存储每个角色按钮的Y偏移，用于动画效果
        button_width = 100
        button_height = 120
        spacing = 20
        total_width = (button_width + spacing) * len(selected_partners) - spacing if selected_partners else 0
        start_x = (SCREEN_WIDTH - total_width) // 2

        # 确保有伙伴才创建按钮
        for i, partner in enumerate(selected_partners):
            if partner and hasattr(partner, 'is_alive') and partner.is_alive:
                button_x = start_x + i * (button_width + spacing)
                button_y = SCREEN_HEIGHT - button_height - 20
                button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                character_buttons.append((button_rect, partner, i))
                character_y_offsets.append(0)

        logging.info(f"Created {len(character_buttons)} character buttons")

        # 添加技能按钮
        skill_buttons = []
        if selected_attacker:
            skill_x = SCREEN_WIDTH // 2 - 150
            normal_attack_button = pygame.Rect(skill_x, SCREEN_HEIGHT - 180, 140, 40)
            skill_buttons.append((normal_attack_button, "普通攻击", 0))

            special_skill_button = pygame.Rect(skill_x + 160, SCREEN_HEIGHT - 180, 140, 40)
            if selected_attacker.npc_type == "lady_duck":
                skill_name = "治疗"
            elif selected_attacker.npc_type == "broccoli_general":
                skill_name = "斩击"
            elif selected_attacker.npc_type == "human_child":
                skill_name = "嘲讽"
            else:
                skill_name = "治疗"
            skill_buttons.append((special_skill_button, skill_name, 5 if selected_attacker.npc_type else 6))

        # 战斗主循环
        clock = pygame.time.Clock()
        battle_running = True

        while battle_running:
            try:
                # 安全检查屏幕是否有效
                if not screen:
                    logging.error("Screen is not available")
                    return True, False

                current_time = pygame.time.get_ticks()

                # 处理可能的事件
                events_to_process = []
                try:
                    events_to_process = list(events)  # 拷贝事件列表防止修改原列表
                except Exception as e:
                    logging.error(f"Error copying events: {e}")
                    events_to_process = []

                for event in events_to_process:
                    if event.type == pygame.QUIT:
                        return True, False

                # 检查游戏结束条件
                if boss.hp <= 0:
                    battle_end = True
                    battle_victory = True
                    break

                # 检查玩家是否失败（所有伙伴都失去战斗能力或团队HP为0）
                if team_hp <= 0 or all(not p.is_alive for p in selected_partners if p):
                    battle_end = True
                    battle_victory = False
                    break

                # 绘制背景
                if background_image:
                    screen.blit(background_image, (0, 0))
                else:
                    screen.fill(WHITE)

                # 显示队伍总战力
                team_power_text = font.render(f"队伍总战力: {int(team_power)}", True, BLACK)
                screen.blit(team_power_text, (SCREEN_WIDTH - 200, 10))

                # 显示团队HP和MP
                hp_text = font.render(f"团队HP: {team_hp}/{team_max_hp}", True, BLACK)
                mp_text = font.render(f"团队MP: {team_mp}/{team_max_mp}", True, BLACK)
                screen.blit(hp_text, (20, 10))
                screen.blit(mp_text, (20, 40))

                # 安全绘制BOSS血条
                try:
                    boss_hp_ratio = max(0, min(boss.hp / boss.max_hp, 1.0))  # 确保比例在0-1之间
                    pygame.draw.rect(screen, RED, (SCREEN_WIDTH // 2 - 100, 20, 200, 20))
                    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH // 2 - 100, 20, int(200 * boss_hp_ratio), 20))
                    hp_text = font.render(f"BOSS HP: {boss.hp}/{boss.max_hp}", True, BLACK)
                    screen.blit(hp_text, (SCREEN_WIDTH // 2 - 80, 50))
                except Exception as e:
                    logging.error(f"Error drawing boss HP bar: {e}")

                # 安全绘制BOSS
                try:
                    boss.draw(screen)
                except Exception as e:
                    logging.error(f"Error drawing boss: {e}")

                if state == "roll_dice":
                    try:
                        if not player_dice:
                            player_dice = random.randint(1, 6)
                            boss_dice = random.randint(1, 6)
                            dice_display_start = current_time
                            logging.info(f"Dice rolled: Player={player_dice}, Boss={boss_dice}")

                        # 确保显示足够长时间
                        if current_time - dice_display_start < dice_display_duration:
                            # 创建更明显的半透明背景
                            dark_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                            dark_background.set_alpha(150)
                            dark_background.fill((0, 0, 0))
                            screen.blit(dark_background, (0, 0))

                            background = pygame.Surface((400, 150))
                            background.set_alpha(230)  # 更不透明
                            background.fill((255, 255, 255))
                            screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 75))

                            # 增加标题
                            title_text = font.render("回合决定", True, (255, 0, 0))
                            screen.blit(title_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 65))

                            # 显示骰子信息
                            text = font.render(f"玩家骰子: {player_dice}  BOSS骰子: {boss_dice}", True, BLACK)
                            screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 30))

                            explain_text = font.render(f"骰子数值大的一方先手!", True, BLACK)
                            screen.blit(explain_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 10))

                            # 添加提示
                            wait_text = font.render("请等待...", True, (0, 0, 255))
                            screen.blit(wait_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 50))

                            # 强制更新显示
                            pygame.display.update()
                            logging.info(
                                f"Drawing dice display at {current_time}, remaining: {dice_display_duration - (current_time - dice_display_start)}ms")
                        else:
                            player_turn = player_dice >= boss_dice
                            state = "player_turn" if player_turn else "boss_turn"
                            info_text = "玩家先手！" if player_turn else "BOSS先手！"
                            info_timer = 120
                            logging.info(f"Turn decided: {'Player' if player_turn else 'Boss'} first")
                    except Exception as e:
                        logging.error(f"Error in roll_dice state: {e}")
                        logging.error(traceback.format_exc())
                        state = "player_turn"  # 出错时默认玩家先手

                # 玩家回合
                elif state == "player_turn":
                    # 检查是否有角色按钮
                    if not character_buttons:
                        logging.error("No character buttons available")
                        # 创建默认按钮
                        for i, partner in enumerate(selected_partners):
                            if partner and hasattr(partner, 'is_alive') and partner.is_alive:
                                button_x = 100 + i * 150
                                button_y = SCREEN_HEIGHT - 150
                                button_rect = pygame.Rect(button_x, button_y, 100, 100)
                                character_buttons.append((button_rect, partner, i))
                                character_y_offsets.append(0)

                        if not character_buttons:
                            logging.error("Still no character buttons - cannot continue battle")
                            return True, False

                    try:
                        # 绘制所有角色按钮
                        for button_rect, partner, index in character_buttons:
                            if partner and hasattr(partner, 'is_alive') and partner.is_alive:
                                # 应用Y轴动画效果 - 选中的角色上移
                                target_y_offset = -20 if selected_attacker == partner else 0
                                character_y_offsets[index] += (target_y_offset - character_y_offsets[index]) * 0.2

                                actual_rect = button_rect.copy()
                                actual_rect.y += character_y_offsets[index]

                                # 绘制角色选择按钮背景
                                bg_color = (220, 220, 255) if selected_attacker == partner else (200, 200, 200)
                                pygame.draw.rect(screen, bg_color, actual_rect)
                                pygame.draw.rect(screen, BLACK, actual_rect, 2)

                                # 在按钮中绘制角色图像
                                if partner.image:
                                    scaled_image = pygame.transform.scale(partner.image, (70, 70))
                                    screen.blit(scaled_image,
                                                (actual_rect.x + (button_width - 70) // 2, actual_rect.y + 5))
                                else:
                                    img_rect = pygame.Rect(actual_rect.x + (button_width - 70) // 2, actual_rect.y + 5,
                                                           70, 70)
                                    pygame.draw.rect(screen, partner.color, img_rect)

                                # 显示角色信息
                                partner_info = f"{partner.index}"
                                if hasattr(partner, 'npc_type') and partner.npc_type:
                                    partner_info += f" ({partner.npc_type})"

                                # 使用小号字体显示信息
                                small_font = pygame.font.SysFont("SimHei", 16)
                                info_text = small_font.render(partner_info, True, BLACK)
                                screen.blit(info_text, (actual_rect.x + 5, actual_rect.y + 80))

                                # 绘制角色的HP和MP条
                                hp_ratio = max(0, min(partner.hp / partner.max_hp, 1.0))
                                mp_ratio = max(0, min(partner.mp / partner.max_mp, 1.0))

                                # 血条背景
                                hp_bg_rect = pygame.Rect(actual_rect.x + 5, actual_rect.y + 100, button_width - 10, 5)
                                pygame.draw.rect(screen, RED, hp_bg_rect)
                                pygame.draw.rect(screen, GREEN, (
                                    hp_bg_rect.x, hp_bg_rect.y, int(hp_bg_rect.width * hp_ratio), hp_bg_rect.height))

                                # 蓝条背景
                                mp_bg_rect = pygame.Rect(actual_rect.x + 5, actual_rect.y + 110, button_width - 10, 5)
                                pygame.draw.rect(screen, (100, 100, 100), mp_bg_rect)
                                pygame.draw.rect(screen, BLUE, (
                                    mp_bg_rect.x, mp_bg_rect.y, int(mp_bg_rect.width * mp_ratio), mp_bg_rect.height))

                                # 显示HP和MP值
                                hp_text = small_font.render(f"{partner.hp}/{partner.max_hp}", True, BLACK)
                                mp_text = small_font.render(f"MP:{partner.mp}", True, BLACK)
                                screen.blit(hp_text, (actual_rect.x + 10, actual_rect.y + 85 + 13))
                                screen.blit(mp_text, (actual_rect.x + button_width - 40, actual_rect.y + 85 + 13))

                        if selected_attacker is None:
                            # 显示选择角色提示
                            prompt = font.render("点击角色选择攻击者", True, BLACK)
                            screen.blit(prompt, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - button_height - 60))

                            # 检测鼠标点击选择角色
                            for event in events_to_process:
                                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                    mouse_pos = event.pos
                                    for button_rect, partner, idx in character_buttons:
                                        # 考虑Y轴偏移
                                        adjusted_rect = button_rect.copy()
                                        adjusted_rect.y += character_y_offsets[idx]

                                        if adjusted_rect.collidepoint(mouse_pos) and partner.is_alive:
                                            selected_attacker = partner
                                            logging.info(f"Selected attacker: Partner {selected_attacker.index}")
                                            # 创建技能按钮
                                            skill_buttons = []
                                            skill_x = SCREEN_WIDTH // 2 - 150
                                            normal_attack_button = pygame.Rect(skill_x, SCREEN_HEIGHT - 180, 140, 40)
                                            skill_buttons.append((normal_attack_button, "普通攻击", 0))

                                            special_skill_button = pygame.Rect(skill_x + 160, SCREEN_HEIGHT - 180, 140,
                                                                               40)
                                            if partner.npc_type == "lady_duck":
                                                skill_name = "治疗"
                                            elif partner.npc_type == "broccoli_general":
                                                skill_name = "斩击"
                                            elif partner.npc_type == "human_child":
                                                skill_name = "嘲讽"
                                            else:
                                                skill_name = "治疗"
                                            mp_cost = 5 if partner.npc_type else 6
                                            skill_buttons.append((special_skill_button, skill_name, mp_cost))
                                            break

                            # 支持键盘选择（兼容原代码）
                            for event in events_to_process:
                                if event.type == pygame.KEYDOWN:
                                    if pygame.K_1 <= event.key <= pygame.K_9:
                                        index = event.key - pygame.K_1
                                        if index < len(selected_partners) and selected_partners[index] and \
                                                selected_partners[index].is_alive:
                                            selected_attacker = selected_partners[index]
                                            logging.info(
                                                f"Selected attacker with key: Partner {selected_attacker.index}")
                                            # 创建技能按钮
                                            skill_buttons = []
                                            skill_x = SCREEN_WIDTH // 2 - 150
                                            normal_attack_button = pygame.Rect(skill_x, SCREEN_HEIGHT - 180, 140, 40)
                                            skill_buttons.append((normal_attack_button, "普通攻击", 0))

                                            special_skill_button = pygame.Rect(skill_x + 160, SCREEN_HEIGHT - 180, 140,
                                                                               40)
                                            if selected_attacker.npc_type == "lady_duck":
                                                skill_name = "治疗"
                                            elif selected_attacker.npc_type == "broccoli_general":
                                                skill_name = "斩击"
                                            elif selected_attacker.npc_type == "human_child":
                                                skill_name = "嘲讽"
                                            else:
                                                skill_name = "治疗"
                                            mp_cost = 5 if selected_attacker.npc_type else 6
                                            skill_buttons.append((special_skill_button, skill_name, mp_cost))
                                            break
                        else:
                            # 已选择攻击者，显示可用技能
                            if not selected_skill:
                                # 绘制技能按钮
                                for button_rect, skill_name, mp_cost in skill_buttons:
                                    button_color = (200, 200, 255)
                                    if mp_cost > 0 and team_mp < mp_cost:  # MP不足时显示灰色
                                        button_color = (150, 150, 150)
                                    pygame.draw.rect(screen, button_color, button_rect)
                                    pygame.draw.rect(screen, BLACK, button_rect, 2)
                                    skill_text = pygame.font.SysFont("SimHei", 20).render(skill_name, True, BLACK)
                                    screen.blit(skill_text, (button_rect.x + 10, button_rect.y + 10))
                                    if mp_cost > 0:
                                        cost_text = pygame.font.SysFont("SimHei", 16).render(f"MP: {mp_cost}", True,
                                                                                             BLUE)
                                        screen.blit(cost_text, (button_rect.x + 10, button_rect.y + 30))

                                # 检测技能按钮点击
                                for event in events_to_process:
                                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                        mouse_pos = event.pos
                                        for button_rect, skill_name, mp_cost in skill_buttons:
                                            if button_rect.collidepoint(mouse_pos):
                                                if mp_cost == 0 or team_mp >= mp_cost:  # 检查MP是否足够
                                                    selected_skill = skill_name
                                                    if skill_name in ["治疗", "嘲讽"]:
                                                        target_selection = True
                                                    else:
                                                        # 执行普通攻击或斩击
                                                        if skill_name == "普通攻击":
                                                            damage = selected_attacker.get_total_power(duck.buffs)
                                                            boss.hp = max(0, boss.hp - damage)
                                                            # 恢复MP
                                                            team_mp = min(team_max_mp, team_mp + 3)
                                                            info_text = f"{selected_attacker.index} 普通攻击! 造成 {damage} 伤害! MP +3"
                                                        elif skill_name == "斩击":
                                                            damage = selected_attacker.get_total_power(duck.buffs) * 2
                                                            boss.hp = max(0, boss.hp - damage)
                                                            team_mp -= mp_cost
                                                            info_text = f"{selected_attacker.index} 使用斩击! 造成 {damage} 伤害! MP -{mp_cost}"

                                                        info_timer = 120
                                                        # 重置选择
                                                        selected_attacker = None
                                                        selected_skill = None
                                                        skill_buttons = []
                                                        # 检查BOSS是否被击败
                                                        if boss.hp <= 0:
                                                            state = "victory"
                                                            battle_end = True
                                                            battle_victory = True
                                                        else:
                                                            state = "boss_turn"
                                                else:
                                                    info_text = "MP不足!"
                                                    info_timer = 60
                            elif target_selection:
                                # 显示治疗对象选择界面
                                healing_text = font.render("选择治疗目标:", True, BLACK)
                                screen.blit(healing_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 220))

                                # 绘制可选目标按钮
                                target_buttons = []
                                for i, partner in enumerate(selected_partners):
                                    if partner.is_alive:
                                        target_rect = pygame.Rect(100 + i * 150, SCREEN_HEIGHT - 180, 100, 40)
                                        pygame.draw.rect(screen, (200, 255, 200), target_rect)
                                        pygame.draw.rect(screen, BLACK, target_rect, 2)
                                        target_text = pygame.font.SysFont("SimHei", 18).render(f"伙伴 {partner.index}",
                                                                                               True, BLACK)
                                        screen.blit(target_text, (target_rect.x + 10, target_rect.y + 10))
                                        target_buttons.append((target_rect, partner))

                                # 检测目标按钮点击
                                for event in events_to_process:
                                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                        mouse_pos = event.pos
                                        for target_rect, partner in target_buttons:
                                            if target_rect.collidepoint(mouse_pos):
                                                heal_target = partner
                                                mp_cost = 5 if selected_attacker.npc_type else 6

                                                # 执行治疗
                                                heal_amount = 15
                                                partner.hp = min(partner.max_hp, partner.hp + heal_amount)
                                                team_mp -= mp_cost

                                                info_text = f"{selected_attacker.index} 治疗了 {partner.index}! HP +{heal_amount}! MP -{mp_cost}"
                                                info_timer = 120

                                                # 重置选择
                                                selected_attacker = None
                                                selected_skill = None
                                                skill_buttons = []
                                                target_selection = False
                                                heal_target = None
                                                state = "boss_turn"
                                                break
                    except Exception as e:
                        logging.error(f"Error rendering player turn: {e}")
                        logging.error(traceback.format_exc())

                # BOSS回合
                elif state == "boss_turn":
                    # 简单AI: BOSS随机选择一个角色攻击
                    alive_partners = [p for p in selected_partners if p and p.is_alive]
                    if alive_partners:
                        target = random.choice(alive_partners)
                        damage = boss.attack_power

                        # 计算实际伤害 (考虑嘲讽效果)
                        taunt_active = any(
                            p.npc_type == "human_child" and p.taunt_active for p in selected_partners if
                            p and p.is_alive)
                        if taunt_active:
                            taunt_partners = [p for p in selected_partners if
                                              p and p.is_alive and p.npc_type == "human_child" and p.taunt_active]
                            if taunt_partners and random.random() < 0.7:  # 70%概率攻击嘲讽者
                                target = random.choice(taunt_partners)

                        target.hp = max(0, target.hp - damage)
                        team_hp = max(0, team_hp - damage // 3)  # 团队也受到部分伤害

                        info_text = f"BOSS攻击了 {target.index}! 造成 {damage} 伤害! 团队受到 {damage // 3} 伤害!"
                        info_timer = 120

                        # 检查目标是否被击败
                        if target.hp <= 0:
                            target.is_alive = False
                            info_text += f" {target.index} 失去战斗能力!"

                        # 检查是否团队失败
                        if team_hp <= 0 or all(not p.is_alive for p in selected_partners if p):
                            state = "defeat"
                            battle_end = True
                            battle_victory = False
                        else:
                            state = "player_turn"
                    else:
                        # 如果没有存活的伙伴，玩家失败
                        state = "defeat"
                        battle_end = True
                        battle_victory = False

                # 胜利状态
                elif state == "victory":
                    background = pygame.Surface((400, 200))
                    background.set_alpha(200)
                    background.fill((255, 255, 255))
                    screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))

                    victory_text = font.render("胜利!", True, (0, 200, 0))
                    screen.blit(victory_text, (SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 - 80))

                    info = font.render("击败了BOSS! 按任意键继续...", True, BLACK)
                    screen.blit(info, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 20))

                    # 检测任意键继续
                    for event in events_to_process:
                        if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                            battle_end = True
                            battle_victory = True
                            battle_running = False

                # 失败状态
                elif state == "defeat":
                    background = pygame.Surface((400, 200))
                    background.set_alpha(200)
                    background.fill((255, 255, 255))
                    screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))

                    defeat_text = font.render("失败!", True, (200, 0, 0))
                    screen.blit(defeat_text, (SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 2 - 80))

                    info = font.render("被BOSS击败! 按任意键继续...", True, BLACK)
                    screen.blit(info, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 20))

                    # 检测任意键继续
                    for event in events_to_process:
                        if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                            battle_end = True
                            battle_victory = False
                            battle_running = False

                # 显示信息文本
                if info_text and info_timer > 0:
                    info_bg = pygame.Surface((500, 40))
                    info_bg.set_alpha(200)
                    info_bg.fill((255, 255, 255))
                    screen.blit(info_bg, (SCREEN_WIDTH // 2 - 250, 80))
                    # 修改后（使用异常处理更可靠）:
                    try:
                        info_render = font.render(str(info_text) if info_text else "", True, BLACK)
                    except Exception as e:
                        logging.error(f"Error rendering info text: {e}")
                        info_render = font.render("", True, BLACK)

                pygame.display.flip()
                clock.tick(60)  # 控制帧率

                # 处理新事件
                try:
                    events = pygame.event.get()
                except Exception as e:
                    logging.error(f"Error getting events: {e}")
                    events = []

            except Exception as e:
                logging.error(f"Critical error in battle loop: {e}")
                logging.error(traceback.format_exc())
                pygame.time.delay(500)  # 延迟一下，防止CPU过载
                # 如果战斗循环出错，确保能够退出战斗
                try:
                    pygame.display.flip()  # 尝试刷新屏幕以避免游戏冻结
                except:
                    pass
                battle_end = True
                battle_victory = False
                break  # 退出战斗循环

        # 战斗结束，返回结果
        logging.info(f"Battle ended: victory={battle_victory}")
        return battle_end, battle_victory

    except Exception as e:
        logging.error(f"Fatal battle error: {e}")
        logging.error(traceback.format_exc())
        return True, False