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

import json
from pathlib import Path
import uvicorn

# ------------------- Read configuration -------------------
CONFIG_PATH = Path(__file__).with_name("config.json")
if not CONFIG_PATH.is_file():
    raise FileNotFoundError(f"Missing configuration file: {CONFIG_PATH}")

with CONFIG_PATH.open(encoding="utf-8") as f:
    cfg = json.load(f)

HOST = cfg.get("host", "0.0.0.0")
PORT = cfg.get("port", 8777)
RELOAD = cfg.get("reload", False)

# ------------------- Start the server -------------------
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=RELOAD)
