# GachaStats - Python项目测试说明

## 测试环境要求
```bash
pip install pytest pytest-fastapi httpx
```

## 运行测试
```bash
# 在项目目录下运行
cd /root/.openclaw/workspace/gachastats
source venv/bin/activate
python3 -m pytest backend/tests/ -v
```

## 已创建的测试文件
1. `backend/tests/test_accounts.py` - 账号相关API测试
   - 测试获取账号列表（空数据库）
   - 测试创建新账号
   - 测试重复UID错误处理

## 待补全的测试
1. 数据导入功能测试
2. 分析功能测试
3. 错误处理测试
4. 数据库读写测试

## 测试覆盖率目标
- 单元测试覆盖率 ≥ 80%
- 主要业务逻辑全覆盖
- 错误处理测试完整