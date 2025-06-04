import pygame
import random
import sys
import logging
from weapon import create_weapons
from partner import create_partners
from battle import handle_battle
from story import StoryEvent
from constants import WHITE, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, MAX_PARTNERS
from npc import NPC
from enemy import Enemy

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR)


class BattlePrepState:
    def __init__(self, duck, font):
        self.duck = duck
        self.font = font
        self.selected_partner = 0
        self.selected_weapon = 0
        self.state = "position"
        self.last_key_press = 0

    def update(self, screen, keys):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_key_press < 200:
            return self.state != "done"

        screen.fill(WHITE)
        alive_partners = [p for p in self.duck.partners if p.is_alive]

        title = self.font.render("战斗准备：选择队友站位和武器分配", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 200, 50))

        for i, partner in enumerate(alive_partners):
            color = (255, 0, 0) if i == self.selected_partner else BLACK
            pos_text = f"队友 {partner.index}: {'前排' if partner.position == 'front' else '后排'}"
            text = self.font.render(pos_text, True, color)
            screen.blit(text, (50, 100 + i * 40))

        for i, weapon in enumerate(self.duck.weapons):
            color = (255, 0, 0) if i == self.selected_weapon else BLACK
            holder = "无"
            if weapon == self.duck.held_weapon:
                holder = "鸭子"
            else:
                for j, partner in enumerate(alive_partners):
                    if weapon == partner.held_weapon:
                        holder = f"队友 {partner.index}"
            weapon_text = f"武器 {i + 1} (类型 {weapon.weapon_type}): {holder}"
            text = self.font.render(weapon_text, True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 + 50, 100 + i * 40))

        if self.duck.predict_risk:
            risk_text = f"预知风险: {self.duck.predict_risk} (按 1/2 选择应对)"
            text = self.font.render(risk_text, True, BLACK)
            screen.blit(text, (50, SCREEN_HEIGHT - 100))

        prompt = "按 1-5 选择队友，Q/W 切换站位，E/R 选择武器，T 分配武器，按空格确认"
        prompt_text = self.font.render(prompt, True, BLACK)
        screen.blit(prompt_text, (50, SCREEN_HEIGHT - 50))

        if keys[pygame.K_1] and len(alive_partners) >= 1:
            self.selected_partner = 0
            self.state = "position"
            self.last_key_press = current_time
        elif keys[pygame.K_2] and len(alive_partners) >= 2:
            self.selected_partner = 1
            self.state = "position"
            self.last_key_press = current_time
        elif keys[pygame.K_3] and len(alive_partners) >= 3:
            self.selected_partner = 2
            self.state = "position"
            self.last_key_press = current_time
        elif keys[pygame.K_4] and len(alive_partners) >= 4:
            self.selected_partner = 3
            self.state = "position"
            self.last_key_press = current_time
        elif keys[pygame.K_5] and len(alive_partners) >= 5:
            self.selected_partner = 4
            self.state = "position"
            self.last_key_press = current_time
        elif keys[pygame.K_q] and alive_partners:
            alive_partners[self.selected_partner].position = "front"
            self.last_key_press = current_time
        elif keys[pygame.K_w] and alive_partners:
            alive_partners[self.selected_partner].position = "back"
            self.last_key_press = current_time
        elif keys[pygame.K_e] and self.duck.weapons:
            self.selected_weapon = max(0, self.selected_weapon - 1)
            self.state = "weapon"
            self.last_key_press = current_time
        elif keys[pygame.K_r] and self.duck.weapons:
            self.selected_weapon = min(len(self.duck.weapons) - 1, self.selected_weapon + 1)
            self.state = "weapon"
            self.last_key_press = current_time
        elif keys[pygame.K_t] and self.state == "weapon" and self.duck.weapons:
            weapon = self.duck.weapons[self.selected_weapon]
            if self.duck.held_weapon == weapon:
                self.duck.unequip_weapon()
            for partner in alive_partners:
                if partner.held_weapon == weapon:
                    partner.unequip_weapon()
            if self.selected_partner == -1:
                self.duck.equip_weapon(weapon)
            else:
                alive_partners[self.selected_partner].equip_weapon(weapon)
            self.last_key_press = current_time
        elif self.duck.predict_risk and keys[pygame.K_1]:
            if self.duck.predict_risk == "战斗陷阱":
                self.trap_damage = 0
                print("陷阱已拆除！")
            elif self.duck.predict_risk == "武器破坏":
                for partner in alive_partners:
                    partner.attack_power += 2
                print("武器已检查！")
            elif self.duck.predict_risk == "伙伴背叛":
                alive_partners[self.selected_partner].attack_power += 5
                print("伙伴已安抚！")
            self.duck.predict_risk = None
            self.last_key_press = current_time
        elif self.duck.predict_risk and keys[pygame.K_2]:
            if self.duck.predict_risk == "战斗陷阱":
                for partner in alive_partners:
                    partner.hp += 10
                print("掩体已加固！")
            elif self.duck.predict_risk == "武器破坏":
                self.duck.weapons.append(
                    Weapon(random.randint(0, SCREEN_WIDTH - 20), random.randint(0, SCREEN_HEIGHT - 20),
                           random.randint(1, 8)))
                print("备用武器已准备！")
            elif self.duck.predict_risk == "伙伴背叛":
                alive_partners.pop(self.selected_partner)
                print("伙伴已隔离！")
            self.duck.predict_risk = None
            self.last_key_press = current_time

        return self.state != "done"


class BuffSelectionState:
    def __init__(self, duck, font):
        self.duck = duck
        self.font = font
        self.selected_buff = 0
        self.selected_partner = 0
        self.buffs = ["攻击增强", "防御增强", "速度增强"]
        self.last_key_press = 0
        self.partner_rects = []

    def update(self, screen, keys):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_key_press < 200:
            return True

        screen.fill(WHITE)
        alive_partners = [p for p in self.duck.partners if p.is_alive]
        if not alive_partners:
            logging.warning("No alive partners available for buff selection.")
            return False

        title = self.font.render("选择一个 BUFF 和队友", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 100, 50))

        # 绘制队友选项
        self.partner_rects = []
        for i, partner in enumerate(alive_partners):
            color = (255, 0, 0) if i == self.selected_partner else BLACK
            text = self.font.render(f"队友 {partner.index}", True, color)
            text_rect = text.get_rect(topleft=(SCREEN_WIDTH // 2 - 50, 100 + i * 40))
            screen.blit(text, text_rect)
            self.partner_rects.append((i, text_rect))

        # 绘制 BUFF 选项
        for i, buff in enumerate(self.buffs):
            color = (255, 0, 0) if i == self.selected_buff else BLACK
            text = self.font.render(f"{buff}", True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - 50, 150 + len(alive_partners) * 40 + i * 40))

        prompt = "鼠标点击选择队友，W/S 选择 BUFF，按空格确认"
        prompt_text = self.font.render(prompt, True, BLACK)
        screen.blit(prompt_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 50))

        # 处理鼠标点击
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for partner_index, rect in self.partner_rects:
                    if rect.collidepoint(mouse_pos):
                        self.selected_partner = partner_index
                        self.last_key_press = current_time
                        logging.info(f"Selected partner {partner_index} via mouse click.")

        # 处理键盘输入
        if keys[pygame.K_w]:
            self.selected_buff = max(0, self.selected_buff - 1)
            self.last_key_press = current_time
            logging.info(f"Selected buff {self.buffs[self.selected_buff]} via W key.")
        elif keys[pygame.K_s]:
            self.selected_buff = min(len(self.buffs) - 1, self.selected_buff + 1)
            self.last_key_press = current_time
            logging.info(f"Selected buff {self.buffs[self.selected_buff]} via S key.")
        elif keys[pygame.K_SPACE]:
            selected_buff = self.buffs[self.selected_buff]
            dice = random.randint(1, 6)
            buff_effect = 0.05 * dice
            if selected_buff == "攻击增强":
                alive_partners[self.selected_partner].attack_power *= (1 + buff_effect)
            elif selected_buff == "防御增强":
                alive_partners[self.selected_partner].max_hp *= (1 + buff_effect)
                alive_partners[self.selected_partner].hp = alive_partners[self.selected_partner].max_hp
            elif selected_buff == "速度增强":
                alive_partners[self.selected_partner].attack_power *= (1 + buff_effect * 0.5)
            print(
                f"选择了 {selected_buff}，掷骰 {dice}，队友 {alive_partners[self.selected_partner].index} 效果提升 {buff_effect * 100}%")
            self.last_key_press = current_time
            return False

        return True


class GameState:
    def __init__(self, duck, enemies):
        self.duck = duck
        self.enemies = enemies
        self.state = "explore"
        self.story_event = StoryEvent()
        self.battle_prep = None
        self.buff_selection = None
        self.in_battle = False
        self.weapons = create_weapons(random.randint(1, 3))
        self.partners = create_partners(random.randint(1, 2))
        self.npc = None
        self.npc_appearances = 0
        self.max_npc_appearances = 2
        self.npc_types = ["lady_duck", "broccoli_general", "human_child"]
        self.font = pygame.font.SysFont("SimHei", 32)
        self.level = 1
        self.max_levels = 5
        self.current_level_type = random.choice(['A', 'B', 'C', 'D'])
        self.info_text = ""
        self.info_timer = 0
        self.last_space_press = 0
        self.trap_damage = 10

    def update(self, screen, keys, events):
        current_time = pygame.time.get_ticks()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.state == "explore":
                if current_time - self.last_space_press > 500:
                    if self.level < self.max_levels:
                        self.level += 1
                        self.current_level_type = random.choice(['A', 'B', 'C', 'D'])
                        self.weapons = create_weapons(random.randint(1, 3))
                        self.partners = create_partners(random.randint(1, 2))
                        self.npc = None
                        self.info_text = f"进入第 {self.level} 关"
                        self.info_timer = 180
                        self.npc_appearances = 0
                        self.enemies = [Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4,
                                              random.choice(["human", "traitor_duck", "soul", "ingredient"]),
                                              is_boss=False)]
                        if self.level == self.max_levels:
                            self.enemies = [Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, "human", is_boss=True)]
                            self.state = "buff_selection"
                            self.buff_selection = BuffSelectionState(self.duck, self.font)
                    self.last_space_press = current_time

        if self.state == "explore":
            self.handle_exploration(screen, keys)

        elif self.state == "buff_selection":
            if not self.buff_selection.update(screen, keys):
                self.state = "battle_prep"
                self.buff_selection = None
                self.battle_prep = BattlePrepState(self.duck, self.font)

        elif self.state == "battle_prep":
            if not self.battle_prep.update(screen, keys) or keys[pygame.K_SPACE]:
                self.state = "battle"
                self.in_battle = True
                self.battle_prep = None

        elif self.state == "battle":
            battle_ended, victory = handle_battle(self.duck, self.enemies, keys, screen, self.font)
            if battle_ended:
                self.state = "story" if not self.story_event.active else "explore"
                self.in_battle = False
                if victory:
                    self.duck.recover_after_battle()
                else:
                    print("Game Over!")
                    pygame.quit()
                    sys.exit()

        elif self.state == "story":
            if not self.story_event.triggered:
                self.story_event.trigger(self.duck, screen, self.font, None)
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.story_event.handle_choice(1, self.duck)
                        self.state = "explore"
                    elif event.key == pygame.K_2:
                        self.story_event.handle_choice(2, self.duck)
                        self.state = "explore"
                    elif event.key == pygame.K_SPACE:
                        self.story_event.reset()
                        self.state = "explore"

    def handle_exploration(self, screen, keys):
        screen.fill(WHITE)
        self.duck.draw(screen)

        for weapon in self.weapons:
            weapon.draw(screen)
            if not weapon.collected and self.duck.rect().colliderect(
                    pygame.Rect(weapon.x, weapon.y, weapon.width, weapon.height)):
                weapon.collected = True
                if self.duck.collect(weapon):
                    self.info_text = "拾取了武器！武器威力提升！"
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
                    self.info_text = "队伍已满，无法添加更多伙伴！"
                    self.info_timer = 120

        if not self.npc and self.npc_appearances < self.max_npc_appearances:
            if random.random() < 0.5:
                npc_type = random.choice(self.npc_types)
                self.npc = NPC(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30), npc_type)
                self.npc_appearances += 1

        if self.npc:
            self.npc.draw(screen)
            if self.duck.rect().colliderect(pygame.Rect(self.npc.x, self.npc.y, self.npc.width, self.npc.height)) and \
                    keys[pygame.K_e]:
                if self.duck.interact(self.npc, screen, self.font, self, keys):
                    self.npc = None  # 交互完成后移除 NPC

        for enemy in self.enemies:
            enemy.draw(screen)

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
            screen.blit(text, (50, SCREEN_HEIGHT - 100))

        # 绘制工具栏
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
        for partner in self.duck.partners:
            if partner.image:
                screen.blit(pygame.transform.scale(partner.image, (20, 20)), (x_offset, SCREEN_HEIGHT - 170))
            else:
                pygame.draw.rect(screen, partner.color, (x_offset, SCREEN_HEIGHT - 170, 20, 20))
            x_offset += 30

        weapon_text = f"武器: {len(self.duck.weapons)}"
        partner_text = f"伙伴: {len(self.duck.partners)}"
        charm_text = f"魅力: {self.duck.charm}"
        rep_text = f"舆论: {self.duck.reputation}"

        texts = [
            self.font.render(weapon_text, True, BLACK),
            self.font.render(partner_text, True, BLACK),
            self.font.render(charm_text, True, BLACK),
            self.font.render(rep_text, True, BLACK)
        ]
        for i, text in enumerate(texts):
            screen.blit(text, (10, SCREEN_HEIGHT - 140 + i * 30))

        prompt_text = self.font.render("按空格进入下一关", True, BLACK)
        screen.blit(prompt_text, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 50))

        level_text = self.font.render(f"Level: {self.level}", True, BLACK)
        screen.blit(level_text, (10, 10))