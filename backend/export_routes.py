"""Export routes for GachaStats."""
from typing import Dict, Any
from io import BytesIO
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
import pandas as pd

from .models import Account, GachaRecord
from .database import get_session

router = APIRouter()


@router.get("/api/export/{account_id}/xlsx")
async def export_to_excel(
    account_id: int,
    session: Session = Depends(get_session)
) -> StreamingResponse:
    """导出账号抽卡记录到 Excel 文件"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 获取抽卡记录
    records = session.exec(
        select(GachaRecord)
        .where(GachaRecord.account_id == account_id)
        .order_by(GachaRecord.time.desc())
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail="该账号暂无抽卡记录")

    # 准备数据
    data = []
    for r in records:
        data.append({
            "抽取时间": r.time,
            "物品名称": r.item_name,
            "物品类型": r.item_type,
            "稀有度": f"{r.rarity}星",
            "卡池类型": r.gacha_name or r.gacha_type,
            "卡池代码": r.gacha_type,
            "是否为NEW": "是" if r.is_new else "否",
            "水位": r.pity
        })

    df = pd.DataFrame(data)

    # 创建 Excel 文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='抽卡记录', index=False)

        # 添加统计信息表
        stats_data = {
            "统计项": ["总抽数", "五星数量", "四星数量", "三星数量", "五星率", "账号UID", "最后同步时间"],
            "数值": [
                len(records),
                sum(1 for r in records if r.rarity == 5),
                sum(1 for r in records if r.rarity == 4),
                sum(1 for r in records if r.rarity == 3),
                f"{sum(1 for r in records if r.rarity == 5) / len(records) * 100:.2f}%",
                account.uid,
                account.last_sync_time or "未同步"
            ]
        }
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='统计信息', index=False)

        # 调整列宽
        worksheet = writer.sheets['抽卡记录']
        worksheet.column_dimensions['A'].width = 20
        worksheet.column_dimensions['B'].width = 15
        worksheet.column_dimensions['C'].width = 10
        worksheet.column_dimensions['D'].width = 10
        worksheet.column_dimensions['E'].width = 20
        worksheet.column_dimensions['F'].width = 12
        worksheet.column_dimensions['G'].width = 12
        worksheet.column_dimensions['H'].width = 10

    output.seek(0)

    game_name = {"genshin": "原神", "honkai": "崩坏3", "starrail": "星穹铁道", "zenless": "绝区零"}.get(account.game_type, account.game_type)
    filename = f"{game_name}_{account.account_name}_{account.uid}_抽卡记录_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/api/export/{account_id}/csv")
async def export_to_csv(
    account_id: int,
    session: Session = Depends(get_session)
) -> StreamingResponse:
    """导出账号抽卡记录到 CSV 文件"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 获取抽卡记录
    records = session.exec(
        select(GachaRecord)
        .where(GachaRecord.account_id == account_id)
        .order_by(GachaRecord.time.desc())
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail="该账号暂无抽卡记录")

    # 准备 CSV 数据
    output = BytesIO()
    output.write("抽取时间,物品名称,物品类型,稀有度,卡池类型,卡池代码,是否为NEW,水位\n".encode('utf-8-sig'))

    for r in records:
        is_new = "是" if r.is_new else "否"
        line = f"{r.time},{r.item_name},{r.item_type},{r.rarity}星,{r.gacha_name or ''},{r.gacha_type},{is_new},{r.pity}\n"
        output.write(line.encode('utf-8'))

    output.seek(0)

    game_name = {"genshin": "原神", "honkai": "崩坏3", "starrail": "星穹铁道", "zenless": "绝区零"}.get(account.game_type, account.game_type)
    filename = f"{game_name}_{account.account_name}_{account.uid}_抽卡记录_{datetime.now().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        output,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/api/export/all/xlsx")
async def export_all_to_excel(
    session: Session = Depends(get_session)
) -> StreamingResponse:
    """导出所有账号的抽卡记录"""
    accounts = session.exec(select(Account)).all()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for account in accounts:
            records = session.exec(
                select(GachaRecord)
                .where(GachaRecord.account_id == account.id)
                .order_by(GachaRecord.time.desc())
            ).all()

            if not records:
                continue

            data = []
            for r in records:
                data.append({
                    "抽取时间": r.time,
                    "物品名称": r.item_name,
                    "稀有度": f"{r.rarity}星",
                    "卡池": r.gacha_name or r.gacha_type
                })

            df = pd.DataFrame(data)
            sheet_name = f"{account.account_name[:20]}"
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    filename = f"GachaStats_全部账号_抽卡记录_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
