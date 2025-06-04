import pygame
import random
import sys
from weapon import create_weapons
from partner import create_partners
from battle import handle_battle
from story import StoryEvent
from constants import WHITE, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, MAX_PARTNERS
from npc import NPC
from enemy import Enemy

class BattlePrepState:
    def __init__(self, duck, font):
        self.duck = duck
        self.font = font
        self.selected_partner = 0
        self.selected_weapon = 0
        self.state = "position"
        self.last_key_press = 0  # 防抖时间

    def update(self, screen, keys):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_key_press < 200:
            return True

        screen.fill(WHITE)
        title = self.font.render("选择一个 BUFF", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 100, 50))

        for i, buff in enumerate(self.buffs):
            color = (255, 0, 0) if i == self.selected_buff else BLACK
            text = self.font.render(f"{i + 1}. {buff}", TrueDados, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - 50, 150 + i * 50))

        prompt = "按 1-3 选择 BUFF，按空格确认"
        prompt_text = self.font.render(prompt, True, BLACK)
        screen.blit(prompt_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 50))

        if keys[pygame.K_1]:
            self.selected_buff = 0
            self.last_key_press = current_time
        elif keys[pygame.K_2]:
            self.selected_buff = 1
            self.last_key_press = current_time
        elif keys[pygame.K_3]:
            self.selected_buff = 2
            self.last_key_press = current_time
        elif keys[pygame.K_SPACE]:
            selected_buff = self.buffs[self.selected_buff]
            print(f"玩家选择了 {selected_buff}")
            self.last_key_press = current_time
            return False  # 结束 BUFF 选择

        return True  # 继续选择

class BuffSelectionState:
    def __init__(self, duck, font):
        self.duck = duck
        self.font = font
        self.selected_buff = 0
        self.buffs = ["buff1", "buff2", "buff3"]
        self.last_key_press = 0  # 防抖时间

    def update(self, screen, keys):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_key_press < 200:  # 200ms 防抖
            return True

        screen.fill(WHITE)
        # 显示标题
        title = self.font.render("选择一个 BUFF", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - 100, 50))

        # 显示 BUFF 选项
        for i, buff in enumerate(self.buffs):
            color = (255, 0, 0) if i == self.selected_buff else BLACK
            text = self.font.render(f"{i+1}. {buff}", True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - 50, 150 + i * 50))

        # 显示提示
        prompt = "按 1-3 选择 BUFF，按空格确认"
        prompt_text = self.font.render(prompt, True, BLACK)
        screen.blit(prompt_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 50))

        # 处理输入
        if keys[pygame.K_1]:
            self.selected_buff = 0
            self.last_key_press = current_time
        elif keys[pygame.K_2]:
            self.selected_buff = 1
            self.last_key_press = current_time
        elif keys[pygame.K_3]:
            self.selected_buff = 2
            self.last_key_press = current_time
        elif keys[pygame.K_SPACE]:
            selected_buff = self.buffs[self.selected_buff]
            print(f"选择了 {selected_buff}")
            self.last_key_press = current_time
            return False  # 结束 BUFF 选择

        return True  # 继续选择

class GameState:
    def __init__(self, duck, enemies):
        self.duck = duck
        self.enemies = enemies
        self.state = "explore"
        self.story_event = StoryEvent()
        self.battle_prep = None
        self.buff_selection = None
        self.in_battle = False
        self.weapons = create_weapons(random.randint(1, 3))  # 每关随机 1-3 把武器
        self.partners = create_partners(random.randint(1, 2))  # 每关随机 1-2 个伙伴
        self.npc = NPC(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30))
        self.font = pygame.font.SysFont("SimHei", 32)
        self.level = 1
        self.max_levels = 5  # 总共 5 关
        self.current_level_type = random.choice(['A', 'B', 'C', 'D'])
        self.info_text = ""
        self.info_timer = 0
        self.last_space_press = 0  # 记录上次空格按下的时间

    def update(self, screen, keys, events):
        # 处理空格键切换关卡
        current_time = pygame.time.get_ticks()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.state == "explore":
                if current_time - self.last_space_press > 500:  # 500ms 防抖
                    if self.level < self.max_levels:
                        self.level += 1
                        self.current_level_type = random.choice(['A', 'B', 'C', 'D'])
                        self.weapons = create_weapons(random.randint(1, 3))
                        self.partners = create_partners(random.randint(1, 2))
                        self.npc = NPC(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30))
                        self.info_text = f"进入第 {self.level} 关"
                        self.info_timer = 180  # 3秒显示
                        if self.level == self.max_levels:
                            self.state = "buff_selection"
                            self.buff_selection = BuffSelectionState(self.duck, self.font)
                            self.enemies = [Enemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, is_boss=True)]
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

        elif self.state == "story":
            self.story_event.trigger(self.duck, screen, self.font)
            self.state = "explore"

    def handle_exploration(self, screen, keys):
        screen.fill(WHITE)
        self.duck.draw(screen)

        for weapon in self.weapons:
            weapon.draw(screen)
            if not weapon.collected and self.duck.rect().colliderect(pygame.Rect(weapon.x, weapon.y, weapon.width, weapon.height)):
                weapon.collected = True
                if self.duck.collect(weapon):
                    self.info_text = "拾取了武器！武器威力提升！"
                    self.info_timer = 120

        for partner in self.partners:
            partner.draw(screen)
            if not partner.collected and self.duck.rect().colliderect(pygame.Rect(partner.x, partner.y, partner.width, partner.height)):
                partner.collected = True
                if self.duck.collect(partner):
                    self.info_text = "伙伴加入了你的队伍！"
                    self.info_timer = 120
                else:
                    self.info_text = "队伍已满，无法添加更多伙伴！"
                    self.info_timer = 120

        self.npc.draw(screen)
        if self.duck.rect().colliderect(pygame.Rect(self.npc.x, self.npc.y, self.npc.width, self.npc.height)) and keys[pygame.K_e]:
            self.duck.interact(self.npc, screen, self.font)

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

        # 添加提示：按空格进入下一关
        prompt_text = self.font.render("按空格进入下一关", True, BLACK)
        screen.blit(prompt_text, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 50))

        level_text = self.font.render(f"Level: {self.level}", True, BLACK)
        screen.blit(level_text, (10, 10))