#!/usr/bin/env python3
"""GachaStats 统一日志配置模块
提供标准化的日志配置，支持控制台和文件输出
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def setup_logging(
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    max_size_mb: int = 10,
    retention_days: int = 7,
    error_retention_days: int = 30
):
    """设置日志配置

    Args:
        log_dir: 日志目录，默认使用 PROJECT_ROOT/logs
        level: 控制台日志级别 (DEBUG, INFO, WARNING, ERROR)
        max_size_mb: 单个日志文件大小限制 (MB)
        retention_days: 普通日志保留天数
        error_retention_days: 错误日志保留天数

    配置包括:
    1. 控制台输出（指定级别以上）
    2. 文件输出（按大小轮转）
    3. 错误日志单独输出（保留更长时间）
    """

    # 优先级: 传入参数 > 配置文件 > 默认值
    if log_dir is None:
        try:
            from .config_loader import get_logging_config
            config = get_logging_config()
            cfg_dir = config.get("directory")
            if cfg_dir:
                log_dir = Path(cfg_dir)
            else:
                log_dir = PROJECT_ROOT / "logs"
            level = config.get("level", level)
            max_size_mb = config.get("max_size_mb", max_size_mb)
            retention_days = config.get("retention_days", retention_days)
            error_retention_days = config.get("error_retention_days", error_retention_days)
        except Exception:
            # 如果无法加载配置（如循环导入），使用默认值
            log_dir = PROJECT_ROOT / "logs"

    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除默认的日志处理器
    logger.remove()

    # 1. 控制台输出配置
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # 2. 普通日志文件输出（按大小轮转）
    logger.add(
        log_dir / "gachastats.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation=f"{max_size_mb} MB",
        retention=f"{retention_days} days",
        compression="zip",
        encoding="utf-8"
    )

    # 3. 错误日志单独输出（保留更长时间）
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=f"{max_size_mb} MB",
        retention=f"{error_retention_days} days",
        compression="zip",
        encoding="utf-8"
    )

    # 4. 访问日志（用于记录API请求）
    logger.add(
        log_dir / "access.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        filter=lambda record: "access" in record["extra"],
        rotation=f"{max_size_mb} MB",
        retention=f"{retention_days} days",
        compression="zip",
        encoding="utf-8"
    )

    logger.info("日志系统初始化完成")
    logger.info(f"日志目录: {log_dir}")
    logger.info(f"日志级别: {level}")

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