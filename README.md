# go-stock Python 版

go-stock 的 Python + React 全栈重构版本，提供股票行情监控、AI 智能分析、价格预警等核心功能，支持 Docker 一键部署。

## 技术栈

### 后端
| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.12+ | 运行环境 |
| FastAPI | 0.115 | 高性能异步 Web 框架 |
| SQLAlchemy | 2.0 | 异步 ORM |
| Alembic | 1.13 | 数据库迁移 |
| Redis | 5.1 | 缓存 / 消息队列 |
| APScheduler | 3.10 | 定时任务调度 |
| LiteLLM | 1.48 | 多模型 AI 统一接口 |
| SSE-Starlette | 2.1 | Server-Sent Events 流式推送 |
| Playwright | 1.47 | 浏览器自动化（K 线截图等） |

### 前端
| 技术 | 版本 | 说明 |
|------|------|------|
| React | 18.3 | UI 框架 |
| TypeScript | 5.5 | 类型安全 |
| Vite | 5.4 | 构建工具 |
| Ant Design | 5.20 | 组件库 |
| ECharts | 5.5 | 图表可视化 |
| lightweight-charts | 4.2 | K 线图 |
| Zustand | 4.5 | 状态管理 |
| Axios | 1.7 | HTTP 客户端 |

### 基础设施
- **Nginx** - 反向代理 + 静态文件服务
- **Redis 7** - 数据缓存
- **SQLite / PostgreSQL** - 持久化存储
- **Docker & Docker Compose** - 容器化部署

---

## 快速开始

### 方式一：Docker Compose（推荐）

**前置条件：** Docker Desktop 已安装并运行

```bash
# 1. 克隆项目
git clone https://github.com/your-org/go-stock.git
cd go-stock/go-stock-python

# 2. 复制并编辑环境变量
cp .env.example .env
# 编辑 .env 文件，至少填写 AI_API_KEY

# 3. 一键启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f backend
```

启动成功后访问：
- **前端页面：** http://localhost（或 http://localhost:3000 直接访问前端）
- **API 文档：** http://localhost/docs（Swagger UI）
- **ReDoc 文档：** http://localhost/redoc

**停止服务：**
```bash
docker-compose down

# 同时删除数据卷（会清除数据库和 Redis 数据）
docker-compose down -v
```

### 方式二：本地开发

#### 后端

**前置条件：** Python 3.12+、Redis（本地运行或 Docker）

```bash
cd go-stock-python/backend

# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（首次）
playwright install chromium

# 复制环境变量
cp ../.env.example ../.env
# 编辑 .env，将 REDIS_URL 改为 redis://localhost:6379/0

# 执行数据库迁移
alembic upgrade head

# 启动开发服务器（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档：http://localhost:8000/docs

#### 前端

**前置条件：** Node.js 18+

```bash
cd go-stock-python/frontend

# 安装依赖
npm install

# 启动开发服务器（热重载）
npm run dev
```

前端开发地址：http://localhost:5173

---

## 项目结构

```
go-stock-python/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口，挂载路由和中间件
│   │   ├── config.py           # 配置管理（从环境变量加载）
│   │   ├── core/               # 核心模块
│   │   │   ├── database.py     # 数据库连接与会话
│   │   │   ├── redis_client.py # Redis 客户端
│   │   │   └── scheduler.py    # 定时任务调度器
│   │   ├── models/             # SQLAlchemy 数据模型
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── routers/            # API 路由（按业务拆分）
│   │   │   ├── stocks.py       # 股票行情接口
│   │   │   ├── ai_chat.py      # AI 对话接口（SSE 流式）
│   │   │   ├── alerts.py       # 价格预警接口
│   │   │   └── settings.py     # 系统设置接口
│   │   └── services/           # 业务逻辑层
│   ├── alembic/                # 数据库迁移脚本
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/         # 可复用组件
│   │   ├── pages/              # 页面组件
│   │   ├── stores/             # Zustand 状态管理
│   │   ├── services/           # API 调用封装
│   │   └── types/              # TypeScript 类型定义
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
│
├── docker-compose.yml          # Docker Compose 编排配置
├── nginx.conf                  # Nginx 反向代理配置
├── .env.example                # 环境变量模板
└── README.md                   # 本文件
```

---

## API 文档

启动服务后，访问以下地址查看交互式 API 文档：

- **Swagger UI：** http://localhost/docs
- **ReDoc：** http://localhost/redoc

主要接口分组：

| 路由前缀 | 说明 |
|----------|------|
| `/api/stocks` | 股票行情查询、批量获取 |
| `/api/ai` | AI 对话、流式推理（SSE） |
| `/api/alerts` | 价格预警管理 |
| `/api/settings` | 系统配置管理 |
| `/ws/` | WebSocket 实时推送 |

---

## 开发指南

### 数据库迁移

```bash
cd backend

# 生成新迁移文件
alembic revision --autogenerate -m "描述变更内容"

# 应用迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1
```

### 代码规范

**后端（Python）：**
- 遵循 PEP 8，使用 `black` 格式化
- 类型注解覆盖所有函数签名
- 异步函数使用 `async/await`
- 路由层只做参数验证，业务逻辑放到 `services/`

**前端（TypeScript）：**
- 严格模式（`strict: true`）
- 组件使用函数式写法 + Hooks
- 全局状态用 Zustand，局部状态用 `useState`

### 常用 Docker 命令

```bash
# 重新构建特定服务
docker-compose build backend
docker-compose up -d backend

# 进入容器 Shell
docker-compose exec backend bash
docker-compose exec frontend sh

# 查看实时日志
docker-compose logs -f

# 清理无用镜像
docker image prune -f
```

### 环境变量说明

详细说明见 [.env.example](.env.example)，主要变量：

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `AI_API_KEY` | ✅ | AI 模型 API 密钥 |
| `AI_BASE_URL` | ✅ | AI 服务地址 |
| `AI_MODEL_NAME` | ✅ | 使用的模型名称 |
| `DATABASE_URL` | ❌ | 数据库连接串（默认 SQLite） |
| `REDIS_URL` | ❌ | Redis 连接串 |
| `DINGDING_WEBHOOK_URL` | ❌ | 钉钉机器人 Webhook（预警功能） |

---

## License

MIT © go-stock contributors
