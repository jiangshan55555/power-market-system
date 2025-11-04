# 🚀 Vercel 在线部署完整指南

## 📋 部署前检查清单

确保您的项目包含以下文件：

```
power-market-system/
├── pages/
│   ├── api/                      ✅ 后端 API
│   │   ├── database/status.js    ✅ 数据库状态
│   │   ├── available-dates.js    ✅ 可用日期
│   │   ├── historical-prices.js  ✅ 历史数据
│   │   ├── predict.js            ✅ 价格预测
│   │   └── optimize.js           ✅ 投标优化
│   ├── index.js                  ✅ 主页面（542行）
│   └── _app.js                   ✅ App 配置
├── styles/
│   └── globals.css               ✅ 全局样式（294行）
├── package.json                  ✅ 依赖配置
├── next.config.js                ✅ Next.js 配置
└── vercel.json                   ✅ Vercel 配置
```

## 🌐 方法一：使用 Vercel CLI（推荐 - 最快）

### 步骤 1：安装 Vercel CLI

```bash
npm install -g vercel
```

### 步骤 2：登录 Vercel

```bash
vercel login
```

会打开浏览器，选择登录方式：
- GitHub
- GitLab
- Bitbucket
- Email

### 步骤 3：部署项目

```bash
cd power-market-system
vercel
```

首次部署会询问：
1. **Set up and deploy?** → 按 `Y`
2. **Which scope?** → 选择您的账户
3. **Link to existing project?** → 按 `N`
4. **What's your project's name?** → 输入 `power-market-system` 或按回车
5. **In which directory is your code located?** → 按回车（当前目录）
6. **Want to override the settings?** → 按 `N`

等待 30-60 秒，部署完成后会显示：
```
✅ Production: https://power-market-system-xxx.vercel.app
```

### 步骤 4：生产环境部署

```bash
vercel --prod
```

## 🌐 方法二：通过 GitHub + Vercel 网站

### 步骤 1：创建 Git 仓库

```bash
cd power-market-system
git init
git add .
git commit -m "Initial commit: 电力市场预测系统"
```

### 步骤 2：推送到 GitHub

```bash
# 在 GitHub 上创建新仓库后
git remote add origin https://github.com/YOUR_USERNAME/power-market-system.git
git branch -M main
git push -u origin main
```

### 步骤 3：在 Vercel 导入项目

1. 访问 https://vercel.com
2. 点击 **"New Project"**
3. 选择 **"Import Git Repository"**
4. 选择您的 GitHub 仓库
5. 配置项目：
   - **Framework Preset**: Next.js
   - **Root Directory**: `./` (默认)
   - **Build Command**: `npm run build` (默认)
   - **Output Directory**: `.next` (默认)
6. 点击 **"Deploy"**

等待 1-2 分钟，部署完成！

## ✅ 部署后测试

部署成功后，访问您的 Vercel URL（例如：`https://power-market-system-xxx.vercel.app`）

### 测试清单：

1. **数据库状态**
   - [ ] 点击"数据库状态"标签
   - [ ] 点击"获取数据库状态"按钮
   - [ ] 应显示：记录数 5731、平均电价 450.25 元/MWh

2. **历史数据**
   - [ ] 点击"历史数据"标签
   - [ ] 选择日期（如 2025-06-30）
   - [ ] 应显示 96 个数据点、平均价格

3. **预测分析**
   - [ ] 点击"预测分析"标签
   - [ ] 选择预测日期
   - [ ] 点击"运行预测分析"
   - [ ] 应显示预测结果和算法来源

4. **投标优化**
   - [ ] 先完成预测分析
   - [ ] 点击"投标优化"标签
   - [ ] 点击"生成投标策略"
   - [ ] 应显示预期收益、建议投标量等

## 🔧 API 端点测试

您也可以直接测试 API：

```bash
# 测试数据库状态
curl https://your-app.vercel.app/api/database/status

# 测试历史数据
curl https://your-app.vercel.app/api/historical-prices?date=2025-06-30

# 测试预测
curl -X POST https://your-app.vercel.app/api/predict \
  -H "Content-Type: application/json" \
  -d '{"date":"2025-06-30","model":"ensemble"}'
```

## 🎯 常见问题

### Q1: 部署后显示 404 错误？
**A:** 检查 `pages/index.js` 文件是否存在且路径正确

### Q2: API 返回 500 错误？
**A:** 检查浏览器控制台（F12）查看详细错误信息

### Q3: 样式没有加载？
**A:** 确保 `styles/globals.css` 文件存在，并在 `_app.js` 中正确导入

### Q4: 如何更新已部署的项目？
**A:** 
- 使用 CLI：再次运行 `vercel --prod`
- 使用 GitHub：推送新代码到 main 分支，Vercel 会自动重新部署

### Q5: 如何查看部署日志？
**A:** 访问 https://vercel.com/dashboard，选择您的项目，点击 "Deployments"

## 📱 分享您的项目

部署成功后，您可以：
- ✅ 分享 URL 给任何人访问
- ✅ 绑定自定义域名
- ✅ 查看访问统计
- ✅ 设置环境变量

## 🎉 恭喜！

您的电力市场预测与投标优化系统已成功部署到 Vercel！

**下一步优化建议：**
1. 连接真实数据库（Vercel Postgres / Supabase）
2. 添加用户认证（NextAuth.js）
3. 集成真实的机器学习模型
4. 添加数据可视化图表（Chart.js）
5. 启用 Vercel Analytics

---

**需要帮助？** 查看 [Vercel 官方文档](https://vercel.com/docs)

