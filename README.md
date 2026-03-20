# Any Auto Register

> ⚠️ **免责声明**：本项目仅供学习和研究使用，不得用于任何商业用途。使用本项目所产生的一切后果由使用者自行承担。

多平台账号自动注册与管理系统，支持插件化扩展，内置 Web UI。

## 功能特性

- **多平台支持**：Trae.ai、Tavily、Cursor、Kiro、ChatGPT、OpenBlockLabs，支持自定义插件扩展
- **多邮箱服务**：Laoudo、TempMail.lol、DuckMail、Cloudflare Worker 自建邮箱
- **多执行模式**：API 协议（无浏览器）、无头浏览器、有头浏览器（各平台按需支持）
- **验证码服务**：YesCaptcha、2Captcha、本地 Solver（Camoufox）
- **代理池管理**：自动轮询、成功率统计、自动禁用失效代理
- **并发注册**：可配置并发数
- **实时日志**：SSE 实时推送注册日志到前端
- **平台扩展操作**：各平台可自定义操作（如 ChatGPT 支持 Token 刷新、支付链接生成、CPA 上传）

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLite（SQLModel）|
| 前端 | React + TypeScript + Vite + TailwindCSS |
| HTTP | curl_cffi（浏览器指纹伪装）|
| 浏览器自动化 | Playwright / Camoufox |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+

### 安装

```bash
# 后端依赖
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 前端构建
cd frontend
npm install
npm run build
cd ..
```

### 启动

```bash
.venv/bin/python3 -m uvicorn main:app --port 8000
```

浏览器访问 `http://localhost:8000`

## 项目结构

```
account_manager/
├── main.py                 # FastAPI 入口
├── api/                    # HTTP 接口层
│   ├── accounts.py         # 账号 CRUD
│   ├── tasks.py            # 注册任务（SSE 日志）
│   ├── actions.py          # 平台操作（通用接口）
│   ├── config.py           # 全局配置持久化
│   └── proxies.py          # 代理管理
├── core/                   # 基础设施层
│   ├── base_platform.py    # 平台基类（register/check_valid/get_platform_actions）
│   ├── base_mailbox.py     # 邮箱服务基类 + 工厂方法
│   ├── base_captcha.py     # 验证码服务基类
│   ├── base_executor.py    # 执行器基类
│   ├── http_client.py      # 通用 HTTP 客户端（curl_cffi）
│   ├── db.py               # 数据模型
│   ├── proxy_pool.py       # 代理池
│   ├── registry.py         # 平台插件注册表
│   └── scheduler.py        # 定时任务
├── platforms/              # 平台插件层
│   ├── {platform}/
│   │   ├── plugin.py       # 平台适配层（实现 BasePlatform）
│   │   └── core.py         # 注册协议核心逻辑
│   └── chatgpt/            # ChatGPT 额外包含 oauth/payment/token_refresh 等
├── services/               # 后台服务
│   ├── solver_manager.py   # Turnstile Solver 进程管理
│   └── turnstile_solver/   # 本地 Camoufox Solver
└── frontend/               # React 前端
```

## 插件开发

添加新平台只需在 `platforms/` 下新建目录，实现 `plugin.py`：

```python
from core.base_platform import BasePlatform, Account, AccountStatus, RegisterConfig
from core.registry import register

@register
class MyPlatform(BasePlatform):
    name = "myplatform"
    display_name = "My Platform"
    version = "1.0.0"
    supported_executors = ["protocol"]

    def register(self, email: str, password: str = None) -> Account:
        # 实现注册逻辑
        # 用 self.mailbox.get_email() 获取邮箱
        # 用 self.mailbox.wait_for_code() 收验证码
        ...

    def check_valid(self, account: Account) -> bool:
        # 实现账号有效性检测
        ...
```

## 邮箱服务

| 服务 | 类型 | 说明 |
|------|------|------|
| Laoudo | 固定邮箱 | 自有域名邮箱，稳定性最高 |
| TempMail.lol | 自动生成 | 免费临时邮箱，CN IP 需代理 |
| DuckMail | 自动生成 | 自动创建随机账号 |
| CF Worker | 自动生成 | 自建 Cloudflare Worker 邮箱 |

**## gpt账号json单独导出**

export_any_auto_register_accounts.py。

   1. 导出全部账号为 CSV

  python .\export_any_auto_register_accounts.py --db .\account_manager.db

  2. 导出为 JSON

  python .\export_any_auto_register_accounts.py --db .\account_manager.db
  --format json --output .\chatgpt_accounts.json

  3. 只导出 chatgpt 且状态为 registered

  python .\export_any_auto_register_accounts.py --db .\account_manager.db
  --platform chatgpt --status registered --format json --output .
  \chatgpt_accounts.json

  4. 导出成 CLIProxyAPI 可用的 auth 文件

  python .\export_any_auto_register_accounts.py --db .\account_manager.db
  --platform chatgpt --status registered --format cliproxyapi --output .
  \CLIProxyAPI_repo\auths

  5. 如果你已经有 chatgpt_accounts.json，再转成 CLIProxyAPI 格式

  python .\export_any_auto_register_accounts.py --input-json .
  \chatgpt_accounts.json --format cliproxyapi --output .\CLIProxyAPI_repo\auths 
  几个关键点：

  - --db 和 --input-json 只能二选一，export_any_auto_register_accounts.py:73。
  - 不写 --format 时默认是 csv；不写 --output 时会自动生成时间戳文件名，
    export_any_auto_register_accounts.py:309。
  - cliproxyapi 模式是一账号一个 JSON；如果你把 --output 写成单个 .json 文件，那
    只能导出 1 个账号，export_any_auto_register_accounts.py:369。
  - 记录里如果缺少 email / id_token / access_token / refresh_token /
    account_id，会被跳过，export_any_auto_register_accounts.py:330。
  - 你仓库里的 CLIProxyAPI_repo/docker-compose.yml:26 已经把 ./auths 挂到容器认
    证目录，所以导到 .\CLIProxyAPI_repo\auths 是对的。




-------------------------------------------------
sudo apt update
sudo apt install -y git curl build-essential python3 python3-venv python3-pip
python3-dev libffi-dev libssl-dev tmux

curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

node -v
npm -v
python3 --version

cd /opt
sudo git clone https://github.com/boomzalk/any-auto-register-fork.git
cd /opt/any-auto-register-fork

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install quart rich patchright camoufox cbor2 jwcrypto

cd /opt/any-auto-register-fork/frontend
npm ci --legacy-peer-deps

然后启动后端：

cd /opt/any-auto-register-fork
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

再开一个终端启动前端：

cd /opt/any-auto-register-fork/frontend
npm run dev -- --host 0.0.0.0 --port 5173

访问：

http://你的服务器IP:5173

如果你要用 DuckMail
进网页 Settings，把 mail_provider 改成 duckmail，然后保存。
不要继续走 laoudo 空邮箱那条路径。

-------------------------------------------------




## License

MIT License — 仅供学习研究，禁止商业使用。
