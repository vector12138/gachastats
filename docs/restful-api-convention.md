# RESTful API Design 规范

## 基本原则

所有后端 API 必须遵循 RESTful 设计规范。

## 路径设计规则

### 1. 使用名词复数形式
✅ **正确：**
- `/api/accounts`
- `/api/imports`
- `/api/exports`

❌ **错误：**
- `/api/account` (单数)
- `/api/get-analysis` (动词开头)
- `/api/createUser` (驼峰命名)

### 2. 子资源通过路径层级表示
✅ **正确：**
- `/api/accounts/{id}/analysis`
- `/api/accounts/{id}/history`
- `/api/imports/{id}/logs`

❌ **错误：**
- `/api/analysis?account_id={id}` (查询参数)
- `/api/get-account-analysis` (平级+动词)

### 3. HTTP 方法表示操作

| 操作 | HTTP 方法 | 示例路径 |
|------|-----------|----------|
| 获取列表 | GET | `/api/accounts` |
| 创建资源 | POST | `/api/accounts` |
| 获取单个 | GET | `/api/accounts/{id}` |
| 更新资源 | PUT | `/api/accounts/{id}` |
| 删除资源 | DELETE | `/api/accounts/{id}` |
| 获取子资源 | GET | `/api/accounts/{id}/analysis` |

## 一致性要求

### 三端保持一致
1. **后端路由** - 实现时使用 RESTful 路径
2. **前端调用** - 调用时使用相同路径
3. **测试代码** - 断言时匹配路径

## 标准示例

```python
# 后端 FastAPI 路由
def register_routes(app: FastAPI):
    # 账户管理
    @app.get("/api/accounts")
    async def list_accounts(): ...
    
    @app.post("/api/accounts")
    async def create_account(): ...
    
    @app.get("/api/accounts/{account_id}")
    async def get_account(account_id: int): ...
    
    @app.put("/api/accounts/{account_id}")
    async def update_account(account_id: int): ...
    
    @app.delete("/api/accounts/{account_id}")
    async def delete_account(account_id: int): ...
    
    # 子资源 - 分析数据
    @app.get("/api/accounts/{account_id}/analysis")
    async def get_account_analysis(account_id: int): ...
```

```javascript
// 前端 JavaScript 调用
// ✅ 正确：使用路径参数
fetch(`/api/accounts/${accountId}/analysis`)

// ❌ 错误：使用查询参数
fetch(`/api/analysis?account_id=${accountId}`)
```

## 检查清单

编写新 API 时，请确认：
- [ ] 路径使用名词复数形式
- [ ] 子资源通过路径层级而非查询参数
- [ ] 使用 HTTP 方法而非动作动词
- [ ] 前端调用与后端路由保持一致
- [ ] 测试路径与实现路径一致
