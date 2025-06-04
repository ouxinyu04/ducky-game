# main.py - 完整修改版 - 卡通冒险主题主菜单
import pygame
import sys
import logging
import traceback
import os
import random
import math
import time
from constants import LIGHT_GREEN
from duck import Duck
from game_state import GameState
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK
from config import ASSETS_DIR  # 导入配置文件中的资源目录

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import safe_render, quit_game, load_image  # 导入我们的新工具函数

# 设置日志配置
logging.basicConfig(
    filename="game_errors.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 忽略libpng警告
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# 星星粒子类
class StarParticle:
    def __init__(self):
        self.reset_position()
        self.speed = 10  # 每秒10px
        
    def reset_position(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        
    def update(self, dt):
        """更新星星位置
        
        参数:
            dt: 时间间隔（毫秒）
        """
        self.y -= self.speed * dt / 1000  # dt是毫秒，转换为秒
        if self.y < -10:  # 星星完全离开屏幕顶部
            self.y = SCREEN_HEIGHT + 10
            self.x = random.randint(0, SCREEN_WIDTH)
    
    def draw(self, screen):
        """绘制星星"""
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), 3)

def draw_rounded_rect(surface, color, rect, radius):
    """绘制圆角矩形
    
    参数:
        surface: 绘制表面
        color: 颜色
        rect: 矩形区域
        radius: 圆角半径
    """
    try:
        # 绘制主体矩形
        inner_rect = pygame.Rect(rect.left + radius, rect.top, 
                                rect.width - 2 * radius, rect.height)
        pygame.draw.rect(surface, color, inner_rect)
        
        inner_rect = pygame.Rect(rect.left, rect.top + radius, 
                                rect.width, rect.height - 2 * radius)
        pygame.draw.rect(surface, color, inner_rect)
        
        # 绘制四个圆角
        pygame.draw.circle(surface, color, (rect.left + radius, rect.top + radius), radius)
        pygame.draw.circle(surface, color, (rect.right - radius, rect.top + radius), radius)
        pygame.draw.circle(surface, color, (rect.left + radius, rect.bottom - radius), radius)
        pygame.draw.circle(surface, color, (rect.right - radius, rect.bottom - radius), radius)
    except Exception as e:
        logging.error(f"Error drawing rounded rect: {e}")
        # 如果圆角绘制失败，回退到普通矩形
        pygame.draw.rect(surface, color, rect)

def draw_rounded_rect_border(surface, color, rect, radius, width):
    """绘制圆角矩形边框
    
    参数:
        surface: 绘制表面
        color: 颜色
        rect: 矩形区域
        radius: 圆角半径
        width: 边框宽度
    """
    try:
        # 绘制边框线段
        # 上边框
        pygame.draw.line(surface, color, (rect.left + radius, rect.top), 
                        (rect.right - radius, rect.top), width)
        # 下边框
        pygame.draw.line(surface, color, (rect.left + radius, rect.bottom), 
                        (rect.right - radius, rect.bottom), width)
        # 左边框
        pygame.draw.line(surface, color, (rect.left, rect.top + radius), 
                        (rect.left, rect.bottom - radius), width)
        # 右边框
        pygame.draw.line(surface, color, (rect.right, rect.top + radius), 
                        (rect.right, rect.bottom - radius), width)
        
        # 绘制四个圆角边框
        pygame.draw.circle(surface, color, (rect.left + radius, rect.top + radius), radius, width)
        pygame.draw.circle(surface, color, (rect.right - radius, rect.top + radius), radius, width)
        pygame.draw.circle(surface, color, (rect.left + radius, rect.bottom - radius), radius, width)
        pygame.draw.circle(surface, color, (rect.right - radius, rect.bottom - radius), radius, width)
    except Exception as e:
        logging.error(f"Error drawing rounded rect border: {e}")
        # 如果圆角边框绘制失败，回退到普通边框
        pygame.draw.rect(surface, color, rect, width)

def main():
    try:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("鸭鸭勇者传")
        font = pygame.font.SysFont("SimHei", 64, bold=True)  # 标题字体48px加粗
        button_font = pygame.font.SysFont("SimHei", 20)  # 按钮字体无加粗

        # 加载背景图 - 更新了路径列表
        background_image = None
        background_paths = [
            r"E:\python_game\DuckEscape-game\assets\images\menu_background.png",  # 用户指定的完整路径
            os.path.join(ASSETS_DIR, "menu_background.png"),  # 使用配置文件中的路径
            "assets/images/menu_background.png",
            "images/menu_background.png", 
            "menu_background.png",
            "assets/menu_background.png"
        ]
        
        for path in background_paths:
            if os.path.exists(path):
                try:
                    background_image = pygame.image.load(path)
                    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    logging.info(f"Successfully loaded background from: {path}")
                    break
                except Exception as e:
                    logging.warning(f"Failed to load background from {path}: {e}")
                    continue
        
        if background_image is None:
            # 如果加载失败，创建渐变背景
            background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for y in range(SCREEN_HEIGHT):
                # 创建从浅蓝到深蓝的渐变
                blue_value = int(135 + (120 * y / SCREEN_HEIGHT))
                color = (135, 206, min(255, blue_value))
                pygame.draw.line(background_image, color, (0, y), (SCREEN_WIDTH, y))
            logging.info("Using default gradient background")

        # 创建星星粒子
        star_count = random.randint(10, 20)
        stars = [StarParticle() for _ in range(star_count)]
        logging.info(f"Created {star_count} star particles")

        # 游戏状态
        game_state = None
        menu_active = True

        # 三个按钮定义 - 尺寸200x60，垂直排列，间距20px
        start_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 30, 200, 60)
        continue_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 60)
        exit_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 130, 200, 60)
        
        # 存档显示相关
        show_saves = False
        save_list_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 100, 300, 200)
                
        # 用于时间跟踪
        clock = pygame.time.Clock()
        last_time = pygame.time.get_ticks()

        def draw_menu():
            """绘制主菜单"""
            # 绘制背景
            screen.blit(background_image, (0, 0))

            # 绘制星星粒子
            for star in stars:
                star.draw(screen)
            
            # 获取鼠标位置用于悬停检测
            mouse_pos = pygame.mouse.get_pos()
            
            # 绘制开始冒险按钮
            start_hover = start_button.collidepoint(mouse_pos)
            start_bg_color = LIGHT_GREEN if start_hover else (255, 255, 255)
            start_text_color = (255, 255, 255) if start_hover else (0, 0, 0)
            
            draw_rounded_rect(screen, start_bg_color, start_button, 10)
            pygame.draw.rect(screen, (0, 100, 0), start_button, width=2, border_radius=10)
            
            start_text = button_font.render("开始冒险", True, start_text_color)
            start_text_rect = start_text.get_rect(center=start_button.center)
            screen.blit(start_text, start_text_rect)
            
            # 绘制继续冒险按钮
            continue_hover = continue_button.collidepoint(mouse_pos)
            continue_bg_color = LIGHT_GREEN if continue_hover else (255, 255, 255)
            continue_text_color = (255, 255, 255) if continue_hover else (0, 0, 0)
            
            draw_rounded_rect(screen, continue_bg_color, continue_button, 10)
            pygame.draw.rect(screen, (0, 100, 0), continue_button, width=2, border_radius=10)

            continue_text = button_font.render("继续冒险", True, continue_text_color)
            continue_text_rect = continue_text.get_rect(center=continue_button.center)
            screen.blit(continue_text, continue_text_rect)
            
            # 绘制结束冒险按钮
            exit_hover = exit_button.collidepoint(mouse_pos)
            exit_bg_color = LIGHT_GREEN if exit_hover else (255, 255, 255)
            exit_text_color = (255, 255, 255) if exit_hover else (0, 0, 0)
            
            draw_rounded_rect(screen, exit_bg_color, exit_button, 10)
            pygame.draw.rect(screen, (0, 100, 0), exit_button, width=2, border_radius=10)

            exit_text = button_font.render("结束冒险", True, exit_text_color)
            exit_text_rect = exit_text.get_rect(center=exit_button.center)
            screen.blit(exit_text, exit_text_rect)

            # 添加游戏标题（位置保持不变）
            title = font.render("鸭鸭勇者传", True, (28, 37, 38))
            shadow_title = font.render("鸭鸭勇者传", True, (128, 128, 128))
            
            # 标题位置保持 y = SCREEN_HEIGHT // 2 - 208
            title_rect = title.get_rect()
            title_x = SCREEN_WIDTH // 2 - title_rect.width // 2
            title_y = SCREEN_HEIGHT // 2 - 158
            
            # 绘制标题阴影（偏移2, 2）
            screen.blit(shadow_title, (title_x + 2, title_y + 2))
            # 绘制标题
            screen.blit(title, (title_x, title_y))
            
            # 如果显示存档列表
            if show_saves:
                draw_save_list()

            pygame.display.flip()

        def draw_save_list():
            """绘制存档列表"""
            # 绘制存档列表背景
            pygame.draw.rect(screen, (255, 255, 255), save_list_rect)
            pygame.draw.rect(screen, (0, 0, 0), save_list_rect, 2)
            
            # 标题
            title_text = button_font.render("选择存档", True, (0, 0, 0))
            screen.blit(title_text, (save_list_rect.x + 10, save_list_rect.y + 10))
            
            # 尝试加载存档信息
            save_files = []
            
            # 检查存档文件
            for i in range(1, 4):  # 检查Save 1, Save 2, Save 3
                save_filename = f"save_game.dat" if i == 1 else f"save_game_{i}.dat"
                if os.path.exists(save_filename):
                    try:
                        # 获取文件修改时间
                        mtime = os.path.getmtime(save_filename)
                        timestamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
                        save_files.append((f"Save {i}", save_filename, timestamp))
                    except:
                        pass
            
            if not save_files:
                # 没有存档文件
                no_save_text = button_font.render("No Saves", True, (128, 128, 128))
                text_rect = no_save_text.get_rect(center=(save_list_rect.centerx, save_list_rect.centery))
                screen.blit(no_save_text, text_rect)
            else:
                # 显示存档列表
                y_offset = 50
                for i, (save_name, filename, timestamp) in enumerate(save_files):
                    save_text = f"{save_name} - {timestamp}"
                    save_surface = button_font.render(save_text, True, (0, 0, 0))
                    screen.blit(save_surface, (save_list_rect.x + 10, save_list_rect.y + y_offset + i * 30))
            
            # 关闭按钮
            close_text = button_font.render("点击空白处关闭", True, (128, 128, 128))
            screen.blit(close_text, (save_list_rect.x + 10, save_list_rect.bottom - 30))

        # 用于检测连续错误
        error_count = 0
        last_error_time = 0
        max_errors_allowed = 3  # 允许的最大连续错误数
        error_timeout = 5000  # 错误重置时间（毫秒）

        running = True
        
        while running:
            try:
                current_time = pygame.time.get_ticks()
                dt = current_time - last_time
                last_time = current_time

                # 重置错误计数器（如果已经过了足够的时间）
                if current_time - last_error_time > error_timeout:
                    error_count = 0

                # 更新星星粒子（只在主菜单时）
                if menu_active:
                    for star in stars:
                        star.update(dt)

                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and menu_active:
                        if show_saves:
                            # 处理存档列表点击
                            if save_list_rect.collidepoint(event.pos):
                                # 检查是否点击了存档项
                                save_files = []
                                
                                for i in range(1, 4):
                                    save_filename = f"save_game_{i}.dat"
                                    if os.path.exists(save_filename):
                                        try:
                                            mtime = os.path.getmtime(save_filename)
                                            timestamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
                                            save_files.append((f"Save {i}", save_filename, timestamp))
                                        except:
                                            pass
                                
                                if save_files:
                                    # 计算点击的存档项
                                    relative_y = event.pos[1] - (save_list_rect.y + 50)
                                    save_index = relative_y // 30
                                    
                                    if 0 <= save_index < len(save_files):
                                        # 加载选中的存档
                                        _, selected_filename, _ = save_files[save_index]
                                        try:
                                            from utils import load_game
                                            save_data = load_game(selected_filename)
                                            if save_data:
                                                # 初始化游戏并加载存档数据
                                                duck = Duck(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                                                # 这里可以根据save_data恢复游戏状态
                                                # 为简化，直接启动新游戏
                                                game_state = GameState(duck)
                                                menu_active = False
                                                show_saves = False
                                                logging.info(f"Game loaded from {selected_filename}")
                                                error_count = 0
                                        except Exception as e:
                                            logging.error(f"Error loading save: {e}")
                            else:
                                # 点击空白处关闭存档列表
                                show_saves = False
                        else:
                            # 处理主菜单按钮点击
                            if start_button.collidepoint(event.pos):
                                # 开始新游戏
                                try:
                                    duck = Duck(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                                    game_state = GameState(duck)
                                    menu_active = False
                                    logging.info("New game started")
                                    error_count = 0
                                except Exception as e:
                                    logging.error(f"Error initializing game: {e}")
                                    logging.error(traceback.format_exc())
                                    error_font = pygame.font.SysFont("SimHei", 20)
                                    error_text = error_font.render("游戏初始化失败，请查看日志文件", True, (255, 0, 0))
                                    screen.blit(error_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 50))
                                    pygame.display.flip()
                            
                            elif continue_button.collidepoint(event.pos):
                                # 显示存档列表
                                show_saves = True
                            
                            elif exit_button.collidepoint(event.pos):
                                # 退出游戏
                                from utils import quit_game
                                quit_game()

                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        if not menu_active:
                            # 按ESC返回主菜单
                            menu_active = True
                            game_state = None
                        else:
                            running = False

                if menu_active:
                    draw_menu()
                    clock.tick(60)  # 只在主菜单时限制帧率
                else:
                    if game_state is None:
                        continue  # 防止 game_state 未初始化

                    # 使用try-except捕获游戏更新过程中的错误
                    try:
                        keys = pygame.key.get_pressed()
                        game_state.update(screen, keys, events)
                        pygame.display.flip()
                        # 游戏时不限制帧率，保持原有速度
                        # 成功更新，重置错误计数
                        error_count = 0
                    except Exception as e:
                        error_count += 1
                        last_error_time = current_time
                        logging.error(f"Game update error ({error_count}/{max_errors_allowed}): {e}")
                        logging.error(traceback.format_exc())

                        # 尝试继续游戏，除非错误太多
                        if error_count >= max_errors_allowed:
                            logging.error(f"Too many errors, returning to main menu")
                            menu_active = True
                            game_state = None

                            # 显示友好的错误信息
                            screen.fill(WHITE)
                            error_font = pygame.font.SysFont("SimHei", 24)
                            error_text1 = error_font.render("游戏遇到问题，已返回主菜单", True, (255, 0, 0))
                            error_text2 = error_font.render("请查看game_errors.log获取详细信息", True, (0, 0, 0))
                            screen.blit(error_text1, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 30))
                            screen.blit(error_text2, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 10))
                            pygame.display.flip()
                            pygame.time.delay(2000)  # 显示错误信息2秒
                            error_count = 0  # 重置错误计数
                        else:
                            # 尝试恢复渲染
                            try:
                                screen.fill(WHITE)
                                small_font = pygame.font.SysFont("SimHei", 20)
                                recovery_text = small_font.render("恢复中...", True, (0, 0, 0))
                                screen.blit(recovery_text, (10, 10))
                                pygame.display.flip()
                                pygame.time.delay(500)  # 给系统一些恢复时间
                            except:
                                pass  # 如果连恢复也失败，就直接继续

            except Exception as e:
                error_count += 1
                last_error_time = current_time
                logging.error(f"Main loop error ({error_count}/{max_errors_allowed}): {e}")
                logging.error(traceback.format_exc())

                # 如果连续错误过多，返回主菜单
                if error_count >= max_errors_allowed:
                    menu_active = True
                    game_state = None
                    try:
                        screen.fill(WHITE)
                        error_font = pygame.font.SysFont("SimHei", 24)
                        error_text = error_font.render("游戏出现严重错误，返回主菜单", True, (255, 0, 0))
                        screen.blit(error_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))
                        pygame.display.flip()
                        pygame.time.delay(2000)
                        error_count = 0
                    except:
                        # 如果连错误显示都失败，只能重置
                        pass

        # 使用我们的安全退出函数
        quit_game()

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        logging.error(traceback.format_exc())
        try:
            pygame.quit()
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()