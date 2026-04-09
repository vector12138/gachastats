"""Utility functions for GachaStats"""
import requests
from datetime import datetime
from fastapi import HTTPException
from .logging_config import logger


def parse_gacha_url(url: str) -> dict:
    """Parse gacha URL and extract query parameters."""
    params = {}
    if "?" in url:
        query_string = url.split("?")[1]
        for param in query_string.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
    return params


def fetch_gacha_records(game_type: str, auth_key: str, gacha_type: str, end_id: str = "0") -> list[dict]:
    """Fetch gacha records from official API."""
    base_urls = {
        "genshin": "https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog",
        "zzz": "https://zzz-zero-api.mihoyo.com/event/zzz_gacha/api/getGachaLog",
        "starrail": "https://api-takumi.mihoyo.com/common/gacha_record/api/getGachaLog",
    }
    if game_type not in base_urls:
        raise HTTPException(status_code=400, detail="不支持的游戏类型")
    base_url = base_urls[game_type]
    params = {
        "authkey": auth_key,
        "authkey_ver": "1",
        "sign_type": "2",
        "lang": "zh-cn",
        "gacha_type": gacha_type,
        "page": "1",
        "size": "20",
        "end_id": end_id,
    }
    all_records = []
    max_pages = 100
    for _ in range(max_pages):
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("retcode") != 0:
                break
            list_data = data["data"]["list"]
            if not list_data:
                break
            all_records.extend(list_data)
            params["end_id"] = list_data[-1]["id"]
            if len(list_data) < 20:
                break
        except Exception as e:
            logger.error(f"获取抽卡记录失败: {e}")
            break
    return all_records
