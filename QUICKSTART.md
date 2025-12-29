# 快速启动指南

## 第一步：配置数据库

1. 确保 MySQL 已安装并运行
2. 编辑 `backend/config.py`，修改数据库密码：
   ```python
   DB_PASSWORD = '你的MySQL密码'
   ```

## 第二步：初始化数据库

```bash
# 激活虚拟环境
source venv/bin/activate

# 初始化数据库
cd backend
python init_db.py
```

## 第三步：启动服务

### 方式一：使用脚本（推荐）

打开两个终端窗口：

**终端 1 - 启动后端：**
```bash
./start_backend.sh
```

**终端 2 - 启动前端：**
```bash
./start_frontend.sh
```

### 方式二：手动启动

**启动后端：**
```bash
source venv/bin/activate
cd backend
python app.py
```

**启动前端：**
```bash
cd frontend
npm install  # 如果还没安装依赖
npm run dev
```

## 第四步：访问应用

打开浏览器访问：`http://localhost:5173`

## 测试账号

- 用户名: `admin`
- 密码: `admin123`

## 常见问题

### 数据库连接失败
- 检查 MySQL 服务是否运行：`mysql -u root -p`
- 检查 `backend/config.py` 中的密码是否正确

### 端口被占用
- 后端端口 5000 被占用：修改 `backend/app.py` 最后一行端口号
- 前端端口 5173 被占用：Vite 会自动使用下一个可用端口

### 前端无法连接后端
- 确保后端已启动（访问 http://localhost:5000/api/health 测试）
- 检查浏览器控制台错误信息

