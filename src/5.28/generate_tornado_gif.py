#!/usr/bin/env python3
"""
生成龙卷风效果GIF文件
从 tornado.png 精灵图生成 tornado_effect.gif 动画文件
"""

import os
import sys
import pygame
from PIL import Image
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入项目模块
from utils import load_image
from config import ASSETS_DIR

def generate_tornado_gif():
    """
    生成龙卷风效果GIF文件
    
    步骤：
    1. 加载 tornado.png 精灵图
    2. 分割为10个44x33的帧（水平排列）
    3. 将每帧放大到132x99（3倍）
    4. 生成GIF文件，每帧200毫秒，无限循环
    """
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 文件路径
    source_path = os.path.join(ASSETS_DIR, "tornado.png")
    output_path = os.path.join(ASSETS_DIR, "tornado_effect.gif")
    
    print(f"源文件路径: {source_path}")
    print(f"输出文件路径: {output_path}")
    
    # 检查源文件是否存在
    if not os.path.exists(source_path):
        print(f"错误: 源文件不存在 - {source_path}")
        return False
    
    try:
        # 步骤1: 加载精灵图
        print("步骤1: 加载精灵图...")
        sprite_sheet = load_image(source_path)
        
        if sprite_sheet is None:
            print("错误: 无法加载精灵图")
            return False
        
        print(f"精灵图尺寸: {sprite_sheet.get_size()}")
        
        # 步骤2: 分割为10个44x33的帧
        print("步骤2: 分割帧...")
        frames = []
        frame_positions = [
            (0, 0, 44, 33),       # 第1帧
            (44, 0, 88, 33),      # 第2帧
            (88, 0, 132, 33),     # 第3帧
            (132, 0, 176, 33),    # 第4帧
            (176, 0, 220, 33),    # 第5帧
            (220, 0, 264, 33),    # 第6帧
            (264, 0, 308, 33),    # 第7帧
            (308, 0, 352, 33),    # 第8帧
            (352, 0, 396, 33),    # 第9帧
            (396, 0, 440, 33)     # 第10帧
        ]
        
        for i, (x, y, x2, y2) in enumerate(frame_positions):
            # 创建44x33的帧
            frame_surface = pygame.Surface((44, 33), pygame.SRCALPHA)
            frame_rect = pygame.Rect(x, y, 44, 33)
            frame_surface.blit(sprite_sheet, (0, 0), frame_rect)
            
            # 步骤3: 放大到132x99（3倍）
            scaled_frame = pygame.transform.scale(frame_surface, (132, 99))
            frames.append(scaled_frame)
            
            print(f"  处理第{i+1}帧: ({x}, {y}) -> 132x99")
        
        print(f"成功分割并放大了 {len(frames)} 帧")
        
        # 步骤4: 转换为PIL图像并生成GIF
        print("步骤4: 生成GIF文件...")
        pil_frames = []
        
        for i, frame in enumerate(frames):
            # 将pygame surface转换为PIL图像
            # 首先转换为字符串数据
            frame_string = pygame.image.tostring(frame, 'RGBA')
            # 创建PIL图像
            pil_image = Image.frombytes('RGBA', frame.get_size(), frame_string)
            pil_frames.append(pil_image)
            print(f"  转换第{i+1}帧为PIL格式")
        
        # 保存为GIF
        if pil_frames:
            pil_frames[0].save(
                output_path,
                save_all=True,
                append_images=pil_frames[1:],
                duration=200,  # 每帧200毫秒
                loop=0,        # 无限循环
                transparency=0,
                disposal=2
            )
            
            print(f"成功生成GIF文件: {output_path}")
            print(f"  帧数: {len(pil_frames)}")
            print(f"  每帧时长: 200毫秒")
            print(f"  循环: 无限")
            print(f"  尺寸: 132x99像素")
            
            return True
        else:
            print("错误: 没有生成任何帧")
            return False
            
    except Exception as e:
        print(f"生成GIF时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_gif():
    """验证生成的GIF文件"""
    output_path = os.path.join(ASSETS_DIR, "tornado_effect.gif")
    
    if not os.path.exists(output_path):
        print("验证失败: GIF文件不存在")
        return False
    
    try:
        # 使用PIL验证GIF
        gif = Image.open(output_path)
        frame_count = gif.n_frames
        
        print(f"\n验证GIF文件:")
        print(f"  文件路径: {output_path}")
        print(f"  文件大小: {os.path.getsize(output_path)} 字节")
        print(f"  帧数: {frame_count}")
        print(f"  图像尺寸: {gif.size}")
        print(f"  图像模式: {gif.mode}")
        
        # 检查每一帧
        for i in range(frame_count):
            gif.seek(i)
            print(f"  第{i+1}帧: {gif.size}")
        
        print("验证成功!")
        return True
        
    except Exception as e:
        print(f"验证GIF时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("=== 龙卷风效果GIF生成器 ===")
    print()
    
    # 初始化pygame（用于图像处理）
    pygame.init()
    
    # 生成GIF
    success = generate_tornado_gif()
    
    if success:
        print()
        # 验证生成的GIF
        verify_gif()
        print()
        print("✅ 龙卷风效果GIF生成完成!")
        print("文件已保存为: tornado_effect.gif")
        print("可以替代原有的龙卷风效果文件使用。")
    else:
        print()
        print("❌ 龙卷风效果GIF生成失败!")
        print("请检查源文件是否存在，以及是否有写入权限。")
    
    pygame.quit()

if __name__ == "__main__":
    main()
