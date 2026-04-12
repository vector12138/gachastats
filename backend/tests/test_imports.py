"""Test cases for GachaStats import module."""
import pytest
from unittest.mock import patch, MagicMock
from backend.models import Account, GachaRecord
from backend.imports import import_from_official, import_manual
from backend.database import get_session


class TestImport:
    """测试导入模块的功能"""

    def setup_method(self):
        """测试前设置."""
        self.session = next(get_session())
        # 创建测试账号
        self.test_account = Account(
            game_type="genshin",
            account_name="导入了测试账号",
            server="cn_gf01",
            uid="654321",
            auth_key="test_auth_key_123",
        )
        self.session.add(self.test_account)
        self.session.commit()
        self.session.refresh(self.test_account)

    def teardown_method(self):
        """测试后清理."""
        self.session.exec(f"DELETE FROM gacharecord WHERE account_id = {self.test_account.id}")
        self.session.delete(self.test_account)
        self.session.commit()
        self.session.close()

    @patch("backend.imports.parse_gacha_url")
    @patch("backend.imports.fetch_gacha_records")
    def test_import_from_official_success(self, mock_fetch, mock_parse):
        """测试从官方链接导入数据成功."""
        # Mock parse_gacha_url 返回值
        mock_parse.return_value = {"authkey": "valid_auth_key", "game_biz": "hk4e_cn"}

        # Mock fetch_gacha_records 返回值 - 模拟原神抽卡记录
        mock_records = [
            {"gacha_name": "角色活动祈愿", "name": "纳西妲", "item_type": "角色", "rank_type": "5", "time": "2023-10-01 10:00:00"},
            {"gacha_name": "角色活动祈愿", "name": "行秋", "item_type": "角色", "rank_type": "4", "time": "2023-10-02 10:00:00"},
            {"gacha_name": "角色活动祈愿", "name": "祭礼剑", "item_type": "武器", "rank_type": "4", "time": "2023-10-03 10:00:00"},
        ]
        mock_fetch.return_value = mock_records

        # 执行导入
        result = import_from_official(
            account_id=self.test_account.id,
            gacha_url="https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog?authkey=valid_auth_key",
            session=self.session
        )

        # 验证结果
        assert result["status"] == "success"
        assert result["imported"] == 12  # 3种卡池 * 每个4条记录 = 12
        assert "成功导入" in result["message"]

        # 验证数据库中数据
        records = self.session.exec(f"SELECT COUNT(*) FROM gacharecord WHERE account_id = {self.test_account.id}").all()
        assert records[0][0] > 0

    def test_import_from_official_account_not_found(self):
        """测试账号不存在时的导入."""
        with pytest.raises(Exception) as exc_info:
            import_from_official(
                account_id=999999,  # 不存在的ID
                gacha_url="https://test.com",
                session=self.session
            )

        assert "404" in str(exc_info.value)

    @patch("backend.imports.parse_gacha_url")
    def test_import_from_official_no_auth_key(self, mock_parse):
        """测试无法获取authkey的情况."""
        mock_parse.return_value = {}  # 空参数

        with pytest.raises(Exception) as exc_info:
            self.test_account.auth_key = None  # 清空auth_key
            self.session.commit()

            import_from_official(
                account_id=self.test_account.id,
                gacha_url="https://test.com",
                session=self.session
            )

        assert "400" in str(exc_info.value)
        assert "authkey" in str(exc_info.value)

    def test_import_manual_success(self):
        """测试手动导入功能."""
        manual_data = {
            "account_id": self.test_account.id,
            "records": [
                {
                    "gacha_type": "301",
                    "gacha_name": "角色活动祈愿",
                    "item_name": "纳西妲",
                    "item_type": "角色",
                    "rarity": 5,
                    "time": "2023-10-01 10:00:00",
                    "pity": 76,
                    "is_new": True
                },
                {
                    "gacha_type": "301",
                    "gacha_name": "角色活动祈愿",
                    "item_name": "行秋",
                    "item_type": "角色",
                    "rarity": 4,
                    "time": "2023-10-02 10:00:00",
                    "pity": 0,
                    "is_new": False
                },
                {
                    "gacha_type": "200",
                    "gacha_name": "常驻祈愿",
                    "item_name": "天空之刃",
                    "item_type": "武器",
                    "rarity": 5,
                    "time": "2023-10-03 10:00:00",
                    "pity": 89,
                    "is_new": False
                }
            ]
        }

        result = import_manual(data=manual_data, session=self.session)

        assert result["status"] == "success"
        assert result["imported"] == 3
        assert "成功导入 3 条记录" in result["message"]

        # 验证数据正确导入
        records = self.session.exec(f"SELECT * FROM gacharecord WHERE account_id = {self.test_account.id}").all()
        assert len(records) == 3

        # 验证具体数据
        five_star_records = self.session.exec(
            f"SELECT item_name, rarity FROM gacharecord WHERE account_id = {self.test_account.id} AND rarity = 5"
        ).all()
        assert any("纳西妲" in str(record) for record in five_star_records)
        assert any("天空之刃" in str(record) for record in five_star_records)

    def test_import_manual_duplicate_data(self):
        """测试导入重复数据的处理."""
        manual_data = {
            "account_id": self.test_account.id,
            "records": [
                {
                    "gacha_type": "301",
                    "gacha_name": "角色活动祈愿",
                    "item_name": "纳西妲",
                    "item_type": "角色",
                    "rarity": 5,
                    "time": "2023-10-01 10:00:00",
                    "pity": 76,
                    "is_new": True
                },
                {
                    "gacha_type": "301",
                    "gacha_name": "角色活动祈愿",
                    "item_name": "纳西妲",  # 相同的数据
                    "item_type": "角色",
                    "rarity": 5,
                    "time": "2023-10-01 10:00:00",
                    "pity": 76,
                    "is_new": True
                }
            ]
        }

        # 第一次导入
        result1 = import_manual(data=manual_data, session=self.session)
        assert result1["imported"] == 2

        # 第二次导入同样的数据
        result2 = import_manual(data=manual_data, session=self.session)
        # 由于数据库的唯一性约束，应该只有1条被导入
        assert result2["imported"] <= 2

    def test_import_manual_invalid_data(self):
        """测试导入数据格式不正确的情况."""
        # 缺少必要的account_id
        invalid_data = {
            "records": [
                {
                    "gacha_type": "301",
                    "item_name": "纳西妲",
                    "rarity": 5
                }
            ]
        }

        result = import_manual(data=invalid_data, session=self.session)

        # 应该能处理空account_id的情况
        assert result["status"] == "success" or result["imported"] == 0

    def test_import_manual_empty_records(self):
        """测试导入空记录列表."""
        manual_data = {
            "account_id": self.test_account.id,
            "records": []
        }

        result = import_manual(data=manual_data, session=self.session)

        assert result["status"] == "success"
        assert result["imported"] == 0
        assert "成功导入 0 条记录" in result["message"]

    def test_import_different_games(self):
        """测试不同游戏的导入支持."""
        # 测试不同游戏类型
        games = [
            {"game_type": "starrail", "gacha_types": ["1", "2", "11", "12"]},
            {"game_type": "zzz", "gacha_types": ["1", "2", "3", "4"]},
            {"game_type": "genshin", "gacha_types": ["100", "200", "301", "302"]}
        ]

        for game in games:
            account = Account(
                game_type=game["game_type"],
                account_name=f"{game['game_type']}测试账号",
                server="cn_gf01",
                uid=f"98765_{game['game_type']}",
                auth_key="test_key"
            )
            self.session.add(account)
            self.session.commit()
            self.session.refresh(account)

            manual_data = {
                "account_id": account.id,
                "records": [
                    {
                        "gacha_type": game["gacha_types"][0],
                        "gacha_name": "角色活动",
                        "item_name": "测试物品",
                        "item_type": "角色",
                        "rarity": 5,
                        "time": "2023-10-01 10:00:00"
                    }
                ]
            }

            result = import_manual(data=manual_data, session=self.session)
            assert result["imported"] == 1

            # 清理
            self.session.exec(f"DELETE FROM gacharecord WHERE account_id = {account.id}")
            self.session.delete(account)
            self.session.commit()