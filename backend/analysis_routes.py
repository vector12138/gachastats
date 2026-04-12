"""Analysis routes for GachaStats."""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .models import Account, GachaRecord
from .database import get_session

router = APIRouter()


@router.get("/api/analysis/{account_id}")
async def get_analysis(
    account_id: int,
    gacha_type: Optional[str] = None,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取抽卡分析报告"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    stmt = select(GachaRecord).where(GachaRecord.account_id == account_id)
    if gacha_type:
        stmt = stmt.where(GachaRecord.gacha_type == gacha_type)
    records_objs = session.exec(stmt.order_by(GachaRecord.time.asc())).all()
    records = [(r.gacha_type, r.gacha_name, r.item_name, r.item_type, r.rarity, r.time) for r in records_objs]

    if not records:
        return {"status": "success", "data": {"message": "暂无抽卡数据"}}

    # 基础统计
    total_pulls = len(records)
    five_star_count = sum(1 for r in records if r[4] == 5)
    four_star_count = sum(1 for r in records if r[4] == 4)

    # 计算各个卡池的水位
    from collections import defaultdict
    pool_records = defaultdict(list)
    for r in records:
        pool_records[r[0]].append(r)

    pool_pity = {}
    five_star_history = []
    for pool_type, pool_data in pool_records.items():
        current_pity = 0
        pity_list = []
        for r in pool_data:
            current_pity += 1
            if r[4] == 5:
                pity_list.append(current_pity)
                five_star_history.append({
                    "name": r[2],
                    "pity": current_pity,
                    "time": r[5],
                    "pool": r[1]
                })
                current_pity = 0

        if pity_list:
            avg_pity = sum(pity_list) / len(pity_list)
            min_pity = min(pity_list)
            max_pity = max(pity_list)
        else:
            avg_pity = min_pity = max_pity = 0

        next_prob = 0.6 if current_pity <= 73 else 0.6 + (current_pity - 73) * 6

        pool_pity[pool_type] = {
            "current_pity": current_pity,
            "five_star_count": len(pity_list),
            "avg_pity": round(avg_pity, 1),
            "min_pity": min_pity,
            "max_pity": max_pity,
            "next_five_star_prob": round(next_prob, 2)
        }

    # 欧非评级
    five_star_rate = (five_star_count / total_pulls) * 100 if total_pulls > 0 else 0
    if five_star_rate >= 2.0:
        level = "欧皇"
        comment = "你是真正的欧皇，快让我吸吸欧气！"
    elif five_star_rate >= 1.6:
        level = "正常水平"
        comment = "抽卡运气正常，继续保持~"
    elif five_star_rate >= 1.0:
        level = "非酋"
        comment = "稍微有点非，下次一定欧！"
    else:
        level = "究极非酋"
        comment = "这运气，建议去买彩票反向选号！"

    analysis = {
        "account_info": {
            "game_type": account.game_type,
            "account_name": account.account_name,
            "uid": account.uid
        },
        "basic_stats": {
            "total_pulls": total_pulls,
            "five_star_count": five_star_count,
            "four_star_count": four_star_count,
            "five_star_rate": round(five_star_rate, 2),
            "four_star_rate": round((four_star_count / total_pulls) * 100, 2) if total_pulls > 0 else 0
        },
        "pool_pity": pool_pity,
        "five_star_history": sorted(five_star_history, key=lambda x: x["time"], reverse=True),
        "level": level,
        "comment": comment
    }
    return {"status": "success", "data": analysis}


@router.get("/api/statistics/all")
async def get_all_statistics(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """获取所有账号的统计对比"""
    accounts = session.exec(select(Account)).all()
    result = []
    for acc in accounts:
        records = session.exec(select(GachaRecord).where(GachaRecord.account_id == acc.id)).all()
        total = len(records)
        five_star = sum(1 for r in records if r.rarity == 5)
        rate = (five_star / total) * 100 if total > 0 else 0
        result.append({
            "account_id": acc.id,
            "game_type": acc.game_type,
            "account_name": acc.account_name,
            "uid": acc.uid,
            "total_pulls": total,
            "five_star_count": five_star,
            "five_star_rate": round(rate, 2)
        })
    return {"status": "success", "data": result}