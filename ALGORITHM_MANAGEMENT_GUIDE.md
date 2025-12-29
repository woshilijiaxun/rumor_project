# 算法管理功能实现指南

## 概述
已成功在前端侧栏添加了"算法管理"功能，包括完整的前后端实现。

## 前端改动

### 1. 侧栏菜单更新
**文件**: `frontend/src/components/Sidebar.vue`
- 在侧栏菜单中添加了"算法管理"菜单项
- 位置：在"用户管理"和"文件管理"之间

### 2. 新增算法管理页面
**文件**: `frontend/src/modules/algorithms/AlgorithmsPage.vue`
- 完整的算法管理界面，包含以下功能：
  - **列表展示**：分页显示所有算法，包含名称、描述、类型、状态、创建时间等信息
  - **搜索功能**：支持按算法名称和描述搜索
  - **状态筛选**：可按启用/禁用状态筛选
  - **新增算法**：弹窗表单创建新算法
  - **编辑算法**：点击编辑按钮修改算法信息
  - **启用/禁用**：快速切换算法状态
  - **删除算法**：删除不需要的算法（带确认提示）
  - **分页导航**：支持上一页/下一页导航

### 3. 路由配置更新
**文件**: `frontend/src/router/index.js`
- 导入 `AlgorithmsPage` 组件
- 在路由配置中添加 `/algorithms` 路由

## 后端改动

### 1. 数据库表创建
**文件**: `backend/init_db.py`
- 添加了 `algorithms` 表，包含以下字段：
  - `id`: 主键
  - `user_id`: 用户ID（外键）
  - `name`: 算法名称（必填）
  - `description`: 算法描述
  - `type`: 算法类型（如：排序、搜索、图论等）
  - `status`: 状态（active/inactive，默认为 active）
  - `created_at`: 创建时间
  - `updated_at`: 更新时间
  - 包含索引优化查询性能

### 2. API 端点实现
**文件**: `backend/app.py`

#### 获取算法列表
```
GET /api/algorithms?page=1&page_size=10
```
- 返回分页的算法列表
- 需要认证

#### 创建算法
```
POST /api/algorithms
Content-Type: application/json

{
  "name": "快速排序",
  "description": "一种高效的排序算法",
  "type": "排序",
  "status": "active"
}
```
- 返回创建的算法ID
- 需要认证

#### 获取单个算法
```
GET /api/algorithms/<algo_id>
```
- 返回指定ID的算法详情
- 需要认证

#### 更新算法
```
PUT /api/algorithms/<algo_id>
Content-Type: application/json

{
  "name": "新名称",
  "description": "新描述",
  "type": "新类型",
  "status": "inactive"
}
```
- 支持部分字段更新
- 需要认证

#### 删除算法
```
DELETE /api/algorithms/<algo_id>
```
- 删除指定ID的算法
- 需要认证

## 使用步骤

### 1. 初始化数据库
运行数据库初始化脚本以创建算法表：
```bash
cd backend
python init_db.py
```

### 2. 启动后端服务
```bash
cd backend
python app.py
```
后端将运行在 `http://localhost:5001`

### 3. 启动前端服务
```bash
cd frontend
npm run dev
```
前端将运行在 `http://localhost:5174`（或其他可用端口）

### 4. 访问应用
1. 打开浏览器访问前端地址
2. 使用测试账号登录（用户名: admin，密码: admin123）
3. 在侧栏点击"算法管理"进入算法管理页面
4. 开始使用各项功能

## 功能特性

### 前端特性
- ✅ 响应式设计，适配不同屏幕尺寸
- ✅ 实时搜索和筛选
- ✅ 模态框表单验证
- ✅ 操作提示信息（成功/失败）
- ✅ 分页导航
- ✅ 日期格式化显示

### 后端特性
- ✅ RESTful API 设计
- ✅ JWT 认证保护
- ✅ 数据库事务处理
- ✅ 错误处理和日志
- ✅ 分页支持
- ✅ 参数验证

## 数据流示例

### 创建新算法的流程
1. 用户点击"+ 新增算法"按钮
2. 弹出表单，用户填写算法信息
3. 点击"保存"按钮
4. 前端发送 POST 请求到 `/api/algorithms`
5. 后端验证数据并插入数据库
6. 返回成功响应
7. 前端刷新列表并显示成功提示

### 编辑算法的流程
1. 用户点击列表中的"编辑"按钮
2. 表单预填充现有数据
3. 用户修改信息
4. 点击"保存"按钮
5. 前端发送 PUT 请求到 `/api/algorithms/<id>`
6. 后端更新数据库记录
7. 返回成功响应
8. 前端刷新列表并显示成功提示

## 扩展建议

### 可以进一步添加的功能
1. **批量操作**：支持批量删除、批量启用/禁用
2. **导出功能**：导出算法列表为 Excel/CSV
3. **算法详情页**：展示算法的详细信息和实现代码
4. **版本管理**：跟踪算法的版本历史
5. **标签系统**：为算法添加标签便于分类
6. **评分系统**：用户可以对算法进行评分
7. **复杂度分析**：显示算法的时间/空间复杂度
8. **代码示例**：存储和展示算法的实现代码

## 常见问题

### Q: 如何修改 API 地址？
A: 在 `frontend/src/modules/algorithms/AlgorithmsPage.vue` 中修改 `apiBaseUrl` 变量

### Q: 如何修改分页大小？
A: 在 `AlgorithmsPage.vue` 中修改 `pageSize` 的初始值

### Q: 如何添加更多字段？
A: 
1. 在数据库表中添加新列
2. 在后端 API 中处理新字段
3. 在前端表单中添加对应的输入框

## 技术栈

### 前端
- Vue 3（Composition API）
- Vue Router
- 原生 CSS（无框架依赖）

### 后端
- Flask
- MySQL
- JWT 认证

## 文件清单

### 新增文件
- `frontend/src/modules/algorithms/AlgorithmsPage.vue` - 算法管理页面组件

### 修改文件
- `frontend/src/components/Sidebar.vue` - 添加侧栏菜单项
- `frontend/src/router/index.js` - 添加路由配置
- `backend/app.py` - 添加 API 端点
- `backend/init_db.py` - 添加数据库表

## 许可证
同项目主许可证

