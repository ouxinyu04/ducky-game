# main.py 更新版本 - 错误处理改进
import pygame
import sys
import logging
import traceback
import os
from duck import Duck
from game_state import GameState
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK

# 设置日志配置
logging.basicConfig(
    filename="game_errors.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 忽略libpng警告
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


def main():
    try:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("鸭子冒险游戏")
        font = pygame.font.SysFont("SimHei", 32)

        # 游戏状态
        game_state = None
        menu_active = True

        # 按钮区域
        start_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, 200, 100)

        def draw_menu():
            screen.fill(WHITE)
            pygame.draw.rect(screen, (0, 255, 0), start_button)
            text = font.render("开始游戏", True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 20))

            # 添加游戏说明
            title = font.render("鸭子冒险游戏", True, BLACK)
            screen.blit(title, (SCREEN_WIDTH // 2 - 80, 50))

            instructions = [
                "游戏目标: 收集伙伴和武器，击败最终BOSS",
                "控制: WASD移动，空格互动，鼠标点击",
                "关卡: 5个关卡，最后一关为BOSS战",
                "战斗: 选择伙伴攻击，使用技能，管理MP"
            ]

            for i, line in enumerate(instructions):
                text = pygame.font.SysFont("SimHei", 24).render(line, True, BLACK)
                screen.blit(text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 80 + i * 30))

            pygame.display.flip()

        # 用于检测连续错误
        error_count = 0
        last_error_time = 0
        max_errors_allowed = 3  # 允许的最大连续错误数
        error_timeout = 5000  # 错误重置时间（毫秒）

        running = True
        while running:
            try:
                current_time = pygame.time.get_ticks()

                # 重置错误计数器（如果已经过了足够的时间）
                if current_time - last_error_time > error_timeout:
                    error_count = 0

                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and menu_active:
                        if start_button.collidepoint(event.pos):
                            # 初始化游戏状态
                            try:
                                duck = Duck(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                                game_state = GameState(duck)
                                menu_active = False
                                logging.info("Game started")
                                error_count = 0  # 重置错误计数
                            except Exception as e:
                                logging.error(f"Error initializing game: {e}")
                                logging.error(traceback.format_exc())
                                # 显示错误提示给用户
                                error_font = pygame.font.SysFont("SimHei", 20)
                                error_text = error_font.render("游戏初始化失败，请查看日志文件", True, (255, 0, 0))
                                screen.blit(error_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 50))
                                pygame.display.flip()
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        if not menu_active:
                            # 按ESC返回主菜单
                            menu_active = True
                            game_state = None
                        else:
                            running = False

                if menu_active:
                    draw_menu()
                else:
                    if game_state is None:
                        continue  # 防止 game_state 未初始化

                    # 使用try-except捕获游戏更新过程中的错误
                    try:
                        keys = pygame.key.get_pressed()
                        game_state.update(screen, keys, events)
                        pygame.display.flip()
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

        pygame.quit()
        sys.exit()

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        logging.error(traceback.format_exc())
        try:
            pygame.quit()
        except:
            pass
        sys.exit()


if __name__ == "__main__":
    main()