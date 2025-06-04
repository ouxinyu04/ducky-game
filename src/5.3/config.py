import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")  # 移除 src
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")

import logging
logging.basicConfig(filename="game_errors.log", level=logging.INFO, encoding='utf-8')
logging.info(f"BASE_DIR 设置为: {BASE_DIR}")
logging.info(f"ASSETS_DIR 设置为: {ASSETS_DIR}")
logging.info(f"IMAGES_DIR 设置为: {IMAGES_DIR}")
