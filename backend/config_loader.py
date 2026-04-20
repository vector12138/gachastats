"""配置加载模块 - 提供统一的配置访问接口

用法:
    from backend.config_loader import get_config, get_login_pages

    config = get_config()  # 返回原始配置字典
    login_pages = get_login_pages()  # 获取登录页面配置
"""

import json
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any


# 默认配置
DEFAULT_CONFIG: Dict[str, Any] = {
    "host": "0.0.0.0",
    "port": 8777,
    "reload": False,
    "login_pages": {
        "genshin": "https://webstatic.mihoyo.com/hk4e/event/e20190909gacha-v3/index.html",
        "zzz": "https://zzz.hoyolab.com/#/zzz/zzz/zZZ/screen_record",
        "starrail": "https://webstatic.mihoyo.com/hkrpg/index.html"
    }
}


def _find_config_file() -> Path:
    """查找配置文件位置"""
    # 可能的配置文件位置（按优先级）
    possible_paths = [
        Path("config.json"),  # 当前目录
        Path(__file__).parent.parent / "config.json",  # 项目根目录
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


@lru_cache(maxsize=1)
def get_config() -> Dict[str, Any]:
    """获取配置对象（带缓存，首次调用时加载文件）

    Returns:
        合并后的配置字典（用户配置 + 默认值）
    """
    config = DEFAULT_CONFIG.copy()

    config_path = _find_config_file()
    if config_path:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # 深度合并配置
                _deep_merge(config, user_config)
        except Exception as e:
            print(f"[Config] 无法读取配置文件，使用默认值: {e}")

    return config


def _deep_merge(base: Dict, override: Dict) -> None:
    """深度合并两个字典"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def get_login_pages() -> Dict[str, str]:
    """获取登录页面配置

    Returns:
        游戏类型 -> URL 的字典
    """
    config = get_config()
    return config.get("login_pages", DEFAULT_CONFIG["login_pages"])


def reload_config() -> None:
    """重新加载配置（清除缓存）"""
    get_config.cache_clear()
