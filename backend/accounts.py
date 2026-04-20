"""Account management routes for GachaStats."""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select
from .models import Account
from .database import get_session

router = APIRouter()

@router.get("/api/accounts")
async def get_accounts(session: Session = Depends(get_session)) -> List[Dict[str, Any]]:
    """获取所有账号"""
    accounts = session.exec(select(Account).order_by(Account.create_time.desc())).all()
    result = []
    for acc in accounts:
        result.append({
            "id": acc.id,
            "game_type": acc.game_type,
            "account_name": acc.account_name,
            "server": acc.server,
            "uid": acc.uid,
            "auth_key": acc.auth_key if acc.auth_key else "",
            "last_sync_time": acc.last_sync_time,
            "create_time": acc.create_time,
        })
    return result

@router.post("/api/accounts")
async def create_account(account: dict, session: Session = Depends(get_session)) -> Dict[str, Any]:
    """创建游戏账号（使用 AccountCreate schema defined in main if needed)"""
    # Expecting fields: game_type, account_name, server, uid, auth_key
    db_account = Account(
        game_type=account.get("game_type"),
        account_name=account.get("account_name"),
        server=account.get("server"),
        uid=account.get("uid"),
        auth_key=account.get("auth_key", ""),
    )
    session.add(db_account)
    try:
        session.commit()
        session.refresh(db_account)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail="该游戏UID已存在")
    return {"status": "success", "account_id": db_account.id, "message": "账号创建成功"}

@router.delete("/api/accounts/{account_id}")
async def delete_account(account_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
    """删除账号"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    session.delete(account)
    session.commit()
    return {"status": "success", "message": "账号已删除"}


@router.get("/api/accounts/{account_id}")
async def get_account(account_id: int, session: Session = Depends(get_session)) -> Dict[str, Any]:
    """获取单个账号详情"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {
        "id": account.id,
        "game_type": account.game_type,
        "account_name": account.account_name,
        "server": account.server,
        "uid": account.uid,
        "auth_key": account.auth_key if account.auth_key else "",
        "last_sync_time": account.last_sync_time,
        "create_time": account.create_time,
    }


@router.put("/api/accounts/{account_id}")
async def update_account(
    account_id: int,
    account_data: dict,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """更新账号信息"""
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 更新允许的字段
    allowed_fields = ["game_type", "account_name", "server", "uid", "auth_key"]
    for field in allowed_fields:
        if field in account_data:
            setattr(account, field, account_data[field])

    session.add(account)
    try:
        session.commit()
        session.refresh(account)
    except Exception:
        session.rollback()
        raise HTTPException(status_code=400, detail="更新账号失败")

    return {"status": "success", "account_id": account.id, "message": "账号更新成功"}


@router.patch("/api/accounts/{account_id}")
async def patch_account(
    account_id: int,
    account_data: dict,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """部分更新账号信息（PATCH用于部分更新）"""
    return await update_account(account_id, account_data, session)