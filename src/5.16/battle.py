# battle.py - BOSS战斗系统增强版
import pygame
import random
import logging
import traceback
import os
import math  # 添加数学库，用于特效计算
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, ORANGE
from config import ASSETS_DIR

logging.basicConfig(filename="game_errors.log", level=logging.ERROR)

# 背景图片路径
BATTLE_BACKGROUND_PATH = os.path.join(ASSETS_DIR, "battle_background.png")


# 战斗特效类定义
class BattleEffect:
    """战斗特效类，用于管理战斗中的视觉特效"""
    def __init__(self, effect_type, target, position, duration=3000):
        self.effect_type = effect_type  # 特效类型: "shake", "claw", "heal", "tornado"
        self.target = target  # 特效目标
        self.position = position  # 特效位置
        self.start_time = pygame.time.get_ticks()  # 特效开始时间
        self.duration = duration  # 特效持续时间(毫秒)，默认3秒
        self.active = True  # 特效是否活跃
        self.original_pos = position.copy() if isinstance(position, pygame.Rect) else position  # 保存原始位置
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
            # 确保目标回到原位
            if self.effect_type == "shake" and hasattr(self.target, 'rect'):
                self.target.rect = self.original_pos.copy()
            return
        
        # 更新不同类型的特效
        if self.effect_type == "shake":
            progress = elapsed / self.duration
            
            # 前半段时间震动并后退
            if progress < 0.3:
                # 震动效果
                self.shake_offset = [
                    random.randint(-5, 5),
                    random.randint(-5, 5)
                ]
                
                # 后退效果 - 向反方向移动
                back_offset = 30 * (progress / 0.3)  # 最大后退30像素
                if isinstance(self.target, pygame.Rect):
                    # 如果目标是玩家角色(位于屏幕下方)，向下后退
                    if self.target.y > SCREEN_HEIGHT // 2:
                        self.target.y = self.original_pos.y + back_offset
                    # 如果目标是boss(位于屏幕上方)，向上后退
                    else:
                        self.target.y = self.original_pos.y - back_offset
                elif hasattr(self.target, 'rect'):
                    # 如果目标是玩家角色(位于屏幕下方)，向下后退
                    if self.target.rect.y > SCREEN_HEIGHT // 2:
                        self.target.rect.y = self.original_pos.y + back_offset
                    # 如果目标是boss(位于屏幕上方)，向上后退
                    else:
                        self.target.rect.y = self.original_pos.y - back_offset
            
            # 后半段时间回到原位
            elif progress > 0.5:
                return_progress = min(1.0, (progress - 0.5) / 0.5)
                if isinstance(self.target, pygame.Rect):
                    self.target.x = self.original_pos.x + self.shake_offset[0] * (1 - return_progress)
                    self.target.y = self.original_pos.y + (self.target.y - self.original_pos.y) * (1 - return_progress)
                elif hasattr(self.target, 'rect'):
                    self.target.rect.x = self.original_pos.x + self.shake_offset[0] * (1 - return_progress)
                    self.target.rect.y = self.original_pos.y + (self.target.rect.y - self.original_pos.y) * (1 - return_progress)
    
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
                    # 治疗效果围绕目标
                    effect_rect = effect_img.get_rect(center=target_pos)
                    # 添加一点旋转效果
                    angle = progress * 360
                    rotated_img = pygame.transform.rotate(effect_img, angle)
                    rotated_rect = rotated_img.get_rect(center=target_pos)
                    screen.blit(rotated_img, rotated_rect)
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

        # 初始化BOSS
        boss = enemies[0]

        # 安全地初始化BOSS的HP
        if not hasattr(boss, 'hp') or boss.hp <= 0:
            boss.hp = 500  # 增加BOSS血量
        if not hasattr(boss, 'max_hp') or boss.max_hp <= 0:
            boss.max_hp = 500  # 增加BOSS最大血量

        # 降低BOSS攻击力，更平衡
        boss.attack_power = 33  # 降低BOSS基础攻击力，使得角色能够承受约三次攻击

        # 新增BOSS战斗属性
        boss.turn_counter = 0  # 回合计数器，用于触发大招
        boss.special_attack_cooldown = 3  # 每3回合放一次大招
        boss.special_attack_damage = boss.attack_power * 1.8  # 大招伤害是普通攻击的1.8倍

        logging.info(f"Boss initialized with HP: {boss.hp}/{boss.max_hp}, Attack: {boss.attack_power}")

        # 战斗开始时，所有伙伴MP恢复满
        for partner in selected_partners:
            if partner and partner.is_alive:
                partner.mp = partner.max_mp
                logging.info(f"Partner {partner.index} MP restored to {partner.mp}")

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
        # 添加特效列表
        active_effects = []

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

        # BOSS大招预警标志
        boss_special_warning = False

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

                # 显示当前回合 - 移到左上角
                turn_text = font.render(f"当前回合: {boss.turn_counter + 1}", True, BLACK)
                screen.blit(turn_text, (20, 10))

                # 安全绘制BOSS血条
                try:
                    boss_hp_ratio = max(0, min(boss.hp / boss.max_hp, 1.0))  # 确保比例在0-1之间
                    pygame.draw.rect(screen, RED, (SCREEN_WIDTH // 2 - 100, 20, 200, 20))
                    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH // 2 - 100, 20, int(200 * boss_hp_ratio), 20))
                    
                    # 在血条中间显示HP值
                    hp_text = pygame.font.SysFont("SimHei", 16).render(f"{boss.hp}/{boss.max_hp}", True, BLACK)
                    hp_text_rect = hp_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
                    screen.blit(hp_text, hp_text_rect)
                    
                    # 显示距离BOSS大招的回合数
                    remaining_turns = boss.special_attack_cooldown - (boss.turn_counter % boss.special_attack_cooldown)
                    if boss.turn_counter > 0:
                        remaining_turns = remaining_turns % boss.special_attack_cooldown
                    if remaining_turns == 0:
                        special_text = font.render(f"BOSS即将释放大招！", True, RED)
                    else:
                        special_text = font.render(f"距离BOSS释放大招还有{remaining_turns}回合", True, RED)
                    special_text_rect = special_text.get_rect(center=(SCREEN_WIDTH // 2, 60))
                    screen.blit(special_text, special_text_rect)
                except Exception as e:
                    logging.error(f"Error drawing boss HP bar: {e}")
                
                # 安全绘制BOSS
                try:
                    boss.draw(screen)
                except Exception as e:
                    logging.error(f"Error drawing boss: {e}")

                # 绘制所有角色按钮
                small_font = pygame.font.SysFont("SimHei", 16)
                for idx, (button_rect, partner, index) in enumerate(character_buttons):
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
                        info_text_surface = small_font.render(partner_info, True, BLACK)
                        screen.blit(info_text_surface, (actual_rect.x + 5, actual_rect.y + 80))

                        # 绘制角色的HP和MP条
                        hp_ratio = max(0, min(partner.hp / partner.max_hp, 1.0))
                        mp_ratio = max(0, min(partner.mp / partner.max_mp, 1.0))

                        # 血条背景
                        hp_bg_rect = pygame.Rect(actual_rect.x + 5, actual_rect.y + 100, button_width - 10, 5)
                        pygame.draw.rect(screen, RED, hp_bg_rect)
                        pygame.draw.rect(screen, GREEN, (
                            hp_bg_rect.x, hp_bg_rect.y, int(hp_bg_rect.width * hp_ratio), hp_bg_rect.height))

                        # 在血条中间显示HP值
                        hp_text = small_font.render(f"{partner.hp}/{partner.max_hp}", True, BLACK)
                        hp_text_rect = hp_text.get_rect(center=(actual_rect.x + button_width // 2, hp_bg_rect.y + hp_bg_rect.height // 2))
                        screen.blit(hp_text, hp_text_rect)

                        # 蓝条背景
                        mp_bg_rect = pygame.Rect(actual_rect.x + 5, actual_rect.y + 110, button_width - 10, 5)
                        pygame.draw.rect(screen, (100, 100, 100), mp_bg_rect)
                        pygame.draw.rect(screen, BLUE, (
                            mp_bg_rect.x, mp_bg_rect.y, int(mp_bg_rect.width * mp_ratio), mp_bg_rect.height))

                        # 在蓝条中间显示MP值
                        mp_text = small_font.render(f"{partner.mp}/{partner.max_mp}", True, BLACK)
                        mp_text_rect = mp_text.get_rect(center=(actual_rect.x + button_width // 2, mp_bg_rect.y + mp_bg_rect.height // 2))
                        screen.blit(mp_text, mp_text_rect)

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
                        # 显示回合提示
                        turn_prompt = font.render("玩家回合", True, BLUE)
                        turn_prompt_rect = turn_prompt.get_rect(center=(SCREEN_WIDTH // 2, 100))
                        screen.blit(turn_prompt, turn_prompt_rect)

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
                                # 绘制取消选择按钮
                                cancel_button = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 220, 100, 30)
                                pygame.draw.rect(screen, (200, 200, 200), cancel_button)
                                pygame.draw.rect(screen, BLACK, cancel_button, 2)
                                cancel_text = pygame.font.SysFont("SimHei", 18).render("取消选择", True, BLACK)
                                screen.blit(cancel_text, (cancel_button.x + 10, cancel_button.y + 5))

                                # 检测取消按钮点击
                                for event in events_to_process:
                                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                        mouse_pos = event.pos
                                        if cancel_button.collidepoint(mouse_pos):
                                            selected_attacker = None
                                            skill_buttons = []
                                            logging.info("Canceled character selection")
                                            break

                                # 绘制技能按钮
                                for button_rect, skill_name, mp_cost in skill_buttons:
                                    button_color = (200, 200, 255)
                                    if mp_cost > 0 and selected_attacker.mp < mp_cost:  # MP不足时显示灰色
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
                                                if mp_cost == 0 or selected_attacker.mp >= mp_cost:  # 检查MP是否足够
                                                    selected_skill = skill_name
                                                    if skill_name in ["治疗", "嘲讽"]:
                                                        target_selection = True
                                                    else:
                                                        # 执行普通攻击或斩击
                                                        if skill_name == "普通攻击":
                                                            # 普通攻击，回复MP
                                                            damage = selected_attacker.get_total_power(duck.buffs)
                                                            boss.hp = max(0, boss.hp - damage)
                                                            # 恢复攻击者的MP
                                                            selected_attacker.mp = min(selected_attacker.max_mp, selected_attacker.mp + 3)
                                                            info_text = f"{selected_attacker.index} 普通攻击! 造成 {damage} 伤害! MP +3"
                                                            
                                                            # 添加攻击特效
                                                            try:
                                                                # Boss震动特效
                                                                active_effects.append(BattleEffect("shake", boss, boss.rect))
                                                                # 爪痕特效
                                                                active_effects.append(BattleEffect("claw", boss, boss.rect))
                                                            except Exception as e:
                                                                logging.error(f"Error creating attack effect: {e}")
                                                                
                                                        elif skill_name == "斩击":
                                                            # 斩击，消耗MP
                                                            damage = selected_attacker.get_total_power(duck.buffs) * 2
                                                            boss.hp = max(0, boss.hp - damage)
                                                            selected_attacker.mp -= mp_cost
                                                            info_text = f"{selected_attacker.index} 使用斩击! 造成 {damage} 伤害! MP -{mp_cost}"
                                                            
                                                            # 添加攻击特效(更强烈)
                                                            try:
                                                                # Boss震动特效(更强烈)
                                                                active_effects.append(BattleEffect("shake", boss, boss.rect))
                                                                # 爪痕特效(更大)
                                                                active_effects.append(BattleEffect("claw", boss, boss.rect))
                                                            except Exception as e:
                                                                logging.error(f"Error creating slash effect: {e}")

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

                                                # 检查MP是否足够
                                                if selected_attacker.mp >= mp_cost:
                                                    # 执行治疗
                                                    heal_amount = 15
                                                    partner.hp = min(partner.max_hp, partner.hp + heal_amount)
                                                    selected_attacker.mp -= mp_cost

                                                    info_text = f"{selected_attacker.index} 治疗了 {partner.index}! HP +{heal_amount}! MP -{mp_cost}"
                                                    info_timer = 120
                                                    
                                                    # 添加治疗特效
                                                    try:
                                                        active_effects.append(BattleEffect("heal", partner, partner.rect))
                                                    except Exception as e:
                                                        logging.error(f"Error creating heal effect: {e}")

                                                    # 重置选择
                                                    selected_attacker = None
                                                    selected_skill = None
                                                    skill_buttons = []
                                                    target_selection = False
                                                    heal_target = None
                                                    state = "boss_turn"
                                                else:
                                                    info_text = "MP不足!"
                                                    info_timer = 60
                                                    # 仅重置技能选择，但保留角色选择
                                                    selected_skill = None
                                                    target_selection = False
                                                    heal_target = None
                                                break
                    except Exception as e:
                        logging.error(f"Error rendering player turn: {e}")
                        logging.error(traceback.format_exc())

                # BOSS回合
                elif state == "boss_turn":
                    # 显示回合提示
                    turn_prompt = font.render("BOSS回合", True, RED)
                    turn_prompt_rect = turn_prompt.get_rect(center=(SCREEN_WIDTH // 2, 100))
                    screen.blit(turn_prompt, turn_prompt_rect)

                    # 延迟一段时间，让玩家看到"BOSS回合"提示
                    if info_timer <= 0:
                        # 检查是否是boss大招回合
                        using_special = boss.turn_counter > 0 and boss.turn_counter % boss.special_attack_cooldown == 0

                        # 简单AI: BOSS随机选择一个角色攻击
                        alive_partners = [p for p in selected_partners if p and p.is_alive]
                        if alive_partners:
                            target = random.choice(alive_partners)
                            
                            # 确定伤害值
                            if using_special:
                                damage = int(boss.special_attack_damage)
                                damage_text = "大招"
                            else:
                                damage = boss.attack_power
                                damage_text = "普通攻击"

                            # 计算实际伤害 (考虑嘲讽效果)
                            taunt_active = any(
                                p.npc_type == "human_child" and hasattr(p, 'taunt_active') and p.taunt_active 
                                for p in selected_partners if p and p.is_alive)
                            
                            # 如果有嘲讽效果，有70%概率攻击嘲讽者
                            if taunt_active:
                                taunt_partners = [p for p in selected_partners if
                                                p and p.is_alive and p.npc_type == "human_child" and p.taunt_active]
                                if taunt_partners and random.random() < 0.7:  # 70%概率攻击嘲讽者
                                    target = random.choice(taunt_partners)
                                    # 嘲讽者受到的伤害降低25%
                                    damage = int(damage * 0.75)
                                    info_text = f"嘲讽生效! BOSS {damage_text}被引导至 {target.index}!"

                            # 应用伤害
                            target.hp = max(0, target.hp - damage)
                            
                            # 添加攻击特效
                            try:
                                # 角色震动特效
                                active_effects.append(BattleEffect("shake", target, target.rect))
                                
                                # 根据攻击类型添加不同的特效
                                if using_special:
                                    # 大招特效 - 龙卷风
                                    active_effects.append(BattleEffect("tornado", target, target.rect))
                                else:
                                    # 普通攻击 - 爪痕
                                    active_effects.append(BattleEffect("claw", target, target.rect))
                            except Exception as e:
                                logging.error(f"Error creating boss attack effect: {e}")

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
                                # BOSS回合结束，更新回合计数
                                boss.turn_counter += 1
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
                    info_timer -= 1
                    info_bg = pygame.Surface((600, 40))  # 增加宽度
                    info_bg.set_alpha(200)
                    info_bg.fill((255, 255, 255))
                    screen.blit(info_bg, (SCREEN_WIDTH // 2 - 300, 130))  # 调整位置
                    # 修改后（使用异常处理更可靠）:
                    try:
                        info_render = font.render(str(info_text) if info_text else "", True, BLACK)
                        screen.blit(info_render, (SCREEN_WIDTH // 2 - 290, 135))  # 调整位置
                    except Exception as e:
                        logging.error(f"Error rendering info text: {e}")
                        info_render = font.render("", True, BLACK)
                
                # 更新和绘制活跃特效
                for effect in active_effects[:]:
                    effect.update()
                    effect.draw(screen)
                    if not effect.active:
                        active_effects.remove(effect)

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