#!/usr/bin/env python3
"""
动画工具模块
提供通用的动画加载和播放功能
"""

import os
import pygame
import logging
from PIL import Image
from config import ASSETS_DIR

def load_animation_frames(animation_name, fallback_image_name=None, target_size=None):
    """
    加载动画帧

    参数:
    animation_name: 动画GIF文件名 (如 "chicken_animation.gif")
    fallback_image_name: 备用静态图像文件名 (如 "lady_duck.png")
    target_size: 目标尺寸 (width, height)，如果为None则使用原始尺寸

    返回:
    (frames_list, is_animated) - 帧列表和是否为动画的标志
    """
    frames = []
    is_animated = False

    # 尝试加载GIF动画
    gif_path = os.path.join(ASSETS_DIR, animation_name)
    if os.path.exists(gif_path):
        try:
            gif = Image.open(gif_path)
            for frame in range(gif.n_frames):
                gif.seek(frame)
                frame_image = gif.convert("RGBA")

                # 创建带透明度的pygame surface
                pygame_image = pygame.Surface(frame_image.size, pygame.SRCALPHA)
                pygame_image = pygame.image.fromstring(frame_image.tobytes(), frame_image.size, frame_image.mode)

                # 确保surface支持透明度
                pygame_image = pygame_image.convert_alpha()

                # 如果指定了目标尺寸，进行缩放
                if target_size:
                    # 创建带透明度的缩放surface
                    scaled_surface = pygame.Surface(target_size, pygame.SRCALPHA)
                    pygame.transform.scale(pygame_image, target_size, scaled_surface)
                    pygame_image = scaled_surface

                frames.append(pygame_image)

            if frames:
                is_animated = True
                logging.info(f"Loaded {len(frames)} frames for animation: {animation_name}")
                return frames, is_animated

        except Exception as e:
            logging.error(f"Failed to load animation {animation_name}: {e}")

    # 如果GIF加载失败，尝试加载备用静态图像
    if fallback_image_name:
        image_path = os.path.join(ASSETS_DIR, fallback_image_name)
        if os.path.exists(image_path):
            try:
                image = pygame.image.load(image_path)
                if target_size:
                    image = pygame.transform.scale(image, target_size)
                frames = [image]
                logging.info(f"Loaded fallback image: {fallback_image_name}")
                return frames, is_animated
            except pygame.error as e:
                logging.error(f"Failed to load fallback image {fallback_image_name}: {e}")

    return frames, is_animated

def update_animation_frame(current_frame, frame_count, last_update_time, frame_duration=200):
    """
    更新动画帧

    参数:
    current_frame: 当前帧索引
    frame_count: 总帧数
    last_update_time: 上次更新时间
    frame_duration: 每帧持续时间（毫秒）

    返回:
    (new_frame_index, new_last_update_time)
    """
    current_time = pygame.time.get_ticks()
    if current_time - last_update_time >= frame_duration:
        new_frame = (current_frame + 1) % frame_count
        return new_frame, current_time
    return current_frame, last_update_time

def draw_animated_sprite(screen, frames, current_frame, x, y, is_animated=True):
    """
    绘制动画精灵

    参数:
    screen: pygame屏幕对象
    frames: 帧列表
    current_frame: 当前帧索引
    x, y: 绘制位置
    is_animated: 是否为动画
    """
    if frames:
        if is_animated and len(frames) > 1:
            screen.blit(frames[current_frame], (x, y))
        else:
            screen.blit(frames[0], (x, y))

class AnimatedSprite:
    """
    动画精灵类
    """
    def __init__(self, animation_name, fallback_image_name=None, target_size=None, frame_duration=200):
        self.frames, self.is_animated = load_animation_frames(animation_name, fallback_image_name, target_size)
        self.current_frame = 0
        self.last_frame_update = 0
        self.frame_duration = frame_duration

    def update(self):
        """更新动画"""
        if self.is_animated and len(self.frames) > 1:
            self.current_frame, self.last_frame_update = update_animation_frame(
                self.current_frame, len(self.frames), self.last_frame_update, self.frame_duration
            )

    def draw(self, screen, x, y):
        """绘制动画"""
        draw_animated_sprite(screen, self.frames, self.current_frame, x, y, self.is_animated)
