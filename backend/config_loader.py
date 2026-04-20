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
    # 服务器配置
    "host": "0.0.0.0",
    "port": 8777,
    "reload": False,

    # 数据库配置
    "database": {
        "path": None,  # None 表示使用默认本地路径 ~/.local/gachastats/gachastats.db
    },

    # 日志配置
    "logging": {
        "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
        "directory": None,  # None 表示使用项目根目录下的 logs/
        "max_size_mb": 10,
        "retention_days": 7,
        "error_retention_days": 30,
    },

    # 游戏登录页面配置
    "login_pages": {
        "genshin": "https://webstatic.mihoyo.com/hk4e/event/e20190909gacha-v3/index.html",
        "zzz": "https://zzz.hoyolab.com/#/zzz/zzz/zZZ/screen_record",
        "starrail": "https://webstatic.mihoyo.com/hkrpg/index.html"
    },

    # API 端点配置（米哈游抽卡 API）
    "api_endpoints": {
        "genshin": "https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog",
        "honkai3": "https://api-tachibana.mihoyo.com/event/gacha_info/api/getGachaLog",
        "starrail": "https://api-takumi.mihoyo.com/event/gacha_info/api/getGachaLog",
        "zzz": "https://api-takumi.mihoyo.com/event/gacha_info/api/getGachaLog",
    },

    # 浏览器配置
    "browser": {
        "headless": False,
        "timeout_seconds": 300,  # 登录等待超时时间
        "check_interval_seconds": 2,  # 检查登录状态间隔
        "args": ["--no-sandbox", "--disable-dev-shm-usage"]
    },

    # 抽卡导入配置
    "import": {
        "max_pages": 100,  # 单次导入最大页数
        "page_size": 20,   # 每页记录数
        "timeout_seconds": 10,  # API 请求超时
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


def get_database_path() -> str:
    """获取数据库路径

    Returns:
        数据库文件完整路径
    """
    config = get_config()
    db_path = config.get("database", {}).get("path")

    if db_path:
        return db_path

    # 默认使用本地目录（避免 CIFS 文件系统限制）
    from pathlib import Path
    local_db_dir = Path.home() / ".local" / "gachastats"
    local_db_dir.mkdir(parents=True, exist_ok=True)
    return str(local_db_dir / "gachastats.db")


def get_logging_config() -> Dict[str, Any]:
    """获取日志配置

    Returns:
        日志配置字典
    """
    config = get_config()
    return config.get("logging", DEFAULT_CONFIG["logging"])


def get_api_endpoints() -> Dict[str, str]:
    """获取米哈游抽卡 API 端点配置

    Returns:
        游戏类型 -> API URL 的字典
    """
    config = get_config()
    return config.get("api_endpoints", DEFAULT_CONFIG["api_endpoints"])


def get_browser_config() -> Dict[str, Any]:
    """获取浏览器配置

    Returns:
        浏览器配置字典
    """
    config = get_config()
    return config.get("browser", DEFAULT_CONFIG["browser"])


def get_import_config() -> Dict[str, Any]:
    """获取导入功能配置

    Returns:
        导入配置字典
    """
    config = get_config()
    return config.get("import", DEFAULT_CONFIG["import"])


def reload_config() -> None:
    """重新加载配置（清除缓存）"""
    get_config.cache_clear()
