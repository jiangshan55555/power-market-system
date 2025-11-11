# 📦 通过 GitHub Desktop 部署到 Vercel 平台 - 完整指南

## 📋 部署步骤总览

1. ✅ 准备项目文件（已完成）
2. 📤 使用 GitHub Desktop 上传到 GitHub
3. 🚀 在 Vercel 导入 GitHub 项目
4. ⚙️ 配置 Vercel 设置
5. 🎉 部署完成

---

## 第一步：使用 GitHub Desktop 上传项目

### 1.1 打开 GitHub Desktop

1. 打开 **GitHub Desktop** 应用
2. 如果还没有登录，先登录你的 GitHub 账号

### 1.2 添加本地仓库

**方法一：拖拽添加**
1. 直接将文件夹 `power-prediction-system` 拖拽到 GitHub Desktop 窗口

**方法二：菜单添加**
1. 点击菜单 **File** → **Add Local Repository**
2. 点击 **Choose...** 按钮
3. 选择文件夹：`C:\Users\86182\Documents\augment-projects\assistance\power-prediction-system`
4. 点击 **Add Repository**

### 1.3 创建新仓库（如果是第一次）

如果 GitHub Desktop 提示 "This directory does not appear to be a Git repository"：

1. 点击 **Create a repository** 按钮
2. 或者点击 **Initialize Git Repository**

填写信息：
- **Name**: `power-prediction-system`（已自动填写）
- **Description**: `电力市场价格预测与投标优化系统`
- **Local Path**: 确认路径正确
- **Initialize this repository with a README**: ❌ 不勾选（我们已有 README）
- **Git Ignore**: 选择 `Python`
- **License**: 选择 `None` 或 `MIT`

点击 **Create Repository** 按钮

### 1.4 查看更改

在 GitHub Desktop 左侧，你会看到所有文件的列表：
- ✅ `api/` - API 后端文件
- ✅ `src/` - 源代码
- ✅ `data/` - 数据文件
- ✅ `config/` - 配置文件
- ✅ `index.html` - 前端页面
- ✅ `vercel.json` - Vercel 配置
- ✅ `requirements.txt` - Python 依赖
- ✅ 其他文件...

### 1.5 提交更改（Commit）

1. 在左下角 **Summary** 框中输入提交信息：
   ```
   Initial commit: 电力市场预测与投标优化系统
   ```

2. 在 **Description** 框中输入详细说明（可选）：
   ```
   - 实现价格预测功能（6个模型）
   - 实现投标优化功能（神经动力学算法）
   - 完整的 Web 界面
   - 准备部署到 Vercel
   ```

3. 点击 **Commit to main** 按钮

### 1.6 发布到 GitHub

1. 点击顶部的 **Publish repository** 按钮

2. 在弹出窗口中设置：
   - **Name**: `power-prediction-system`
   - **Description**: `电力市场价格预测与投标优化系统`
   - **Keep this code private**: 
     - ✅ 勾选 = 私有仓库（推荐）
     - ❌ 不勾选 = 公开仓库
   - **Organization**: 选择你的账号（或组织）

3. 点击 **Publish Repository** 按钮

4. 等待上传完成（可能需要几分钟，因为有数据文件）

5. 上传完成后，点击 **View on GitHub** 查看仓库

---

## 第二步：在 Vercel 导入项目

### 2.1 登录 Vercel

1. 打开浏览器，访问：https://vercel.com
2. 点击右上角 **Sign Up** 或 **Log In**
3. 选择 **Continue with GitHub** 使用 GitHub 账号登录
4. 授权 Vercel 访问你的 GitHub 账号

### 2.2 导入 GitHub 项目

1. 登录后，点击右上角 **Add New...** → **Project**
2. 或者直接访问：https://vercel.com/new

3. 在 **Import Git Repository** 页面：
   - 找到 `power-prediction-system` 仓库
   - 点击 **Import** 按钮

4. 如果没有看到仓库：
   - 点击 **Adjust GitHub App Permissions**
   - 授权 Vercel 访问该仓库
   - 返回后刷新页面

### 2.3 配置项目设置

在 **Configure Project** 页面：

#### 基本设置
- **Project Name**: `power-prediction-system`（可以修改）
- **Framework Preset**: 选择 `Other`
- **Root Directory**: `./`（保持默认）

#### 构建设置（Build Settings）
- **Build Command**: 留空（不需要构建）
- **Output Directory**: 留空
- **Install Command**: `pip install -r requirements.txt`

#### 环境变量（Environment Variables）
暂时不需要添加，点击 **Deploy** 即可

### 2.4 开始部署

1. 检查所有设置正确
2. 点击 **Deploy** 按钮
3. 等待部署完成（3-5 分钟）

---

## 第三步：部署过程

### 3.1 观察部署日志

部署过程中，你会看到：
1. **Building** - 安装依赖
2. **Deploying** - 部署文件
3. **Ready** - 部署完成

### 3.2 可能遇到的问题

#### ⚠️ 问题 1：依赖安装失败
**原因**：某些 Python 包在 Vercel 上不可用

**解决方案**：
- 检查 `requirements.txt` 中的包版本
- 移除不必要的包

#### ⚠️ 问题 2：超时限制
**原因**：Vercel 免费版有 10 秒超时限制

**影响**：
- ✅ 页面加载：正常
- ✅ 简单 API：正常
- ❌ 预测功能：可能超时（需要 1-2 分钟）
- ❌ 投标优化：可能超时（需要 2-5 分钟）

**解决方案**：
1. 升级到 Vercel Pro（60 秒超时）
2. 或使用其他平台（Railway、Render）

#### ⚠️ 问题 3：文件大小限制
**原因**：Vercel 有文件大小限制

**解决方案**：
- 压缩大文件
- 使用外部存储（如 AWS S3）

---

## 第四步：部署完成

### 4.1 访问网站

部署成功后，Vercel 会显示：
```
🎉 Congratulations!
Your project has been deployed.
```

你会看到：
- **Production URL**: `https://power-prediction-system.vercel.app`
- 或自定义域名

点击 **Visit** 按钮访问网站

### 4.2 测试功能

1. **测试页面加载**：
   - 访问首页
   - 检查 4 个标签页是否正常

2. **测试数据库状态**：
   - 点击 "📊 数据库状态" 标签
   - 查看数据统计

3. **测试历史数据**：
   - 点击 "📈 历史数据" 标签
   - 查看数据表格

4. **测试预测功能**（可能超时）：
   - 点击 "🔮 预测价格" 标签
   - 点击 "🚀 运行原项目预测"
   - ⚠️ 如果超时，需要升级 Vercel 或换平台

5. **测试投标优化**（可能超时）：
   - 点击 "⚙️ 投标优化" 标签
   - 点击 "🎯 运行投标优化"
   - ⚠️ 如果超时，需要升级 Vercel 或换平台

---

## 第五步：后续更新

### 5.1 修改代码后更新

1. 在本地修改代码
2. 打开 GitHub Desktop
3. 查看更改
4. 填写 Commit 信息
5. 点击 **Commit to main**
6. 点击 **Push origin**
7. Vercel 会自动检测并重新部署

### 5.2 查看部署历史

1. 登录 Vercel Dashboard
2. 选择项目 `power-prediction-system`
3. 点击 **Deployments** 标签
4. 查看所有部署记录

---

## ⚠️ 重要提醒

### Vercel 免费版限制

| 限制项 | 免费版 | Pro 版 |
|--------|--------|--------|
| **超时时间** | 10 秒 | 60 秒 |
| **部署次数** | 100/天 | 无限 |
| **带宽** | 100 GB/月 | 1 TB/月 |
| **团队成员** | 1 人 | 无限 |

### 我们的系统需求

| 功能 | 需要时间 | Vercel 免费版 | 建议 |
|------|----------|---------------|------|
| 页面加载 | < 1 秒 | ✅ 支持 | 正常使用 |
| 数据查询 | < 1 秒 | ✅ 支持 | 正常使用 |
| 预测功能 | 1-2 分钟 | ❌ 超时 | 升级或换平台 |
| 投标优化 | 2-5 分钟 | ❌ 超时 | 升级或换平台 |

### 替代方案

如果 Vercel 免费版不满足需求，可以考虑：

1. **Railway.app**（推荐）
   - 免费版：5 小时/月
   - 无超时限制
   - 支持 Python

2. **Render.com**
   - 免费版：750 小时/月
   - 无超时限制
   - 支持 Python

3. **Heroku**
   - 免费版已取消
   - 付费版：$7/月

---

## 📝 快速检查清单

部署前检查：
- [ ] GitHub Desktop 已安装并登录
- [ ] 项目文件夹路径正确
- [ ] 所有文件已提交（Commit）
- [ ] 已发布到 GitHub（Publish）
- [ ] Vercel 账号已创建
- [ ] GitHub 授权给 Vercel

部署后检查：
- [ ] 网站可以访问
- [ ] 页面正常显示
- [ ] 数据库状态正常
- [ ] 历史数据可查看
- [ ] 预测功能测试（可能超时）
- [ ] 投标优化测试（可能超时）

---

## 🆘 需要帮助？

如果遇到问题：
1. 查看 Vercel 部署日志
2. 检查 GitHub Desktop 是否成功推送
3. 确认 `vercel.json` 配置正确
4. 检查 `requirements.txt` 依赖

---

**祝你部署顺利！** 🚀

