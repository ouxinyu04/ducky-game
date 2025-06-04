# enemy.py
import pygame
import os
import logging
import random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, RED
from config import ASSETS_DIR
from animation_utils import load_animation_frames
from constants import (BOSS_HP, BOSS_HUNTING_CLAW_DAMAGE, BOSS_HUNTING_CLAW_DAMAGE_REDUCTION,
                      BOSS_WHIRLWIND_DAMAGE, BOSS_WHIRLWIND_DAMAGE_INCREASE,
                      BOSS_CLAIM_KING_DAMAGE, BOSS_CLAIM_KING_HEALING,
                      BOSS_TAME_DISABLE_CHANCE, BOSS_SERVE_ME_DAMAGE_MULTIPLIER,
                      BOSS_FATAL_TEMPTATION_DAMAGE, BOSS_FATAL_TEMPTATION_DURATION,
                      NORMAL_ATTACK_DAMAGE, NPC_ATTACK_DAMAGE)

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)


class Enemy:
    def __init__(self, x, y, enemy_type="human", is_boss=False, is_special=False):
        self.x = x
        self.y = y
        self.width = 50 if is_boss else 30
        self.height = 50 if is_boss else 30
        self.enemy_type = enemy_type
        self.is_boss = is_boss
        self.is_special = is_special

        # 初始化HP属性
        self.hp = 250 if is_boss else 50
        self.max_hp = 250 if is_boss else 50

        # 初始化动画属性
        self.gif_frames = []
        self.current_frame = 0
        self.frame_time = 200  # 每帧200毫秒
        self.last_frame_update = 0

        if enemy_type == "human":
            self.attack_power = 12
        elif enemy_type == "traitor_duck":
            self.attack_power = 10
        elif enemy_type == "soul":
            self.attack_power = 8
        elif enemy_type == "ingredient":
            self.attack_power = 6
            # ingredient类型调整到120x96（与缩小后的GIF尺寸匹配）
            self.width = 120
            self.height = 96
        if is_boss:
            self.attack_power = 50  # BOSS 固定战力
        if is_special:
            self.attack_power = int(self.attack_power * 1.5)  # 特殊敌人战力增加 50%

        self.image = None

        # 特殊处理ingredient类型，使用mushroom_animation.gif
        if enemy_type == "ingredient":
            # 加载mushroom动画
            self.gif_frames, _ = load_animation_frames("mushroom_animation.gif", "mushroom.png", (self.width, self.height))
            if not self.gif_frames:
                # 如果动画加载失败，尝试加载静态图像
                fallback_path = os.path.join(ASSETS_DIR, "ingredient.png")
                if os.path.exists(fallback_path):
                    try:
                        self.image = pygame.image.load(fallback_path)
                        self.image = pygame.transform.scale(self.image, (self.width, self.height))
                    except pygame.error as e:
                        logging.error(f"Failed to load ingredient.png: {e}")
        else:
            # 其他敌人类型使用原有逻辑
            image_name = "boss_human.png" if is_boss else f"{enemy_type}.png"
            image_path = os.path.join(ASSETS_DIR, image_name)
            if os.path.exists(image_path):
                try:
                    self.image = pygame.image.load(image_path)
                    self.image = pygame.transform.scale(self.image, (self.width, self.height))
                except pygame.error as e:
                    logging.error(f"Failed to load {image_name}: {e}")

    def draw(self, screen):
        # ingredient类型使用动画
        if self.enemy_type == "ingredient" and self.gif_frames:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_frame_update >= self.frame_time:
                self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                self.last_frame_update = current_time
            screen.blit(self.gif_frames[self.current_frame], (self.x, self.y))
        elif self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))

class Boss:
    def __init__(self, boss_type=1):
        self.boss_type = boss_type  # 1或2，对应不同的BOSS
        self.hp = BOSS_HP
        self.max_hp = BOSS_HP
        self.attack_power = 20  # 基础攻击力（再减去10伤害：30 -> 20）
        self.turn_counter = 0
        self.damage_reduction = 0  # 伤害减免
        self.damage_increase = 0   # 伤害增加
        self.x = SCREEN_WIDTH // 2 - 150  # 调整x位置以居中
        self.y = 50
        self.width = 300  # 放大1.5倍：200 * 1.5 = 300
        self.height = 300  # 放大1.5倍：200 * 1.5 = 300

        # 创建rect属性用于特效定位
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # 受击状态
        self.hit_effect_active = False
        self.hit_effect_progress = 0.0

        # 动画相关属性
        self.gif_frames = []
        self.current_frame = 0
        self.frame_time = 200  # 每帧200毫秒
        self.last_frame_update = 0

        # 加载BOSS动画
        self.image = None
        self.gif_frames, _ = load_animation_frames("boss_animation.gif", "boss.png", (self.width, self.height))
        if not self.gif_frames:
            # 如果动画加载失败，尝试加载静态图像
            boss_image_path = os.path.join(ASSETS_DIR, "boss.png")
            try:
                if os.path.exists(boss_image_path):
                    self.image = pygame.image.load(boss_image_path)
                    self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except Exception as e:
                logging.error(f"Failed to load boss image: {e}")

        # 加载BOSS攻击动画
        self.attacking_frames = []
        self.current_attack_frame = 0
        self.last_attack_frame_update = 0
        self.attack_frame_time = 200  # 每帧200毫秒
        self.is_attacking = False
        self.attack_animation_start_time = 0
        self.attack_animation_duration = 1200  # 6帧 * 200ms = 1200ms

        # 加载攻击动画GIF
        attack_gif_path = os.path.join(ASSETS_DIR, "boss_attacking_animation.gif")
        if os.path.exists(attack_gif_path):
            try:
                self.attacking_frames, _ = load_animation_frames("boss_attacking_animation.gif", target_size=(self.width, self.height))
                if self.attacking_frames:
                    logging.info(f"Loaded BOSS attack animation with {len(self.attacking_frames)} frames")
                else:
                    logging.warning("Failed to load BOSS attack animation frames")
            except Exception as e:
                logging.error(f"Error loading BOSS attack animation: {e}")
                self.attacking_frames = []

        # 死亡动画相关属性
        self.is_dying = False
        self.death_animation_frames = []
        self.death_current_frame = 0
        self.death_frame_time = 200  # 每帧200毫秒
        self.death_last_frame_update = 0
        self.death_animation_finished = False

        # 加载死亡动画帧
        self.load_death_animation()

    def load_death_animation(self):
        """加载死亡动画帧"""
        try:
            # 尝试加载death.png精灵图
            death_png_path = os.path.join(ASSETS_DIR, "death.png")
            if os.path.exists(death_png_path):
                import pygame
                sprite_sheet = pygame.image.load(death_png_path)

                # 定义18帧的位置（每帧100x100，上下两行）
                frame_positions = [
                    # 第一行（帧1-10）
                    (0, 0, 100, 100), (100, 0, 200, 100), (200, 0, 300, 100), (300, 0, 400, 100), (400, 0, 500, 100),
                    (500, 0, 600, 100), (600, 0, 700, 100), (700, 0, 800, 100), (800, 0, 900, 100), (900, 0, 1000, 100),
                    # 第二行（帧11-18）
                    (0, 100, 100, 200), (100, 100, 200, 200), (200, 100, 300, 200), (300, 100, 400, 200),
                    (400, 100, 500, 200), (500, 100, 600, 200), (600, 100, 700, 200), (700, 100, 800, 200)
                ]

                # 提取并放大每一帧
                for left, top, right, bottom in frame_positions:
                    # 提取帧
                    frame_rect = pygame.Rect(left, top, right - left, bottom - top)
                    frame = sprite_sheet.subsurface(frame_rect).copy()

                    # 放大到200x200（2倍）
                    frame_scaled = pygame.transform.scale(frame, (200, 200))
                    self.death_animation_frames.append(frame_scaled)

                logging.info(f"Loaded {len(self.death_animation_frames)} death animation frames")
            else:
                logging.warning(f"Death animation sprite sheet not found: {death_png_path}")
        except Exception as e:
            logging.error(f"Error loading death animation: {e}")

    def start_death_animation(self):
        """开始死亡动画"""
        if self.death_animation_frames:
            self.is_dying = True
            self.death_current_frame = 0
            self.death_last_frame_update = pygame.time.get_ticks()
            self.death_animation_finished = False
            logging.info("BOSS death animation started")

    def start_attack_animation(self):
        """开始攻击动画"""
        if self.attacking_frames:
            self.is_attacking = True
            self.attack_animation_start_time = pygame.time.get_ticks()
            self.current_attack_frame = 0
            self.last_attack_frame_update = pygame.time.get_ticks()
            logging.info("BOSS attack animation started")

    def use_skill(self, targets):
        """
        BOSS使用技能
        targets: 目标角色列表
        """
        # 开始攻击动画
        self.start_attack_animation()

        self.turn_counter += 1

        # 第3回合使用大招
        if self.turn_counter % 3 == 0:
            return self.use_big_move(targets)
        else:
            return self.use_normal_skill(targets)

    def use_normal_skill(self, targets):
        """使用普通技能"""
        if self.boss_type == 1:
            # Boss 1: Hunting Claw 或 Whirlwind
            if random.random() < 0.5:
                # Hunting Claw - 单体攻击
                if targets:
                    target = random.choice([t for t in targets if t.is_alive])
                    damage = BOSS_HUNTING_CLAW_DAMAGE
                    # 使用新的伤害处理方法，优先扣除护盾
                    if hasattr(target, 'take_damage'):
                        target.take_damage(damage)
                    else:
                        target.hp = max(0, target.hp - damage)
                    self.damage_reduction = BOSS_HUNTING_CLAW_DAMAGE_REDUCTION  # 下回合伤害减免30%
                    return f"BOSS使用猎杀之爪！对{target.index}造成{damage}伤害", [target]
            else:
                # Whirlwind - 群体攻击
                damage = BOSS_WHIRLWIND_DAMAGE
                damaged_targets = []
                for target in targets:
                    if target.is_alive:
                        # 使用新的伤害处理方法，优先扣除护盾
                        if hasattr(target, 'take_damage'):
                            target.take_damage(damage)
                        else:
                            target.hp = max(0, target.hp - damage)
                        damaged_targets.append(target)
                self.damage_increase = BOSS_WHIRLWIND_DAMAGE_INCREASE  # 下回合伤害增加20%
                return f"BOSS使用旋风！对所有角色造成{damage}伤害", damaged_targets

        elif self.boss_type == 2:
            # Boss 2: Tame 或 Serve Me
            if random.random() < 0.5:
                # Tame - 50%概率禁用随机角色
                alive_targets = [t for t in targets if t.is_alive]
                if alive_targets and random.random() < (BOSS_TAME_DISABLE_CHANCE / 100):
                    target = random.choice(alive_targets)
                    target.disabled_next_turn = True
                    return f"BOSS使用驯服！{target.index}下回合无法行动", [target]
                else:
                    return "BOSS的驯服失败了！", []
            else:
                # Serve Me - 控制角色攻击队友
                alive_targets = [t for t in targets if t.is_alive]
                if len(alive_targets) >= 2:
                    attacker = random.choice(alive_targets)
                    victims = [t for t in alive_targets if t != attacker]
                    victim = random.choice(victims)

                    # 计算伤害（150%普通攻击）
                    base_damage = NPC_ATTACK_DAMAGE if attacker.npc_type else NORMAL_ATTACK_DAMAGE
                    damage = int(base_damage * BOSS_SERVE_ME_DAMAGE_MULTIPLIER)
                    # 使用新的伤害处理方法，优先扣除护盾
                    if hasattr(victim, 'take_damage'):
                        victim.take_damage(damage)
                    else:
                        victim.hp = max(0, victim.hp - damage)

                    return f"BOSS控制{attacker.index}攻击{victim.index}！造成{damage}伤害", [victim]

        return "BOSS什么都没做", []

    def use_big_move(self, targets):
        """使用大招"""
        if self.boss_type == 1:
            # Claim King - 群体伤害+自我治疗
            damage = BOSS_CLAIM_KING_DAMAGE
            damaged_targets = []
            for target in targets:
                if target.is_alive:
                    # 使用新的伤害处理方法，优先扣除护盾
                    if hasattr(target, 'take_damage'):
                        target.take_damage(damage)
                    else:
                        target.hp = max(0, target.hp - damage)
                    damaged_targets.append(target)

            # 恢复自身HP
            self.hp = min(self.max_hp, self.hp + BOSS_CLAIM_KING_HEALING)
            return f"BOSS使用王者宣言！对所有角色造成{damage}伤害并恢复{BOSS_CLAIM_KING_HEALING}HP", damaged_targets

        elif self.boss_type == 2:
            # Fatal Temptation - 施加沼泽效果
            for target in targets:
                if target.is_alive:
                    target.swamp_effect = True
                    target.swamp_duration = BOSS_FATAL_TEMPTATION_DURATION
            return "BOSS使用致命诱惑！所有角色被沼泽诅咒", targets


    def draw(self, screen):
        """绘制BOSS"""
        current_time = pygame.time.get_ticks()
        current_image = None

        # 优先检查是否正在播放死亡动画
        if self.is_dying and self.death_animation_frames:
            # 更新死亡动画帧
            if current_time - self.death_last_frame_update >= self.death_frame_time:
                if self.death_current_frame < len(self.death_animation_frames) - 1:
                    self.death_current_frame += 1
                    self.death_last_frame_update = current_time
                else:
                    # 动画播放完成，停留在最后一帧
                    self.death_animation_finished = True

            # 使用死亡动画帧 - 实现"用完就丢"的GIF效果
            # 直接使用当前帧，每帧完全替换前一帧（背景清除由battle.py处理）
            current_image = self.death_animation_frames[self.death_current_frame]

        # 如果没有死亡动画，检查是否正在播放攻击动画
        elif self.is_attacking and self.attacking_frames:
            # 检查攻击动画是否结束
            if current_time - self.attack_animation_start_time >= self.attack_animation_duration:
                self.is_attacking = False
                logging.info("BOSS attack animation finished")
            else:
                # 更新攻击动画帧
                if current_time - self.last_attack_frame_update >= self.attack_frame_time:
                    self.current_attack_frame = (self.current_attack_frame + 1) % len(self.attacking_frames)
                    self.last_attack_frame_update = current_time

                # 使用攻击动画帧
                current_image = self.attacking_frames[self.current_attack_frame]

        # 如果没有攻击动画，使用普通动画或静态图像
        if current_image is None:
            if self.gif_frames:
                # 更新普通动画帧
                if current_time - self.last_frame_update >= self.frame_time:
                    self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                    self.last_frame_update = current_time

                # 使用当前普通动画帧
                current_image = self.gif_frames[self.current_frame]
            elif self.image:
                # 使用静态图像
                current_image = self.image

        if current_image:
            # 检查BOSS是否处于受击状态
            if hasattr(self, 'hit_effect_active') and self.hit_effect_active:
                # 创建红色滤镜效果
                red_intensity = int(150 * getattr(self, 'hit_effect_progress', 1.0))

                # 创建红色覆盖层
                red_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                red_overlay.fill((255, 0, 0, red_intensity))

                # 先绘制BOSS图像
                screen.blit(current_image, (self.x, self.y))
                # 再绘制红色覆盖层
                screen.blit(red_overlay, (self.x, self.y))
            else:
                # 正常绘制BOSS
                screen.blit(current_image, (self.x, self.y))
        else:
            # 如果没有图片，绘制矩形
            boss_rect = pygame.Rect(self.x, self.y, self.width, self.height)

            # 检查受击状态
            if hasattr(self, 'hit_effect_active') and self.hit_effect_active:
                # 受击时显示红色
                red_intensity = getattr(self, 'hit_effect_progress', 1.0)
                hit_color = (
                    int(200 * red_intensity),
                    0,
                    0
                )
                pygame.draw.rect(screen, hit_color, boss_rect)
            else:
                # 正常黑色
                pygame.draw.rect(screen, (0, 0, 0), boss_rect)