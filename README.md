# 谣言检测与分析系统

基于 **Flask + Vue 3 + MySQL** 的谣言检测与分析平台，提供用户管理、文件上传、算法管理与网络分析等能力。

Author：Jiaxun Li
---

## 目录

- [项目简介](#项目简介)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [本地运行](#本地运行)
  - [1) 数据库准备](#1-数据库准备)
  - [2) 后端启动](#2-后端启动)
  - [3) 前端启动](#3-前端启动)
  - [4) 访问地址](#4-访问地址)
- [核心模块说明](#核心模块说明)
  - [后端](#后端)
  - [前端](#前端)
- [常用脚本](#常用脚本)
- [开发提示](#开发提示)
- [许可证](#许可证)

---

## 项目简介

本项目为一个前后端分离的全栈 Web 应用：

- 后端采用 Flask，按 **Blueprint + Service + Repository** 分层组织代码。
- 前端采用 Vue 3 + Vite，按业务模块组织页面与组件。
- 支持算法模块化接入（registry 注册），用于识别/分析任务与结果展示。
- 提供文件上传管理及静态资源访问。

> 说明：仓库内还包含若干指南文档（如 `QUICKSTART.md`、`ALGORITHM_MANAGEMENT_GUIDE.md` 等），可作为补充参考。

---

## 技术栈

- **后端**：Flask（含 Blueprint 组织）、PyMySQL/数据库访问、CORS（以依赖为准）
- **前端**：Vue 3、Vue Router、Axios、Vite
- **数据库**：MySQL（或兼容实现）

---

## 项目结构

> 以仓库当前目录结构为准（已省略 `venv/`、`node_modules/`、`dist/` 等生成内容）。

```text
flaskProject/
├── backend/                       # Flask 后端
│   ├── app.py                     # 后端入口
│   ├── config.py                  # 配置
│   ├── requirements.txt           # Python 依赖
│   ├── init_db.py                 # 数据库初始化
│   ├── init_db_immigate.py        # 数据库初始化/迁移相关脚本（如使用）
│   └── application/
│       ├── factory.py             # 应用工厂
│       ├── algorithms/            # 算法模块（registry + 各算法实现）
│       ├── blueprints/            # API 路由（auth/users/uploads/...）
│       ├── common/                # 公共工具（db/auth/errors/responses）
│       ├── repositories/          # 数据访问层
│       └── services/              # 业务服务层
│
├── frontend/                      # Vue 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/                # 路由
│       ├── layouts/               # 布局
│       ├── components/            # 通用组件
│       ├── views/                 # 视图
│       └── modules/               # 业务模块（dashboard/users/files/...）
│
├── static/                        # 静态资源/上传文件（当前有 uploads/）
├── templates/                     # 模板目录（如使用）
│
├── start_backend.sh               # 后端启动脚本
├── start_frontend.sh              # 前端启动脚本
├── run_crawler.sh                 # 爬虫脚本（如使用）
├── pachong.py                     # 爬虫脚本（如使用）
│
├── QUICKSTART.md
├── ALGORITHM_MANAGEMENT_GUIDE.md
├── ALGORITHM_SETUP_CHECKLIST.md
└── FILE_MANAGEMENT_FIXES.md
```

---

## 环境要求

- Python 3.9+
- Node.js 16+
- MySQL 5.7+ / MySQL 8.0+

---

## 本地运行

### 1) 数据库准备

1. 确保 MySQL 服务已启动。
2. 修改后端数据库连接配置：`backend/config.py`。
3. 初始化数据库：

```bash
# 进入后端目录
cd backend

#（建议）激活虚拟环境
source ../venv/bin/activate

# 初始化数据库
python init_db.py
```

> 若项目使用 `init_db_immigate.py` 或其它迁移脚本，请按实际需求执行对应脚本。

### 2) 后端启动

方式 A：脚本启动（推荐）

```bash
./start_backend.sh
```

方式 B：手动启动

```bash
cd backend
source ../venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 3) 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 4) 访问地址

- 前端默认：`http://localhost:5173`
- 后端默认：`http://localhost:5000`

---

## 核心模块说明

### 后端

后端主要按以下层级组织：

- `application/blueprints/`：路由与接口聚合（如 `auth.py`、`users.py`、`uploads.py`、`algorithms.py`、`network.py`、`stats.py` 等）
- `application/services/`：业务逻辑（如用户、上传、算法、图谱、统计、健康检查等）
- `application/repositories/`：数据库/持久层访问（如 users、uploads、system_config、audit_logs 等）
- `application/algorithms/`：算法实现与注册
  - `registry.py`：算法注册中心
  - `*_algo.py`：对外暴露的算法适配/封装
  - `my_algo_module/`：算法实现细节模块

### 前端

前端主要按模块划分：

- `src/modules/`：业务页面模块
  - `dashboard/` 仪表盘
  - `users/` 用户管理
  - `files/` 文件管理
  - `algorithms/` 算法相关
  - `identification/` 识别/任务/结果展示
  - `settings/` 设置
- `src/layouts/`：布局（Admin/Auth）
- `src/router/`：路由

---

## 常用脚本

- 启动后端：`./start_backend.sh`
- 启动前端：`./start_frontend.sh`
- 运行爬虫：`./run_crawler.sh` 或 `python pachong.py`（按实际脚本内容使用）

---

## 开发提示

- 若新增算法：在 `backend/application/algorithms/` 添加实现，并在 `registry.py` 中注册。
- 若新增接口：优先在对应 `blueprints` 中添加路由，并将业务逻辑放在 `services`，数据库访问放在 `repositories`。
- 上传文件默认存放于 `static/uploads/`（以代码实现为准）。

---

## 许可证

如无特别说明，默认仅用于学习/内部使用。若需开源发布，请补充明确的 LICENSE。
