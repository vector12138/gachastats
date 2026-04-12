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