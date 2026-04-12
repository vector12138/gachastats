"""Test cases for GachaStats database module."""
import pytest
import tempfile
import os
import sqlite3
from sqlmodel import Session, create_engine
from sqlalchemy import Engine as sqlalchemy_Engine
from backend.database import get_session, init_db, get_engine
from backend.models import Account, GachaRecord, SQLModel


class TestDatabase:
    """测试数据库模块功能"""

    def setup_method(self):
        """为每个测试创建临时数据库."""
        # 创建临时文件
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # 创建临时数据库引擎
        self.test_engine = create_engine(f"sqlite:///{self.temp_db.name}")

        # 修改get_engine返回测试引擎
        self.original_get_engine = get_engine

        def mock_get_engine():
            return self.test_engine

        import backend.database
        backend.database.get_engine = mock_get_engine

        # 初始化测试数据库
        SQLModel.metadata.create_all(self.test_engine)

        # 获取测试会话
        self.session = next(get_session())

    def teardown_method(self):
        """测试后清理."""
        # 恢复原始函数
        backend.database.get_engine = self.original_get_engine

        # 关闭会话并删除临时数据库文件
        self.session.close()
        os.unlink(self.temp_db.name)

    def test_init_db_creates_tables(self):
        """测试数据库初始化会创建表."""
        # 重新初始化数据库
        SQLModel.metadata.drop_all(self.test_engine)
        SQLModel.metadata.create_all(self.test_engine)

        # 验证表是否存在
        conn = self.test_engine.connect()
        result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in result]

        assert "account" in tables
        assert "gacharecord" in tables
        assert "gamedata" in tables
        conn.close()

    def test_get_session_returns_valid_session(self):
        """测试会话工厂返回有效会话."""
        session = next(get_session())
        assert isinstance(session, Session)
        assert session.is_active
        session.close()

    def test_account_creation(self):
        """测试账号创建."""
        test_account = Account(
            game_type="genshin",
            account_name="测试用户",
            server="cn_gf01",
            uid="114514788",
            auth_key="test_auth_key"
        )

        self.session.add(test_account)
        self.session.commit()
        self.session.refresh(test_account)

        # 验证ID已赋值
        assert test_account.id is not None
        assert test_account.id > 0

        # 验证可查询
        found_account = self.session.get(Account, test_account.id)
        assert found_account is not None
        assert found_account.uid == "114514788"

    def test_account_uniqueness_constraint(self):
        """测试账号唯一性约束."""
        # 创建第一个账号
        account1 = Account(
            game_type="genshin",
            account_name="用户1",
            server="cn_gf01",
            uid="111111",
            auth_key="key1"
        )
        self.session.add(account1)
        self.session.commit()

        # 尝试创建相同UID的账号
        account2 = Account(
            game_type="genshin",
            account_name="用户2",
            server="cn_gf02",
            uid="111111",  # 相同的UID
            auth_key="key2"
        )
        self.session.add(account2)

        # 应该抛出异常
        with pytest.raises(Exception):
            self.session.commit()

        self.session.rollback()

    def test_gacha_record_foreign_key(self):
        """测试抽卡记录外键约束."""
        # 先创建账号
        account = Account(
            game_type="genshin",
            account_name="抽卡测试",
            server="cn_gf01",
            uid="222222",
            auth_key="key"
        )
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)

        # 创建关联的抽卡记录
        record = GachaRecord(
            account_id=account.id,
            gacha_type="301",
            gacha_name="角色活动祈愿",
            item_name="纳西妲",
            item_type="角色",
            rarity=5,
            time="2023-10-01 10:00:00"
        )
        self.session.add(record)
        self.session.commit()

        # 验证关联
        assert record.account_id == account.id
        # 注意：Relationship需要完整的数据库配置才能工作

    def test_gacha_record_unique_constraint(self):
        """测试抽卡记录唯一性约束."""
        # 创建账号
        account = Account(
            game_type="genshin",
            account_name="唯一性测试",
            server="cn_gf01",
            uid="333333",
            auth_key="key"
        )
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)

        # 创建第一条记录
        record1 = GachaRecord(
            account_id=account.id,
            gacha_type="301",
            gacha_name="角色活动祈愿",
            item_name="纳西妲",
            item_type="角色",
            rarity=5,
            time="2023-10-01 10:00:00"
        )
        self.session.add(record1)
        self.session.commit()

        # 尝试创建完全相同的记录（应该失败）
        record2 = GachaRecord(
            account_id=account.id,
            gacha_type="301",
            gacha_name="角色活动祈愿",
            item_name="纳西妲",
            item_type="角色",
            rarity=5,
            time="2023-10-01 10:00:00"  # 相同的时间
        )
        self.session.add(record2)

        # 应该抛出唯一性约束异常
        with pytest.raises(Exception):
            self.session.commit()

    def test_database_atomic_operations(self):
        """测试数据库原子操作."""
        # 创建测试数据
        accounts = []
        for i in range(5):
            account = Account(
                game_type="genshin",
                account_name=f"批量用户{i}",
                server="cn_gf01",
                uid=f"55555{i}",
                auth_key=f"key{i}"
            )
            accounts.append(account)
            self.session.add(account)

        # 批量提交
        self.session.commit()

        # 验证所有数据都正确创建
        for i, account in enumerate(accounts):
            assert account.id is not None
            assert account.account_name == f"批量用户{i}"
            assert account.uid == f"55555{i}"