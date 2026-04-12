"""Analysis functions for GachaStats."""
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


def calculate_statistics(account_id: int, session) -> Tuple[int, int, int, int]:
    """计算基础抽卡统计信息
    返回: (总次数, 五星次数, 四星次数, 三星次数)
    """
    from .models import GachaRecord
    from sqlmodel import select

    results = session.exec(select(GachaRecord).where(GachaRecord.account_id == account_id)).all()
    total = len(results)
    five_star = sum(1 for r in results if r.rarity == 5)
    four_star = sum(1 for r in results if r.rarity == 4)
    three_star = sum(1 for r in results if r.rarity == 3)

    return total, five_star, four_star, three_star


def analyze_pity(account_id: int, session) -> Dict[str, Any]:
    """分析账号的保底情况"""
    from .models import GachaRecord
    from sqlmodel import select

    # 获取所有抽卡记录
    records = session.exec(
        select(GachaRecord).where(GachaRecord.account_id == account_id)
        .order_by(GachaRecord.time.asc())
    ).all()

    if not records:
        return {
            "total_pulls": 0,
            "current_pity": 0,
            "pity_distribution": {"five_star": 0, "four_star": 0, "three_star": 0},
            "has_five_star": False
        }

    # 按卡池分组
    pool_records = defaultdict(list)
    for record in records:
        pool_records[record.gacha_type].append(record)

    # 分析每个卡池的保底
    pool_pity_results = {}
    for gacha_type, pool_data in pool_records.items():
        current_pity = 0
        pity_list = []

        for record in pool_data:
            current_pity += 1
            if record.rarity == 5:
                pity_list.append(current_pity)
                current_pity = 0

        # 分析保底范围
        if pity_list:
            five_star_count = len(pity_list)
            min_pity = min(pity_list)
            max_pity = max(pity_list)
            avg_pity = sum(pity_list) / len(pity_list)
        else:
            min_pity = max_pity = avg_pity = five_star_count = 0

        # 计算下一次抽到五星的概率（基于原神标准）
        next_prob = calculate_base_probability(current_pity)

        pool_pity_results[gacha_type] = {
            "current_pity": current_pity,
            "five_star_count": five_star_count,
            "min_pity": min_pity,
            "max_pity": max_pity,
            "avg_pity": round(avg_pity, 2) if five_star_count > 0 else 0,
            "next_five_star_prob": next_prob
        }

    # 总体保底分析
    total_pity = calculate_pity_for_records(records)

    return {
        "total_pulls": total_pity["total_pulls"],
        "current_pity": total_pity["current_pity"],
        "pity_distribution": total_pity["pity_distribution"],
        "has_five_star": total_pity["total_pulls"] > 0 and total_pity["pity_distribution"]["five_star"] > 0,
        "pool_analysis": pool_pity_results,
        "pity_statistics": total_pity["pity_statistics"]
    }


def calculate_pity_for_records(records: List[Any]) -> Dict[str, Any]:
    """计算一组记录的保底情况"""
    if not records:
        return {
            "total_pulls": 0,
            "current_pity": 0,
            "pity_distribution": {"five_star": 0, "four_star": 0, "three_star": 0},
            "pity_statistics": {"min": 0, "max": 0, "avg": 0}
        }

    total_pulls = len(records)

    # 统计各星级出现次数
    rarity_count = {
        5: sum(1 for r in records if r.rarity == 5),
        4: sum(1 for r in records if r.rarity == 4),
        3: sum(1 for r in records if r.rarity == 3),
    }

    # 计算保底间隔
    pity_list = []
    current_pity = 0

    for record in records:
        current_pity += 1
        if record.rarity == 5:
            pity_list.append(current_pity)
            current_pity = 0

    # 保底统计
    if pity_list:
        min_pity = min(pity_list)
        max_pity = max(pity_list)
        avg_pity = sum(pity_list) / len(pity_list)
    else:
        min_pity = max_pity = avg_pity = 0
        current_pity = total_pulls  # 如果没有五星，则从第一抽开始计数

    return {
        "total_pulls": total_pulls,
        "current_pity": current_pity,
        "pity_distribution": {
            "five_star": rarity_count[5],
            "four_star": rarity_count[4],
            "three_star": rarity_count[3],
        },
        "pity_statistics": {
            "min": min_pity,
            "max": max_pity,
            "avg": round(avg_pity, 2) if pity_list else 0
        }
    }


def calculate_item_frequencies(account_id: int, session) -> Dict[str, List[Dict[str, Any]]]:
    """计算物品获取频率"""
    from .models import GachaRecord
    from sqlmodel import select

    records = session.exec(
        select(GachaRecord).where(GachaRecord.account_id == account_id)
        .order_by(GachaRecord.time.desc())
    ).all()

    # 按星级和类型分组
    frequencies = {
        "five_star_characters": [],
        "five_star_weapons": [],
        "four_star_characters": [],
        "four_star_weapons": [],
    }

    for record in records:
        if record.rarity == 5:
            if record.item_type == "角色":
                frequencies["five_star_characters"].append({
                    "name": record.item_name,
                    "time": record.time,
                    "pity": record.pity,
                    "is_new": record.is_new
                })
            elif record.item_type == "武器":
                frequencies["five_star_weapons"].append({
                    "name": record.item_name,
                    "time": record.time,
                    "pity": record.pity,
                    "is_new": record.is_new
                })
        elif record.rarity == 4:
            if record.item_type == "角色":
                frequencies["four_star_characters"].append({
                    "name": record.item_name,
                    "time": record.time,
                    "pity": record.pity,
                    "is_new": record.is_new
                })
            elif record.item_type == "武器":
                frequencies["four_star_weapons"].append({
                    "name": record.item_name,
                    "time": record.time,
                    "pity": record.pity,
                    "is_new": record.is_new
                })

    return frequencies


def analyze_spending_patterns(account_id: int, session) -> Dict[str, Any]:
    """分析花费模式"""
    from .models import GachaRecord
    from sqlmodel import select
    from datetime import datetime

    records = session.exec(
        select(GachaRecord).where(GachaRecord.account_id == account_id)
        .order_by(GachaRecord.time.desc())
    ).all()

    if not records:
        return {
            "status": "empty",
            "message": "暂无抽卡数据"
        }

    # 月度抽卡统计
    monthly_stats = defaultdict(int)
    for record in records:
        try:
            date_obj = datetime.fromisoformat(record.time.replace(' ', 'T'))
            month_key = date_obj.strftime('%Y-%m')
            monthly_stats[month_key] += 1
        except ValueError:
            continue

    # 花费估算（基于平均价每160原石一抽）
    total_pulls = len(records)
    # 原神每抽160原石，约等于人民币16元
    estimated_spending = total_pulls * 16.0

    # 分类分析
    five_star_records = [r for r in records if r.rarity == 5]
    four_star_records = [r for r in records if r.rarity == 4]

    return {
        "total_pulls": total_pulls,
        "estimated_spending": estimated_spending,
        "currency": "CNY",
        "five_star_pulls": len(five_star_records),
        "four_star_pulls": len(four_star_records),
        "monthly_active_months": len(monthly_stats),
        "most_active_month": max(monthly_stats.items(), key=lambda x: x[1]) if monthly_stats else None,
        "spending_category": classify_spending_level(estimated_spending)
    }


def classify_spending_level(amount: float) -> str:
    """划分花费等级"""
    if amount >= 10000:
        return "重氪玩家"
    elif amount >= 5000:
        return "中氪玩家"
    elif amount >= 1000:
        return "轻氪玩家"
    elif amount >= 100:
        return "微氪玩家"
    else:
        return "零氪玩家"


def calculate_base_probability(pity: int) -> float:
    """计算原神保底的基础概率（简化模型）"""
    if pity <= 73:
        return 0.6
    else:
        # 从73到89概率线性增加
        base_prob = 0.6
        increase_per_pull = (100.0 - base_prob) / (89 - 73)
        additional_prob = (pity - 73) * increase_per_pull
        return base_prob + additional_prob