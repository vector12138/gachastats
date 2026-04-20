"""Chart data routes for GachaStats - provides data for ECharts visualization.

基于RESTful规范:
- /api/accounts/{account_id}/charts/* - 账号图表子资源
- /api/charts/all/* - 全局图表（无特定账号）
"""
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .models import Account, GachaRecord
from .database import get_session

router = APIRouter()


@router.get("/api/accounts/{account_id}/charts/trend")
async def get_trend_chart(
    account_id: int,
    days: int = 90,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取抽卡趋势数据（折线图）"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    records = session.exec(
        select(GachaRecord)
        .where(GachaRecord.account_id == account_id)
        .order_by(GachaRecord.time.asc())
    ).all()

    if not records:
        return {"status": "success", "data": {"categories": [], "series": []}}

    # 按日期统计
    daily_counts = defaultdict(lambda: {"total": 0, "five_star": 0, "four_star": 0})

    for r in records:
        try:
            date = r.time[:10]  # YYYY-MM-DD
            daily_counts[date]["total"] += 1
            if r.rarity == 5:
                daily_counts[date]["five_star"] += 1
            elif r.rarity == 4:
                daily_counts[date]["four_star"] += 1
        except:
            continue

    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = []
    current = start_date
    while current <= end_date:
        date_range.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    categories = date_range
    total_data = [daily_counts[d]["total"] for d in date_range]
    five_star_data = [daily_counts[d]["five_star"] for d in date_range]
    four_star_data = [daily_counts[d]["four_star"] for d in date_range]

    return {
        "status": "success",
        "data": {
            "categories": categories,
            "series": [
                {"name": "总抽数", "type": "line", "smooth": True, "data": total_data},
                {"name": "五星", "type": "bar", "data": five_star_data},
                {"name": "四星", "type": "bar", "data": four_star_data}
            ]
        }
    }


# 旧端点兼容（已废弃）
@router.get("/api/charts/{account_id}/trend", deprecated=True)
async def get_trend_chart_legacy(
    account_id: int,
    days: int = 90,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取抽卡趋势数据（旧版本，请使用 /api/accounts/{account_id}/charts/trend）"""
    return await get_trend_chart(account_id, days, session)


@router.get("/api/accounts/{account_id}/charts/pity-distribution")
async def get_pity_distribution(
    account_id: int,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取五星出货分布（柱状图）"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    records = session.exec(
        select(GachaRecord)
        .where(GachaRecord.account_id == account_id)
        .order_by(GachaRecord.time.asc())
    ).all()

    if not records:
        return {"status": "success", "data": {"categories": [], "data": []}}

    # 计算所有五星的水位
    pity_list = []
    current_pity = 0

    for r in records:
        current_pity += 1
        if r.rarity == 5:
            pity_list.append(current_pity)
            current_pity = 0

    # 按水位区间分组
    bins = {
        "1-30": 0, "31-50": 0, "51-60": 0, "61-70": 0,
        "71-75": 0, "76-80": 0, "81-85": 0, "86-90": 0
    }

    for pity in pity_list:
        if pity <= 30:
            bins["1-30"] += 1
        elif pity <= 50:
            bins["31-50"] += 1
        elif pity <= 60:
            bins["51-60"] += 1
        elif pity <= 70:
            bins["61-70"] += 1
        elif pity <= 75:
            bins["71-75"] += 1
        elif pity <= 80:
            bins["76-80"] += 1
        elif pity <= 85:
            bins["81-85"] += 1
        else:
            bins["86-90"] += 1

    return {
        "status": "success",
        "data": {
            "categories": list(bins.keys()),
            "data": list(bins.values()),
            "avg_pity": round(sum(pity_list) / len(pity_list), 2) if pity_list else 0,
            "min_pity": min(pity_list) if pity_list else 0,
            "max_pity": max(pity_list) if pity_list else 0
        }
    }


# 旧端点兼容
@router.get("/api/charts/{account_id}/pity-distribution", deprecated=True)
async def get_pity_distribution_legacy(
    account_id: int,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取五星出货分布（旧版本）"""
    return await get_pity_distribution(account_id, session)


@router.get("/api/accounts/{account_id}/charts/item-types")
async def get_item_types(
    account_id: int,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取物品类型分布（饼图）"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    records = session.exec(
        select(GachaRecord)
        .where(GachaRecord.account_id == account_id)
    ).all()

    if not records:
        return {"status": "success", "data": []}

    # 按稀有度和类型统计
    type_counts = defaultdict(int)

    for r in records:
        key = f"{r.rarity}星{r.item_type}"
        type_counts[key] += 1

    data = [{"name": k, "value": v} for k, v in type_counts.items()]

    return {
        "status": "success",
        "data": data
    }


# 旧端点兼容
@router.get("/api/charts/{account_id}/item-types", deprecated=True)
async def get_item_types_legacy(
    account_id: int,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取物品类型分布（旧版本）"""
    return await get_item_types(account_id, session)


@router.get("/api/accounts/{account_id}/charts/monthly")
async def get_monthly_stats(
    account_id: int,
    months: int = 12,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取月度统计（柱状图）"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    records = session.exec(
        select(GachaRecord)
        .where(GachaRecord.account_id == account_id)
    ).all()

    if not records:
        return {"status": "success", "data": {"categories": [], "series": []}}

    # 按月份统计
    monthly_data = defaultdict(lambda: {"total": 0, "five_star": 0})

    for r in records:
        try:
            month = r.time[:7]  # YYYY-MM
            monthly_data[month]["total"] += 1
            if r.rarity == 5:
                monthly_data[month]["five_star"] += 1
        except:
            continue

    # 生成月份范围
    end_month = datetime.now()
    month_range = []
    for i in range(months):
        month = end_month - timedelta(days=30 * i)
        month_range.insert(0, month.strftime("%Y-%m"))

    categories = month_range
    total_data = [monthly_data[m]["total"] for m in month_range]
    five_star_data = [monthly_data[m]["five_star"] for m in month_range]

    return {
        "status": "success",
        "data": {
            "categories": categories,
            "series": [
                {"name": "总抽数", "type": "bar", "data": total_data},
                {"name": "五星数", "type": "line", "data": five_star_data}
            ]
        }
    }


# 旧端点兼容
@router.get("/api/charts/{account_id}/monthly", deprecated=True)
async def get_monthly_stats_legacy(
    account_id: int,
    months: int = 12,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取月度统计（旧版本）"""
    return await get_monthly_stats(account_id, months, session)


@router.get("/api/charts/all/radar")
async def get_all_accounts_radar(
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """获取所有账号对比（雷达图） - 无需特定账号ID"""
    accounts = session.exec(select(Account)).all()

    indicators = [
        {"name": "总抽数", "max": 1000},
        {"name": "五星率", "max": 3},
        {"name": "平均水位", "max": 90},
        {"name": "活跃度", "max": 100},
        {"name": "欧气值", "max": 100}
    ]

    series_data = []

    for acc in accounts:
        records = session.exec(
            select(GachaRecord)
            .where(GachaRecord.account_id == acc.id)
        ).all()

        if not records:
            continue

        total = len(records)
        five_star = sum(1 for r in records if r.rarity == 5)

        # 计算平均水位
        pity_list = []
        current_pity = 0
        for r in records:
            current_pity += 1
            if r.rarity == 5:
                pity_list.append(current_pity)
                current_pity = 0

        avg_pity = sum(pity_list) / len(pity_list) if pity_list else 90
        five_star_rate = (five_star / total * 100) if total > 0 else 0

        # 活跃度：有抽卡记录的天数占比
        unique_days = len(set(r.time[:10] for r in records))
        activity = min(unique_days, 100)

        # 欧气值：基于五星率 (2%为标准)
        luck = min(five_star_rate / 2 * 100, 100)

        series_data.append({
            "name": acc.account_name,
            "value": [
                min(total, 1000),
                round(five_star_rate, 2),
                round(avg_pity, 1),
                activity,
                round(luck, 1)
            ]
        })

    return {
        "status": "success",
        "data": {
            "indicators": indicators,
            "series": series_data
        }
    }
