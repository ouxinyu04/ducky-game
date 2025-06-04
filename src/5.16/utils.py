# utils.py - 新增辅助工具文件
import pygame
import logging
import os
import sys
import traceback

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