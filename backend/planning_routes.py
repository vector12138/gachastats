"""Planning routes for GachaStats - provides gacha planning recommendations."""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from collections import defaultdict

from .models import Account, GachaRecord
from .database import get_session

router = APIRouter()


@router.get("/api/planning/{account_id}")
async def get_planning_recommendations(
    account_id: int,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """基于历史数据提供抽卡策略建议"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 获取抽卡记录
    records = session.exec(
        select(GachaRecord)
        .where(GachaRecord.account_id == account_id)
        .order_by(GachaRecord.time.asc())
    ).all()

    if not records:
        return {
            "status": "success",
            "data": {
                "message": "暂无抽卡数据，建议先导入数据",
                "historical_avg_pity": None,
                "current_pity_status": {},
                "recommendations": []
            }
        }

    # 按卡池类型分组分析
    pool_analysis = analyze_by_pool(records)

    # 生成建议
    recommendations = generate_recommendations(pool_analysis, account.game_type)

    # 计算攒抽建议
    saving_plan = calculate_saving_plan(pool_analysis)

    return {
        "status": "success",
        "data": {
            "historical_avg_pity": calculate_overall_avg_pity(records),
            "current_pity_status": pool_analysis,
            "luck_rating": calculate_luck_rating(records),
            "recommendations": recommendations,
            "saving_plan": saving_plan,
            "next_legendary_probability": calculate_next_probabilities(pool_analysis)
        }
    }


def analyze_by_pool(records: List[GachaRecord]) -> Dict[str, Any]:
    """按卡池分析当前水位和历史数据"""
    pool_records = defaultdict(list)
    for r in records:
        pool_records[r.gacha_type].append(r)

    pool_analysis = {}
    for pool_type, pool_data in pool_records.items():
        pity_list = []
        current_pity = 0

        for record in pool_data:
            current_pity += 1
            if record.rarity == 5:
                pity_list.append(current_pity)
                current_pity = 0

        # 计算统计数据
        if pity_list:
            avg_pity = sum(pity_list) / len(pity_list)
            min_pity = min(pity_list)
            max_pity = max(pity_list)
            total_five_star = len(pity_list)
        else:
            avg_pity = min_pity = max_pity = total_five_star = 0

        # 计算下次五星概率
        next_probability = calculate_probability_at_pity(current_pity)

        pool_analysis[pool_type] = {
            "current_pity": current_pity,
            "historical_avg_pity": round(avg_pity, 2),
            "min_pity": min_pity,
            "max_pity": max_pity,
            "total_five_star": total_five_star,
            "next_probability": next_probability,
            "pulls_to_soft_pity": max(0, 74 - current_pity),  # 74抽开始软保底
            "pulls_to_hard_pity": max(0, 90 - current_pity),  # 90抽硬保底
            "recommended_action": get_recommended_action(current_pity, avg_pity)
        }

    return pool_analysis


def calculate_overall_avg_pity(records: List[GachaRecord]) -> float:
    """计算整体平均五星水位"""
    pity_list = []
    current_pity = 0

    for r in records:
        current_pity += 1
        if r.rarity == 5:
            pity_list.append(current_pity)
            current_pity = 0

    return round(sum(pity_list) / len(pity_list), 2) if pity_list else 0


def calculate_probability_at_pity(pity: int) -> Dict[str, float]:
    """计算在当前水位的五星概率"""
    base_rate = 0.6  # 基础概率 0.6%

    if pity <= 73:
        probability = base_rate
        expected_pulls = 90
    elif pity < 90:
        # 74-89抽概率递增
        probability = base_rate + (pity - 73) * 6.0  # 每抽增加6%
        expected_pulls = 90 - pity
    else:
        probability = 100.0
        expected_pulls = 1

    return {
        "current_rate": round(probability, 2),
        "expected_pulls": expected_pulls,
        "to_soft_pity": max(0, 74 - pity),
        "to_hard_pity": max(0, 90 - pity)
    }


def get_recommended_action(current_pity: int, avg_pity: float) -> str:
    """基于当前水位给出建议"""
    if current_pity >= 80:
        return "immediate"  # 立即抽
    elif current_pity >= 74:
        return "consider"  # 考虑抽
    elif current_pity >= 60:
        return "prepare"  # 准备抽
    elif avg_pity > 0 and current_pity >= avg_pity * 0.8:
        return "watch"  # 观望
    else:
        return "save"  # 攒抽


def generate_recommendations(pool_analysis: Dict[str, Any], game_type: str) -> List[Dict[str, Any]]:
    """生成抽卡建议列表"""
    recs = []

    # 游戏类型对应的货币名称
    currency_names = {
        "genshin": {"currency": "原石", "fate": "纠缠之缘/相遇之缘"},
        "starrail": {"currency": "星琼", "fate": "星轨专票/星轨通票"},
        "zzz": {"currency": "菲林", "fate": "加密母带/原装母带"},
        "honkai": {"currency": "水晶", "fate": "补给卡"}
    }
    cn = currency_names.get(game_type, currency_names["genshin"])

    for pool_type, analysis in pool_analysis.items():
        pity = analysis["current_pity"]
        action = analysis["recommended_action"]

        if action == "immediate":
            recs.append({
                "priority": "high",
                "pool": pool_type,
                "title": "🎯 立即抽取",
                "message": f"当前水位 {pity}，距离保底仅剩 {90 - pity} 抽，五星概率已达 {analysis['next_probability']['current_rate']}%！",
                "action": "pull_now",
                "needed_currency": (90 - pity) * 160
            })
        elif action == "consider":
            recs.append({
                "priority": "medium",
                "pool": pool_type,
                "title": "⏰ 考虑抽取",
                "message": f"当前水位 {pity}，下 {74 - pity} 抽后将进入软保底（概率递增）。",
                "action": "consider_pull",
                "needed_currency": (74 - pity) * 160
            })
        elif action == "prepare":
            recs.append({
                "priority": "low",
                "pool": pool_type,
                "title": "📝 准备抽卡",
                "message": f"当前水位 {pity}，建议准备 {(74 - pity) * 160} {cn['currency']}（约{(74 - pity)}抽）",
                "action": "prepare",
                "needed_currency": (74 - pity) * 160
            })
        else:
            recs.append({
                "priority": "info",
                "pool": pool_type,
                "title": "💎 继续攒抽",
                "message": f"当前水位 {pity}，距离保底较远。建议攒到至少 70 抽再考虑。",
                "action": "save",
                "needed_currency": (70 - pity) * 160
            })

    # 按优先级排序
    priority_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    recs.sort(key=lambda x: priority_order.get(x["priority"], 4))

    return recs


def calculate_saving_plan(pool_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """计算攒抽计划"""
    max_needed = 0
    for pool, analysis in pool_analysis.items():
        needed = analysis["pulls_to_hard_pity"]
        if needed > max_needed:
            max_needed = needed

    # 计算获取所需抽数的时间
    daily_primo = 150  # 平均每天150原石（日常+活动）
    monthly_card = 90 * 160  # 月卡每天90原石

    return {
        "max_pulls_needed": max_needed,
        "primogem_needed": max_needed * 160,
        "estimated_days_f2p": max_needed * 160 // daily_primo,
        "estimated_days_with_monthly": max_needed * 160 // (daily_primo + 90),
        "daily_primogem": daily_primo,
        "monthly_card_bonus": monthly_card // 160
    }


def calculate_luck_rating(records: List[GachaRecord]) -> Dict[str, Any]:
    """计算欧非评级"""
    if not records:
        return {"level": "unknown", "description": "暂无数据"}

    total = len(records)
    five_star = sum(1 for r in records if r.rarity == 5)
    rate = (five_star / total) * 100 if total > 0 else 0

    if rate >= 2.0:
        return {"level": "lucky", "description": "欧皇", "icon": "🌟"}
    elif rate >= 1.6:
        return {"level": "normal", "description": "正常", "icon": "⭐"}
    elif rate >= 1.0:
        return {"level": "unlucky", "description": "非酋", "icon": "🌙"}
    else:
        return {"level": "very_unlucky", "description": "究极非酋", "icon": "☁️"}


def calculate_next_probabilities(pool_analysis: Dict[str, Any]) -> Dict[str, float]:
    """计算各卡池下次五星概率"""
    result = {}
    for pool, analysis in pool_analysis.items():
        result[pool] = analysis["next_probability"]["current_rate"]
    return result
