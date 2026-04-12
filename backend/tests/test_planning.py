"""Test planning routes for GachaStats."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.main import app
from backend.models import Account, GachaRecord
from backend.database import get_session

client = TestClient(app)


def create_test_account(session: Session, **kwargs):
    """Helper to create a test account"""
    account = Account(
        game_type=kwargs.get("game_type", "genshin"),
        account_name=kwargs.get("account_name", "测试账号"),
        server=kwargs.get("server", "cn_gf01"),
        uid=kwargs.get("uid", "123456789"),
        auth_key=kwargs.get("auth_key", "test_key")
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def create_test_records(session: Session, account_id: int, records_data: list):
    """Helper to create test gacha records"""
    for data in records_data:
        record = GachaRecord(
            account_id=account_id,
            gacha_type=data.get("gacha_type", "301"),
            gacha_name=data.get("gacha_name", "活动祈愿"),
            item_name=data.get("item_name", "测试物品"),
            item_type=data.get("item_type", "角色"),
            rarity=data.get("rarity", 3),
            time=data.get("time", "2024-01-01 12:00:00"),
            pity=data.get("pity", 0),
            is_new=data.get("is_new", False)
        )
        session.add(record)
    session.commit()


def test_get_planning_without_account():
    """Test getting planning for non-existent account"""
    response = client.get("/api/planning/99999")
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_get_planning_empty_records(db_session):
    """Test getting planning with no records"""
    account = create_test_account(db_session)

    response = client.get(f"/api/planning/{account.id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["message"] == "暂无抽卡数据，建议先导入数据"


def test_get_planning_with_records(db_session):
    """Test getting planning with actual records"""
    account = create_test_account(db_session)

    # Create records with a 5-star at pity 75
    records = []
    for i in range(74):
        records.append({
            "item_name": f"三星武器{i}",
            "item_type": "武器",
            "rarity": 3,
            "time": f"2024-01-{i+1:02d} 12:00:00",
            "gacha_type": "301"
        })
    records.append({
        "item_name": "五星角色",
        "item_type": "角色",
        "rarity": 5,
        "time": "2024-01-15 12:00:00",
        "gacha_type": "301"
    })

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/planning/{account.id}")
    assert response.status_code == 200
    data = response.json()["data"]

    assert "historical_avg_pity" in data
    assert data["historical_avg_pity"] == 75.0
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0


def test_get_planning_near_soft_pity(db_session):
    """Test planning when near soft pity (73+)"""
    account = create_test_account(db_session)

    # Create records at pity 74
    records = []
    for i in range(74):
        records.append({
            "item_name": f"物品{i}",
            "item_type": "武器",
            "rarity": 3,
            "time": f"2024-01-{i+1:02d} 12:00:00",
            "gacha_type": "301"
        })

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/planning/{account.id}")
    data = response.json()["data"]

    # Check probability calculation
    pity_status = data["current_pity_status"].get("301", {})
    assert pity_status.get("current_pity") == 74
    assert pity_status.get("next_probability", {}).get("current_rate", 0) > 0.6


def test_luck_rating_calculation(db_session):
    """Test luck rating calculation"""
    account = create_test_account(db_session)

    # Create records with 2% five-star rate
    records = []
    for i in range(100):
        rarity = 5 if i < 2 else 3
        records.append({
            "item_name": f"物品{i}",
            "item_type": "角色" if rarity == 5 else "武器",
            "rarity": rarity,
            "time": f"2024-01-{i % 30 + 1:02d} 12:00:00",
            "gacha_type": "301"
        })

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/planning/{account.id}")
    data = response.json()["data"]

    assert "luck_rating" in data
    # 2% rate should be "lucky" or "normal"
    assert data["luck_rating"]["level"] in ["lucky", "normal"]


def test_saving_plan_calculation(db_session):
    """Test saving plan calculation"""
    account = create_test_account(db_session)

    # Create records at high pity
    records = []
    for i in range(85):
        records.append({
            "item_name": f"物品{i}",
            "item_type": "武器",
            "rarity": 3,
            "time": f"2024-01-{i+1:02d} 12:00:00",
            "gacha_type": "301"
        })

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/planning/{account.id}")
    data = response.json()["data"]

    assert "saving_plan" in data
    saving_plan = data["saving_plan"]
    assert "max_pulls_needed" in saving_plan
    assert "primogem_needed" in saving_plan
    assert "estimated_days_f2p" in saving_plan

    # Should need about 5 more pulls
    assert saving_plan["max_pulls_needed"] <= 5


def test_planning_multiple_pools(db_session):
    """Test planning with multiple gacha pools"""
    account = create_test_account(db_session)

    # Records for different pools
    records = []

    # Character event (301)
    for i in range(50):
        records.append({
            "item_name": f"物品{i}",
            "item_type": "角色",
            "rarity": 3,
            "time": f"2024-01-{i+1:02d} 12:00:00",
            "gacha_type": "301"
        })

    # Weapon event (302)
    for i in range(30):
        records.append({
            "item_name": f"武器{i}",
            "item_type": "武器",
            "rarity": 3,
            "time": f"2024-01-{i+1:02d} 12:00:00",
            "gacha_type": "302"
        })

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/planning/{account.id}")
    data = response.json()["data"]

    # Should have analysis for both pools
    assert "301" in data["current_pity_status"]
    assert "302" in data["current_pity_status"]

    # Character event should have higher pity
    pity_301 = data["current_pity_status"]["301"]["current_pity"]
    pity_302 = data["current_pity_status"]["302"]["current_pity"]
    assert pity_301 > pity_302
