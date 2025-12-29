# Flask + Vue + MySQL Web 应用

这是一个完整的全栈 Web 应用示例，使用 Flask 作为后端，Vue 3 作为前端，MySQL 作为数据库。

## 项目结构

```
flaskProject/
├── backend/              # Flask 后端
│   ├── app.py           # 主应用文件
│   ├── config.py        # 配置文件
│   ├── init_db.py       # 数据库初始化脚本
│   └── requirements.txt # Python 依赖
├── frontend/            # Vue 前端
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── router/      # 路由配置
│   │   └── App.vue      # 根组件
│   ├── package.json     # Node 依赖
│   └── vite.config.js   # Vite 配置
├── start_backend.sh     # 后端启动脚本
└── start_frontend.sh    # 前端启动脚本
```

## 功能特性

- ✅ 用户注册
- ✅ 用户登录
- ✅ 用户列表展示
- ✅ 响应式设计
- ✅ 前后端分离架构
- ✅ RESTful API

## 快速开始

### 1. 环境要求

- Python 3.9+
- Node.js 16+
- MySQL 5.7+ 或 MySQL 8.0+

### 2. 数据库配置

#### 安装 MySQL

确保 MySQL 服务已安装并运行。

#### 修改数据库配置

编辑 `backend/config.py` 文件，修改数据库连接信息：

```python
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'your_password'  # 修改为你的 MySQL 密码
DB_NAME = 'testdb'
```

#### 初始化数据库

```bash
# 激活虚拟环境
source venv/bin/activate

# 进入后端目录
cd backend

# 运行初始化脚本
python init_db.py
```

这将自动创建数据库和表，并插入一个测试用户：
- 用户名: `admin`
- 密码: `admin123`

### 3. 安装后端依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
cd backend
pip install -r requirements.txt
```

### 4. 安装前端依赖

```bash
cd frontend
npm install
```

### 5. 启动服务

#### 方式一：使用启动脚本（推荐）

**终端 1 - 启动后端：**
```bash
./start_backend.sh
```

**终端 2 - 启动前端：**
```bash
./start_frontend.sh
```

#### 方式二：手动启动

**启动后端：**
```bash
source venv/bin/activate
cd backend
python app.py
```

后端将在 `http://localhost:5000` 运行

**启动前端：**
```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 运行

### 6. 访问应用

打开浏览器访问：`http://localhost:5173`

## API 端点

### 健康检查
- `GET /api/health` - 检查服务状态

### 用户相关
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录
- `GET /api/users` - 获取用户列表

## 测试账号

初始化数据库后，可以使用以下账号登录：
- 用户名: `admin`
- 密码: `admin123`

## 开发说明

### 后端开发

- Flask 应用入口：`backend/app.py`
- 配置文件：`backend/config.py`
- 数据库初始化：`backend/init_db.py`

### 前端开发

- 路由配置：`frontend/src/router/index.js`
- 页面组件：`frontend/src/views/`
- Vite 配置：`frontend/vite.config.js`

前端通过 Vite 代理访问后端 API，代理配置在 `vite.config.js` 中。

## 常见问题

### 1. 数据库连接失败

- 检查 MySQL 服务是否运行
- 检查 `backend/config.py` 中的数据库配置是否正确
- 确保数据库用户有创建数据库的权限

### 2. 端口被占用

- 后端默认端口：5000
- 前端默认端口：5173
- 可以在配置文件中修改端口

### 3. 前端无法连接后端

- 确保后端服务已启动
- 检查 `frontend/vite.config.js` 中的代理配置
- 检查浏览器控制台是否有错误信息

## 技术栈

- **后端**: Flask 2.3.2, PyMySQL, Flask-CORS
- **前端**: Vue 3, Vue Router, Axios, Vite
- **数据库**: MySQL

## 许可证

MIT License

