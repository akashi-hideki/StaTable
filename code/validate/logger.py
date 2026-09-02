# codegen/validate/logger.py
"""
検証モジュール用ロガー設定
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str = "validate", log_dir: str = None) -> logging.Logger:
    """ロガーをセットアップ"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # ファイルハンドラ
    if log_dir is None:
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'logs'
        )
    
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'validate_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    logger.debug(f"Logger setup completed: {name} -> {log_file}")
    return logger


# デフォルトロガー
logger = setup_logger()