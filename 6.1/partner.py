# partner.py - 完整修改版
import pygame
import random
import os
import logging
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, GREEN
from config import ASSETS_DIR
from animation_utils import load_animation_frames
from constants import (NORMAL_BASE_HP, NORMAL_BASE_MP, NPC_BASE_HP, NPC_BASE_MP,
                      NORMAL_ATTACK_DAMAGE, NPC_ATTACK_DAMAGE, NORMAL_MP_RECOVERY,
                      NPC_MP_RECOVERY, NORMAL_HEAL_TARGET_HEALING, NORMAL_HEAL_TARGET_MP_COST,
                      NORMAL_SHIELD_ABSORPTION, NORMAL_SHIELD_MP_COST, NORMAL_SHIELD_DURATION,
                      NORMAL_SHIELD_TAUNT_DURATION, NORMAL_SLASH_DAMAGE, NORMAL_SLASH_MP_COST,
                      NPC_HEAL_ALL_HEALING, NPC_HEAL_ALL_MP_COST, NPC_BLESS_MP_COST,
                      NPC_REFLECT_MP_COST, NPC_REFLECT_TAUNT_DURATION, NORMAL_SHIELD_TAUNT_CHANCE,
                      NORMAL_SHIELD_DAMAGE_REDUCTION, NPC_REFLECT_TAUNT_CHANCE,
                      NPC_REFLECT_HP_RESTORE_PERCENT, NPC_BLESS_DAMAGE_MULTIPLIER)

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)


class Partner:
    def __init__(self, x, y, index, is_special=False, npc_type=None):
        self.x = x
        self.y = y
        self.width = 60  # 普通伙伴放大一倍：30 * 2 = 60
        self.height = 60  # 普通伙伴放大一倍：30 * 2 = 60
        self.color = GREEN
        self.collected = False
        self.is_special = is_special
        self.npc_type = npc_type
        self.image = None

        # 初始化动画属性（所有伙伴都支持动画）
        self.gif_frames = []
        self.current_frame = 0
        self.frame_time = 200  # 每帧200毫秒
        self.last_frame_update = 0

        # 如果是动画NPC类型的伙伴，放大三倍
        if npc_type in ["lady_duck", "broccoli_general", "human_child"]:
            self.width = 90
            self.height = 90

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

                # 尝试通用伙伴动画
                self.gif_frames, _ = load_animation_frames("duck_friend_animation.gif", "duck_friend.png", (self.width, self.height))
                if not self.gif_frames:
                    # 如果动画加载失败，尝试加载partner.png
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
            # 对于普通伙伴，尝试加载通用伙伴动画
            self.gif_frames, _ = load_animation_frames("duck_friend_animation.gif", "duck_friend.png", (self.width, self.height))
            if not self.gif_frames:
                # 如果动画加载失败，尝试加载partner.png
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

        # 根据角色类型设置HP/MP
        if is_special and npc_type:
            # NPC角色
            self.hp = NPC_BASE_HP
            self.max_hp = NPC_BASE_HP
            self.mp = NPC_BASE_MP
            self.max_mp = NPC_BASE_MP
            self.attack_power = NPC_ATTACK_DAMAGE
        else:
            # 普通角色
            self.hp = NORMAL_BASE_HP
            self.max_hp = NORMAL_BASE_HP
            self.mp = NORMAL_BASE_MP
            self.max_mp = NORMAL_BASE_MP
            self.attack_power = NORMAL_ATTACK_DAMAGE

        self.is_alive = True
        self.index = index
        self.weapon_power_bonus = 0  # 武器加成

        # 特殊技能效果标记
        self.taunt_active = False  # 嘲讽效果是否激活
        self.taunt_duration = 0  # 嘲讽回合数

        self.shield_active = False
        self.shield_duration = 0
        self.shield_absorption = 0
        self.shield_hp = 0  # 护盾HP
        self.max_shield_hp = 30  # 最大护盾HP
        self.blessed = False  # 祝福状态
        self.damage_reduction_next_turn = 0  # 下回合伤害减免
        self.damage_increase_next_turn = 0   # 下回合伤害增加
        self.disabled_next_turn = False      # 下回合被禁用
        self.swamp_effect = False            # 沼泽效果
        self.swamp_duration = 0
        self.reflect_active = False          # 反射状态

        # 技能分配
        self.assigned_skill = None
        self.assign_character_skill()

        # 鸡的待机动画相关属性
        self.chicken_animation_frames = []
        self.chicken_current_frame = 0
        self.chicken_frame_time = 200  # 每帧200毫秒
        self.chicken_last_frame_update = 0
        self.is_chicken = False  # 标记是否为鸡角色

        # 检查是否为鸡角色并加载动画
        self.load_chicken_animation()

    def load_chicken_animation(self):
        """加载鸡的待机动画帧"""
        try:
            # 检查是否为鸡角色（可以根据npc_type或其他标识判断）
            if (hasattr(self, 'npc_type') and self.npc_type and 'chicken' in self.npc_type.lower()) or \
               (hasattr(self, 'index') and self.index and str(self.index) == '鸡'):
                self.is_chicken = True

            # 如果是鸡角色，尝试加载chicken_animation.gif
            if self.is_chicken:
                from animation_utils import load_animation_frames

                # 使用透明背景的鸡动画 GIF 文件
                self.chicken_animation_frames, is_animated = load_animation_frames(
                    "chicken_animation.gif",
                    "chicken-idle.png",  # 备用静态图像
                    target_size=(216, 216)  # 目标尺寸 216x216 (1.5倍扩大)
                )

                if self.chicken_animation_frames:
                    logging.info(f"Loaded chicken GIF animation with {len(self.chicken_animation_frames)} frames")
                    # 更新伙伴尺寸以匹配动画帧
                    self.width = 216
                    self.height = 216
                else:
                    logging.warning("Failed to load chicken animation GIF")
        except Exception as e:
            logging.error(f"Error loading chicken animation: {e}")

    def assign_character_skill(self):
        """根据角色类型分配技能"""
        if self.npc_type == "lady_duck_animation":
            self.assigned_skill = "bless"  # 鸭子小姐 - Bless
        elif self.npc_type == "bat_animation":
            self.assigned_skill = "substitute"  # 蝙蝠王子 - Substitute
        elif self.npc_type == "good_boy_animation":
            self.assigned_skill = "reflect"  # 正义人类 - Reflect
        elif self.npc_type == "mushroom_animation":
            self.assigned_skill = "heal_all"  # 蘑菇勇者 - Heal All
        elif self.npc_type == "duck_friend_animation":
            # 小屁鸭 - 随机技能
            import random
            skills = ["heal_target", "shield", "slash"]
            self.assigned_skill = random.choice(skills)
        else:
            # 普通角色随机分配一个技能
            import random
            skills = ["heal_target", "shield", "slash"]
            self.assigned_skill = random.choice(skills)

    def get_skill_info(self):
        """获取角色的技能信息"""
        skill_info = {
            "heal_target": {"name": "治疗", "mp_cost": 5, "icon": "heal_icon.gif"},
            "shield": {"name": "护盾", "mp_cost": 8, "icon": "shield_icon.gif"},
            "slash": {"name": "斩击", "mp_cost": 8, "icon": "slash_icon.gif"},
            "heal_all": {"name": "群疗", "mp_cost": 6, "icon": "heal_all_icon.gif"},
            "bless": {"name": "祝福", "mp_cost": 10, "icon": "bless_icon.gif"},
            "substitute": {"name": "替代", "mp_cost": 0, "icon": "substitute_icon.gif"},
            "reflect": {"name": "反射", "mp_cost": 12, "icon": "reflect_icon.gif"}
        }
        return skill_info.get(self.assigned_skill, {"name": "未知", "mp_cost": 0, "icon": None})

    # 新增获取总战力的方法
    def get_total_power(self, duck_buffs=None):
        base_power = self.attack_power
        weapon_power = self.weapon_power_bonus
        buff_power = 15 if duck_buffs and "勇敢 BUFF" in duck_buffs else 0
        return base_power + weapon_power + buff_power

    def take_damage(self, damage):
        """
        受到伤害的处理函数，优先扣除护盾值

        参数:
            damage: 受到的伤害值

        返回:
            实际造成的伤害值
        """
        original_damage = damage

        # 如果有护盾，优先扣除护盾值
        if hasattr(self, 'shield_active') and self.shield_active and hasattr(self, 'shield_hp') and self.shield_hp > 0:
            if damage <= self.shield_hp:
                # 伤害完全被护盾吸收
                self.shield_hp -= damage
                damage = 0
                logging.info(f"Partner {self.index}: Shield absorbed {original_damage} damage, shield HP: {self.shield_hp}")
            else:
                # 护盾被打破，剩余伤害作用于HP
                remaining_damage = damage - self.shield_hp
                logging.info(f"Partner {self.index}: Shield absorbed {self.shield_hp} damage, remaining: {remaining_damage}")
                self.shield_hp = 0
                damage = remaining_damage

            # 如果护盾值为0，移除护盾状态
            if self.shield_hp <= 0:
                self.shield_active = False
                self.shield_duration = 0
                self.shield_absorption = 0
                logging.info(f"Partner {self.index}: Shield broken, shield effect removed")

        # 扣除剩余伤害从HP
        if damage > 0:
            self.hp = max(0, self.hp - damage)
            logging.info(f"Partner {self.index}: Took {damage} HP damage, current HP: {self.hp}")

        return original_damage

    # 普通攻击(不耗MP并恢复MP)
    def normal_attack(self, target, team_mp, team_max_mp):
        damage = int(self.get_total_power())  # 确保伤害为整数

        # 检查是否有祝福效果
        if hasattr(self, 'blessed') and self.blessed:
            damage = int(damage * NPC_BLESS_DAMAGE_MULTIPLIER)
            self.blessed = False  # 消耗祝福效果

        new_team_mp = min(team_max_mp, team_mp + 3)  # 恢复3点MP，但不超过上限
        target.hp = max(0, target.hp - int(damage))  # 确保HP为整数
        return int(damage), new_team_mp

    # 技能攻击
    def use_skill(self, target=None, all_allies=None, boss=None, substitute_target=None):
        """
        使用角色分配的技能
        target: 目标角色 (单体技能)
        all_allies: 所有队友列表 (群体技能)
        boss: BOSS对象 (攻击技能)
        substitute_target: 替代技能的目标角色
        """
        import random

        skill = self.assigned_skill
        if not skill:
            return "无技能", 0, "heal"

        # 根据分配的技能执行相应逻辑
        if skill == "heal_target":
            if self.mp < NORMAL_HEAL_TARGET_MP_COST:
                return "MP不足", 0, "heal"
            if target and target.is_alive:
                old_hp = target.hp
                target.hp = min(target.max_hp, target.hp + NORMAL_HEAL_TARGET_HEALING)
                healing = int(target.hp - old_hp)  # 确保治疗量为整数
                self.mp -= NORMAL_HEAL_TARGET_MP_COST
                return f"治疗了{target.index}！恢复了{healing}点HP", healing, "heal"

        elif skill == "shield":
            if self.mp < NORMAL_SHIELD_MP_COST:
                return "MP不足", 0, "shield"

            # 60%概率激活嘲讽
            if random.random() < (NORMAL_SHIELD_TAUNT_CHANCE / 100):
                self.taunt_active = True
                self.taunt_duration = NORMAL_SHIELD_TAUNT_DURATION
                self.damage_reduction_next_turn = NORMAL_SHIELD_DAMAGE_REDUCTION
                taunt_msg = "嘲讽成功！"
            else:
                taunt_msg = "嘲讽失败！"

            # 给所有队友护盾
            if all_allies:
                for ally in all_allies:
                    if ally.is_alive:
                        ally.shield_active = True
                        ally.shield_duration = NORMAL_SHIELD_DURATION
                        ally.shield_absorption = NORMAL_SHIELD_ABSORPTION
                        ally.shield_hp = ally.max_shield_hp  # 设置护盾HP

            self.mp -= NORMAL_SHIELD_MP_COST
            return f"{self.index}激活了护盾！{taunt_msg}给全队护盾", 0, "shield"

        elif skill == "slash":
            if self.mp < NORMAL_SLASH_MP_COST:
                return "MP不足", 0, "claw"
            if boss:
                # 检查是否有祝福效果
                damage = int(NORMAL_SLASH_DAMAGE)  # 确保基础伤害为整数
                if hasattr(self, 'blessed') and self.blessed:
                    damage = int(damage * NPC_BLESS_DAMAGE_MULTIPLIER)
                    self.blessed = False  # 消耗祝福效果

                boss.hp = max(0, boss.hp - damage)
                self.mp -= NORMAL_SLASH_MP_COST
                return f"斩击！对BOSS造成{damage}点伤害", damage, "claw"

        elif skill == "heal_all":
            if self.mp < NPC_HEAL_ALL_MP_COST:
                return "MP不足", 0, "heal"
            if all_allies:
                total_healing = 0
                for ally in all_allies:
                    if ally.is_alive:
                        old_hp = ally.hp
                        ally.hp = min(ally.max_hp, ally.hp + NPC_HEAL_ALL_HEALING)
                        total_healing += int(ally.hp - old_hp)  # 确保治疗量为整数
                self.mp -= NPC_HEAL_ALL_MP_COST
                return f"群体治疗！恢复了{total_healing}点HP", total_healing, "heal"

        elif skill == "bless":
            if self.mp < NPC_BLESS_MP_COST:
                return "MP不足", 0, "bless"
            if target and target.is_alive:
                target.blessed = True
                self.mp -= NPC_BLESS_MP_COST
                return f"祝福了{target.index}！下次攻击伤害×1.8", 0, "bless"

        elif skill == "substitute":
            if substitute_target and substitute_target.is_alive:
                # 返回特殊标记，由战斗系统处理
                return "SUBSTITUTE_SKILL", substitute_target, "substitute"
            return "需要选择替代目标", 0, "substitute"

        elif skill == "reflect":
            if self.mp < NPC_REFLECT_MP_COST:
                return "MP不足", 0, "reflect"

            # 60%概率激活嘲讽
            if random.random() < (NPC_REFLECT_TAUNT_CHANCE / 100):
                self.taunt_active = True
                self.taunt_duration = NPC_REFLECT_TAUNT_DURATION
                self.reflect_active = True
                self.mp -= NPC_REFLECT_MP_COST
                return f"{self.index}激活了反射！吸引BOSS攻击并反弹伤害", 0, "reflect"
            else:
                # 嘲讽失败，恢复80%HP给受伤最重的队友
                if all_allies:
                    damaged_allies = [p for p in all_allies if p.is_alive and p.hp < p.max_hp]
                    if damaged_allies:
                        most_damaged = min(damaged_allies, key=lambda p: p.hp / p.max_hp)
                        heal_amount = int(most_damaged.max_hp * (NPC_REFLECT_HP_RESTORE_PERCENT / 100))
                        most_damaged.hp = min(most_damaged.max_hp, most_damaged.hp + heal_amount)
                        self.mp -= NPC_REFLECT_MP_COST
                        return f"反射失败！治疗{most_damaged.index} {heal_amount}HP", int(heal_amount), "reflect"
                self.mp -= NPC_REFLECT_MP_COST
                return f"反射失败！没有需要治疗的队友", 0, "reflect"

        return "无效技能", 0, "heal"

    def draw(self, screen):
        if not self.collected and self.is_alive:
            # 优先使用鸡动画（如果是鸡角色）
            if hasattr(self, 'is_chicken') and self.is_chicken and hasattr(self, 'chicken_animation_frames') and self.chicken_animation_frames:
                current_time = pygame.time.get_ticks()
                if current_time - self.chicken_last_frame_update >= self.chicken_frame_time:
                    self.chicken_current_frame = (self.chicken_current_frame + 1) % len(self.chicken_animation_frames)
                    self.chicken_last_frame_update = current_time
                screen.blit(self.chicken_animation_frames[self.chicken_current_frame], (self.x, self.y))
            # 其他伙伴使用通用动画
            elif hasattr(self, 'gif_frames') and self.gif_frames:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_frame_update >= self.frame_time:
                    self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                    self.last_frame_update = current_time
                screen.blit(self.gif_frames[self.current_frame], (self.x, self.y))
            elif self.image:
                screen.blit(self.image, (self.x, self.y))
            else:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))


def create_partners(num):
    return [Partner(random.randint(0, SCREEN_WIDTH - 60), random.randint(100, 520), i + 1) for i in range(num)]