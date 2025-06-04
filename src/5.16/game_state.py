# game_state.py - 完整修改版
import pygame
import os
import random
import traceback
import sys
import logging
from weapon import create_weapons
from partner import create_partners
from battle import handle_battle
from constants import WHITE, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, MAX_PARTNERS, BOSS_LEVEL, RED, BLUE
from npc import NPC
from enemy import Enemy
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)


def get_partner_power(partner, weapons, duck_buffs):
    base_power = partner.attack_power
    weapon_power = sum(w.attack_power for w in weapons) / (len(weapons) + 1) if weapons else 0
    buff_power = 15 if "勇敢 BUFF" in duck_buffs else 0
    return base_power + weapon_power + buff_power

# BattlePrepState 改进版
class BattlePrepState:
    def __init__(self, duck, font):
        self.duck = duck
        self.font = font
        self.selected_partners = []
        self.selected_weapons = []
        self.partner_index = 0
        self.weapon_index = 0
        self.state = "选择伙伴"  # 默认选择伙伴状态
        self.last_key_press = 0

        # 更大的对话框
        self.partner_dialog = pygame.Surface((600, 200))
        self.partner_dialog.set_alpha(255)
        self.weapon_dialog = pygame.Surface((600, 200))
        self.weapon_dialog.set_alpha(255)

        self.partner_offset = 0
        self.weapon_offset = 0
        self.partner_slide_x = 0
        self.weapon_slide_x = 0
        self.target_partner_slide_x = 0
        self.target_weapon_slide_x = 0
        self.initial_delay = pygame.time.get_ticks() + 500

        # 按钮区域
        self.partner_button = pygame.Rect(SCREEN_WIDTH // 2 - 150, 50, 140, 40)
        self.weapon_button = pygame.Rect(SCREEN_WIDTH // 2 + 10, 50, 140, 40)
        self.battle_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, 480, 200, 60)  # 调整位置防止被文字遮挡

        # 当前选择的项目
        self.current_selected_partner = None
        self.current_selected_weapon = None

        pygame.event.clear()

        # 按战力排序
        self.duck.partners.sort(key=lambda p: getattr(p, 'get_total_power', lambda x: p.attack_power)(self.duck.buffs),
                                reverse=True)
        self.duck.weapons.sort(key=lambda w: w.attack_power, reverse=True)
        logging.info(
            f"BattlePrepState initialized. Partners: {len(self.duck.partners)}, Weapons: {len(self.duck.weapons)}")


    def update(self, screen, keys, events):
        current_time = pygame.time.get_ticks()
        if current_time < self.initial_delay:
            return True

        if current_time - self.last_key_press < 100:
            return True

        self.partner_slide_x += (self.target_partner_slide_x - self.partner_slide_x) * 0.2
        self.weapon_slide_x += (self.target_weapon_slide_x - self.weapon_slide_x) * 0.2

        screen.fill(WHITE)
        title = self.font.render("BOSS 战准备", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 70, 10))

        # 绘制选择按钮
        pygame.draw.rect(screen, (200, 200, 255) if self.state == "选择伙伴" else (150, 150, 200), self.partner_button)
        pygame.draw.rect(screen, (200, 200, 255) if self.state == "选择武器" else (150, 150, 200), self.weapon_button)

        partner_text = self.font.render("选择伙伴", True, BLACK)
        weapon_text = self.font.render("选择武器", True, BLACK)
        screen.blit(partner_text, (self.partner_button.x + 20, self.partner_button.y + 10))
        screen.blit(weapon_text, (self.weapon_button.x + 20, self.weapon_button.y + 10))

        # 绘制对话框
        partner_dialog_pos = (SCREEN_WIDTH // 2 - 300, 100)
        weapon_dialog_pos = (SCREEN_WIDTH // 2 - 300, 310)

        # 伙伴选择对话框
        self.partner_dialog.fill((255, 255, 255))
        pygame.draw.rect(self.partner_dialog, BLACK, (0, 0, 600, 200), 2)

        # 显示当前选择的伙伴数量
        selected_count_text = self.font.render(f"已选择: {len(self.selected_partners)}/3", True, BLACK)
        self.partner_dialog.blit(selected_count_text, (20, 10))

        # 显示伙伴
        for i in range(4):  # 每行显示4个伙伴
            x = 50 + i * 140 + self.partner_slide_x
            y = 50
            index = self.partner_offset + i
            if index < len(self.duck.partners):
                partner = self.duck.partners[index]

                # 伙伴图像区域
                partner_rect = pygame.Rect(x, y, 60, 60)

                # 绘制伙伴图像
                try:
                    if partner.image and isinstance(partner.image, pygame.Surface):
                        # 确保图像是一个有效的Surface
                        scaled_image = pygame.transform.scale(partner.image, (60, 60))
                        self.partner_dialog.blit(scaled_image, (x, y))
                    else:
                        # 如果没有有效图像，画一个矩形并添加日志
                        pygame.draw.rect(self.partner_dialog, partner.color, (x, y, 60, 60))
                        if not hasattr(partner, 'image_log_done'):
                            logging.info(f"Partner {partner.index} has no valid image, using color block")
                            partner.image_log_done = True
                except Exception as e:
                    logging.error(f"Error displaying partner image: {e}")
                    pygame.draw.rect(self.partner_dialog, partner.color, (x, y, 60, 60))

                # 高亮显示当前选中的伙伴
                if index == self.partner_index and self.state == "选择伙伴":
                    pygame.draw.rect(self.partner_dialog, (255, 0, 0), (x - 2, y - 2, 64, 64), 2)
                    self.current_selected_partner = partner

                # 如果伙伴已被选择，显示绿色边框
                if partner in self.selected_partners:
                    pygame.draw.rect(self.partner_dialog, (0, 255, 0), (x - 4, y - 4, 68, 68), 3)

                # 获取伙伴战力
                try:
                    power = int(partner.get_total_power(self.duck.buffs))
                except:
                    power = partner.attack_power

                # 只显示战力，使用小号字体
                small_font = pygame.font.SysFont("SimHei", 18)
                power_text = small_font.render(f"战力: {power}", True, BLACK)
                self.partner_dialog.blit(power_text, (x, y + 70))

                # 检测鼠标点击
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        dialog_mouse_pos = (mouse_pos[0] - partner_dialog_pos[0], mouse_pos[1] - partner_dialog_pos[1])

                        if partner_rect.collidepoint(dialog_mouse_pos) and self.state == "选择伙伴":
                            self.partner_index = index
                            self.current_selected_partner = partner

                            # 如果伙伴未被选择且还没选满3个，则选择它
                            if partner not in self.selected_partners and len(self.selected_partners) < 3:
                                self.selected_partners.append(partner)
                                logging.info(f"Selected partner at index {index}")
                            # 如果已被选择，则取消选择
                            elif partner in self.selected_partners:
                                self.selected_partners.remove(partner)
                                logging.info(f"Unselected partner at index {index}")
            else:
                pygame.draw.rect(self.partner_dialog, (200, 200, 200), (x, y, 60, 60))

        screen.blit(self.partner_dialog, partner_dialog_pos)

        # 武器选择对话框
        self.weapon_dialog.fill((255, 255, 255))
        pygame.draw.rect(self.weapon_dialog, BLACK, (0, 0, 600, 200), 2)

        # 显示当前选择的武器数量
        selected_count_text = self.font.render(f"已选择: {len(self.selected_weapons)}/3", True, BLACK)
        self.weapon_dialog.blit(selected_count_text, (20, 10))

        # 显示武器
        for i in range(5):  # 每行显示5个武器
            x = 40 + i * 110 + self.weapon_slide_x
            y = 50
            index = self.weapon_offset + i
            if index < len(self.duck.weapons):
                weapon = self.duck.weapons[index]

                # 武器图像区域
                weapon_rect = pygame.Rect(x, y, 50, 50)

                # 绘制武器图像
                if weapon.image:
                    self.weapon_dialog.blit(pygame.transform.scale(weapon.image, (50, 50)), (x, y))
                else:
                    pygame.draw.rect(self.weapon_dialog, weapon.color, (x, y, 50, 50))

                # 高亮显示当前选中的武器
                if index == self.weapon_index and self.state == "选择武器":
                    pygame.draw.rect(self.weapon_dialog, (255, 0, 0), (x - 2, y - 2, 54, 54), 2)
                    self.current_selected_weapon = weapon

                # 如果武器已被选择，显示绿色边框
                if weapon in self.selected_weapons:
                    pygame.draw.rect(self.weapon_dialog, (0, 255, 0), (x - 4, y - 4, 58, 58), 3)

                # 只显示战力，使用小号字体
                small_font = pygame.font.SysFont("SimHei", 18)
                power_text = small_font.render(f"战力: {weapon.attack_power}", True, BLACK)
                self.weapon_dialog.blit(power_text, (x, y + 60))

                # 检测鼠标点击
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        dialog_mouse_pos = (mouse_pos[0] - weapon_dialog_pos[0], mouse_pos[1] - weapon_dialog_pos[1])

                        if weapon_rect.collidepoint(dialog_mouse_pos) and self.state == "选择武器":
                            self.weapon_index = index
                            self.current_selected_weapon = weapon

                            # 如果武器未被选择且还没选满3个，则选择它
                            if weapon not in self.selected_weapons and len(self.selected_weapons) < 3:
                                self.selected_weapons.append(weapon)
                                logging.info(f"Selected weapon at index {index}")
                            # 如果已被选择，则取消选择
                            elif weapon in self.selected_weapons:
                                self.selected_weapons.remove(weapon)
                                logging.info(f"Unselected weapon at index {index}")
            else:
                pygame.draw.rect(self.weapon_dialog, (200, 200, 200), (x, y, 50, 50))

        screen.blit(self.weapon_dialog, weapon_dialog_pos)

        # 绘制明显的进入战斗按钮 - 调整位置以避免文本阻挡
        battle_button_color = (255, 50, 50) if len(self.selected_partners) > 0 else (150, 150, 150)
        pygame.draw.rect(screen, battle_button_color, self.battle_button)
        pygame.draw.rect(screen, (0, 0, 0), self.battle_button, 3)  # 黑色边框
        battle_text = self.font.render("进入战斗!", True, (255, 255, 255))  # 白色文字
        screen.blit(battle_text, (self.battle_button.x + 40, self.battle_button.y + 15))

        # 处理事件
        for event in events:
            # 空格键取消当前选中项
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.state == "选择伙伴" and self.current_selected_partner:
                    if self.current_selected_partner in self.selected_partners:
                        self.selected_partners.remove(self.current_selected_partner)
                        logging.info(f"Unselected partner using space key")
                    self.last_key_press = current_time

                elif self.state == "选择武器" and self.current_selected_weapon:
                    if self.current_selected_weapon in self.selected_weapons:
                        self.selected_weapons.remove(self.current_selected_weapon)
                        logging.info(f"Unselected weapon using space key")
                    self.last_key_press = current_time

            # 鼠标点击
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # 检测伙伴/武器选择按钮
                if self.partner_button.collidepoint(mouse_pos):
                    self.state = "选择伙伴"
                    logging.info("Switched to 选择伙伴")

                elif self.weapon_button.collidepoint(mouse_pos):
                    self.state = "选择武器"
                    logging.info("Switched to 选择武器")

                # 检测战斗按钮
                elif self.battle_button.collidepoint(mouse_pos):
                    # 确保至少选择了一个伙伴
                    if len(self.selected_partners) > 0:
                        logging.info(
                            f"Battle button clicked! Entering battle with {len(self.selected_partners)} partners and {len(self.selected_weapons)} weapons")
                        return False  # 返回False表示准备完毕，进入战斗
                    else:
                        # 如果没有选择伙伴，显示提示
                        logging.info("No partners selected, cannot start battle")

            # 支持键盘导航 - 使用A和D键
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1 or event.key == pygame.K_a:
                    self.state = "选择伙伴"
                    self.last_key_press = current_time
                elif event.key == pygame.K_2 or event.key == pygame.K_d:
                    self.state = "选择武器"
                    self.last_key_press = current_time

                # 使用A和D键滚动
                elif self.state == "选择伙伴":
                    if event.key == pygame.K_a:  # A键向左
                        if self.partner_offset > 0:
                            self.partner_offset -= 1
                            self.target_partner_slide_x += 140
                        self.last_key_press = current_time
                    elif event.key == pygame.K_d:  # D键向右
                        if self.partner_offset + 4 < len(self.duck.partners):
                            self.partner_offset += 1
                            self.target_partner_slide_x -= 140
                        self.last_key_press = current_time
                    # 支持ENTER键直接进入战斗
                    elif event.key == pygame.K_RETURN and len(self.selected_partners) > 0:
                        logging.info(f"Enter key pressed! Starting battle with {len(self.selected_partners)} partners")
                        return False
                elif self.state == "选择武器":
                    if event.key == pygame.K_a:  # A键向左
                        if self.weapon_offset > 0:
                            self.weapon_offset -= 1
                            self.target_weapon_slide_x += 110
                        self.last_key_press = current_time
                    elif event.key == pygame.K_d:  # D键向右
                        if self.weapon_offset + 5 < len(self.duck.weapons):
                            self.weapon_offset += 1
                            self.target_weapon_slide_x -= 110
                        self.last_key_press = current_time
                    # 支持ENTER键直接进入战斗
                    elif event.key == pygame.K_RETURN and len(self.selected_partners) > 0:
                        logging.info(f"Enter key pressed! Starting battle with {len(self.selected_partners)} partners")
                        return False

        # 也支持A和D按住不放时连续滚动
        if current_time - self.last_key_press > 200:  # 控制滚动速度
            if self.state == "选择伙伴":
                if keys[pygame.K_a]:  # A键向左
                    if self.partner_offset > 0:
                        self.partner_offset -= 1
                        self.target_partner_slide_x += 140
                        self.last_key_press = current_time
                elif keys[pygame.K_d]:  # D键向右
                    if self.partner_offset + 4 < len(self.duck.partners):
                        self.partner_offset += 1
                        self.target_partner_slide_x -= 140
                        self.last_key_press = current_time
            elif self.state == "选择武器":
                if keys[pygame.K_a]:  # A键向左
                    if self.weapon_offset > 0:
                        self.weapon_offset -= 1
                        self.target_weapon_slide_x += 110
                        self.last_key_press = current_time
                elif keys[pygame.K_d]:  # D键向右
                    if self.weapon_offset + 5 < len(self.duck.weapons):
                        self.weapon_offset += 1
                        self.target_weapon_slide_x -= 110
                        self.last_key_press = current_time

        pygame.display.flip()
        return True

# game_state.py (第2部分)
class GameState:
    def __init__(self, duck):
        self.duck = duck
        self.state = "explore"
        self.in_battle = False
        self.weapons = []
        self.partners = []
        self.npc = None
        self.enemy = None
        self.trap = None
        self.level = 0
        self.max_levels = 5
        self.level_types = ["explore", "explore", "npc", "rest"]
        self.assigned_levels = []
        self.current_level_type = None
        self.font = pygame.font.SysFont("SimHei", 32)
        self.info_text = ""
        self.info_timer = 0
        self.last_space_press = 0
        self.buffs = [
            ("勇敢 BUFF", "战力加 15"),
            ("幸运 BUFF", "骰子点数 +2"),
            ("魅力 BUFF", "魅力加 15"),
            ("恢复 HP", "恢复 HP")
        ]
        self.selected_buffs = []
        self.buff_selected = False
        self.battle_prep = None
        self.selected_partners = []
        self.selected_weapons = []
        
        # 添加探索背景图片加载
        self.exploration_background = None
        exploration_bg_path = os.path.join(ASSETS_DIR, "exploration_background.png")
        if os.path.exists(exploration_bg_path):
            try:
                self.exploration_background = pygame.image.load(exploration_bg_path)
                self.exploration_background = pygame.transform.scale(self.exploration_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
                logging.info("Exploration background loaded successfully")
            except Exception as e:
                logging.error(f"Failed to load exploration background: {e}")
                
        logging.info("GameState initialized, advancing to level 1")
        self.advance_level()

    def advance_level(self):
        try:
            self.level += 1
            if self.level <= self.max_levels:
                if self.level == self.max_levels:
                    self.current_level_type = "battle_prep"
                    self.state = "battle_prep"
                    self.battle_prep = BattlePrepState(self.duck, self.font)
                    logging.info(f"Advancing to level {self.level}: battle_prep")
                else:
                    available_types = [t for t in self.level_types if
                                       t not in self.assigned_levels or self.assigned_levels.count(
                                           t) < self.level_types.count(t)]
                    self.current_level_type = random.choice(available_types)
                    self.assigned_levels.append(self.current_level_type)
                    logging.info(f"Advancing to level {self.level}: {self.current_level_type}")
                self.weapons = create_weapons(random.randint(1, 3)) if self.current_level_type == "explore" else []
                self.partners = create_partners(random.randint(1, 2)) if self.current_level_type == "explore" else []
                self.npc = None
                self.enemy = None
                self.trap = None
                self.buff_selected = False
                self.selected_buffs = random.sample(self.buffs, 2) if self.current_level_type == "rest" else []
                self.info_text = f"进入第 {self.level} 关：{self.get_level_type_name()}"
                self.info_timer = 180
                if self.current_level_type == "npc":
                    self.npc = NPC(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30),
                                   random.choice(["lady_duck", "broccoli_general", "human_child"]))
                elif self.current_level_type == "explore" and random.random() < 0.3:
                    self.trap = {"type": "trap", "x": random.randint(0, SCREEN_WIDTH - 30),
                                 "y": random.randint(0, SCREEN_HEIGHT - 30)}
                elif self.current_level_type == "explore" and random.random() < 0.2:
                    self.enemy = Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4,
                                       random.choice(["human", "traitor_duck", "soul", "ingredient"]), is_special=True)
            else:
                self.current_level_type = "battle_prep"
                self.state = "battle_prep"
                self.battle_prep = BattlePrepState(self.duck, self.font)
                logging.info(f"Advancing to level {self.level}: battle_prep (max level)")
        except Exception as e:
            logging.error(f"Failed to advance level: {e}")

    def update(self, screen, keys, events):
        if self.current_level_type is None:
            logging.error("current_level_type is None, initializing first level")
            self.advance_level()

        current_time = pygame.time.get_ticks()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.state == "explore":
                if current_time - self.last_space_press > 500:
                    self.advance_level()
                    self.last_space_press = current_time

        logging.info(f"Current state: {self.state}, Level: {self.level}, Type: {self.current_level_type}")

        if self.state == "explore":
            self.handle_exploration(screen, keys, events)
        elif self.state == "battle_prep":
            if not self.battle_prep.update(screen, keys, events):
                self.selected_partners = self.battle_prep.selected_partners
                self.selected_weapons = self.battle_prep.selected_weapons

                # 安全检查：确保有至少一个伙伴
                if not self.selected_partners:
                    # 如果没有选择伙伴，自动选择第一个可用的伙伴
                    if self.duck.partners:
                        self.selected_partners = [self.duck.partners[0]]

                logging.info(
                    f"Starting battle with {len(self.selected_partners)} partners and {len(self.selected_weapons)} weapons")
                self.state = "battle"
                self.in_battle = True
                self.battle_prep = None
                self.current_level_type = "battle"
                self.enemy = Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, "human", is_boss=True)
                logging.info("Transitioning to battle state")
        elif self.state == "battle":
            try:
                logging.info("Handling battle")
                battle_ended, victory = handle_battle(self.duck, [self.enemy] if self.enemy else [], keys, screen,
                                                      self.font, self.level, self.selected_partners,
                                                      self.selected_weapons, events)
                if battle_ended:
                    self.state = "explore"
                    self.in_battle = False
                    if not victory:
                        print("游戏结束！")
                        pygame.quit()
                        sys.exit()
                    self.enemy = None
                    self.selected_partners = []
                    self.selected_weapons = []
            except Exception as e:
                logging.error(f"Error during battle: {e}")
                logging.error(traceback.format_exc())
                # 发生错误时，返回探索状态
                self.state = "explore"
                self.in_battle = False

    # game_state.py 中 handle_exploration 方法优化
    def handle_exploration(self, screen, keys, events):
        # 绘制背景
        if hasattr(self, 'exploration_background') and self.exploration_background:
            screen.blit(self.exploration_background, (0, 0))
        else:
            screen.fill(WHITE)  # 原有代码
            
        self.duck.move(keys)
        self.duck.draw(screen)

        if self.current_level_type == "explore":
            for weapon in self.weapons:
                weapon.draw(screen)
                if not weapon.collected and self.duck.rect().colliderect(
                        pygame.Rect(weapon.x, weapon.y, weapon.width, weapon.height)):
                    weapon.collected = True
                    if self.duck.collect(weapon):
                        self.info_text = "拾取了武器！攻击力提升！"
                        self.info_timer = 120

            for partner in self.partners:
                partner.draw(screen)
                if not partner.collected and self.duck.rect().colliderect(
                        pygame.Rect(partner.x, partner.y, partner.width, partner.height)):
                    partner.collected = True
                    if self.duck.collect(partner):
                        self.info_text = "伙伴加入了你的队伍！"
                        self.info_timer = 120
                    else:
                        self.info_text = "队伍已满！"
                        self.info_timer = 120

            if self.trap:
                pygame.draw.rect(screen, RED, (self.trap["x"], self.trap["y"], 30, 30))
                if self.duck.rect().colliderect(pygame.Rect(self.trap["x"], self.trap["y"], 30, 30)):
                    if self.duck.interact(self.trap, screen, self.font, self, events):
                        self.trap = None

            if self.enemy and self.enemy.is_special:
                self.enemy.draw(screen)
                if self.duck.rect().colliderect(
                        pygame.Rect(self.enemy.x, self.enemy.y, self.enemy.width, self.enemy.height)):
                    if self.duck.interact(self.enemy, screen, self.font, self, events):
                        self.enemy = None

        elif self.current_level_type == "rest":
            background = pygame.Surface((400, 200))
            background.set_alpha(200)
            background.fill((255, 255, 255))
            screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))
            text = self.font.render("休息关卡：选择行动", True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 80))
            if self.selected_buffs:
                buff1_name, buff1_desc = self.selected_buffs[0]
                buff2_name, buff2_desc = self.selected_buffs[1]
                option1_text = self.font.render(f"按 1 {buff1_desc}", True, BLACK)
                option2_text = self.font.render(f"按 2 {buff2_desc}", True, BLACK)
                screen.blit(option1_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 40))
                screen.blit(option2_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
                for event in events:
                    if event.type == pygame.KEYDOWN and not self.buff_selected:
                        if event.key == pygame.K_1:
                            self.duck.add_buff(buff1_name)
                            self.buff_selected = True
                            self.info_text = f"获得 {buff1_name}！"
                            self.info_timer = 120
                            self.selected_buffs = []
                            logging.info(f"BUFF selected: {buff1_name}, advancing to next level")
                            self.advance_level()
                        elif event.key == pygame.K_2:
                            self.duck.add_buff(buff2_name)
                            self.buff_selected = True
                            self.info_text = f"获得 {buff2_name}！"
                            self.info_timer = 120
                            self.selected_buffs = []
                            logging.info(f"BUFF selected: {buff2_name}, advancing to next level")
                            self.advance_level()

        elif self.current_level_type == "npc" and self.npc:
            self.npc.draw(screen)
            if self.duck.rect().colliderect(pygame.Rect(self.npc.x, self.npc.y, self.npc.width, self.npc.height)):
                if self.duck.interact(self.npc, screen, self.font, self, events):
                    self.npc = None

        elif self.current_level_type == "battle" and self.enemy:
            self.enemy.draw(screen)
            if self.duck.rect().colliderect(
                    pygame.Rect(self.enemy.x, self.enemy.y, self.enemy.width, self.enemy.height)):
                self.state = "battle"
                self.in_battle = True

        if self.info_timer > 0:
            self.info_timer -= 1
        else:
            self.info_text = ""

        if self.info_text:
            background = pygame.Surface((300, 50))
            background.set_alpha(200)
            background.fill((255, 255, 255))
            screen.blit(background, (50, SCREEN_HEIGHT - 110))
            text = self.font.render(self.info_text, True, BLACK)
            screen.blit(text, (50, SCREEN_HEIGHT - 110))

        # 优化状态栏 - 添加半透明背景但位置下移
        toolbar_height = 80  # 降低高度
        toolbar = pygame.Surface((SCREEN_WIDTH, toolbar_height))
        toolbar.set_alpha(200)
        toolbar.fill((200, 200, 200))
        screen.blit(toolbar, (0, SCREEN_HEIGHT - toolbar_height))

        # 横向排列属性，不再显示战力
        small_font = pygame.font.SysFont("SimHei", 22)  # 使用小一号字体

        # 计算横向布局
        attr_spacing = 15  # 属性间距
        attr_x = 20  # 初始X位置

        # 武器数量
        weapon_text = small_font.render(f"武器: {len(self.duck.weapons)}", True, BLACK)
        screen.blit(weapon_text, (attr_x, SCREEN_HEIGHT - toolbar_height + 15))
        attr_x += weapon_text.get_width() + attr_spacing * 2

        # 伙伴数量
        partner_text = small_font.render(f"伙伴: {len(self.duck.partners)}", True, BLACK)
        screen.blit(partner_text, (attr_x, SCREEN_HEIGHT - toolbar_height + 15))
        attr_x += partner_text.get_width() + attr_spacing * 2

        # 魅力
        charm_text = small_font.render(f"魅力: {self.duck.charm}", True, BLACK)
        screen.blit(charm_text, (attr_x, SCREEN_HEIGHT - toolbar_height + 15))
        attr_x += charm_text.get_width() + attr_spacing * 2

        # 舆论
        rep_text = small_font.render(f"舆论: {self.duck.reputation}", True, BLACK)
        screen.blit(rep_text, (attr_x, SCREEN_HEIGHT - toolbar_height + 15))

        # 显示当前BUFF (如果有)
        if self.duck.buffs:
            buff_text = small_font.render(f"当前BUFF: {', '.join(self.duck.buffs)}", True, BLACK)
            screen.blit(buff_text, (20, SCREEN_HEIGHT - toolbar_height + 45))

        # HP显示
        hp_text = small_font.render(f"HP: {self.duck.hp}/{self.duck.max_hp}", True, BLACK)
        screen.blit(hp_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - toolbar_height + 15))

        # 将"按空格进入下一关"提示移到状态栏右上角
        prompt_text = small_font.render("按空格进入下一关", True, BLACK)
        screen.blit(prompt_text, (SCREEN_WIDTH - prompt_text.get_width() - 20, SCREEN_HEIGHT - toolbar_height + 45))

        # 关卡信息显示在左上角 - 添加半透明背景使文字更突出
        level_bg = pygame.Surface((250, 40))
        level_bg.set_alpha(180)
        level_bg.fill((255, 255, 255))
        screen.blit(level_bg, (5, 5))
        
        level_text = self.font.render(f"Level: {self.level} ({self.get_level_type_name()})", True, BLACK)
        screen.blit(level_text, (10, 10))

    def get_level_type_name(self):
        if self.current_level_type is None:
            return "未初始化"
        if self.current_level_type == "explore":
            return "探索关卡"
        elif self.current_level_type == "rest":
            return "休息关卡"
        elif self.current_level_type == "npc":
            return "NPC 关卡"
        elif self.current_level_type == "battle":
            return "BOSS 关卡"
        elif self.current_level_type == "battle_prep":
            return "BOSS 战准备"
        return "未知关卡"

    def handle_interaction_success(self, target):
        try:
            if isinstance(target, NPC):
                # 成功互动后NPC加入队伍
                new_partner = target.convert_to_partner(len(self.duck.partners) + 1)
                self.duck.partners.append(new_partner)

                if target.npc_type == "broccoli_general":
                    self.duck.attack_power += 5
                    self.info_text = "与西兰花将军互动成功，加入队伍！攻击力 +5！"
                elif target.npc_type == "human_child":
                    self.duck.reputation += 10
                    self.info_text = "与人类小孩互动成功，加入队伍！舆论 +10！"
                elif target.npc_type == "lady_duck":
                    self.duck.charm += 2
                    self.info_text = "与女士鸭互动成功，加入队伍！魅力 +2！"

                self.info_timer = 120
                self.npc = None

            elif isinstance(target, dict) and target["type"] == "trap":
                self.info_text = "成功拆除陷阱！"
                self.info_timer = 120
            elif isinstance(target, Enemy) and target.is_special:
                target.attack_power = int(target.attack_power * 0.5)
                self.info_text = "勇气挑战成功，敌人战力减半！"
                self.info_timer = 120
        except Exception as e:
            logging.error(f"Interaction success handling failed: {e}")