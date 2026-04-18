"""Import routes for GachaStats."""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from datetime import datetime
import json
import re

from .models import Account, GachaRecord
from .database import get_session
from .utils import parse_gacha_url, fetch_gacha_records

router = APIRouter()

@router.post("/api/import/official")
async def import_from_official(
    account_id: int,
    gacha_url: str,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """从官方抽卡链接导入数据"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    params = parse_gacha_url(gacha_url)
    auth_key = params.get("authkey", account.auth_key)
    if not auth_key:
        raise HTTPException(status_code=400, detail="无法获取authkey，请检查抽卡链接")
    gacha_types = {
        "genshin": ["100", "200", "301", "302"],
        "zzz": ["1", "2", "3", "4"],
        "starrail": ["1", "2", "11", "12"]
    }
    total_imported = 0
    for gacha_type in gacha_types.get(account.game_type, []):
        records = fetch_gacha_records(account.game_type, auth_key, gacha_type)
        for rec in records:
            gr = GachaRecord(
                account_id=account_id,
                gacha_type=gacha_type,
                gacha_name=rec.get("gacha_name", ""),
                item_name=rec.get("name", ""),
                item_type=rec.get("item_type", ""),
                rarity=int(rec.get("rank_type", 3)),
                time=rec.get("time", "")
            )
            session.add(gr)
            try:
                session.commit()
                total_imported += 1
            except Exception:
                session.rollback()
                continue
    account.last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.add(account)
    session.commit()
    return {"status": "success", "imported": total_imported, "message": f"成功导入 {total_imported} 条抽卡记录"}

@router.post("/api/import/manual")
async def import_manual(data: Dict[str, Any], session: Session = Depends(get_session)) -> Dict[str, Any]:
    """手动导入抽卡记录"""
    # Expected data schema: {"account_id": int, "records": List[dict]}
    account_id = data.get("account_id")
    records = data.get("records", [])
    imported = 0
    for rec in records:
        gr = GachaRecord(
            account_id=account_id,
            gacha_type=rec.get("gacha_type", ""),
            gacha_name=rec.get("gacha_name", ""),
            item_name=rec.get("item_name", ""),
            item_type=rec.get("item_type", ""),
            rarity=rec.get("rarity", 3),
            time=rec.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        session.add(gr)
        try:
            session.commit()
            imported += 1
        except Exception:
            session.rollback()
            continue
    return {"status": "success", "imported": imported, "message": f"成功导入 {imported} 条记录"}


@router.post("/api/import/json")
async def import_from_json(
    account_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """从 JSON 文件导入抽卡记录，支持多种格式（wish-export、snap-genshin 等）"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="请上传 JSON 文件")

    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    records = []

    # 检测并解析不同格式
    if isinstance(data, list):
        # wish-export 格式: 直接是记录列表
        records = _parse_wish_export_format(data, account)
    elif isinstance(data, dict):
        if 'result' in data and isinstance(data['result'], list):
            # snap-genshin 格式
            records = _parse_snap_genshin_format(data['result'], account)
        elif 'list' in data and isinstance(data['list'], list):
            # 通用列表格式
            records = _parse_generic_format(data['list'], account)
        elif 'data' in data and isinstance(data['data'], list):
            # 其他通用格式
            records = _parse_generic_format(data['data'], account)
        else:
            # 尝试直接解析 dict 键值
            records = _parse_dict_format(data, account)

    if not records:
        raise HTTPException(status_code=400, detail="未能识别的数据格式")

    # 导入记录
    imported = 0
    skipped = 0
    for rec in records:
        gr = GachaRecord(
            account_id=account_id,
            gacha_type=rec.get("gacha_type", ""),
            gacha_name=rec.get("gacha_name", ""),
            item_name=rec.get("item_name", ""),
            item_type=rec.get("item_type", ""),
            rarity=rec.get("rarity", 3),
            time=rec.get("time", ""),
            pity=rec.get("pity", 0),
            is_new=rec.get("is_new", False)
        )
        session.add(gr)
        try:
            session.commit()
            imported += 1
        except Exception:
            session.rollback()
            skipped += 1
            continue

    # 更新账号同步时间
    account.last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.add(account)
    session.commit()

    return {
        "status": "success",
        "imported": imported,
        "skipped": skipped,
        "message": f"成功导入 {imported} 条记录，跳过 {skipped} 条重复记录"
    }


def _parse_wish_export_format(data: List[Dict], account: Account) -> List[Dict]:
    """解析 wish-export 格式"""
    records = []
    for item in data:
        if not isinstance(item, dict):
            continue
        record = _normalize_record(item, account.game_type)
        if record:
            records.append(record)
    return records


def _parse_snap_genshin_format(data: List[Dict], account: Account) -> List[Dict]:
    """解析 Snap Genshin 格式"""
    records = []
    for item in data:
        if not isinstance(item, dict):
            continue
        record = _normalize_record(item, account.game_type)
        if record:
            records.append(record)
    return records


def _parse_generic_format(data: List[Dict], account: Account) -> List[Dict]:
    """解析通用列表格式"""
    records = []
    for item in data:
        if not isinstance(item, dict):
            continue
        record = _normalize_record(item, account.game_type)
        if record:
            records.append(record)
    return records


def _parse_dict_format(data: Dict, account: Account) -> List[Dict]:
    """解析字典格式（键为卡池类型，值为记录列表）"""
    records = []
    for gacha_type, items in data.items():
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                record = _normalize_record(item, account.game_type, gacha_type)
                if record:
                    records.append(record)
    return records


def _normalize_record(item: Dict, game_type: str, default_gacha_type: str = "") -> Dict:
    """标准化记录格式"""
    # 字段映射
    time_fields = ['time', 'datetime', 'timestamp', 'create_time', '抽卡时间', '时间']
    name_fields = ['name', 'item_name', 'item', '物品名称', '物品', '角色', '武器']
    type_fields = ['item_type', 'type', '物品类型', '类型']
    rarity_fields = ['rank_type', 'rarity', 'rare', 'star', 'rank', '稀有度', '星级']
    gacha_fields = ['gacha_type', 'gacha_id', 'pool', 'banner', '卡池类型', '祈愿类型', '卡池']
    gacha_name_fields = ['gacha_name', 'pool_name', 'banner_name', '卡池名称']

    def get_field(mapping: List[str]):
        for field in mapping:
            if field in item:
                return item[field]
        return None

    # 获取时间
    time_val = get_field(time_fields) or ""
    if time_val:
        # 统一时间格式
        time_str = str(time_val)
        if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', time_str):
            pass
        elif re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', time_str):
            time_str = time_str.replace('T', ' ')[:19]
        elif re.match(r'^\d{10}$', time_str):
            time_str = datetime.fromtimestamp(int(time_str)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            try:
                time_str = str(datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                               .replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S"))
            except:
                time_str = time_str
    else:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 获取物品名称
    item_name = get_field(name_fields) or "未知物品"

    # 获取物品类型
    item_type = get_field(type_fields) or "角色"
    if 'weapon' in str(item_type).lower() or '武器' in str(item_type):
        item_type = "武器"
    else:
        item_type = "角色"

    # 获取稀有度
    rarity = get_field(rarity_fields)
    try:
        rarity = int(rarity) if rarity else 3
    except:
        rarity = 3

    # 获取卡池类型
    gacha_type = get_field(gacha_fields)
    if not gacha_type:
        gacha_type = default_gacha_type or _infer_gacha_type(game_type, item)

    # 获取卡池名称
    gacha_name = get_field(gacha_name_fields) or ""

    return {
        "time": time_str,
        "item_name": str(item_name),
        "item_type": item_type,
        "rarity": rarity,
        "gacha_type": str(gacha_type),
        "gacha_name": str(gacha_name) if gacha_name else "",
        "pity": 0,
        "is_new": False
    }


def _infer_gacha_type(game_type: str, item: Dict) -> str:
    """推断卡池类型"""
    # 根据物品名称或ID推断
    item_name = str(item.get('name', item.get('item_name', ''))).lower()

    # 检查是否是限定物品（需要维护列表，这里简单处理）
    # 优先检查字段
    if 'pool' in item:
        pool = str(item['pool']).lower()
        if 'char' in pool or 'role' in pool or 'character' in pool:
            return '301'
        elif 'weapon' in pool or '武器' in pool:
            return '302'

    # 根据游戏类型返回默认值
    gacha_defaults = {
        'genshin': '301',  # 角色活动
        'honkai': '1',     # 扩充
        'starrail': '11',  # 角色活动跃迁
        'zenless': '1'     # 独家频段
    }
    return gacha_defaults.get(game_type, '301')
