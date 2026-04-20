#!/usr/bin/env python3
"""Entry point to run GachaStats FastAPI using `python run.py`.

端口、host、reload 等参数放在项目根目录的 `config.json`，示例内容：

```json
{
    "host": "0.0.0.0",
    "port": 8777,
    "reload": true
}
```
"""

import os

# ⚠️ 关键点：必须在导入任何其他模块之前设置 DISPLAY
# 这样 backend.browser_login 的 has_display() 才能检测到正确的环境
if not os.environ.get('DISPLAY'):
    os.environ['DISPLAY'] = ':10'

import uvicorn
from backend.config_loader import get_config

# ------------------- Read configuration -------------------
CONFIG = get_config()

HOST = CONFIG.get("host", "0.0.0.0")
PORT = CONFIG.get("port", 8777)
RELOAD = CONFIG.get("reload", False)

# ------------------- Start the server -------------------
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=RELOAD)
