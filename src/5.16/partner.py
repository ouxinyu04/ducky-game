# partner.py - 完整修改版
import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, GREEN
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)


class Partner:
    def __init__(self, x, y, index, is_special=False, npc_type=None):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.color = GREEN
        self.collected = False
        self.is_special = is_special
        self.npc_type = npc_type
        self.image = None

        # 修改图片加载逻辑
        if self.npc_type:
            image_name = f"{self.npc_type}.png"
            image_path = os.path.join(ASSETS_DIR, image_name)
            logging.info(f"Attempting to load partner image: {image_path}")

            if os.path.exists(image_path):
                try:
                    self.image = pygame.image.load(image_path)
                    self.image = pygame.transform.scale(self.image, (self.width, self.height))
                    logging.info(f"Successfully loaded partner image: {image_name}")
                except Exception as e:
                    logging.error(f"Failed to load partner image {image_name}: {e}")
                    self.image = None
            else:
                logging.warning(f"Partner image file not found: {image_path}")
                
                # 尝试通用伙伴图像
                generic_path = os.path.join(ASSETS_DIR, "partner.png")
                if os.path.exists(generic_path):
                    try:
                        self.image = pygame.image.load(generic_path)
                        self.image = pygame.transform.scale(self.image, (self.width, self.height))
                        logging.info(f"Loaded generic partner image")
                    except Exception as e:
                        logging.error(f"Failed to load generic partner image: {e}")
                        self.image = None
        else:
            # 对于普通伙伴，尝试加载通用伙伴图像
            generic_path = os.path.join(ASSETS_DIR, "partner.png")
            if os.path.exists(generic_path):
                try:
                    self.image = pygame.image.load(generic_path)
                    self.image = pygame.transform.scale(self.image, (self.width, self.height))
                    logging.info(f"Loaded generic partner image for regular partner")
                except Exception as e:
                    logging.error(f"Failed to load generic partner image: {e}")
                    self.image = None

        # 根据类型设置战力
        if is_special and npc_type:
            self.attack_power = 8  # 特殊NPC固定战力为8
        else:
            self.attack_power = random.randint(3, 5)  # 普通伙伴战力为3-5

        self.hp = 100
        self.max_hp = 100
        self.mp = 15  # 新增MP属性
        self.max_mp = 15
        self.is_alive = True
        self.index = index
        self.weapon_power_bonus = 0  # 武器加成

        # 特殊技能效果标记
        self.taunt_active = False  # 嘲讽效果是否激活
        self.taunt_duration = 0  # 嘲讽回合数

    # 新增获取总战力的方法
    def get_total_power(self, duck_buffs=None):
        base_power = self.attack_power
        weapon_power = self.weapon_power_bonus
        buff_power = 15 if duck_buffs and "勇敢 BUFF" in duck_buffs else 0
        return base_power + weapon_power + buff_power

    # 普通攻击(不耗MP并恢复MP)
    def normal_attack(self, target, team_mp, team_max_mp):
        damage = self.get_total_power()
        new_team_mp = min(team_max_mp, team_mp + 3)  # 恢复3点MP，但不超过上限
        target.hp = max(0, target.hp - damage)
        return damage, new_team_mp

    # 技能攻击
    def use_skill(self, target=None, team_mp=0, target_partners=None):
        mp_cost = 5 if self.npc_type else 6  # 特殊NPC技能消耗5MP，普通角色消耗6MP

        # MP不足
        if team_mp < mp_cost:
            return None, 0, team_mp

        # 根据角色类型执行不同技能
        if self.npc_type == "lady_duck" and target:
            # 治疗技能
            heal_amount = 15
            target.hp = min(target.max_hp, target.hp + heal_amount)
            return "heal", heal_amount, team_mp - mp_cost
        elif self.npc_type == "broccoli_general" and target:
            # 斩击技能
            damage = self.get_total_power() * 2
            target.hp = max(0, target.hp - damage)
            return "damage", damage, team_mp - mp_cost
        elif self.npc_type == "human_child":
            # 嘲讽技能
            self.taunt_active = True
            self.taunt_duration = 2  # 嘲讽持续2回合
            return "taunt", 0, team_mp - mp_cost
        else:
            # 默认治疗技能
            if target:
                heal_amount = 15
                target.hp = min(target.max_hp, target.hp + heal_amount)
                return "heal", heal_amount, team_mp - mp_cost

        return None, 0, team_mp

    def draw(self, screen):
        if not self.collected and self.is_alive:
            if self.image:
                screen.blit(self.image, (self.x, self.y))
            else:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))


def create_partners(num):
    return [Partner(random.randint(0, SCREEN_WIDTH - 30), random.randint(0, SCREEN_HEIGHT - 30), i + 1) for i in
            range(num)]