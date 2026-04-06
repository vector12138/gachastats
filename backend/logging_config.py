#!/usr/bin/env python3
"""
GachaStats 统一日志配置模块
提供标准化的日志配置，支持控制台和文件输出
"""

import os
import sys
from pathlib import Path
from loguru import logger

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

def setup_logging():
    """
    设置日志配置
    
    配置包括：
    1. 控制台输出（INFO级别以上）
    2. 文件输出（按大小轮转，保留7天）
    3. 错误日志单独输出（保留30天）
    """
    
    # 日志目录
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 1. 控制台输出配置
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # 2. 普通日志文件输出（按大小轮转）
    logger.add(
        log_dir / "gachastats.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",  # 文件达到10MB时轮转
        retention="7 days",  # 保留7天的日志
        compression="zip",  # 轮转时压缩旧日志
        encoding="utf-8"
    )
    
    # 3. 错误日志单独输出（保留更长时间）
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",  # 错误日志保留30天
        compression="zip",
        encoding="utf-8"
    )
    
    # 4. 访问日志（用于记录API请求）
    logger.add(
        log_dir / "access.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        filter=lambda record: "access" in record["extra"],
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")
    logger.info(f"日志目录: {log_dir}")
    
    return logger

# 创建访问日志记录器
access_logger = logger.bind(access=True)

if __name__ == "__main__":
    # 测试日志配置
    setup_logging()
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    access_logger.info("GET /api/test 200 12ms")