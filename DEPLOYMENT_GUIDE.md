# 🚀 部署指南 - 电力市场预测与投标优化系统

## 📋 部署前准备

### 1. 确保项目结构完整

您的项目应该包含以下文件：

```
power-market-system/
├── pages/
│   ├── api/
│   │   ├── database/
│   │   │   └── status.js
│   │   ├── available-dates.js
│   │   ├── historical-prices.js
│   │   ├── predict.js
│   │   └── optimize.js
│   ├── index.js          ← 需要手动创建
│   └── _app.js
├── styles/
│   └── globals.css
├── package.json
├── next.config.js
├── vercel.json
└── README.md
```

### 2. 创建 index.js 文件

由于文件较大，请按以下步骤操作：

1. 在 `power-market-system/pages/` 目录下创建 `index.js` 文件
2. 复制 `INDEX_JS_CONTENT.txt` 中的完整内容
3. 粘贴到 `index.js` 文件中
4. 保存文件

## 🌐 部署到 Vercel

### 方法1：使用 Vercel CLI（推荐）

```bash
# 1. 安装 Vercel CLI
npm install -g vercel

# 2. 登录 Vercel
vercel login

# 3. 进入项目目录
cd power-market-system

# 4. 部署
vercel

# 5. 生产部署
vercel --prod
```

### 方法2：通过 GitHub + Vercel 网站

#### 步骤1：推送到 GitHub

```bash
# 初始化 Git（如果还没有）
cd power-market-system
git init
git add .
git commit -m "Initial commit: Power Market System"

# 创建 GitHub 仓库并推送
git remote add origin https://github.com/YOUR_USERNAME/power-market-system.git
git branch -M main
git push -u origin main
```

#### 步骤2：在 Vercel 上导入

1. 访问 https://vercel.com
2. 点击 "New Project"
3. 选择 "Import Git Repository"
4. 选择您的 GitHub 仓库
5. **重要**：设置 Root Directory 为 `power-market-system`
6. Framework Preset 选择 "Next.js"
7. 点击 "Deploy"

### 方法3：直接拖拽部署

1. 访问 https://vercel.com
2. 点击 "New Project"
3. 选择 "Upload"
4. 将整个 `power-market-system` 文件夹拖拽到页面
5. 点击 "Deploy"

## ✅ 部署后验证

部署成功后，Vercel 会提供一个 URL，例如：
```
https://power-market-system-xxx.vercel.app
```

### 测试 API 端点

```bash
# 测试数据库状态
curl https://your-app.vercel.app/api/database/status

# 测试可用日期
curl https://your-app.vercel.app/api/available-dates

# 测试历史数据
curl https://your-app.vercel.app/api/historical-prices?date=2025-06-30
```

## 🔧 常见问题

### Q1: 部署失败，提示找不到 index.js
**A**: 确保 `pages/index.js` 文件存在且内容完整

### Q2: API 返回 404
**A**: 检查 `pages/api/` 目录下的文件是否都存在

### Q3: 页面显示空白
**A**: 打开浏览器控制台查看错误信息，通常是 index.js 文件内容不完整

### Q4: 本地开发正常，部署后出错
**A**: 检查 `next.config.js` 和 `vercel.json` 配置是否正确

## 📝 下一步优化

1. **添加环境变量**
   - 在 Vercel 项目设置中添加环境变量
   - 用于数据库连接、API 密钥等

2. **连接真实数据库**
   - 推荐使用 Vercel Postgres
   - 或者 Supabase、MongoDB Atlas

3. **添加域名**
   - 在 Vercel 项目设置中添加自定义域名

4. **性能优化**
   - 启用 Vercel Analytics
   - 配置 CDN 缓存

## 🎉 完成！

部署成功后，您的电力市场预测系统就可以在线访问了！

访问您的网站，测试所有功能：
- ✅ 数据库状态查询
- ✅ 历史数据查看
- ✅ 价格预测
- ✅ 投标优化

---

**需要帮助？** 查看 [Vercel 文档](https://vercel.com/docs) 或联系技术支持。

