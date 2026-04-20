"""Utility functions for GachaStats."""
from typing import Dict, List, Any
import requests
from datetime import datetime
from fastapi import HTTPException
from .logging_config import logger
from .config_loader import get_api_endpoints, get_import_config


def parse_gacha_url(url: str) -> Dict[str, str]:
    """Parse gacha URL and extract query parameters."""
    params = {}
    if "?" in url:
        query_string = url.split("?")[1]
        for param in query_string.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
    return params


def fetch_gacha_records(game_type: str, auth_key: str, gacha_type: str, end_id: str = "0") -> List[Dict[str, Any]]:
    """Fetch gacha records from official API."""
    # 从配置加载器获取 API 端点和导入配置（支持用户自定义）
    base_urls = get_api_endpoints()
    import_config = get_import_config()
    base_url = base_urls.get(game_type, base_urls.get("genshin"))

    max_pages = import_config.get("max_pages", 100)
    page_size = import_config.get("page_size", 20)
    timeout_seconds = import_config.get("timeout_seconds", 10)

    params = {
        "authkey": auth_key,
        "authkey_ver": "1",
        "sign_type": "2",
        "lang": "zh-cn",
        "gacha_type": gacha_type,
        "page": "1",
        "size": str(page_size),
        "end_id": end_id,
    }
    all_records = []
    for _ in range(max_pages):
        try:
            response = requests.get(base_url, params=params, timeout=timeout_seconds)
            response.raise_for_status()
            data = response.json()
            if data.get("retcode") != 0:
                break
            list_data = data["data"]["list"]
            if not list_data:
                break
            all_records.extend(list_data)
            params["end_id"] = list_data[-1]["id"]
            if len(list_data) < page_size:
                break
        except Exception as e:
            logger.error(f"获取抽卡记录失败: {e}")
            break
    return all_records


def calculate_pity(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate pity statistics from gacha records.

    Args:
        records: List of dictionaries containing rarity and time information

    Returns:
        Dictionary containing pity analysis:
        - total_pulls: Total number of pulls
        - current_pity: Current pity count since last 5-star
        - last_five_star_index: Index of last 5-star pull
        - pity_distribution: Count by rarity
        - pity_statistics: Min, max, average pity between 5-stars
    """
    if not records:
        return {
            "total_pulls": 0,
            "current_pity": 0,
            "pity_distribution": {"five_star": 0, "four_star": 0, "three_star": 0},
            "pity_statistics": {"min": 0, "max": 0, "avg": 0}
        }

    total_pulls = len(records)

    # Count by rarity
    pity_distribution = {
        "five_star": 0,
        "four_star": 0,
        "three_star": 0
    }

    # Calculate pity intervals
    pity_list = []
    current_pity = 0
    last_five_star_index = -1

    for i, record in enumerate(records):
        current_pity += 1
        rarity = record.get("rarity", 0)

        if rarity >= 5:
            pity_distribution["five_star"] += 1
            pity_list.append(current_pity)
            current_pity = 0
            last_five_star_index = i
        elif rarity == 4:
            pity_distribution["four_star"] += 1
        elif rarity == 3:
            pity_distribution["three_star"] += 1

    # Calculate statistics
    if pity_list:
        min_pity = min(pity_list)
        max_pity = max(pity_list)
        avg_pity = sum(pity_list) / len(pity_list)
        pity_stats = {
            "min": min_pity,
            "max": max_pity,
            "avg": round(avg_pity, 2)
        }
    else:
        # No 5-stars found
        current_pity = total_pulls # Count from the beginning
        pity_stats = {"min": 0, "max": 0, "avg": 0}

    return {
        "total_pulls": total_pulls,
        "current_pity": current_pity,
        "last_five_star_index": last_five_star_index,
        "pity_distribution": pity_distribution,
        "pity_statistics": pity_stats
    }
