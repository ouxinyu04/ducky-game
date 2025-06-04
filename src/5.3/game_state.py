import pygame
import random
import sys
import logging
from weapon import create_weapons
from partner import create_partners
from battle import handle_battle
from duck import Duck
from enemy import Enemy
from npc import NPC
from constants import WHITE, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, MAX_PARTNERS
from config import IMAGES_DIR

# 设置日志
logging.basicConfig(filename="game_errors.log", level=logging.ERROR, encoding='utf-8')


class GameState:
    def __init__(self):
        self.duck = Duck(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.enemies = []
        self.state = "path_selection"
        self.weapons = create_weapons(random.randint(1, 2))
        self.partners = create_partners(random.randint(1, 2))
        self.npc = None
        self.npc_appearances = 0
        self.max_npc_appearances = 2
        self.npc_types = ["lady_duck", "broccoli_general", "human_child"]
        self.font = pygame.font.SysFont("SimHei", 32)
        self.level = 1
        self.max_levels = 5
        self.current_level_type = random.choice(['A', 'B', 'C'])
        self.info_text = ""
        self.info_timer = 0
        self.last_space_press = 0
        # 路径与祝福
        self.paths = ["勇敢", "智慧", "团结"]
        self.selected_path = None
        self.blessings = []
        self.rooms = []
        self.current_room = 0
        self.feathers = 0
        self.charm = 0
        self.reputation = 0

    def initialize_rooms(self):
        self.rooms = []
        for _ in range(3):
            self.rooms.append(random.choice(["combat", "event", "rest"]))
        if self.level == self.max_levels:
            self.rooms.append("boss")
        else:
            self.rooms.append(random.choice(["combat", "event", "rest"]))
        self.current_room = 0

    def select_path(self, screen, keys):
        screen.fill(WHITE)
        title = self.font.render("选择你的路径", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 100, 50))
        for i, path in enumerate(self.paths):
            color = (255, 0, 0) if i == self.paths.index(self.selected_path or self.paths[0]) else BLACK
            text = self.font.render(f"{i + 1}. {path}", True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - 50, 100 + i * 40))
        prompt = self.font.render("按 1-3 选择路径，按空格确认", True, BLACK)
        screen.blit(prompt, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 50))

        if keys[pygame.K_1]:
            self.selected_path = "勇敢"
        elif keys[pygame.K_2]:
            self.selected_path = "智慧"
        elif keys[pygame.K_3]:
            self.selected_path = "团结"
        elif keys[pygame.K_SPACE] and self.selected_path is not None:
            self.state = "explore"
            self.initialize_rooms()

    def choose_blessing(self, screen, keys):
        blessings_options = {
            "勇敢": [("攻击力 +5", lambda: setattr(self.duck, "attack_power", self.duck.attack_power + 5)),
                     ("20% 几率双倍伤害", lambda: None)],
            "智慧": [("骰子点数 +1", lambda: None),
                     ("成功条件 -1", lambda: None)],
            "团结": [("伙伴 HP +10",
                      lambda: [setattr(p, "max_hp", p.max_hp + 10) or setattr(p, "hp", p.hp + 10) for p in
                               self.duck.partners]),
                     ("伙伴攻击力 +3",
                      lambda: [setattr(p, "attack_power", p.attack_power + 3) for p in self.duck.partners])]
        }
        available_blessings = blessings_options[self.selected_path] + random.sample(
            sum([blessings_options[path] for path in self.paths if path != self.selected_path], []), 1)
        random.shuffle(available_blessings)

        screen.fill(WHITE)
        title = self.font.render("选择一个祝福", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 100, 50))
        for i, (blessing_name, _) in enumerate(available_blessings[:3]):
            # 修复：为每个选项动态设置 color
            color = (255, 0, 0) if i == 0 else BLACK  # 默认高亮第一个选项
            text = self.font.render(f"{i + 1}. {blessing_name}", True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - 50, 100 + i * 40))
        prompt = self.font.render("按 1-3 选择祝福", True, BLACK)
        screen.blit(prompt, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 50))

        selected_blessing = available_blessings[0]  # 自动选择第一个祝福
        blessing_name, blessing_effect = selected_blessing
        blessing_effect()
        self.blessings.append(blessing_name)
        self.state = "explore"
        self.info_text = f"获得了祝福：{blessing_name}"
        self.info_timer = 120

    def handle_room(self, screen, keys):
        if self.current_room >= len(self.rooms):
            self.level += 1
            if self.level > self.max_levels:
                print("游戏通关！")
                pygame.quit()
                sys.exit()
            self.initialize_rooms()
            self.info_text = f"进入第 {self.level} 关"
            self.info_timer = 180
            return

        room_type = self.rooms[self.current_room]
        room_text = self.font.render(f"房间 {self.current_room + 1}: {room_type.capitalize()}", True, BLACK)
        screen.blit(room_text, (10, 50))

        if room_type == "combat" or room_type == "boss":
            enemy = Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, "human", is_boss=(room_type == "boss"))
            battle_ended, victory = handle_battle(self.duck, enemy, screen, self.font)
            if battle_ended:
                if victory:
                    self.feathers += 5
                    self.info_text = f"战斗胜利！获得 5 羽毛，总计 {self.feathers} 羽毛"
                else:
                    self.info_text = "战斗失败！队伍损失 HP"
                self.info_timer = 120
                if not victory or (room_type == "boss" and self.duck.get_total_power() < 50):
                    print("游戏结束！")
                    pygame.quit()
                    sys.exit()
                # 战斗结束后立即检测空格
                if keys[pygame.K_SPACE]:
                    self.current_room += 1
                    self.state = "blessing"

        elif room_type == "event":
            if not self.npc and self.npc_appearances < self.max_npc_appearances:
                npc_type = random.choice(self.npc_types)
                self.npc = NPC(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30), npc_type)
                self.npc_appearances += 1

            if self.npc:
                self.npc.draw(screen)
                if self.duck.rect().colliderect(
                        pygame.Rect(self.npc.x, self.npc.y, self.npc.width, self.npc.height)) and keys[pygame.K_e]:
                    try:
                        try:
                            if self.duck.interact(screen, self.font, keys, "npc"):
                                self.npc = None
                                if self.duck.interaction_result:  # 检查是否为空字符串
                                    if "成功" in self.duck.interaction_result:
                                        self.charm += 5
                                        self.reputation += 3
                                        self.info_text = f"事件成功！魅力 +5，舆论 +3，总计 魅力 {self.charm}, 舆论 {self.reputation}"
                                    else:
                                        self.info_text = "事件失败！"
                                else:
                                    self.info_text = "交互结果无效！"
                                self.info_timer = 120
                                self.current_room += 1
                                self.state = "blessing"
                        except Exception as e:
                            logging.error(f"NPC 交互错误: {e}")
                            self.npc = None
                            self.info_text = "NPC 交互失败！"
                            self.info_timer = 120
                    except Exception as e:
                        logging.error(f"NPC 交互错误: {e}")
                        self.npc = None
                        self.info_text = "NPC 交互失败！"
                        self.info_timer = 120
                return
            event_type = random.choice(["trap", "special_enemy"])
            if self.duck.interact(screen, self.font, keys, event_type):
                if "成功" in self.duck.interaction_result:
                    self.charm += 3
                    self.reputation += 3
                    self.info_text = f"事件成功！魅力 +3，舆论 +3，总计 魅力 {self.charm}, 舆论 {self.reputation}"
                else:
                    self.duck.hp = max(0, self.duck.hp - int(self.duck.max_hp * 0.1))
                    self.info_text = "事件失败！鸭子损失 10% HP"
                    if self.duck.hp == 0:
                        print("游戏结束！")
                        pygame.quit()
                        sys.exit()
                self.info_timer = 120
                self.current_room += 1
                self.state = "blessing"

        elif room_type == "rest":
            self.duck.hp = min(self.duck.max_hp, self.duck.hp + 20)
            for partner in self.duck.partners:
                partner.hp = min(partner.max_hp, partner.hp + 20)
            if random.random() < 0.5:
                self.feathers += 5
                self.info_text = f"休息恢复 20 HP！获得 5 羽毛，总计 {self.feathers} 羽毛"
            else:
                self.info_text = "休息恢复 20 HP！"
            self.info_timer = 120
            self.current_room += 1
            self.state = "blessing"

    def update(self, screen, keys, events):
        current_time = pygame.time.get_ticks()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.state == "explore":
                if current_time - self.last_space_press > 500:
                    self.last_space_press = current_time

        if self.state == "path_selection":
            self.select_path(screen, keys)

        elif self.state == "explore":
            screen.fill(WHITE)
            self.duck.move(keys)  # 添加移动逻辑
            self.duck.draw(screen)
            for weapon in self.weapons:
                weapon.draw(screen)
                if not weapon.collected and self.duck.rect().colliderect(
                        pygame.Rect(weapon.x, weapon.y, weapon.width, weapon.height)):
                    weapon.collected = True
                    if self.duck.collect(weapon):
                        self.info_text = "拾取了武器！"
                        self.info_timer = 120
            for partner in self.partners:
                partner.draw(screen)
                if not partner.collected and self.duck.rect().colliderect(
                        pygame.Rect(partner.x, partner.y, partner.width, partner.height)):
                    partner.collected = True
                    if self.duck.collect(partner):
                        self.info_text = "伙伴加入了队伍！"
                        self.info_timer = 120
            self.handle_room(screen, keys)

        elif self.state == "blessing":
            self.choose_blessing(screen, keys)

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

        toolbar = pygame.Surface((SCREEN_WIDTH, 180))
        toolbar.set_alpha(200)
        toolbar.fill((200, 200, 200))
        screen.blit(toolbar, (0, SCREEN_HEIGHT - 180))

        x_offset = 10
        for weapon in self.duck.weapons:
            if weapon.image:
                screen.blit(pygame.transform.scale(weapon.image, (20, 20)), (x_offset, SCREEN_HEIGHT - 170))
            x_offset += 30
        x_offset += 10
        for partner in self.duck.partners:
            if partner.image:
                screen.blit(pygame.transform.scale(partner.image, (20, 20)), (x_offset, SCREEN_HEIGHT - 170))
            x_offset += 30

        texts = [
            self.font.render(f"羽毛: {self.feathers}", True, BLACK),
            self.font.render(f"魅力: {self.charm}", True, BLACK),
            self.font.render(f"舆论: {self.reputation}", True, BLACK),
            self.font.render(f"HP: {self.duck.hp}/{self.duck.max_hp}", True, BLACK),
        ]
        for i, text in enumerate(texts):
            screen.blit(text, (10, SCREEN_HEIGHT - 140 + i * 30))

        level_text = self.font.render(f"关卡: {self.level}", True, BLACK)
        screen.blit(level_text, (10, 10))