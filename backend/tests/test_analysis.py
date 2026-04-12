"""Test cases for GachaStats data analysis module."""
import pytest
from datetime import datetime
from backend.models import Account, GachaRecord
from backend.analysis import (
    calculate_statistics,
    analyze_pity,
    calculate_item_frequencies,
    analyze_spending_patterns,
)
from backend.database import get_session
from sqlmodel import Session


def create_test_account():
    """Create a test account for analysis."""
    return Account(
        game_type="genshin",
        account_name="测试账号",
        server="cn_gf01",
        uid="123456",
        auth_key="test_key",
    )


def create_test_gacha_records(account_id):
    """Create test gacha records for analysis."""
    records = []
    # 模拟抽卡记录 - 各种稀有度
    test_data = [
        {"gacha_type": "301", "gacha_name": "角色活动祈愿", "item_name": "纳西妲", "item_type": "角色", "rarity": 5, "time": "2023-10-01 10:00:00", "pity": 0, "is_new": True},
        {"gacha_type": "301", "gacha_name": "角色活动祈愿", "item_name": "欧洛伦", "item_type": "角色", "rarity": 4, "time": "2023-10-25 15:30:00", "pity": 0, "is_new": False},
        {"gacha_type": "301", "gacha_name": "角色活动祈愿", "item_name": "九条裟罗", "item_type": "角色", "rarity": 4, "time": "2023-10-26 08:00:00", "pity": 0, "is_new": False},
        {"gacha_type": "301", "gacha_name": "角色活动祈愿", "item_name": "早柚", "item_type": "角色", "rarity": 4, "time": "2023-10-28 12:00:00", "pity": 0, "is_new": False},
        {"gacha_type": "301", "gacha_name": "角色活动祈愿", "item_name": "行秋", "item_type": "角色", "rarity": 4, "time": "2023-10-30 18:00:00", "pity": 0, "is_new": False},
        {"gacha_type": "302", "gacha_name": "武器活动祈愿", "item_name": "苍古自由之誓", "item_type": "武器", "rarity": 5, "time": "2023-11-01 20:00:00", "pity": 68, "is_new": True},
        {"gacha_type": "302", "gacha_name": "武器活动祈愿", "item_name": "祭礼剑", "item_type": "武器", "rarity": 4, "time": "2023-11-03 10:00:00", "pity": 0, "is_new": False},
        {"gacha_type": "200", "gacha_name": "常驻祈愿", "item_name": "迪卢克", "item_type": "角色", "rarity": 5, "time": "2023-11-05 14:00:00", "pity": 0, "is_new": False},
    ]

    for data in test_data:
        record = GachaRecord(
            account_id=account_id,
            gacha_type=data["gacha_type"],
            gacha_name=data["gacha_name"],
            item_name=data["item_name"],
            item_type=data["item_type"],
            rarity=data["rarity"],
            time=data["time"],
            pity=data["pity"],
            is_new=data["is_new"],
        )
        records.append(record)

    return records


class TestAnalysis:
    """测试数据分析模块的功能"""

    def setup_method(self):
        """测试前设置."""
        self.session = next(get_session())
        self.account = create_test_account()
        self.session.add(self.account)
        self.session.commit()
        self.session.refresh(self.account)

    def teardown_method(self):
        """测试后清理."""
        # 删除测试数据
        self.session.exec(f"DELETE FROM gacharecord WHERE account_id = {self.account.id}")
        self.session.delete(self.account)
        self.session.commit()
        self.session.close()

    def test_calculate_statistics(self):
        """测试基本统计计算."""
        # 添加测试数据
        records = create_test_gacha_records(self.account.id)
        for record in records:
            self.session.add(record)
        self.session.commit()

        # 统计抽卡数据
        total, five_star, four_star, three_star = calculate_statistics(self.account.id, self.session)

        assert total == 8, "总抽卡次数应为8次"
        assert five_star == 3, "五星抽卡次数应为3次"
        assert four_star == 4, "四星抽卡次数应为4次"
        assert three_star == 0, "三星抽卡次数应为0次（这里没有测试数据）"

    def test_analyze_pity(self):
        """测试保底分析功能."""
        # 添加测试数据
        records = create_test_gacha_records(self.account.id)
        for record in records:
            self.session.add(record)
        self.session.commit()

        # 分析保底情况
        pity_analysis = analyze_pity(self.account.id, self.session)

        assert "five_star_pity" in pity_analysis
        assert pity_analysis["total_pulls"] == 8
        # 验证当前保底进度
        assert pity_analysis["five_star_pity"] >= 0

    def test_calculate_item_frequencies(self):
        """测试物品频率统计."""
        # 添加测试数据
        records = create_test_gacha_records(self.account.id)
        for record in records:
            self.session.add(record)
        self.session.commit()

        # 计算物品频率
        frequencies = calculate_item_frequencies(self.account.id, self.session)

        assert isinstance(frequencies, dict)
        assert "five_star_characters" in frequencies
        assert "four_star_characters" in frequencies
        assert "four_star_weapons" in frequencies

        # 验证纳西妲被统计到
        if "纳西妲" not in [char["name"] for char in frequencies["five_star_characters"]]:
            assert False, "纳西妲应该出现在五星角色列表中"

    def test_analyze_spending_patterns(self):
        """测试花费模式分析."""
        # 添加测试数据
        records = create_test_gacha_records(self.account.id)
        for record in records:
            self.session.add(record)
        self.session.commit()

        # 分析花费模式
        spending = analyze_spending_patterns(self.account.id, self.session)

        assert isinstance(spending, dict)
        # 理论上应该包含估算信息
        assert "estimated_spending" in spending or "total_cost" in spending

    def test_calculate_statistics_no_data(self):
        """测试没有抽卡数据时的统计计算."""
        # 不添加任何记录，直接测试
        total, five_star, four_star, three_star = calculate_statistics(self.account.id, self.session)

        assert total == 0, "没有数据时总次数应为0"
        assert five_star == 0, "没有数据时五星次数应为0"
        assert four_star == 0, "没有数据时四星次数应为0"
        assert three_star == 0, "没有数据时三星次数应为0"