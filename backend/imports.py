"""Import routes for GachaStats"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime

from .models import Account, GachaRecord
from .database import get_session
from .utils import parse_gacha_url, fetch_gacha_records

router = APIRouter()

@router.post("/api/import/official")
async def import_from_official(account_id: int, gacha_url: str, session: Session = Depends(get_session)):
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
async def import_manual(data: dict, session: Session = Depends(get_session)):
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
