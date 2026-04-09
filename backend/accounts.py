"""Account management routes for GachaStats"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from .models import Account
from .database import get_session

router = APIRouter()

@router.get("/api/accounts")
async def get_accounts(session: Session = Depends(get_session)):
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
            "last_sync_time": acc.last_sync_time,
            "create_time": acc.create_time,
        })
    return result

@router.post("/api/accounts")
async def create_account(account: dict, session: Session = Depends(get_session)):
    """创建游戏账号（使用 AccountCreate schema defined in main if needed)"""
    # Removed duplicate import – Account already imported above
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
