# utils.py - 新增辅助工具文件
import pygame
import logging
import os
import sys
import traceback
from PIL import Image

def safe_render(screen, font, text, position, color=(0, 0, 0)):
    """安全渲染文本的辅助函数

    参数:
        screen: pygame的屏幕对象
        font: pygame的字体对象
        text: 要渲染的文本
        position: 文本位置(x, y)
        color: 文本颜色，默认黑色

    返回:
        无
    """
    try:
        if isinstance(text, str):
            text_surface = font.render(text, True, color)
            screen.blit(text_surface, position)
        else:
            text_surface = font.render(str(text), True, color)
            screen.blit(text_surface, position)
    except Exception as e:
        logging.error(f"Error rendering text: {e}")
        logging.error(traceback.format_exc())

def load_image(path, size=None, default_color=None):
    """安全加载图像的辅助函数

    参数:
        path: 图像文件路径
        size: 调整后的大小(width, height)，默认为None表示不调整大小
        default_color: 如果图像加载失败，使用这个颜色创建一个默认Surface

    返回:
        图像对象，如果加载失败且提供了default_color，则返回一个填充了该颜色的Surface
    """
    image = None
    if os.path.exists(path):
        try:
            image = pygame.image.load(path)
            if size:
                image = pygame.transform.scale(image, size)
        except Exception as e:
            logging.error(f"Failed to load image {path}: {e}")
            logging.error(traceback.format_exc())
            # 如果提供了默认颜色，创建一个默认的Surface
            if default_color:
                image = pygame.Surface(size if size else (30, 30))
                image.fill(default_color)
    else:
        logging.warning(f"Image file not found: {path}")
        # 如果提供了默认颜色，创建一个默认的Surface
        if default_color and size:
            image = pygame.Surface(size)
            image.fill(default_color)
    return image

def create_gif_from_sprite_sheet(sprite_sheet_path, output_path, frame_width=48, frame_height=48,
                                 num_frames=2, scale_factor=3, frame_duration=200, transparent=True):
    """从精灵图创建 GIF 动画

    参数:
        sprite_sheet_path: 精灵图文件路径
        output_path: 输出 GIF 文件路径
        frame_width: 每帧的宽度
        frame_height: 每帧的高度
        num_frames: 帧数
        scale_factor: 放大倍数
        frame_duration: 每帧持续时间（毫秒）
        transparent: 是否保持透明背景

    返回:
        是否成功创建 GIF
    """
    try:
        # 加载精灵图
        sprite_sheet = Image.open(sprite_sheet_path)

        # 如果需要透明背景，确保图像有 alpha 通道
        if transparent and sprite_sheet.mode != 'RGBA':
            sprite_sheet = sprite_sheet.convert('RGBA')

        # 提取帧
        frames = []
        for i in range(num_frames):
            # 计算每帧的位置（水平排列）
            left = i * frame_width
            top = 0
            right = left + frame_width
            bottom = top + frame_height

            # 提取帧
            frame = sprite_sheet.crop((left, top, right, bottom))

            # 放大帧
            new_size = (frame_width * scale_factor, frame_height * scale_factor)
            frame_scaled = frame.resize(new_size, Image.NEAREST)  # 使用最近邻插值保持像素风格

            frames.append(frame_scaled)

        # 保存为 GIF
        if frames:
            save_kwargs = {
                'save_all': True,
                'append_images': frames[1:],
                'duration': frame_duration,
                'loop': 0  # 无限循环
            }

            # 如果需要透明背景，添加透明度设置
            if transparent:
                save_kwargs['transparency'] = 0
                save_kwargs['disposal'] = 2  # 清除到背景色

            frames[0].save(output_path, **save_kwargs)
            logging.info(f"Successfully created {'transparent' if transparent else 'opaque'} GIF: {output_path}")
            return True
        else:
            logging.error("No frames extracted from sprite sheet")
            return False

    except Exception as e:
        logging.error(f"Error creating GIF from sprite sheet {sprite_sheet_path}: {e}")
        logging.error(traceback.format_exc())
        return False

def create_transparent_gif_from_sprite_sheet(sprite_sheet_path, output_path, frame_width=48, frame_height=48,
                                           num_frames=2, scale_factor=3, frame_duration=200,
                                           auto_detect_bg=True, bg_color=None):
    """从精灵图创建透明背景的 GIF 动画（高级版本）

    参数:
        sprite_sheet_path: 精灵图文件路径
        output_path: 输出 GIF 文件路径
        frame_width: 每帧的宽度
        frame_height: 每帧的高度
        num_frames: 帧数
        scale_factor: 放大倍数
        frame_duration: 每帧持续时间（毫秒）
        auto_detect_bg: 是否自动检测背景色
        bg_color: 指定的背景色 (R, G, B) 或 (R, G, B, A)

    返回:
        是否成功创建 GIF
    """
    try:
        # 加载精灵图
        sprite_sheet = Image.open(sprite_sheet_path)

        # 转换为 RGBA 模式以支持透明度
        if sprite_sheet.mode != 'RGBA':
            sprite_sheet = sprite_sheet.convert('RGBA')

        # 自动检测背景色（使用左上角像素）
        if auto_detect_bg and bg_color is None:
            bg_color = sprite_sheet.getpixel((0, 0))
            logging.info(f"Auto-detected background color: {bg_color}")

        # 提取帧并处理透明度
        frames = []
        for i in range(num_frames):
            # 计算每帧的位置（水平排列）
            left = i * frame_width
            top = 0
            right = left + frame_width
            bottom = top + frame_height

            # 提取帧
            frame = sprite_sheet.crop((left, top, right, bottom))

            # 如果指定了背景色，将其设为透明
            if bg_color is not None:
                # 创建新的透明图像
                transparent_frame = Image.new('RGBA', frame.size, (0, 0, 0, 0))

                # 遍历每个像素
                for x in range(frame.width):
                    for y in range(frame.height):
                        pixel = frame.getpixel((x, y))

                        # 检查是否为背景色（允许一定的容差）
                        if len(pixel) == 4:  # RGBA
                            r, g, b, a = pixel
                            bg_r, bg_g, bg_b = bg_color[:3]

                            # 计算颜色差异
                            color_diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)

                            # 保护黑色像素点（不设为透明）
                            is_black_pixel = r < 50 and g < 50 and b < 50

                            if color_diff <= 10 and not is_black_pixel:  # 容差为 10，但保护黑色像素
                                # 背景色设为透明
                                transparent_frame.putpixel((x, y), (0, 0, 0, 0))
                            else:
                                # 保持原像素
                                transparent_frame.putpixel((x, y), pixel)
                        else:  # RGB
                            r, g, b = pixel
                            bg_r, bg_g, bg_b = bg_color[:3]

                            color_diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)

                            # 保护黑色像素点（不设为透明）
                            is_black_pixel = r < 50 and g < 50 and b < 50

                            if color_diff <= 10 and not is_black_pixel:
                                transparent_frame.putpixel((x, y), (0, 0, 0, 0))
                            else:
                                transparent_frame.putpixel((x, y), (r, g, b, 255))

                frame = transparent_frame

            # 放大帧
            new_size = (frame_width * scale_factor, frame_height * scale_factor)
            frame_scaled = frame.resize(new_size, Image.NEAREST)

            frames.append(frame_scaled)

        # 保存为透明 GIF
        if frames:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration,
                loop=0,
                transparency=0,
                disposal=2
            )
            logging.info(f"Successfully created transparent GIF: {output_path}")
            return True
        else:
            logging.error("No frames extracted from sprite sheet")
            return False

    except Exception as e:
        logging.error(f"Error creating transparent GIF from sprite sheet {sprite_sheet_path}: {e}")
        logging.error(traceback.format_exc())
        return False

def quit_game():
    """安全退出游戏，确保资源被正确释放"""
    try:
        try:
            pygame.mixer.quit()  # 释放音频资源
        except:
            pass
        pygame.quit()        # 释放pygame资源
        sys.exit(0)          # 使用0表示正常退出
    except Exception as e:
        logging.error(f"Error during game exit: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)          # 使用非零值表示异常退出

def create_text_surface(font, text, color=(0, 0, 0), max_width=None):
    """创建一个多行文本Surface

    参数:
        font: pygame的字体对象
        text: 要渲染的文本
        color: 文本颜色，默认黑色
        max_width: 最大宽度，超过此宽度将自动换行

    返回:
        渲染好的多行文本Surface
    """
    if not max_width:
        return font.render(text, True, color)

    words = text.split(' ')
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        test_width = font.size(test_line)[0]

        if test_width < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    # 计算所需的高度
    line_height = font.get_linesize()
    total_height = line_height * len(lines)

    # 创建surface
    surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)

    # 渲染每行文本
    for i, line in enumerate(lines):
        line_surface = font.render(line, True, color)
        surface.blit(line_surface, (0, i * line_height))

    return surface

def draw_button(screen, rect, text, font, normal_color=(200, 200, 200),
                hover_color=(220, 220, 220), text_color=(0, 0, 0), border_color=(0, 0, 0),
                border_width=2, mouse_pos=None):
    """绘制一个可点击的按钮

    参数:
        screen: pygame的屏幕对象
        rect: 按钮矩形区域
        text: 按钮文本
        font: 使用的字体
        normal_color: 普通状态的按钮颜色
        hover_color: 鼠标悬停时的按钮颜色
        text_color: 文本颜色
        border_color: 边框颜色
        border_width: 边框宽度
        mouse_pos: 当前鼠标位置，用于检测悬停

    返回:
        按钮是否被悬停
    """
    is_hover = False
    if mouse_pos and rect.collidepoint(mouse_pos):
        is_hover = True
        pygame.draw.rect(screen, hover_color, rect)
    else:
        pygame.draw.rect(screen, normal_color, rect)

    if border_width > 0:
        pygame.draw.rect(screen, border_color, rect, border_width)

    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)

    return is_hover

def save_game(game_state, filename="save_game.dat"):
    """保存游戏状态

    参数:
        game_state: 游戏状态对象
        filename: 保存文件名

    返回:
        是否保存成功
    """
    import pickle

    try:
        # 创建一个简化的游戏状态字典，只包含必要数据
        save_data = {
            'level': game_state.level,
            'duck_hp': game_state.duck.hp,
            'duck_max_hp': game_state.duck.max_hp,
            'duck_attack_power': game_state.duck.attack_power,
            'duck_charm': game_state.duck.charm,
            'duck_reputation': game_state.duck.reputation,
            'duck_buffs': game_state.duck.buffs,
            'partner_count': len(game_state.duck.partners),
            'weapon_count': len(game_state.duck.weapons)
        }

        with open(filename, 'wb') as f:
            pickle.dump(save_data, f)
        return True
    except Exception as e:
        logging.error(f"Error saving game: {e}")
        logging.error(traceback.format_exc())
        return False

def load_game(filename="save_game.dat"):
    """加载游戏状态

    参数:
        filename: 保存文件名

    返回:
        加载的游戏状态字典，如果加载失败则返回None
    """
    import pickle

    try:
        if not os.path.exists(filename):
            return None

        with open(filename, 'rb') as f:
            save_data = pickle.load(f)
        return save_data
    except Exception as e:
        logging.error(f"Error loading game: {e}")
        logging.error(traceback.format_exc())
        return None

def draw_progress_bar(screen, x, y, width, height, value, max_value,
                      bg_color=(200, 0, 0), fg_color=(0, 200, 0), border_color=(0, 0, 0),
                      border_width=1, show_text=True, font=None, text_color=(0, 0, 0)):
    """绘制进度条

    参数:
        screen: pygame的屏幕对象
        x, y: 进度条位置
        width, height: 进度条大小
        value: 当前值
        max_value: 最大值
        bg_color: 背景颜色
        fg_color: 前景颜色
        border_color: 边框颜色
        border_width: 边框宽度
        show_text: 是否显示进度文本
        font: 文本字体
        text_color: 文本颜色

    返回:
        无
    """
    try:
        # 确保value在0到max_value之间
        value = max(0, min(value, max_value))

        # 绘制背景
        pygame.draw.rect(screen, bg_color, (x, y, width, height))

        # 计算前景宽度
        if max_value > 0:  # 防止除以零
            fg_width = int(width * (value / max_value))
        else:
            fg_width = 0

        # 绘制前景
        if fg_width > 0:
            pygame.draw.rect(screen, fg_color, (x, y, fg_width, height))

        # 绘制边框
        if border_width > 0:
            pygame.draw.rect(screen, border_color, (x, y, width, height), border_width)

        # 绘制文本
        if show_text and font:
            text = f"{value}/{max_value}"
            text_surf = font.render(text, True, text_color)
            text_rect = text_surf.get_rect(center=(x + width//2, y + height//2))
            screen.blit(text_surf, text_rect)
    except Exception as e:
        logging.error(f"Error drawing progress bar: {e}")
        logging.error(traceback.format_exc())

def draw_shield_bar(screen, x, y, width, height, current_shield, max_shield, font):
    """绘制黄色护盾条

    参数:
        screen: pygame的屏幕对象
        x, y: 护盾条左上角位置
        width, height: 护盾条尺寸
        current_shield: 当前护盾值
        max_shield: 最大护盾值
        font: 用于显示数值的字体

    返回:
        无
    """
    try:
        from constants import YELLOW

        # 绘制护盾条
        draw_progress_bar(screen, x, y, width, height, current_shield, max_shield,
                         fg_color=YELLOW, bg_color=(80, 80, 80),
                         border_color=(0, 0, 0), border_width=1,
                         show_text=False)

        # 绘制护盾数值文本
        if current_shield > 0:
            shield_text = f"{current_shield}/{max_shield}"
            text_surface = font.render(shield_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
            screen.blit(text_surface, text_rect)

    except Exception as e:
        logging.error(f"Error drawing shield bar: {e}")

def load_skill_icon(icon_filename, size=(24, 24)):
    """加载技能图标

    参数:
        icon_filename: 图标文件名
        size: 图标尺寸 (width, height)

    返回:
        pygame.Surface 或 None
    """
    try:
        from config import ASSETS_DIR
        import os

        if not icon_filename:
            return None

        icon_path = os.path.join(ASSETS_DIR, icon_filename)
        if os.path.exists(icon_path):
            icon = pygame.image.load(icon_path)
            # 如果是GIF，只取第一帧
            if icon_filename.endswith('.gif'):
                # 对于GIF图标，使用animation_utils加载第一帧
                try:
                    from animation_utils import load_animation_frames
                    frames, _ = load_animation_frames(icon_filename, None, size)
                    if frames:
                        return frames[0]
                except:
                    pass

            # 普通图像处理
            icon = pygame.transform.scale(icon, size)
            return icon
        else:
            logging.warning(f"Skill icon not found: {icon_path}")
            return None

    except Exception as e:
        logging.error(f"Error loading skill icon {icon_filename}: {e}")
        return None

def draw_rounded_rect_with_shadow(screen, x, y, width, height,
                                  bg_color=(255, 255, 255), bg_alpha=220,
                                  shadow_color=(136, 136, 136), shadow_offset=(5, 5),
                                  shadow_blur=5, border_radius=10):
    """绘制带阴影效果的圆角矩形

    参数:
        screen: pygame的屏幕对象
        x, y: 矩形位置
        width, height: 矩形大小
        bg_color: 背景颜色，默认白色
        bg_alpha: 背景透明度，默认220
        shadow_color: 阴影颜色，默认灰色
        shadow_offset: 阴影偏移(x_offset, y_offset)，默认(5, 5)
        shadow_blur: 阴影模糊半径，默认5
        border_radius: 圆角半径，默认10

    返回:
        创建的背景Surface对象
    """
    try:
        shadow_offset_x, shadow_offset_y = shadow_offset

        # 绘制阴影效果（通过多层半透明矩形模拟模糊）
        for i in range(shadow_blur):
            # 计算当前层的透明度（从外到内逐渐变浓）
            alpha = int(30 * (shadow_blur - i) / shadow_blur)

            # 创建阴影层Surface
            shadow_surface = pygame.Surface((width + i*2, height + i*2), pygame.SRCALPHA)
            shadow_surface.set_alpha(alpha)

            # 绘制圆角矩形阴影（如果pygame版本支持）
            try:
                pygame.draw.rect(shadow_surface, shadow_color,
                               (0, 0, width + i*2, height + i*2),
                               border_radius=border_radius)
            except TypeError:
                # 如果不支持圆角，使用普通矩形
                pygame.draw.rect(shadow_surface, shadow_color,
                               (0, 0, width + i*2, height + i*2))

            # 绘制阴影到屏幕
            screen.blit(shadow_surface,
                       (x + shadow_offset_x - i, y + shadow_offset_y - i))

        # 创建主背景Surface
        bg_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        bg_surface.set_alpha(bg_alpha)

        # 绘制圆角矩形背景
        try:
            # pygame 2.0+ 支持圆角
            pygame.draw.rect(bg_surface, bg_color,
                           (0, 0, width, height),
                           border_radius=border_radius)
        except TypeError:
            # 如果不支持圆角，使用普通矩形
            pygame.draw.rect(bg_surface, bg_color,
                           (0, 0, width, height))

        # 将背景绘制到屏幕
        screen.blit(bg_surface, (x, y))

        return bg_surface

    except Exception as e:
        logging.error(f"Error drawing rounded rect with shadow: {e}")
        logging.error(traceback.format_exc())
        # 如果出错，绘制简单矩形
        pygame.draw.rect(screen, bg_color, (x, y, width, height))
        return None

def draw_text_with_background(screen, font, text, x, y,
                             text_color=(0, 0, 0),
                             bg_color=(255, 255, 255), bg_alpha=220,
                             padding=10, min_width=0,
                             shadow_color=(136, 136, 136), shadow_offset=(5, 5),
                             shadow_blur=5, border_radius=10):
    """绘制带背景和阴影的文本

    参数:
        screen: pygame的屏幕对象
        font: 字体对象
        text: 要绘制的文本
        x, y: 文本位置
        text_color: 文本颜色
        bg_color: 背景颜色
        bg_alpha: 背景透明度
        padding: 文本周围的内边距
        min_width: 背景最小宽度
        shadow_color: 阴影颜色
        shadow_offset: 阴影偏移
        shadow_blur: 阴影模糊半径
        border_radius: 圆角半径

    返回:
        文本Surface对象
    """
    try:
        # 渲染文本
        text_surface = font.render(text, True, text_color)
        text_width = text_surface.get_width()
        text_height = text_surface.get_height()

        # 计算背景尺寸
        bg_width = max(text_width + padding * 2, min_width)
        bg_height = text_height + padding * 2

        # 绘制背景和阴影
        draw_rounded_rect_with_shadow(screen, x, y, bg_width, bg_height,
                                    bg_color, bg_alpha, shadow_color,
                                    shadow_offset, shadow_blur, border_radius)

        # 计算文本居中位置
        text_x = x + (bg_width - text_width) // 2
        text_y = y + (bg_height - text_height) // 2

        # 绘制文本
        screen.blit(text_surface, (text_x, text_y))

        return text_surface

    except Exception as e:
        logging.error(f"Error drawing text with background: {e}")
        logging.error(traceback.format_exc())
        # 如果出错，绘制简单文本
        text_surface = font.render(text, True, text_color)
        screen.blit(text_surface, (x, y))
        return text_surface



def draw_skill_button_with_icon(screen, rect, skill_name, icon_name, mp_cost, font,
                               current_mp, normal_color=(200, 200, 255),
                               disabled_color=(150, 150, 150), text_color=(0, 0, 0),
                               border_color=(0, 0, 0), border_width=2):
    """绘制带图标的技能按钮

    参数:
        screen: pygame屏幕对象
        rect: 按钮矩形区域
        skill_name: 技能名称
        icon_name: 图标文件名
        mp_cost: MP消耗
        font: 字体对象
        current_mp: 当前MP
        normal_color: 正常状态颜色
        disabled_color: 禁用状态颜色
        text_color: 文本颜色
        border_color: 边框颜色
        border_width: 边框宽度

    返回:
        是否可用（MP足够）
    """
    try:
        # 检查MP是否足够
        is_available = current_mp >= mp_cost
        button_color = normal_color if is_available else disabled_color

        # 绘制按钮背景
        pygame.draw.rect(screen, button_color, rect)
        pygame.draw.rect(screen, border_color, rect, border_width)

        # 加载并绘制图标
        icon = load_skill_icon(icon_name, (24, 24))
        if icon:
            icon_x = rect.x + 5
            icon_y = rect.y + (rect.height - 24) // 2
            screen.blit(icon, (icon_x, icon_y))
            text_start_x = icon_x + 28
        else:
            text_start_x = rect.x + 5

        # 绘制技能名称
        skill_text = font.render(skill_name, True, text_color)
        text_y = rect.y + 5
        screen.blit(skill_text, (text_start_x, text_y))

        # 绘制MP消耗
        if mp_cost > 0:
            mp_text = font.render(f"MP:{mp_cost}", True, text_color)
            mp_x = rect.x + rect.width - mp_text.get_width() - 5
            mp_y = rect.y + rect.height - mp_text.get_height() - 5
            screen.blit(mp_text, (mp_x, mp_y))

        return is_available

    except Exception as e:
        logging.error(f"Error drawing skill button: {e}")
        # 绘制简单按钮作为备用
        pygame.draw.rect(screen, button_color, rect)
        pygame.draw.rect(screen, border_color, rect, border_width)
        text = font.render(skill_name, True, text_color)
        screen.blit(text, (rect.x + 5, rect.y + 5))
        return is_available

def draw_character_status_effects(screen, character, x, y, width, height):
    """绘制角色状态效果

    参数:
        screen: pygame屏幕对象
        character: 角色对象
        x, y: 角色位置
        width, height: 角色尺寸
    """
    try:
        # 绘制护盾效果（绿色光晕）
        if hasattr(character, 'shield_active') and character.shield_active:
            pygame.draw.rect(screen, (0, 255, 0), (x-2, y-2, width+4, height+4), 3)

        # 绘制祝福效果（金色边框）
        if hasattr(character, 'blessed') and character.blessed:
            pygame.draw.rect(screen, (255, 215, 0), (x-3, y-3, width+6, height+6), 2)

        # 绘制嘲讽效果（红色轮廓）
        if hasattr(character, 'taunt_active') and character.taunt_active:
            pygame.draw.rect(screen, (255, 0, 0), (x-4, y-4, width+8, height+8), 2)

        # 绘制反射效果（紫色光环）
        if hasattr(character, 'reflect_active') and character.reflect_active:
            pygame.draw.rect(screen, (128, 0, 128), (x-5, y-5, width+10, height+10), 3)

    except Exception as e:
        logging.error(f"Error drawing character status effects: {e}")

def draw_skill_result_prompt(screen, font, text, x, y, duration=120):
    """绘制技能结果提示

    参数:
        screen: pygame屏幕对象
        font: 字体对象
        text: 提示文本
        x, y: 显示位置
        duration: 显示持续时间（帧数）

    返回:
        文本Surface对象
    """
    try:
        return draw_text_with_background(
            screen, font, text, x, y,
            text_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            bg_alpha=180,
            padding=15,
            shadow_color=(100, 100, 100),
            shadow_offset=(3, 3),
            shadow_blur=3,
            border_radius=8
        )
    except Exception as e:
        logging.error(f"Error drawing skill result prompt: {e}")
        # 简单文本作为备用
        text_surface = font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, (x, y))
        return text_surface