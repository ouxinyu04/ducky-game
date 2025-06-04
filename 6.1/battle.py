# battle.py - BOSS战斗系统增强版 - 完整修复版
import pygame
import random
import logging
import traceback
import os
import math  # 添加数学库，用于特效计算

# 设置错误日志
error_logger = logging.getLogger('game_errors')
error_handler = logging.FileHandler('game_errors.log')
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)
from constants import (NORMAL_MP_RECOVERY, NPC_MP_RECOVERY, NORMAL_BASE_HP, NORMAL_BASE_MP, NPC_BASE_HP, NPC_BASE_MP, BOSS_HP)
from constants import NORMAL_SHIELD_TAUNT_CHANCE, NPC_REFLECT_TAUNT_CHANCE, NPC_REFLECT_HP_RESTORE_PERCENT
from enemy import Boss
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, ORANGE
from config import ASSETS_DIR
from utils import (load_image, draw_skill_button_with_icon,
                  draw_character_status_effects, draw_skill_result_prompt,
                  draw_shield_bar, draw_progress_bar)
from animation_utils import load_animation_frames

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

# 背景图片路径
BATTLE_BACKGROUND_PATH = os.path.join(ASSETS_DIR, "battle_background.png")

# 粒子特效类 - 新增
class ParticleEffect:
    """粒子特效类，用于BOSS攻击时的粒子效果"""
    def __init__(self, target_rect, effect_type="attack"):
        self.target_rect = target_rect
        self.effect_type = effect_type
        self.particles = []
        self.start_time = pygame.time.get_ticks()
        self.duration = 1000  # 1秒持续时间
        self.active = True

        # 创建粒子
        self.create_particles()

    def create_particles(self):
        """创建粒子"""
        particle_count = 15  # 粒子数量
        for _ in range(particle_count):
            # 随机位置围绕目标
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(20, 80)
            center_x = self.target_rect.centerx
            center_y = self.target_rect.centery

            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)

            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-2, 2),  # 速度
                'vy': random.uniform(-2, 2),
                'size': random.uniform(3, 8),  # 粒子大小
                'color': random.choice([(255, 100, 100), (255, 150, 0), (255, 255, 0)]),  # 红/橙/黄色
                'alpha': 255,
                'life': 1.0  # 生命值 0-1
            }
            self.particles.append(particle)

    def update(self):
        """更新粒子状态"""
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time

        if elapsed > self.duration:
            self.active = False
            return

        # 更新每个粒子
        progress = elapsed / self.duration
        for particle in self.particles:
            # 更新位置
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']

            # 更新生命值和透明度
            particle['life'] = 1.0 - progress
            particle['alpha'] = int(255 * particle['life'])

            # 粒子大小随时间减小
            particle['size'] *= 0.98

    def draw(self, screen):
        """绘制粒子"""
        if not self.active:
            return

        for particle in self.particles:
            if particle['life'] > 0:
                # 创建带透明度的surface
                particle_surface = pygame.Surface((int(particle['size']) * 2, int(particle['size']) * 2), pygame.SRCALPHA)

                # 绘制发光效果 - 外层模糊
                outer_color = (*particle['color'], max(0, particle['alpha'] // 4))
                pygame.draw.circle(particle_surface, outer_color,
                                 (int(particle['size']), int(particle['size'])),
                                 int(particle['size']))

                # 绘制内核 - 明亮中心
                inner_color = (*particle['color'], max(0, particle['alpha']))
                pygame.draw.circle(particle_surface, inner_color,
                                 (int(particle['size']), int(particle['size'])),
                                 max(1, int(particle['size'] * 0.6)))

                # 绘制到屏幕
                screen.blit(particle_surface,
                           (particle['x'] - particle['size'], particle['y'] - particle['size']))


# 视觉特效管理类
class VisualEffect:
    """视觉特效类，用于管理战斗中的视觉特效"""
    def __init__(self, effect_type, target_pos, duration=1500, persistent=False):
        self.effect_type = effect_type  # 特效类型
        self.target_pos = target_pos  # 目标位置 (x, y)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration  # 特效持续时间(毫秒)
        self.persistent = persistent  # 是否为持续特效
        self.active = True

        # 动画相关属性
        self.frames = []  # 动画帧列表
        self.current_frame = 0  # 当前帧索引
        self.last_frame_update = 0  # 上次帧更新时间
        self.frame_duration = 100  # 每帧持续时间(毫秒) - 10 FPS
        self.is_animated = False  # 是否为动画

        # 加载特效图像
        self.load_effect_image()

    def load_effect_image(self):
        """加载特效图像 - 支持GIF动画"""
        try:
            effect_files = {
                "claw": "claw_effect.gif",
                "heal": "heal_effect.gif",
                "heal_all": "heal_all_effect.gif",  # 群体治疗特效
                "shield": "yellow_shield_effect.gif",  # 使用黄色护盾特效
                "slash": "claw_effect.gif",
                "bless": "bless_effect.gif",
                "substitute": "substitute_effect.gif",
                "reflect": "reflect_effect.gif",
                "tornado": "tornado_effect.gif",
                "particle": "particle_effect.gif"
            }

            if self.effect_type in effect_files:
                effect_path = os.path.join(ASSETS_DIR, effect_files[self.effect_type])

                # 如果yellow_shield_effect.gif不存在，回退到shield_effect.gif
                if self.effect_type == "shield" and not os.path.exists(effect_path):
                    effect_path = os.path.join(ASSETS_DIR, "shield_effect.gif")
                    effect_files[self.effect_type] = "shield_effect.gif"

                if os.path.exists(effect_path):
                    # 使用animation_utils加载GIF动画帧，确保透明背景
                    from animation_utils import load_animation_frames
                    self.frames, self.is_animated = load_animation_frames(
                        effect_files[self.effect_type],
                        target_size=None
                    )

                    if self.frames:
                        # 确保所有帧都有透明背景 - 改进版
                        transparent_frames = []
                        for frame in self.frames:
                            # 如果帧已经支持透明度，直接使用
                            if frame.get_flags() & pygame.SRCALPHA:
                                transparent_frames.append(frame)
                            else:
                                # 创建带透明度的新surface并转换
                                transparent_frame = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                                transparent_frame = frame.convert_alpha()
                                transparent_frames.append(transparent_frame)
                        self.frames = transparent_frames

                        # 设置动画参数
                        if self.is_animated:
                            # 根据特效类型调整帧率
                            if self.effect_type in ["claw", "slash", "tornado"]:
                                self.frame_duration = 80  # 12.5 FPS - 快速动画
                            elif self.effect_type in ["heal", "bless", "substitute"]:
                                self.frame_duration = 120  # 8.3 FPS - 中等速度
                            else:
                                self.frame_duration = 100  # 10 FPS - 默认速度

                        error_logger.info(f"Loaded effect animation with transparency: {effect_files[self.effect_type]} - {len(self.frames)} frames, animated: {self.is_animated}")
                    else:
                        error_logger.warning(f"No frames loaded for effect: {effect_path}")
                        self.create_fallback_effect()
                else:
                    error_logger.warning(f"Effect image not found: {effect_path}")
                    self.create_fallback_effect()
            else:
                error_logger.warning(f"Unknown effect type: {self.effect_type}")
                self.create_fallback_effect()

        except Exception as e:
            error_logger.error(f"Error loading effect image for {self.effect_type}: {e}")
            self.create_fallback_effect()

    def create_fallback_effect(self):
        """创建备用特效"""
        size = 80
        fallback_image = pygame.Surface((size, size), pygame.SRCALPHA)

        if self.effect_type in ["claw", "slash"]:
            # 红色爪痕
            for i in range(3):
                offset = i * 15 - 15
                start_pos = (15 + offset, 10)
                end_pos = (65 + offset, 70)
                pygame.draw.line(fallback_image, (255, 0, 0), start_pos, end_pos, 4)
        elif self.effect_type in ["heal", "shield", "bless", "substitute", "reflect"]:
            # 彩色光环
            colors = {
                "heal": (0, 255, 0),
                "shield": (255, 255, 0),  # 黄色护盾
                "bless": (255, 215, 0),
                "substitute": (150, 0, 150),
                "reflect": (128, 0, 128)
            }
            color = colors.get(self.effect_type, (255, 255, 255))
            pygame.draw.circle(fallback_image, color, (size//2, size//2), size//2 - 5, 5)
        elif self.effect_type == "tornado":
            # 蓝色旋涡
            for i in range(8):
                radius = 10 + i * 5
                alpha = 255 - i * 25
                color = (*[100, 100, 255], max(0, alpha))
                pygame.draw.circle(fallback_image, color, (size//2, size//2), radius, 3)
        else:
            # 默认白色圆圈
            pygame.draw.circle(fallback_image, (255, 255, 255), (size//2, size//2), size//2 - 5, 3)

        # 将备用图像添加到frames列表
        self.frames = [fallback_image]
        self.is_animated = False

    def update(self):
        """更新特效状态"""
        current_time = pygame.time.get_ticks()

        # 更新动画帧
        if self.is_animated and len(self.frames) > 1:
            if current_time - self.last_frame_update >= self.frame_duration:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.last_frame_update = current_time

        # 检查特效是否应该结束
        if not self.persistent:
            elapsed = current_time - self.start_time
            if elapsed > self.duration:
                self.active = False

    def draw(self, screen):
        """绘制特效"""
        if not self.active:
            return

        try:
            # 获取当前帧图像
            current_image = None
            if self.frames:
                if self.is_animated and len(self.frames) > 1:
                    current_image = self.frames[self.current_frame]
                else:
                    current_image = self.frames[0]
            elif hasattr(self, 'effect_image') and self.effect_image:
                current_image = self.effect_image
            else:
                return

            # 计算特效位置（居中显示在目标上）
            effect_rect = current_image.get_rect(center=self.target_pos)

            # 添加动画效果
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.start_time
            progress = min(1.0, elapsed / self.duration) if not self.persistent else (current_time % 2000) / 2000.0

            # 所有特效都使用静态显示（只播放GIF动画，不添加旋转或缩放）
            screen.blit(current_image, effect_rect)

        except Exception as e:
            error_logger.error(f"Error drawing effect {self.effect_type}: {e}")

# 战斗特效类定义
class BattleEffect:
    """战斗特效类，用于管理战斗中的视觉特效"""
    def __init__(self, effect_type, target, position, duration=2000):
        self.effect_type = effect_type  # 特效类型: "shake", "claw", "heal", "tornado"
        self.target = target  # 特效目标
        self.position = position  # 特效位置
        self.start_time = pygame.time.get_ticks()  # 特效开始时间
        self.duration = duration  # 特效持续时间(毫秒)，默认2秒
        self.active = True  # 特效是否活跃

        # 保存原始位置 - 改进版
        if isinstance(position, pygame.Rect):
            self.original_pos = position.copy()
        elif hasattr(target, 'rect'):
            self.original_pos = target.rect.copy()
        else:
            self.original_pos = position

        self.shake_offset = [0, 0]  # 震动偏移
        self.return_progress = 0  # 回位进度

        # 加载特效图像
        self.effect_images = []
        if effect_type == "claw":
            try:
                claw_path = os.path.join(ASSETS_DIR, "claw_effect.png")
                if os.path.exists(claw_path):
                    self.effect_images.append(pygame.image.load(claw_path))
                else:
                    # 如果没有图像，创建一个简单的爪痕效果
                    self.create_claw_effect()
            except:
                self.create_claw_effect()
        elif effect_type == "heal":
            try:
                heal_path = os.path.join(ASSETS_DIR, "heal_effect.png")
                if os.path.exists(heal_path):
                    self.effect_images.append(pygame.image.load(heal_path))
                else:
                    # 如果没有图像，创建一个简单的治疗效果
                    self.create_heal_effect()
            except:
                self.create_heal_effect()
        elif effect_type == "tornado":
            try:
                tornado_path = os.path.join(ASSETS_DIR, "tornado_effect.png")
                if os.path.exists(tornado_path):
                    self.effect_images.append(pygame.image.load(tornado_path))
                else:
                    # 如果没有图像，创建一个简单的龙卷风效果
                    self.create_tornado_effect()
            except:
                self.create_tornado_effect()

    def create_claw_effect(self):
        """创建简单的爪痕效果"""
        effect_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        # 绘制三条红色爪痕
        for i in range(3):
            offset = i * 20 - 20
            start_pos = (20 + offset, 10)
            end_pos = (60 + offset, 70)
            pygame.draw.line(effect_surf, (255, 0, 0), start_pos, end_pos, 5)
        self.effect_images.append(effect_surf)

    def create_heal_effect(self):
        """创建简单的治疗效果"""
        effect_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        # 绘制绿色光环
        pygame.draw.circle(effect_surf, (0, 255, 0, 100), (50, 50), 45)
        pygame.draw.circle(effect_surf, (0, 255, 0, 150), (50, 50), 45, 3)
        # 绘制几个绿色小星星
        for i in range(5):
            angle = i * (2 * math.pi / 5)
            x = 50 + 35 * math.cos(angle)
            y = 50 + 35 * math.sin(angle)
            pygame.draw.circle(effect_surf, (100, 255, 100), (int(x), int(y)), 5)
        self.effect_images.append(effect_surf)

    def create_tornado_effect(self):
        """创建简单的龙卷风效果"""
        effect_surf = pygame.Surface((120, 180), pygame.SRCALPHA)
        # 绘制旋转的龙卷风
        for i in range(10):
            height = i * 15
            width = 30 + i * 6
            alpha = 200 - i * 15
            color = (100, 100, 255, max(0, alpha))
            pygame.draw.ellipse(effect_surf, color,
                               (60 - width/2, 180 - height - 10, width, 20))
        self.effect_images.append(effect_surf)

    def update(self):
        """更新特效状态"""
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time

        # 检查特效是否结束
        if elapsed > self.duration:
            self.active = False
            # 确保目标回到原位并恢复正常状态
            if self.effect_type == "shake" and hasattr(self.target, 'rect'):
                self.target.rect = self.original_pos.copy()
                # 清除受击状态
                if hasattr(self.target, 'hit_effect_active'):
                    self.target.hit_effect_active = False
            return

        # 更新不同类型的特效
        if self.effect_type == "shake":
            progress = elapsed / self.duration

            # 阶段1: 受击反应 (0-0.3秒) - 变红+小幅抖动+后退
            if progress < 0.3:
                shake_intensity = 8  # 抖动强度
                self.shake_offset = [
                    random.randint(-shake_intensity, shake_intensity),
                    random.randint(-shake_intensity, shake_intensity)
                ]

                # 后退效果 - 向反方向移动
                back_distance = 25  # 后退距离
                back_progress = progress / 0.3  # 0-1的后退进度
                current_back_offset = back_distance * back_progress

                if isinstance(self.target, pygame.Rect):
                    # 矩形目标处理
                    self.target.x = self.original_pos.x + self.shake_offset[0]
                    if self.target.y > SCREEN_HEIGHT // 2:
                        self.target.y = self.original_pos.y + current_back_offset  # 玩家向下后退
                    else:
                        self.target.y = self.original_pos.y - current_back_offset  # BOSS向上后退
                elif hasattr(self.target, 'rect'):
                    # 角色对象处理
                    self.target.rect.x = self.original_pos.x + self.shake_offset[0]
                    if self.target.rect.y > SCREEN_HEIGHT // 2:
                        self.target.rect.y = self.original_pos.y + current_back_offset  # 玩家向下后退
                    else:
                        self.target.rect.y = self.original_pos.y - current_back_offset  # BOSS向上后退

                    # 设置受击状态 - 变红效果
                    self.target.hit_effect_active = True
                    self.target.hit_effect_progress = progress / 0.3  # 0-1的红色效果进度

            # 阶段2: 持续受击状态 (0.3-0.7秒) - 保持红色+轻微抖动
            elif progress < 0.7:
                shake_intensity = 3  # 较小的抖动
                self.shake_offset = [
                    random.randint(-shake_intensity, shake_intensity),
                    random.randint(-shake_intensity, shake_intensity)
                ]

                if isinstance(self.target, pygame.Rect):
                    self.target.x = self.original_pos.x + self.shake_offset[0]
                    # 保持后退位置
                    if self.target.y > SCREEN_HEIGHT // 2:
                        self.target.y = self.original_pos.y + 25
                    else:
                        self.target.y = self.original_pos.y - 25
                elif hasattr(self.target, 'rect'):
                    self.target.rect.x = self.original_pos.x + self.shake_offset[0]
                    # 保持后退位置
                    if self.target.rect.y > SCREEN_HEIGHT // 2:
                        self.target.rect.y = self.original_pos.y + 25
                    else:
                        self.target.rect.y = self.original_pos.y - 25

                    # 继续受击状态
                    self.target.hit_effect_active = True
                    self.target.hit_effect_progress = 1.0  # 最大红色效果

            # 阶段3: 恢复阶段 (0.7-1.0秒) - 回到原位+红色淡化
            else:
                return_progress = (progress - 0.7) / 0.3  # 0-1的恢复进度

                if isinstance(self.target, pygame.Rect):
                    # 平滑回到原位
                    current_x = self.original_pos.x + self.shake_offset[0] * (1 - return_progress)
                    current_y_offset = 25 * (1 - return_progress)

                    self.target.x = current_x
                    if self.target.y > SCREEN_HEIGHT // 2:
                        self.target.y = self.original_pos.y + current_y_offset
                    else:
                        self.target.y = self.original_pos.y - current_y_offset
                elif hasattr(self.target, 'rect'):
                    # 平滑回到原位
                    current_x = self.original_pos.x + self.shake_offset[0] * (1 - return_progress)
                    current_y_offset = 25 * (1 - return_progress)

                    self.target.rect.x = current_x
                    if self.target.rect.y > SCREEN_HEIGHT // 2:
                        self.target.rect.y = self.original_pos.y + current_y_offset
                    else:
                        self.target.rect.y = self.original_pos.y - current_y_offset

                    # 红色效果淡化
                    self.target.hit_effect_active = True
                    self.target.hit_effect_progress = 1.0 - return_progress  # 从1淡化到0

    def draw(self, screen):
        """绘制特效"""
        if not self.active:
            return

        # 特效动画的进度比例
        current_time = pygame.time.get_ticks()
        progress = min(1.0, (current_time - self.start_time) / self.duration)

        # 根据特效类型绘制不同的效果
        if self.effect_type in ["claw", "heal", "tornado"] and self.effect_images:
            effect_img = self.effect_images[0]

            # 根据进度调整透明度
            if progress > 0.7:
                fade_factor = 1.0 - (progress - 0.7) / 0.3
                effect_copy = effect_img.copy()
                # 创建透明表面
                alpha_surf = pygame.Surface(effect_img.get_size(), pygame.SRCALPHA)
                alpha_surf.fill((255, 255, 255, int(255 * fade_factor)))
                effect_copy.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                effect_img = effect_copy

            # 获取目标位置
            target_pos = None
            if isinstance(self.position, pygame.Rect):
                target_pos = (self.position.centerx, self.position.centery)
            elif isinstance(self.position, tuple):
                target_pos = self.position
            elif hasattr(self.target, 'rect'):
                target_pos = (self.target.rect.centerx, self.target.rect.centery)

            if target_pos:
                # 根据特效类型调整位置
                if self.effect_type == "claw":
                    # 爪痕效果居中显示在目标上
                    effect_rect = effect_img.get_rect(center=target_pos)
                    screen.blit(effect_img, effect_rect)
                elif self.effect_type == "heal":
                    # 治疗效果静态显示（不旋转）
                    effect_rect = effect_img.get_rect(center=target_pos)
                    screen.blit(effect_img, effect_rect)
                elif self.effect_type == "tornado":
                    # 龙卷风效果
                    offset_y = -20 * math.sin(progress * math.pi)  # 上下浮动效果
                    effect_rect = effect_img.get_rect(midbottom=(target_pos[0], target_pos[1] + offset_y))
                    screen.blit(effect_img, effect_rect)


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


# battle.py 角色选择和BOSS战斗逻辑增强
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

        # 加载BOSS动画（注意：battle.py中的boss图像现在由Boss类自己管理）
        # 这里不再需要单独加载boss图像，因为Boss类已经处理了动画
        boss_image = None  # 保留变量以兼容现有代码，但实际不使用

        # 回合提示相关变量
        turn_notification_active = False
        turn_notification_start_time = 0
        turn_notification_text = ""
        turn_notification_color = (255, 255, 255)  # 白色
        turn_border_color = (0, 0, 255)  # 蓝色或红色
        turn_notification_duration = 3000  # 3秒
        turn_notification_shown = False  # 标记当前回合的提示是否已显示
        current_turn_state = None  # 记录当前回合状态，用于检测回合切换
        turn_notification_finished = False  # 标记当前回合提示是否已完全结束

        # 创建大字体用于回合提示
        large_font = pygame.font.SysFont("SimHei", 30)

        # 初始化BOSS - 修复版
        boss = enemies[0]

        # 安全地初始化BOSS的HP - 使用新的Boss类
        if not isinstance(boss, Boss):
            # 如果不是Boss类实例，创建一个新的Boss实例
            boss = Boss(boss_type=1)  # 默认使用Boss 1
            enemies[0] = boss

        # 确保BOSS有正确的HP
        if not hasattr(boss, 'hp') or boss.hp <= 0:
            boss.hp = BOSS_HP
        if not hasattr(boss, 'max_hp') or boss.max_hp <= 0:
            boss.max_hp = BOSS_HP

        # 降低BOSS攻击力，更平衡
        boss.attack_power = 13  # 降低BOSS基础攻击力（再减去10伤害：23 -> 13）

        # 添加缺失的BOSS属性 - 重要修复
        if not hasattr(boss, 'special_attack_cooldown'):
            boss.special_attack_cooldown = 3  # 每3回合释放一次大招
        if not hasattr(boss, 'turn_counter'):
            boss.turn_counter = 0  # 回合计数器
        if not hasattr(boss, 'special_attack_damage'):
            boss.special_attack_damage = 30  # 大招伤害（再减去10伤害：40 -> 30）

        # 添加rect属性给BOSS（用于特效定位）- 重要修复
        if not hasattr(boss, 'rect'):
            boss.rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 50, 200, 200)

        # 初始化受击状态
        boss.hit_effect_active = False
        boss.hit_effect_progress = 0.0

        # 为所有伙伴初始化受击状态和rect属性 - 重要修复
        for i, partner in enumerate(selected_partners):
            if partner:
                partner.hit_effect_active = False
                partner.hit_effect_progress = 0.0

                # 添加rect属性给伙伴（用于特效定位）
                if not hasattr(partner, 'rect'):
                    button_width = 100
                    button_height = 120
                    spacing = 20
                    total_width = (button_width + spacing) * len(selected_partners) - spacing
                    start_x = (SCREEN_WIDTH - total_width) // 2
                    button_x = start_x + i * (button_width + spacing)
                    button_y = SCREEN_HEIGHT - button_height - 20
                    partner.rect = pygame.Rect(button_x, button_y, button_width, button_height)

        logging.info(f"Boss initialized with HP: {boss.hp}/{boss.max_hp}, Attack: {boss.attack_power}")

        # 战斗开始时，所有伙伴MP恢复满
        for partner in selected_partners:
            if partner and partner.is_alive:
                partner.mp = partner.max_mp
                logging.info(f"Partner {partner.index} MP restored to {partner.mp}")

        # 初始化战斗状态变量
        state = "roll_dice"  # 直接开始骰子阶段，跳过准备界面
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
        # 添加特效列表
        active_effects = []
        # 添加粒子特效列表
        active_particles = []
        # 添加视觉特效列表
        visual_effects = []
        # 添加持续特效列表
        persistent_effects = []

        # 安全创建特效的辅助函数 - 重要修复
        def create_safe_effect(effect_type, target, effect_name="attack"):
            """安全创建特效，处理缺失的rect属性"""
            try:
                target_rect = None

                # 获取目标矩形
                if hasattr(target, 'rect'):
                    target_rect = target.rect
                elif isinstance(target, pygame.Rect):
                    target_rect = target
                else:
                    # 为没有rect的对象创建默认rect
                    if target == boss:
                        target_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 50, 200, 200)
                        target.rect = target_rect  # 保存rect给对象
                    else:
                        # 为伙伴创建默认rect
                        target_rect = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200, 100, 100)
                        if not hasattr(target, 'rect'):
                            target.rect = target_rect

                if target_rect:
                    active_effects.append(BattleEffect(effect_type, target, target_rect))
                    logging.info(f"Created {effect_name} effect for target")
                else:
                    logging.warning(f"Could not create {effect_name} effect - no valid rect")

            except Exception as e:
                logging.error(f"Error creating {effect_name} effect: {e}")

        # 创建视觉特效的辅助函数
        def create_visual_effect(effect_type, target, persistent=False):
            """创建视觉特效"""
            try:
                # 获取目标位置
                target_pos = None
                if hasattr(target, 'rect'):
                    target_pos = (target.rect.centerx, target.rect.centery)
                elif isinstance(target, pygame.Rect):
                    target_pos = (target.centerx, target.centery)
                elif target == boss:
                    target_pos = (SCREEN_WIDTH // 2, 150)  # BOSS位置
                else:
                    # 查找角色在按钮中的位置
                    for button_rect, partner, _ in character_buttons:
                        if partner == target:
                            target_pos = (button_rect.centerx, button_rect.centery - 30)
                            break
                    if not target_pos:
                        target_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)  # 默认位置

                if target_pos:
                    effect = VisualEffect(effect_type, target_pos, persistent=persistent)
                    if persistent:
                        # 检查是否已有相同类型的持续特效
                        existing_effect = None
                        for i, (eff_target, eff) in enumerate(persistent_effects):
                            if eff_target == target and eff.effect_type == effect_type:
                                existing_effect = i
                                break

                        if existing_effect is not None:
                            # 更新现有特效
                            persistent_effects[existing_effect] = (target, effect)
                        else:
                            # 添加新的持续特效
                            persistent_effects.append((target, effect))
                    else:
                        visual_effects.append(effect)

                    error_logger.info(f"Created visual effect: {effect_type} for target")
                else:
                    error_logger.warning(f"Could not create visual effect {effect_type} - no valid position")

            except Exception as e:
                error_logger.error(f"Error creating visual effect {effect_type}: {e}")

        # 移除持续特效的辅助函数
        def remove_persistent_effect(target, effect_type):
            """移除指定目标的持续特效"""
            try:
                for i, (eff_target, eff) in enumerate(persistent_effects):
                    if eff_target == target and eff.effect_type == effect_type:
                        persistent_effects.pop(i)
                        break
            except Exception as e:
                error_logger.error(f"Error removing persistent effect: {e}")

        # 骰子相关属性
        dice_state = "showing_condition"
        dice_animation_start = pygame.time.get_ticks()
        dice_animation_duration = 1000
        dice_display_time = 3000
        dice_current_number = 1
        dice_images = {}

        # 加载骰子图片
        for i in range(1, 7):
            dice_path = os.path.join(ASSETS_DIR, f"dice_{i}.png")
            if os.path.exists(dice_path):
                try:
                    dice_image = pygame.image.load(dice_path)
                    dice_images[i] = pygame.transform.scale(dice_image, (60, 60))  # 放大骰子图像
                except pygame.error as e:
                    logging.error(f"Failed to load dice_{i}.png: {e}")

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

        # 创建角色选择按钮区域 - 修复版，确保UI不溢出
        character_buttons = []
        character_y_offsets = []
        button_width = 95  # 减小按钮宽度以适应屏幕
        button_height = 115  # 减小按钮高度
        spacing = 15  # 减小间距

        # 只计算活着的伙伴
        alive_partners = [p for p in selected_partners if p and hasattr(p, 'is_alive') and p.is_alive]
        total_width = (button_width + spacing) * len(alive_partners) - spacing if alive_partners else 0

        # 确保按钮不超出屏幕边界
        max_width = SCREEN_WIDTH - 20  # 留出10像素边距
        if total_width > max_width:
            # 如果总宽度超出屏幕，调整按钮大小和间距
            button_width = min(85, (max_width - (len(alive_partners) - 1) * 10) // len(alive_partners))
            spacing = 10
            total_width = (button_width + spacing) * len(alive_partners) - spacing

        start_x = max(10, (SCREEN_WIDTH - total_width) // 2)

        # 确保有伙伴才创建按钮，并修复索引问题
        button_index = 0
        for i, partner in enumerate(selected_partners):
            if partner and hasattr(partner, 'is_alive') and partner.is_alive:
                button_x = start_x + button_index * (button_width + spacing)
                button_y = SCREEN_HEIGHT - button_height - 15  # 距离底部15像素

                # 确保按钮不超出屏幕右边界
                if button_x + button_width > SCREEN_WIDTH - 10:
                    button_x = SCREEN_WIDTH - button_width - 10

                button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                character_buttons.append((button_rect, partner, i))
                character_y_offsets.append(0)

                # 确保伙伴有rect属性
                if not hasattr(partner, 'rect'):
                    partner.rect = button_rect.copy()

                button_index += 1

        logging.info(f"Created {len(character_buttons)} character buttons")

        # 添加技能按钮
        skill_buttons = []
        if selected_attacker:
            skill_x = SCREEN_WIDTH // 2 - 150
            normal_attack_button = pygame.Rect(skill_x, SCREEN_HEIGHT - 220, 140, 40)
            skill_buttons.append((normal_attack_button, "普通攻击", 0))

            special_skill_button = pygame.Rect(skill_x + 160, SCREEN_HEIGHT - 220, 140, 40)
            if selected_attacker.npc_type == "duck_friend_animation":
                skill_name = "治疗"
            elif selected_attacker.npc_type == "bat_animation":
                skill_name = "斩击"
            elif selected_attacker.npc_type == "good_boy_animation":
                skill_name = "嘲讽"
            else:
                skill_name = "治疗"
            skill_buttons.append((special_skill_button, skill_name, 5 if selected_attacker.npc_type else 6))

        # 战斗主循环
        clock = pygame.time.Clock()
        battle_running = True

        # BOSS大招预警标志
        boss_special_warning = False

        # 第一回合标记
        first_player_turn = True
        last_click_time = 0
        last_clicked_partner = None

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
                    # 触发BOSS死亡动画
                    if hasattr(boss, 'start_death_animation') and not getattr(boss, 'is_dying', False):
                        boss.start_death_animation()
                        logging.info("BOSS death animation triggered")

                    # 如果死亡动画播放完成或没有死亡动画，结束战斗
                    if not hasattr(boss, 'death_animation_frames') or not boss.death_animation_frames or getattr(boss, 'death_animation_finished', False):
                        battle_end = True
                        battle_victory = True
                        break

                # 检查玩家是否失败（所有伙伴都失去战斗能力）
                if all(not p.is_alive for p in selected_partners if p):
                    battle_end = True
                    battle_victory = False
                    break

                # 绘制背景
                if background_image:
                    screen.blit(background_image, (0, 0))
                else:
                    screen.fill(WHITE)

                # 安全绘制BOSS血条 - 扩展到接近全屏宽度，红色背景
                try:
                    boss_hp_ratio = max(0, min(boss.hp / boss.max_hp, 1.0))
                    healthbar_width = SCREEN_WIDTH - 40  # 接近全屏宽度，左右各留20像素
                    healthbar_x = 20

                    # 红色背景血条
                    pygame.draw.rect(screen, (200, 0, 0), (healthbar_x, 20, healthbar_width, 25))
                    # 更深红色的当前血量
                    pygame.draw.rect(screen, (120, 0, 0), (healthbar_x, 20, int(healthbar_width * boss_hp_ratio), 25))
                    # 黑色边框
                    pygame.draw.rect(screen, BLACK, (healthbar_x, 20, healthbar_width, 25), 2)

                    # 在血条中间显示HP值
                    hp_text = pygame.font.SysFont("SimHei", 18).render(f"{boss.hp}/{boss.max_hp}", True, WHITE)
                    hp_text_rect = hp_text.get_rect(center=(SCREEN_WIDTH // 2, 32))
                    screen.blit(hp_text, hp_text_rect)

                    # 显示BOSS技能点系统
                    if hasattr(boss, 'special_attack_cooldown') and hasattr(boss, 'turn_counter'):
                        # 计算当前技能点数（每回合增加1点，最多3点）
                        current_skill_points = min(3, boss.turn_counter % boss.special_attack_cooldown)
                        if boss.turn_counter > 0 and boss.turn_counter % boss.special_attack_cooldown == 0:
                            current_skill_points = 3  # 大招回合显示满点

                        # 绘制技能点图标
                        skill_point_size = 16
                        skill_point_spacing = 20
                        start_x = SCREEN_WIDTH // 2 - (3 * skill_point_spacing) // 2
                        skill_point_y = 40

                        for i in range(3):
                            point_x = start_x + i * skill_point_spacing

                            # 尝试加载技能点图标
                            try:
                                if i < current_skill_points:
                                    # 激活的技能点
                                    icon_path = os.path.join(ASSETS_DIR, "skill_point_on.gif")
                                    if os.path.exists(icon_path):
                                        icon = pygame.image.load(icon_path)
                                        icon = pygame.transform.scale(icon, (skill_point_size, skill_point_size))
                                        screen.blit(icon, (point_x, skill_point_y))
                                    else:
                                        # 备用：黄色圆点
                                        pygame.draw.circle(screen, (255, 255, 0), (point_x + skill_point_size//2, skill_point_y + skill_point_size//2), skill_point_size//2)
                                else:
                                    # 未激活的技能点
                                    icon_path = os.path.join(ASSETS_DIR, "skill_point_off.gif")
                                    if os.path.exists(icon_path):
                                        icon = pygame.image.load(icon_path)
                                        icon = pygame.transform.scale(icon, (skill_point_size, skill_point_size))
                                        screen.blit(icon, (point_x, skill_point_y))
                                    else:
                                        # 备用：灰色圆点
                                        pygame.draw.circle(screen, (128, 128, 128), (point_x + skill_point_size//2, skill_point_y + skill_point_size//2), skill_point_size//2)
                            except Exception as e:
                                # 如果图标加载失败，使用备用绘制
                                if i < current_skill_points:
                                    pygame.draw.circle(screen, (255, 255, 0), (point_x + skill_point_size//2, skill_point_y + skill_point_size//2), skill_point_size//2)
                                else:
                                    pygame.draw.circle(screen, (128, 128, 128), (point_x + skill_point_size//2, skill_point_y + skill_point_size//2), skill_point_size//2)

                        # 如果技能点满了，显示警告
                        if current_skill_points >= 3:
                            warning_time = current_time % 1000  # 1秒周期
                            warning_alpha = int(128 + 127 * math.sin(warning_time / 1000.0 * 2 * math.pi))  # 128-255之间

                            special_text = font.render("BOSS即将释放大招！", True, (255, warning_alpha // 2, 0))
                            special_text_rect = special_text.get_rect(center=(SCREEN_WIDTH // 2, 70))
                            screen.blit(special_text, special_text_rect)

                except Exception as e:
                    logging.error(f"Error drawing boss HP bar: {e}")
                    # 绘制简化版血条
                    pygame.draw.rect(screen, RED, (SCREEN_WIDTH // 2 - 100, 20, 200, 20))
                    if hasattr(boss, 'hp') and hasattr(boss, 'max_hp') and boss.max_hp > 0:
                        hp_ratio = max(0, min(boss.hp / boss.max_hp, 1.0))
                        pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH // 2 - 100, 20, int(200 * hp_ratio), 20))

                # 绘制BOSS - 使用Boss类的draw方法（支持动画和受击效果）
                try:
                    # 如果BOSS正在播放死亡动画，先清除BOSS区域实现"用完就丢"效果
                    if getattr(boss, 'is_dying', False) and getattr(boss, 'death_animation_frames', []):
                        # 清除BOSS区域的背景，确保每帧完全替换前一帧
                        boss_area = pygame.Rect(SCREEN_WIDTH // 2 - 100, 50, 200, 200)
                        if background_image:
                            # 如果有背景图，用背景图的对应区域填充
                            screen.blit(background_image, boss_area, boss_area)
                        else:
                            # 如果没有背景图，用白色填充
                            pygame.draw.rect(screen, WHITE, boss_area)

                    boss.draw(screen)
                except Exception as e:
                    logging.error(f"Error drawing boss: {e}")
                    # 出错时绘制默认矩形（放大1.5倍）
                    boss_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 50, 300, 300)
                    pygame.draw.rect(screen, (0, 0, 0), boss_rect)

                # 绘制所有角色按钮 - 修复版
                small_font = pygame.font.SysFont("SimHei", 16)
                for btn_idx, (button_rect, partner, partner_index) in enumerate(character_buttons):
                    if partner and hasattr(partner, 'is_alive') and partner.is_alive:
                        # 应用Y轴动画效果，添加边界检查 - 重要修复
                        target_y_offset = -20 if selected_attacker == partner else 0

                        # 确保索引在有效范围内
                        if btn_idx < len(character_y_offsets):
                            character_y_offsets[btn_idx] += (target_y_offset - character_y_offsets[btn_idx]) * 0.5  # 加快动画速度
                            actual_y_offset = character_y_offsets[btn_idx]
                        else:
                            actual_y_offset = target_y_offset

                        actual_rect = button_rect.copy()
                        actual_rect.y += actual_y_offset

                        # 绘制角色选择按钮背景
                        bg_color = (220, 220, 255) if selected_attacker == partner else (200, 200, 200)
                        pygame.draw.rect(screen, bg_color, actual_rect)
                        pygame.draw.rect(screen, BLACK, actual_rect, 2)

                        # 在按钮中绘制角色图像 - 支持受击变红效果
                        image_x = actual_rect.x + (button_width - 70) // 2
                        image_y = actual_rect.y + 5

                        # 检查是否有动画帧
                        if hasattr(partner, 'gif_frames') and partner.gif_frames:
                            # 更新动画帧
                            current_time = pygame.time.get_ticks()
                            if current_time - partner.last_frame_update >= partner.frame_time:
                                partner.current_frame = (partner.current_frame + 1) % len(partner.gif_frames)
                                partner.last_frame_update = current_time

                            # 缩放当前动画帧
                            scaled_image = pygame.transform.scale(partner.gif_frames[partner.current_frame], (70, 70))
                        elif partner.image:
                            scaled_image = pygame.transform.scale(partner.image, (70, 70))
                        else:
                            scaled_image = None

                        if scaled_image:
                            # 检查是否处于受击状态
                            if hasattr(partner, 'hit_effect_active') and partner.hit_effect_active:
                                # 创建红色滤镜效果
                                red_intensity = int(180 * getattr(partner, 'hit_effect_progress', 1.0))  # 最大180的红色强度

                                # 创建红色覆盖层
                                red_overlay = pygame.Surface((70, 70), pygame.SRCALPHA)
                                red_overlay.fill((255, 0, 0, red_intensity))

                                # 先绘制原图像
                                screen.blit(scaled_image, (image_x, image_y))
                                # 再绘制红色覆盖层
                                screen.blit(red_overlay, (image_x, image_y))
                            else:
                                # 正常绘制
                                screen.blit(scaled_image, (image_x, image_y))
                        else:
                            # 没有图像时的处理
                            img_rect = pygame.Rect(image_x, image_y, 70, 70)

                            # 检查受击状态
                            if hasattr(partner, 'hit_effect_active') and partner.hit_effect_active:
                                # 受击时显示更红的颜色
                                red_intensity = getattr(partner, 'hit_effect_progress', 1.0)
                                hit_color = (
                                    min(255, getattr(partner, 'color', (100, 100, 100))[0] + int(100 * red_intensity)),
                                    max(0, getattr(partner, 'color', (100, 100, 100))[1] - int(50 * red_intensity)),
                                    max(0, getattr(partner, 'color', (100, 100, 100))[2] - int(50 * red_intensity))
                                )
                                pygame.draw.rect(screen, hit_color, img_rect)
                            else:
                                # 正常颜色
                                default_color = getattr(partner, 'color', (100, 100, 100))
                                pygame.draw.rect(screen, default_color, img_rect)

                        # 显示角色信息
                        partner_info = f"{partner.index}"
                        if hasattr(partner, 'npc_type') and partner.npc_type:
                            partner_info += f" ({partner.npc_type})"

                        # 使用小号字体显示信息
                        info_text_surface = small_font.render(partner_info, True, BLACK)
                        screen.blit(info_text_surface, (actual_rect.x + 5, actual_rect.y + 80))

                        # 绘制角色的HP和MP条 - 使用utils.py的draw_progress_bar精确对齐
                        from utils import draw_progress_bar, draw_shield_bar

                        # 计算条形图位置和大小，确保在UI区域内
                        bar_width = button_width - 8  # 留出4像素边距
                        bar_height = 6  # 稍微增加高度以便显示
                        bar_x = actual_rect.x + 4

                        # HP条
                        hp_y = actual_rect.y + button_height - 35
                        draw_progress_bar(
                            screen, bar_x, hp_y, bar_width, bar_height,
                            int(partner.hp), int(partner.max_hp),
                            bg_color=RED, fg_color=GREEN, border_color=BLACK,
                            border_width=1, show_text=False
                        )

                        # HP数值显示
                        tiny_font = pygame.font.SysFont("SimHei", 10)
                        hp_text = tiny_font.render(f"HP:{int(partner.hp)}/{int(partner.max_hp)}", True, BLACK)
                        screen.blit(hp_text, (bar_x, hp_y - 12))

                        # MP条
                        mp_y = actual_rect.y + button_height - 25
                        draw_progress_bar(
                            screen, bar_x, mp_y, bar_width, bar_height,
                            int(partner.mp), int(partner.max_mp),
                            bg_color=(100, 100, 100), fg_color=BLUE, border_color=BLACK,
                            border_width=1, show_text=False
                        )

                        # MP数值显示
                        mp_text = tiny_font.render(f"MP:{int(partner.mp)}/{int(partner.max_mp)}", True, BLACK)
                        screen.blit(mp_text, (bar_x, mp_y + bar_height + 2))

                        # 绘制护盾条（如果角色有护盾）- 使用utils.py的draw_shield_bar
                        if hasattr(partner, 'shield_active') and partner.shield_active and hasattr(partner, 'shield_hp') and partner.shield_hp > 0:
                            shield_y = actual_rect.y + button_height - 15
                            try:
                                draw_shield_bar(
                                    screen, bar_x, shield_y, bar_width, bar_height,
                                    int(partner.shield_hp), getattr(partner, 'max_shield_hp', 30),
                                    tiny_font
                                )
                            except Exception as e:
                                error_logger.error(f"Error drawing shield bar: {e}")
                                # 备用护盾条绘制
                                draw_progress_bar(
                                    screen, bar_x, shield_y, bar_width, bar_height,
                                    int(partner.shield_hp), getattr(partner, 'max_shield_hp', 30),
                                    bg_color=(80, 80, 80), fg_color=YELLOW, border_color=BLACK,
                                    border_width=1, show_text=False
                                )

                        # 绘制角色状态效果 - 新增
                        try:
                            draw_character_status_effects(screen, partner, image_x, image_y, 70, 70)
                        except Exception as e:
                            error_logger.error(f"Error drawing character status effects: {e}")

                # 更新和绘制所有特效 - 在角色绘制之后，UI元素之前
                try:
                    # 更新战斗特效
                    for effect in active_effects[:]:
                        effect.update()
                        if not effect.active:
                            active_effects.remove(effect)

                    # 更新粒子特效
                    for particle in active_particles[:]:
                        particle.update()
                        if not particle.active:
                            active_particles.remove(particle)

                    # 更新视觉特效
                    for effect in visual_effects[:]:
                        effect.update()
                        if not effect.active:
                            visual_effects.remove(effect)

                    # 更新持续特效
                    for target, effect in persistent_effects[:]:
                        effect.update()
                        # 检查目标状态，如果状态效果消失则移除特效
                        # 护盾特效：当护盾不活跃或护盾值为0时移除
                        if (effect.effect_type == "shield" and
                            (not getattr(target, 'shield_active', False) or
                             getattr(target, 'shield_hp', 0) <= 0)):
                            remove_persistent_effect(target, "shield")
                        elif effect.effect_type == "bless" and not getattr(target, 'blessed', False):
                            remove_persistent_effect(target, "bless")
                        elif effect.effect_type == "reflect" and not getattr(target, 'reflect_active', False):
                            remove_persistent_effect(target, "reflect")

                    # 为有状态效果但没有持续特效的角色添加特效
                    for button_rect, partner, _ in character_buttons:
                        if partner and partner.is_alive:
                            # 检查护盾状态 - 只有护盾值大于0时才显示特效
                            if (getattr(partner, 'shield_active', False) and
                                getattr(partner, 'shield_hp', 0) > 0):
                                # 检查是否已有护盾特效
                                has_shield_effect = any(eff_target == partner and eff.effect_type == "shield"
                                                      for eff_target, eff in persistent_effects)
                                if not has_shield_effect:
                                    create_visual_effect("shield", partner, persistent=True)

                            # 检查祝福状态
                            if getattr(partner, 'blessed', False):
                                # 检查是否已有祝福特效
                                has_bless_effect = any(eff_target == partner and eff.effect_type == "bless"
                                                     for eff_target, eff in persistent_effects)
                                if not has_bless_effect:
                                    create_visual_effect("bless", partner, persistent=True)

                            # 检查反射状态
                            if getattr(partner, 'reflect_active', False):
                                # 检查是否已有反射特效
                                has_reflect_effect = any(eff_target == partner and eff.effect_type == "reflect"
                                                       for eff_target, eff in persistent_effects)
                                if not has_reflect_effect:
                                    create_visual_effect("reflect", partner, persistent=True)

                    # 绘制战斗特效
                    for effect in active_effects:
                        effect.draw(screen)

                    # 绘制粒子特效
                    for particle in active_particles:
                        particle.draw(screen)

                    # 绘制视觉特效
                    for effect in visual_effects:
                        effect.draw(screen)

                    # 绘制持续特效
                    for target, effect in persistent_effects:
                        effect.draw(screen)

                except Exception as e:
                    error_logger.error(f"Error updating/drawing effects: {e}")

                # 骰子阶段 - 优化为类似于NPC交互的骰子系统
                if state == "roll_dice":
                    try:
                        # 绘制暗色半透明背景
                        dark_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                        dark_background.set_alpha(150)
                        dark_background.fill((0, 0, 0))
                        screen.blit(dark_background, (0, 0))

                        # 绘制骰子对话框
                        background = pygame.Surface((500, 250))
                        background.set_alpha(230)
                        background.fill((255, 255, 255))
                        screen.blit(background, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 125))

                        # 标题
                        title_text = font.render("战斗开始 - 决定先手", True, (200, 0, 0))
                        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
                        screen.blit(title_text, title_rect)

                        # 分隔线
                        pygame.draw.line(screen, BLACK,
                                        (SCREEN_WIDTH // 2 - 230, SCREEN_HEIGHT // 2 - 75),
                                        (SCREEN_WIDTH // 2 + 230, SCREEN_HEIGHT // 2 - 75), 1)

                        if dice_state == "showing_condition":
                            # 显示规则和提示
                            rule_text = font.render("骰子点数大的一方先手", True, BLACK)
                            rule_rect = rule_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
                            screen.blit(rule_text, rule_rect)

                            # 按钮
                            button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
                            pygame.draw.rect(screen, (100, 150, 255), button_rect)
                            pygame.draw.rect(screen, BLACK, button_rect, 2)
                            button_text = font.render("投掷骰子", True, BLACK)
                            button_text_rect = button_text.get_rect(center=button_rect.center)
                            screen.blit(button_text, button_text_rect)

                            # 检测点击或按键
                            pressed = False
                            for event in events_to_process:
                                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                    if button_rect.collidepoint(event.pos):
                                        pressed = True
                                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                                    pressed = True

                            if pressed:
                                dice_state = "animating"
                                dice_animation_start = current_time
                                player_dice = random.randint(1, 6)
                                boss_dice = random.randint(1, 6)
                                logging.info(f"Dice rolled: Player={player_dice}, Boss={boss_dice}")

                        elif dice_state == "animating":
                            if current_time - dice_animation_start < dice_animation_duration:
                                # 动画中
                                if (current_time - dice_animation_start) % 100 < 50:
                                    dice_current_number = random.randint(1, 6)

                                # 显示玩家和BOSS骰子（动画）
                                player_dice_text = font.render("玩家骰子:", True, BLUE)
                                screen.blit(player_dice_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 30))

                                boss_dice_text = font.render("BOSS骰子:", True, RED)
                                screen.blit(boss_dice_text, (SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 30))

                                # 显示骰子图像
                                if dice_current_number in dice_images:
                                    player_dice_img = dice_images[dice_current_number]
                                    boss_dice_img = dice_images[dice_current_number]

                                    screen.blit(player_dice_img, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))
                                    screen.blit(boss_dice_img, (SCREEN_WIDTH // 2 + 40, SCREEN_HEIGHT // 2))
                                else:
                                    # 没有图像就显示文本
                                    player_num = font.render(str(dice_current_number), True, BLUE)
                                    boss_num = font.render(str(dice_current_number), True, RED)

                                    screen.blit(player_num, (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2))
                                    screen.blit(boss_num, (SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT // 2))

                                # 显示正在投掷的提示
                                rolling_text = font.render("正在投掷骰子...", True, BLACK)
                                rolling_rect = rolling_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
                                screen.blit(rolling_text, rolling_rect)
                            else:
                                dice_state = "showing_result"
                                dice_animation_start = current_time

                        elif dice_state == "showing_result":
                            if current_time - dice_animation_start < dice_display_time:
                                # 显示最终结果
                                player_dice_text = font.render("玩家骰子:", True, BLUE)
                                screen.blit(player_dice_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 30))

                                boss_dice_text = font.render("BOSS骰子:", True, RED)
                                screen.blit(boss_dice_text, (SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 30))

                                # 显示最终骰子图像或数值
                                if player_dice in dice_images and boss_dice in dice_images:
                                    player_dice_img = dice_images[player_dice]
                                    boss_dice_img = dice_images[boss_dice]

                                    screen.blit(player_dice_img, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))
                                    screen.blit(boss_dice_img, (SCREEN_WIDTH // 2 + 40, SCREEN_HEIGHT // 2))
                                else:
                                    # 没有图像就显示文本
                                    player_num = font.render(str(player_dice), True, BLUE)
                                    boss_num = font.render(str(boss_dice), True, RED)

                                    screen.blit(player_num, (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2))
                                    screen.blit(boss_num, (SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT // 2))

                                # 显示谁先手
                                player_turn = player_dice >= boss_dice  # 玩家点数大于等于BOSS时玩家先手
                                result_text = font.render(
                                    f"{'玩家' if player_turn else 'BOSS'}先手！",
                                    True,
                                    BLUE if player_turn else RED
                                )
                                result_rect = result_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
                                screen.blit(result_text, result_rect)
                            else:
                                # 骰子阶段结束，进入战斗阶段

                                state = "player_turn" if player_turn else "boss_turn"
                                info_text = "玩家回合开始！" if player_turn else "BOSS回合开始！"
                                info_timer = 120
                                logging.info(f"Turn decided: {'Player' if player_turn else 'Boss'} first")

                        # 强制更新显示
                        pygame.display.update()

                    except Exception as e:
                        logging.error(f"Error in roll_dice state: {e}")
                        logging.error(traceback.format_exc())
                        state = "player_turn"  # 出错时默认玩家先手

                # 玩家回合
                elif state == "player_turn":
                    # 检测回合切换，只在回合刚开始时显示提示
                    if current_turn_state != "player_turn":
                        current_turn_state = "player_turn"
                        turn_notification_shown = False  # 重置提示状态
                        turn_notification_finished = False  # 重置完成状态

                    # 启动回合提示（仅在回合刚开始且未显示过时）
                    if not turn_notification_shown and not turn_notification_active:
                        turn_notification_active = True
                        turn_notification_start_time = current_time
                        turn_notification_text = "你的回合"
                        turn_border_color = (0, 0, 255)  # 蓝色边框
                        turn_notification_shown = True  # 标记已显示
                        logging.info("Player turn notification started")
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
                        # 删除冗余的"点击角色选择攻击者"提示文字，简化UI

                        # 检测鼠标点击选择角色（单击切换选择） - 移到外面，不受selected_attacker限制
                        for event in events_to_process:
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                mouse_pos = event.pos
                                click_time = current_time

                                # 优先检查是否在目标选择模式
                                if target_selection:
                                    # 目标选择模式：点击任意存活角色都是目标
                                    for button_rect, partner, idx in character_buttons:
                                        adjusted_rect = button_rect.copy()
                                        if idx < len(character_y_offsets):
                                            adjusted_rect.y += character_y_offsets[idx]

                                        if adjusted_rect.collidepoint(mouse_pos) and partner.is_alive:
                                            # 执行技能逻辑
                                            heal_target = partner

                                            try:
                                                # 执行技能 - 使用新的技能系统
                                                if selected_attacker.assigned_skill == "substitute":
                                                    result_text, damage, effect_type = selected_attacker.use_skill(
                                                        target=heal_target, all_allies=selected_partners,
                                                        boss=boss, substitute_target=heal_target
                                                    )
                                                else:
                                                    result_text, damage, effect_type = selected_attacker.use_skill(
                                                        target=heal_target, all_allies=selected_partners, boss=boss
                                                    )
                                                info_text = result_text

                                                # 添加相应特效 - 使用新的视觉特效系统
                                                if effect_type in ["heal", "bless", "substitute"]:
                                                    create_visual_effect(effect_type, heal_target)
                                                    create_safe_effect("shake", heal_target, f"{effect_type}_shake")
                                                elif effect_type == "claw":
                                                    create_visual_effect("claw", boss)
                                                    create_safe_effect("shake", boss, "boss_shake")

                                                # 重置选择状态
                                                selected_attacker = None
                                                selected_skill = None
                                                skill_buttons = []
                                                target_selection = False
                                                heal_target = None
                                                info_timer = 120

                                                # 检查胜利条件
                                                if boss.hp <= 0:
                                                    # 触发BOSS死亡动画
                                                    if hasattr(boss, 'start_death_animation') and not getattr(boss, 'is_dying', False):
                                                        boss.start_death_animation()
                                                        logging.info("BOSS death animation triggered")

                                                    # 如果死亡动画播放完成或没有死亡动画，进入胜利状态
                                                    if not hasattr(boss, 'death_animation_frames') or not boss.death_animation_frames or getattr(boss, 'death_animation_finished', False):
                                                        state = "victory"
                                                        battle_end = True
                                                        battle_victory = True
                                                    # 否则继续当前状态，让动画播放
                                                else:
                                                    turn_notification_active = False
                                                    state = "boss_turn"

                                            except Exception as e:
                                                error_logger.error(f"Error executing targeted skill: {e}")
                                                logging.error(f"Error executing targeted skill: {e}")
                                                info_text = "技能执行失败"
                                                info_timer = 60
                                                # 重置技能选择但保留角色选择
                                                selected_skill = None
                                                target_selection = False
                                                heal_target = None
                                            break
                                else:
                                    # 正常的角色选择/取消选择模式
                                    for button_rect, partner, idx in character_buttons:
                                        adjusted_rect = button_rect.copy()
                                        if idx < len(character_y_offsets):
                                            adjusted_rect.y += character_y_offsets[idx]

                                        if adjusted_rect.collidepoint(mouse_pos) and partner.is_alive:
                                            # 单击选择/取消逻辑：点击同一角色取消选择
                                            if selected_attacker == partner:
                                                # 取消选择逻辑（保持不变）
                                                selected_attacker = None
                                                selected_skill = None
                                                skill_buttons = []
                                                target_selection = False
                                                heal_target = None
                                                first_player_turn = False

                                                info_text = f"已取消选择角色 {partner.index}"
                                                info_timer = 60
                                                logging.info(f"Deselected attacker: Partner {partner.index} - smooth slide back")
                                            else:
                                                # 选择新角色逻辑（保持不变）
                                                selected_attacker = partner

                                                first_player_turn = False
                                                info_text = f"选中角色 {partner.index}"
                                                info_timer = 60
                                                logging.info(f"Selected attacker: Partner {selected_attacker.index} - smooth slide up")

                                                # 创建技能按钮 - 使用新的技能分配系统
                                                skill_buttons = []
                                                skill_x = SCREEN_WIDTH // 2 - 150

                                                # 普通攻击按钮
                                                normal_attack_button = pygame.Rect(skill_x, SCREEN_HEIGHT - 220, 120, 50)
                                                skill_buttons.append((normal_attack_button, "普通攻击", 0, "normal_attack", None))

                                                # 根据角色分配的技能创建按钮
                                                if hasattr(partner, 'assigned_skill') and partner.assigned_skill:
                                                    skill_info = partner.get_skill_info()
                                                    skill_button = pygame.Rect(skill_x + 130, SCREEN_HEIGHT - 220, 120, 50)
                                                    skill_buttons.append((
                                                        skill_button,
                                                        skill_info["name"],
                                                        skill_info["mp_cost"],
                                                        partner.assigned_skill,
                                                        skill_info["icon"]
                                                    ))

                                            last_click_time = click_time
                                            last_clicked_partner = partner
                                            break

                                # 如果点击了角色，跳出事件循环
                                if last_click_time == click_time or target_selection:
                                    break

                        else:
                            # 已选择攻击者，显示可用技能
                            if not selected_skill:

                                # 绘制技能按钮 - 使用增强的UI系统
                                button_font = pygame.font.SysFont("SimHei", 14)
                                for button_rect, skill_name, mp_cost, skill_type, icon_name in skill_buttons:
                                    try:
                                        draw_skill_button_with_icon(
                                            screen, button_rect, skill_name, icon_name or "default_icon.png",
                                            mp_cost, button_font, selected_attacker.mp
                                        )
                                    except Exception as e:
                                        error_logger.error(f"Error drawing skill button: {e}")
                                        # 绘制简单按钮作为备用
                                        button_color = (200, 200, 255) if selected_attacker.mp >= mp_cost else (150, 150, 150)
                                        pygame.draw.rect(screen, button_color, button_rect)
                                        pygame.draw.rect(screen, BLACK, button_rect, 2)
                                        text = button_font.render(skill_name, True, BLACK)
                                        screen.blit(text, (button_rect.x + 5, button_rect.y + 5))

                                # 检测技能按钮点击 - 使用新的技能系统
                                for event in events_to_process:
                                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                        mouse_pos = event.pos
                                        for button_rect, skill_name, mp_cost, skill_type, icon_name in skill_buttons:
                                            if button_rect.collidepoint(mouse_pos):
                                                if mp_cost == 0 or selected_attacker.mp >= mp_cost:  # 检查MP是否足够
                                                    selected_skill = skill_name

                                                    # 根据技能类型决定是否需要目标选择
                                                    if skill_type == "normal_attack":  # 普通攻击
                                                        # 执行普通攻击
                                                        damage, _ = selected_attacker.normal_attack(boss, 0, 0)
                                                        selected_attacker.mp = min(selected_attacker.max_mp, selected_attacker.mp + 3)
                                                        info_text = f"{selected_attacker.index} 普通攻击! 造成 {damage} 伤害! MP +3"

                                                        # 添加攻击特效 - 使用新的视觉特效系统
                                                        create_visual_effect("claw", boss)
                                                        create_safe_effect("shake", boss, "boss_shake")

                                                        # 重置选择并检查胜利
                                                        selected_attacker = None
                                                        selected_skill = None
                                                        skill_buttons = []
                                                        info_timer = 120

                                                        if boss.hp <= 0:
                                                            # 触发BOSS死亡动画
                                                            if hasattr(boss, 'start_death_animation') and not getattr(boss, 'is_dying', False):
                                                                boss.start_death_animation()
                                                                logging.info("BOSS death animation triggered")

                                                            # 如果死亡动画播放完成或没有死亡动画，进入胜利状态
                                                            if not hasattr(boss, 'death_animation_frames') or not boss.death_animation_frames or getattr(boss, 'death_animation_finished', False):
                                                                state = "victory"
                                                                battle_end = True
                                                                battle_victory = True
                                                            # 否则继续当前状态，让动画播放
                                                        else:
                                                            turn_notification_active = False
                                                            state = "boss_turn"

                                                    elif skill_type in ["heal_target", "bless", "substitute"]:  # 需要目标选择的技能
                                                        target_selection = True

                                                    else:  # 直接执行的技能
                                                        # 执行技能
                                                        try:
                                                            result_text, damage, effect_type = selected_attacker.use_skill(
                                                                boss=boss, all_allies=selected_partners
                                                            )
                                                            info_text = result_text

                                                            # 添加相应特效 - 使用新的视觉特效系统
                                                            if effect_type == "claw":
                                                                create_visual_effect("claw", boss)
                                                                create_safe_effect("shake", boss, "boss_shake")
                                                            elif effect_type == "heal":
                                                                # 检查是否为群体治疗
                                                                if selected_attacker.assigned_skill == "heal_all":
                                                                    # 为所有活着的角色创建群体治疗特效，覆盖在角色图像上层
                                                                    for ally in selected_partners:
                                                                        if ally and ally.is_alive:
                                                                            # 获取角色在UI中的位置
                                                                            ally_pos = None
                                                                            for button_rect, partner, _ in character_buttons:
                                                                                if partner == ally:
                                                                                    ally_pos = (button_rect.centerx, button_rect.centery - 20)  # 稍微上移以覆盖角色图像
                                                                                    break
                                                                            if ally_pos:
                                                                                effect = VisualEffect("heal_all", ally_pos, duration=2000)
                                                                                visual_effects.append(effect)
                                                                                error_logger.info(f"Created heal_all effect for ally at {ally_pos}")
                                                                else:
                                                                    # 单体治疗特效
                                                                    create_visual_effect(effect_type, selected_attacker)
                                                            elif effect_type in ["shield", "reflect"]:
                                                                create_visual_effect(effect_type, selected_attacker)
                                                                # 对于持续技能，创建持续特效
                                                                create_visual_effect(effect_type, selected_attacker, persistent=True)
                                                            elif effect_type in ["bless", "substitute"]:
                                                                create_visual_effect(effect_type, selected_attacker)

                                                            # 重置选择并检查胜利
                                                            selected_attacker = None
                                                            selected_skill = None
                                                            skill_buttons = []
                                                            info_timer = 120

                                                            if boss.hp <= 0:
                                                                # 触发BOSS死亡动画
                                                                if hasattr(boss, 'start_death_animation') and not getattr(boss, 'is_dying', False):
                                                                    boss.start_death_animation()
                                                                    logging.info("BOSS death animation triggered")

                                                                # 如果死亡动画播放完成或没有死亡动画，进入胜利状态
                                                                if not hasattr(boss, 'death_animation_frames') or not boss.death_animation_frames or getattr(boss, 'death_animation_finished', False):
                                                                    state = "victory"
                                                                    battle_end = True
                                                                    battle_victory = True
                                                                # 否则继续当前状态，让动画播放
                                                            else:
                                                                turn_notification_active = False
                                                                state = "boss_turn"

                                                        except Exception as e:
                                                            error_logger.error(f"Error executing skill: {e}")
                                                            logging.error(f"Error executing skill: {e}")
                                                            info_text = "技能执行失败"
                                                            info_timer = 60
                                                else:
                                                    info_text = "MP不足!"
                                                    info_timer = 60

                            # 目标选择提示
                            elif target_selection:
                                # 1. 屏幕中央显示大字提示
                                healing_prompt_text = "请选择目标角色"

                                # 创建半透明背景
                                prompt_bg = pygame.Surface((400, 60), pygame.SRCALPHA)
                                prompt_bg.fill((0, 0, 0, 150))  # 半透明黑色背景
                                prompt_bg_rect = prompt_bg.get_rect(center=(SCREEN_WIDTH // 2, 150))
                                screen.blit(prompt_bg, prompt_bg_rect)

                                # 绘制边框
                                pygame.draw.rect(screen, (255, 255, 255), prompt_bg_rect, 2)

                                # 绘制主提示文字（白色，带黑色描边）
                                healing_font = pygame.font.SysFont("SimHei", 24)

                                # 黑色描边
                                outline_width = 2
                                for dx in [-outline_width, 0, outline_width]:
                                    for dy in [-outline_width, 0, outline_width]:
                                        if dx != 0 or dy != 0:
                                            outline_surface = healing_font.render(healing_prompt_text, True, (0, 0, 0))
                                            outline_x = SCREEN_WIDTH // 2 - outline_surface.get_width() // 2 + dx
                                            outline_y = 150 - outline_surface.get_height() // 2 + dy
                                            screen.blit(outline_surface, (outline_x, outline_y))

                                # 白色主文字
                                main_text = healing_font.render(healing_prompt_text, True, (255, 255, 255))
                                main_x = SCREEN_WIDTH // 2 - main_text.get_width() // 2
                                main_y = 150 - main_text.get_height() // 2
                                screen.blit(main_text, (main_x, main_y))

                                # 2. 在每个角色上方显示"点击治疗"小字提示
                                for btn_idx, (button_rect, partner, partner_index) in enumerate(character_buttons):
                                    if partner and partner.is_alive:
                                        # 获取角色按钮的实际位置
                                        actual_rect = button_rect.copy()
                                        if btn_idx < len(character_y_offsets):
                                            actual_rect.y += character_y_offsets[btn_idx]

                                        # 在角色图像上方显示"点击选择"文字
                                        heal_text = "点击选择"
                                        text_width = pygame.font.SysFont("SimHei", 16).size(heal_text)[0]
                                        text_x = actual_rect.centerx - text_width // 2  # 精确居中
                                        text_y = actual_rect.y - 25

                                        # 绘制黑色描边
                                        outline_width = 1
                                        outline_surface = pygame.font.SysFont("SimHei", 16).render(heal_text, True, BLACK)
                                        for dx in [-outline_width, 0, outline_width]:
                                            for dy in [-outline_width, 0, outline_width]:
                                                if dx != 0 or dy != 0:
                                                    screen.blit(outline_surface, (text_x + dx, text_y + dy))

                                        # 绘制白色主文字
                                        heal_surface = pygame.font.SysFont("SimHei", 16).render(heal_text, True, WHITE)
                                        screen.blit(heal_surface, (text_x, text_y))

                                # 3. 可选：为可治疗的角色添加绿色发光边框效果
                                for btn_idx, (button_rect, partner, partner_index) in enumerate(character_buttons):
                                    if partner and partner.is_alive:
                                        actual_rect = button_rect.copy()
                                        if btn_idx < len(character_y_offsets):
                                            actual_rect.y += character_y_offsets[btn_idx]

                                        # 绘制绿色发光边框（目标可选提示）
                                        glow_time = current_time % 2000  # 2秒周期
                                        glow_intensity = (math.sin(glow_time / 2000.0 * 2 * math.pi) + 1) / 2  # 0-1之间
                                        glow_alpha = int(100 + glow_intensity * 100)  # 100-200之间

                                        # 创建发光边框
                                        glow_color = (0, 255, 0, glow_alpha)  # 绿色发光
                                        glow_surface = pygame.Surface((actual_rect.width + 6, actual_rect.height + 6), pygame.SRCALPHA)
                                        pygame.draw.rect(glow_surface, glow_color, (0, 0, actual_rect.width + 6, actual_rect.height + 6), 3)
                                        screen.blit(glow_surface, (actual_rect.x - 3, actual_rect.y - 3))

                    except Exception as e:
                        logging.error(f"Error rendering player turn: {e}")
                        logging.error(traceback.format_exc())

                # BOSS回合 - 修复版
                elif state == "boss_turn":
                    # 检测回合切换，只在回合刚开始时显示提示 - 修改版
                    if current_turn_state != "boss_turn":
                        current_turn_state = "boss_turn"
                        turn_notification_shown = False  # 重置提示状态
                        turn_notification_finished = False  # 重置完成状态

                    # 启动回合提示（仅在回合刚开始且未显示过时）
                    if not turn_notification_shown and not turn_notification_active and not turn_notification_finished:
                        turn_notification_active = True
                        turn_notification_start_time = current_time
                        turn_notification_text = "BOSS回合"
                        turn_border_color = (255, 0, 0)  # 红色边框
                        turn_notification_shown = True  # 标记已显示
                        logging.info("Boss turn notification started")

                    # 延迟一段时间，让玩家看到"BOSS回合"提示
                    if info_timer <= 0:
                        # 简单AI: BOSS随机选择一个角色攻击
                        alive_partners = [p for p in selected_partners if p and p.is_alive]
                        if alive_partners:
                            # 调用BOSS的use_skill方法，这会触发攻击动画
                            skill_result, affected_targets = boss.use_skill(alive_partners)

                            # 从技能结果中提取信息
                            info_text = skill_result

                            # 检查是否是boss大招回合，添加属性检查 - 重要修复
                            using_special = False
                            if hasattr(boss, 'turn_counter') and hasattr(boss, 'special_attack_cooldown'):
                                using_special = (boss.turn_counter - 1) % boss.special_attack_cooldown == 0  # turn_counter已经在use_skill中增加了

                            # 如果use_skill没有返回具体的目标，使用随机目标
                            if not affected_targets:
                                target = random.choice(alive_partners)
                                affected_targets = [target]
                            else:
                                target = affected_targets[0]  # 使用第一个受影响的目标

                            # 确定伤害值
                            if using_special:
                                damage = round(getattr(boss, 'special_attack_damage', 50))
                                damage_text = "大招"
                            else:
                                damage = boss.attack_power
                                damage_text = "普通攻击"

                            # 注意：实际的伤害计算和应用已经在boss.use_skill()中处理了
                            # 这里主要处理额外的特效和嘲讽逻辑

                            # 检查嘲讽效果（如果需要的话）
                            taunt_partners = [p for p in selected_partners if
                                            p and p.is_alive and hasattr(p, 'taunt_active') and p.taunt_active]

                            # 如果有嘲讽效果，可能需要重新选择目标（这取决于boss.use_skill的实现）
                            if taunt_partners and random.random() < 0.6:  # 60%概率攻击嘲讽者
                                target = random.choice(taunt_partners)
                                # 更新info_text以反映嘲讽效果
                                if "攻击了" in info_text:
                                    info_text = info_text.replace("攻击了", f"被嘲讽，攻击了")

                            # 应用实际伤害（如果boss.use_skill没有处理的话）
                            # 注意：这里可能需要根据boss.use_skill的具体实现来调整
                            if damage > 0:
                                # 使用新的伤害处理方法，优先扣除护盾
                                if hasattr(target, 'take_damage'):
                                    target.take_damage(damage)
                                else:
                                    target.hp = max(0, target.hp - damage)

                            # 添加攻击特效 - 使用安全函数，包含粒子特效
                            create_safe_effect("shake", target, "target_shake")

                            # 添加粒子特效 - 修复版
                            try:
                                if hasattr(target, 'rect'):
                                    active_particles.append(ParticleEffect(target.rect, "boss_attack"))
                                else:
                                    logging.warning("Target has no rect for particle effect")
                            except Exception as e:
                                logging.error(f"Error creating particle effect: {e}")

                            # 根据攻击类型添加不同的特效 - 使用新的视觉特效系统
                            if using_special:
                                # 大招特效 - 龙卷风
                                create_visual_effect("tornado", target)
                            else:
                                # 普通攻击 - 爪痕
                                create_visual_effect("claw", target)

                            # 添加通用攻击反馈特效
                            create_visual_effect("particle", target)

                            # 设置信息文本
                            if not info_text:  # 如果没有嘲讽文本
                                info_text = f"BOSS使用{damage_text}攻击了 {target.index}! 造成 {damage} 伤害!"
                            else:
                                info_text += f" 造成 {damage} 伤害!"

                            info_timer = 120

                            # 检查目标是否被击败
                            if target.hp <= 0:
                                target.is_alive = False
                                info_text += f" {target.index} 失去战斗能力!"

                            # 检查是否团队失败
                            if all(not p.is_alive for p in selected_partners if p):
                                state = "defeat"
                                battle_end = True
                                battle_victory = False
                            else:
                                # BOSS回合结束，更新回合计数，添加属性检查
                                if hasattr(boss, 'turn_counter'):
                                    boss.turn_counter += 1
                                else:
                                    boss.turn_counter = 1
                                # 重置回合提示状态
                                turn_notification_active = False
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

                # 显示信息文本 - 修复版
                if info_text and info_timer > 0:
                    info_timer -= 1
                    info_bg = pygame.Surface((600, 40))  # 增加宽度
                    info_bg.set_alpha(200)
                    info_bg.fill((255, 255, 255))
                    screen.blit(info_bg, (SCREEN_WIDTH // 2 - 300, 130))  # 调整位置

                    # 修复文本渲染 - 重要修复
                    try:
                        # 确保info_text是字符串类型
                        text_to_render = str(info_text) if info_text is not None else ""
                        if text_to_render:  # 只有非空字符串才渲染
                            info_render = font.render(text_to_render, True, BLACK)
                            screen.blit(info_render, (SCREEN_WIDTH // 2 - 290, 135))
                    except Exception as e:
                        logging.error(f"Error rendering info text: {e}")
                        # 渲染默认错误信息
                        error_text = font.render("显示信息时出错", True, BLACK)
                        screen.blit(error_text, (SCREEN_WIDTH // 2 - 290, 135))

                # 更新和绘制活跃特效
                for effect in active_effects[:]:
                    effect.update()
                    effect.draw(screen)
                    if not effect.active:
                        active_effects.remove(effect)

                # 更新和绘制粒子特效 - 新增
                for particle in active_particles[:]:
                    particle.update()
                    particle.draw(screen)
                    if not particle.active:
                        active_particles.remove(particle)

                # 绘制回合提示和边框效果 - 居中显示
                if turn_notification_active:
                    elapsed_time = current_time - turn_notification_start_time

                    if elapsed_time < turn_notification_duration:
                        # 计算文本淡入淡出效果
                        if elapsed_time < 1000:  # 第一秒：淡入
                            text_alpha = int(255 * (elapsed_time / 1000))
                        elif elapsed_time < 2000:  # 第二秒：保持
                            text_alpha = 255
                        else:  # 第三秒：淡出
                            text_alpha = int(255 * (1 - (elapsed_time - 2000) / 1000))

                        text_alpha = max(0, min(255, text_alpha))

                        # 居中显示回合提示文本
                        text_surface = large_font.render(turn_notification_text, True, turn_notification_color)
                        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                        text_x, text_y = text_rect.topleft

                        # 创建带透明度的文本
                        text_surface = large_font.render(turn_notification_text, True, turn_notification_color)
                        text_surface.set_alpha(text_alpha)

                        # 绘制黑色描边（8个方向）
                        outline_width = 2
                        outline_surface = large_font.render(turn_notification_text, True, (0, 0, 0))
                        outline_surface.set_alpha(text_alpha)

                        for dx in [-outline_width, 0, outline_width]:
                            for dy in [-outline_width, 0, outline_width]:
                                if dx != 0 or dy != 0:  # 跳过中心位置
                                    screen.blit(outline_surface, (text_x + dx, text_y + dy))

                        # 绘制主文本
                        screen.blit(text_surface, (text_x, text_y))
                    else:
                        # 回合提示完全结束 - 修改
                        turn_notification_active = False
                        turn_notification_finished = True  # 标记为已完成，防止重复显示

                # 新增：整个回合期间的边框持续闪烁效果
                # 只要处于玩家回合或BOSS回合，就显示闪烁边框
                if state in ["player_turn", "boss_turn"]:
                    # 计算平滑的闪烁效果 - 使用sin函数创建丝滑过渡
                    flash_time = current_time % 2000  # 2秒为一个完整周期
                    flash_progress = flash_time / 2000.0  # 0-1之间的进度

                    # 使用sin函数创建平滑的淡入淡出效果
                    border_intensity = (math.sin(flash_progress * 2 * math.pi) + 1) / 2  # 0-1之间

                    # 确保有最小亮度，让边框始终可见
                    border_intensity = 0.3 + border_intensity * 0.7  # 调整到0.3-1.0之间

                    border_width = 5

                    # 绘制多层发光效果（4层，增强模糊效果）
                    glow_layers = [
                        {"offset": 8, "alpha_base": 50},   # 最外层，最淡
                        {"offset": 6, "alpha_base": 100},  # 第二层
                        {"offset": 4, "alpha_base": 150},  # 第三层
                        {"offset": 2, "alpha_base": 200},  # 最内层，最亮
                    ]

                    for layer in glow_layers:
                        offset = layer["offset"]
                        alpha_base = layer["alpha_base"]

                        # 根据闪烁强度调整透明度
                        layer_alpha = int(alpha_base * border_intensity)
                        glow_color = (*turn_border_color, layer_alpha)

                        # 创建发光层Surface
                        glow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

                        # 绘制四边发光
                        pygame.draw.rect(glow_surface, glow_color,
                                    (-offset, -offset, SCREEN_WIDTH + offset*2, border_width + offset*2))  # 上边
                        pygame.draw.rect(glow_surface, glow_color,
                                    (-offset, SCREEN_HEIGHT - border_width - offset, SCREEN_WIDTH + offset*2, border_width + offset*2))  # 下边
                        pygame.draw.rect(glow_surface, glow_color,
                                    (-offset, -offset, border_width + offset*2, SCREEN_HEIGHT + offset*2))  # 左边
                        pygame.draw.rect(glow_surface, glow_color,
                                    (SCREEN_WIDTH - border_width - offset, -offset, border_width + offset*2, SCREEN_HEIGHT + offset*2))  # 右边

                        screen.blit(glow_surface, (0, 0))

                    # 绘制主边框（也带有闪烁效果）
                    main_border_alpha = int(255 * border_intensity)
                    main_border_color = (*turn_border_color, main_border_alpha)

                    # 创建主边框Surface
                    main_border_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

                    pygame.draw.rect(main_border_surface, main_border_color,
                                (0, 0, SCREEN_WIDTH, border_width))  # 上边
                    pygame.draw.rect(main_border_surface, main_border_color,
                                (0, SCREEN_HEIGHT - border_width, SCREEN_WIDTH, border_width))  # 下边
                    pygame.draw.rect(main_border_surface, main_border_color,
                                (0, 0, border_width, SCREEN_HEIGHT))  # 左边
                    pygame.draw.rect(main_border_surface, main_border_color,
                                (SCREEN_WIDTH - border_width, 0, border_width, SCREEN_HEIGHT))  # 右边

                    screen.blit(main_border_surface, (0, 0))


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