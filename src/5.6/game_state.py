import pygame
import random
import sys
import logging
from weapon import create_weapons
from partner import create_partners
from battle import handle_battle
from constants import WHITE, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, MAX_PARTNERS, BOSS_LEVEL, RED
from npc import NPC
from enemy import Enemy

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

class BattlePrepState:
    def __init__(self, duck, font):
        self.duck = duck
        self.font = font
        self.selected_partners = []
        self.selected_weapons = []
        self.partner_index = 0
        self.weapon_index = 0
        self.state = "选择完毕"
        self.last_key_press = 0
        self.partner_dialog = pygame.Surface((450, 150))
        self.partner_dialog.set_alpha(255)
        self.weapon_dialog = pygame.Surface((450, 150))
        self.weapon_dialog.set_alpha(255)
        logging.info(f"BattlePrepState initialized. Partners: {len(self.duck.partners)}, Weapons: {len(self.duck.weapons)}")

    def update(self, screen, keys, events):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_key_press < 100:
            return True

        screen.fill(WHITE)
        title = self.font.render("BOSS 战准备：选择伙伴和武器（各 3 个）", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 200, 50))

        partner_dialog_pos = (SCREEN_WIDTH // 2 - 225, 100)
        weapon_dialog_pos = (SCREEN_WIDTH // 2 - 225, 350)
        pygame.draw.rect(screen, (255, 0, 0), (partner_dialog_pos[0], partner_dialog_pos[1], 450, 150), 2)
        pygame.draw.rect(screen, (255, 0, 0), (weapon_dialog_pos[0], weapon_dialog_pos[1], 450, 150), 2)

        self.partner_dialog.fill((255, 255, 255))
        pygame.draw.rect(self.partner_dialog, BLACK, (0, 0, 450, 150), 2)
        text = self.font.render("伙伴选择", True, BLACK)
        self.partner_dialog.blit(text, (10, 10))
        if not self.duck.partners:
            text = self.font.render("无可用伙伴", True, BLACK)
            self.partner_dialog.blit(text, (50, 60))
            for i in range(3):
                x = 50 + i * 120
                y = 40
                pygame.draw.rect(self.partner_dialog, (200, 200, 200), (x, y, 40, 40))
        for i, partner in enumerate(self.duck.partners):
            x = 50 + (i % 3) * 120
            y = 40
            highlight = i == self.partner_index and self.state == "选择伙伴"
            if partner.image:
                self.partner_dialog.blit(partner.image, (x, y))
            else:
                pygame.draw.rect(self.partner_dialog, partner.color, (x, y, 40, 40))
            if highlight:
                pygame.draw.rect(self.partner_dialog, (255, 0, 0), (x - 2, y - 2, 44, 44), 2)
            selected = "已选择" if partner in self.selected_partners else ""
            text = self.font.render(f"{partner.index} {selected}", True, BLACK)
            self.partner_dialog.blit(text, (x, y + 50))
        screen.blit(self.partner_dialog, partner_dialog_pos)

        self.weapon_dialog.fill((255, 255, 255))
        pygame.draw.rect(self.weapon_dialog, BLACK, (0, 0, 450, 150), 2)
        text = self.font.render("武器选择", True, BLACK)
        self.weapon_dialog.blit(text, (10, 10))
        if not self.duck.weapons:
            text = self.font.render("无可用武器", True, BLACK)
            self.weapon_dialog.blit(text, (50, 60))
            for i in range(3):
                x = 50 + i * 120
                y = 40
                pygame.draw.rect(self.weapon_dialog, (200, 200, 200), (x, y, 40, 40))
        for i, weapon in enumerate(self.duck.weapons):
            x = 50 + (i % 3) * 120
            y = 40
            highlight = i == self.weapon_index and self.state == "选择武器"
            if weapon.image:
                self.weapon_dialog.blit(weapon.image, (x, y))
            else:
                pygame.draw.rect(self.weapon_dialog, weapon.color, (x, y, 40, 40))
            if highlight:
                pygame.draw.rect(self.weapon_dialog, (255, 0, 0), (x - 2, y - 2, 44, 44), 2)
            selected = "已选择" if weapon in self.selected_weapons else ""
            text = self.font.render(f"{weapon.weapon_type} {selected}", True, BLACK)
            self.weapon_dialog.blit(text, (x, y + 50))
        screen.blit(self.weapon_dialog, weapon_dialog_pos)

        debug_text = self.font.render(f"状态: {self.state}", True, BLACK)
        screen.blit(debug_text, (10, SCREEN_HEIGHT - 100))

        prompt = self.font.render("按 1 选择伙伴，2 选择武器，左右键移动，空格确认", True, BLACK)
        screen.blit(prompt, (50, SCREEN_HEIGHT - 50))

        for event in events:
            if event.type == pygame.KEYDOWN:
                logging.info(f"Key pressed: {event.key}, State: {self.state}")
                if self.state == "选择完毕":
                    if event.key == pygame.K_1:
                        self.state = "选择伙伴"
                        self.last_key_press = current_time
                        logging.info("Switched to 选择伙伴")
                    elif event.key == pygame.K_2:
                        self.state = "选择武器"
                        self.last_key_press = current_time
                        logging.info("Switched to 选择武器")
                    elif event.key == pygame.K_SPACE:
                        logging.info("Space pressed, transitioning to battle")
                        return False
                elif self.state == "选择伙伴":
                    if event.key == pygame.K_LEFT and self.duck.partners:
                        self.partner_index = max(0, self.partner_index - 1)
                        self.last_key_press = current_time
                    elif event.key == pygame.K_RIGHT and self.duck.partners:
                        self.partner_index = min(len(self.duck.partners) - 1, self.partner_index + 1)
                        self.last_key_press = current_time
                    elif event.key == pygame.K_SPACE and self.duck.partners and len(self.selected_partners) < 3:
                        partner = self.duck.partners[self.partner_index]
                        if partner not in self.selected_partners:
                            self.selected_partners.append(partner)
                            self.last_key_press = current_time
                    elif event.key == pygame.K_1:
                        self.state = "选择完毕"
                        self.last_key_press = current_time
                        logging.info("Switched to 选择完毕 from 选择伙伴")
                elif self.state == "选择武器":
                    if event.key == pygame.K_LEFT and self.duck.weapons:
                        self.weapon_index = max(0, self.weapon_index - 1)
                        self.last_key_press = current_time
                    elif event.key == pygame.K_RIGHT and self.duck.weapons:
                        self.weapon_index = min(len(self.duck.weapons) - 1, self.weapon_index + 1)
                        self.last_key_press = current_time
                    elif event.key == pygame.K_SPACE and self.duck.weapons and len(self.selected_weapons) < 3:
                        weapon = self.duck.weapons[self.weapon_index]
                        if weapon not in self.selected_weapons:
                            self.selected_weapons.append(weapon)
                            self.last_key_press = current_time
                    elif event.key == pygame.K_2:
                        self.state = "选择完毕"
                        self.last_key_press = current_time
                        logging.info("Switched to 选择完毕 from 选择武器")

        pygame.display.flip()
        return True

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
        self.buffs = ["勇敢", "智慧", "团结"]
        self.buff_selected = False
        self.battle_prep = None
        self.selected_partners = []
        self.selected_weapons = []
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
                    available_types = [t for t in self.level_types if t not in self.assigned_levels or self.assigned_levels.count(t) < self.level_types.count(t)]
                    self.current_level_type = random.choice(available_types)
                    self.assigned_levels.append(self.current_level_type)
                    logging.info(f"Advancing to level {self.level}: {self.current_level_type}")
                self.weapons = create_weapons(random.randint(1, 3)) if self.current_level_type == "explore" else []
                self.partners = create_partners(random.randint(1, 2)) if self.current_level_type == "explore" else []
                self.npc = None
                self.enemy = None
                self.trap = None
                self.buff_selected = False
                self.info_text = f"进入第 {self.level} 关：{self.get_level_type_name()}"
                self.info_timer = 180
                if self.current_level_type == "npc":
                    self.npc = NPC(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30), random.choice(["lady_duck", "broccoli_general", "human_child"]))
                elif self.current_level_type == "explore" and random.random() < 0.3:
                    self.trap = {"type": "trap", "x": random.randint(0, SCREEN_WIDTH - 30), "y": random.randint(0, SCREEN_HEIGHT - 30)}
                elif self.current_level_type == "explore" and random.random() < 0.2:
                    self.enemy = Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, random.choice(["human", "traitor_duck", "soul", "ingredient"]), is_special=True)
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
                self.state = "battle"
                self.in_battle = True
                self.battle_prep = None
                self.current_level_type = "battle"
                self.enemy = Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, "human", is_boss=True)
                logging.info("Transitioning to battle state")
        elif self.state == "battle":
            battle_ended, victory = handle_battle(self.duck, [self.enemy] if self.enemy else [], keys, screen, self.font, self.level, self.selected_partners, self.selected_weapons)
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

    def handle_exploration(self, screen, keys, events):
        screen.fill(WHITE)
        self.duck.move(keys)
        self.duck.draw(screen)

        if self.current_level_type == "explore":
            for weapon in self.weapons:
                weapon.draw(screen)
                if not weapon.collected and self.duck.rect().colliderect(pygame.Rect(weapon.x, weapon.y, weapon.width, weapon.height)):
                    weapon.collected = True
                    if self.duck.collect(weapon):
                        self.info_text = "拾取了武器！攻击力提升！"
                        self.info_timer = 120

            for partner in self.partners:
                partner.draw(screen)
                if not partner.collected and self.duck.rect().colliderect(pygame.Rect(partner.x, partner.y, partner.width, partner.height)):
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
                if self.duck.rect().colliderect(pygame.Rect(self.enemy.x, self.enemy.y, self.enemy.width, self.enemy.height)):
                    if self.duck.interact(self.enemy, screen, self.font, self, events):
                        self.enemy = None

        elif self.current_level_type == "rest":
            background = pygame.Surface((400, 200))
            background.set_alpha(200)
            background.fill((255, 255, 255))
            screen.blit(background, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))
            text = self.font.render("休息关卡：选择行动", True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 80))
            recover_text = self.font.render("按 1 恢复 HP", True, BLACK)
            buff_text = self.font.render("按 2 选择 BUFF" if not self.buff_selected else "BUFF 已选择", True, BLACK)
            screen.blit(recover_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 40))
            screen.blit(buff_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.duck.recover()
                        self.info_text = "HP 已恢复！"
                        self.info_timer = 120
                        logging.info("HP recovered, advancing to next level")
                        self.advance_level()
                    elif event.key == pygame.K_2 and not self.buff_selected:
                        buff = random.choice(self.buffs)
                        self.duck.add_buff(buff)
                        self.buff_selected = True
                        self.info_text = f"获得 {buff} BUFF！"
                        self.info_timer = 120
                        logging.info(f"BUFF selected: {buff}, advancing to next level")
                        self.advance_level()

        elif self.current_level_type == "npc" and self.npc:
            self.npc.draw(screen)
            if self.duck.rect().colliderect(pygame.Rect(self.npc.x, self.npc.y, self.npc.width, self.npc.height)):
                if self.duck.interact(self.npc, screen, self.font, self, events):
                    self.npc = None

        elif self.current_level_type == "battle" and self.enemy:
            self.enemy.draw(screen)
            if self.duck.rect().colliderect(pygame.Rect(self.enemy.x, self.enemy.y, self.enemy.width, self.enemy.height)):
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

        toolbar = pygame.Surface((SCREEN_WIDTH, 180))
        toolbar.set_alpha(200)
        toolbar.fill((200, 200, 200))
        screen.blit(toolbar, (0, SCREEN_HEIGHT - 180))

        x_offset = 10
        for weapon in self.duck.weapons:
            if weapon.image:
                screen.blit(pygame.transform.scale(weapon.image, (20, 20)), (x_offset, SCREEN_HEIGHT - 170))
            else:
                pygame.draw.rect(screen, weapon.color, (x_offset, SCREEN_HEIGHT - 170, 20, 20))
            x_offset += 30
        x_offset += 10
        for partner in self.partners:
            if partner.image:
                screen.blit(pygame.transform.scale(partner.image, (20, 20)), (x_offset, SCREEN_HEIGHT - 170))
            else:
                pygame.draw.rect(screen, partner.color, (x_offset, SCREEN_HEIGHT - 170, 20, 20))
            x_offset += 30

        texts = [
            self.font.render(f"武器: {len(self.duck.weapons)}", True, BLACK),
            self.font.render(f"伙伴: {len(self.duck.partners)}", True, BLACK),
            self.font.render(f"魅力: {self.duck.charm}", True, BLACK),
            self.font.render(f"舆论: {self.duck.reputation}", True, BLACK),
            self.font.render(f"战力: {self.duck.get_total_power()}", True, BLACK)
        ]
        for i, text in enumerate(texts):
            screen.blit(text, (10, SCREEN_HEIGHT - 140 + i * 30))

        prompt_text = self.font.render("按空格进入下一关", True, BLACK)
        screen.blit(prompt_text, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 50))

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
                if target.npc_type == "broccoli_general":
                    self.duck.attack_power += 5
                    self.info_text = "与西兰花将军互动，攻击力 +5！"
                elif target.npc_type == "human_child":
                    self.duck.reputation += 10
                    self.info_text = "与人类小孩互动，舆论 +10！"
                elif target.npc_type == "lady_duck":
                    self.duck.charm += 2
                    self.info_text = "与女士鸭互动，魅力 +2！"
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