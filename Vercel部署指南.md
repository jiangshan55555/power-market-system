# 🚀 Vercel 部署完整指南

## 📍 项目位置
```
C:\Users\86182\Documents\augment-projects\assistance\power-market-system\
```

---

## 方法一：一键部署（最简单）⭐

### 步骤：
1. **双击运行**：`部署到Vercel.bat`
2. **首次使用**：会自动检查并安装 Vercel CLI
3. **登录账户**：按提示登录 Vercel
4. **确认部署**：按照提示选择选项
5. **获取 URL**：部署完成后复制在线地址

---

## 方法二：命令行部署（推荐）

### 第 1 步：安装 Vercel CLI
打开 PowerShell 或 CMD，运行：
```bash
npm install -g vercel
```

### 第 2 步：登录 Vercel
```bash
vercel login
```
- 会打开浏览器
- 选择登录方式（GitHub/GitLab/Email）
- 完成登录后返回命令行

### 第 3 步：进入项目目录
```bash
cd C:\Users\86182\Documents\augment-projects\assistance\power-market-system
```

### 第 4 步：部署
```bash
vercel --prod
```

### 第 5 步：按照提示操作
```
? Set up and deploy "C:\Users\...\power-market-system"? 
  → 输入: Y

? Which scope do you want to deploy to? 
  → 选择您的账户名

? Link to existing project? 
  → 输入: N (首次部署)

? What's your project's name? 
  → 输入: power-market-system

? In which directory is your code located? 
  → 按回车（默认 ./）

? Want to override the settings? 
  → 输入: N
```

### 第 6 步：等待部署
```
🔍 Inspect: https://vercel.com/...
✅ Production: https://power-market-system-xxx.vercel.app
```

**复制 Production URL，这就是您的在线地址！**

---

## 方法三：Vercel 网页界面部署

### 前提：项目需要在 GitHub 上

#### A. 如果项目还没有推送到 GitHub：

1. **创建 GitHub 仓库**：
   - 访问 https://github.com/new
   - 仓库名：`power-market-system`
   - 设为 Public 或 Private

2. **推送代码**：
```bash
cd C:\Users\86182\Documents\augment-projects\assistance\power-market-system

git init
git add .
git commit -m "Initial commit: Power Market System"
git branch -M main
git remote add origin https://github.com/你的用户名/power-market-system.git
git push -u origin main
```

#### B. 在 Vercel 导入项目：

1. **访问 Vercel**：https://vercel.com
2. **登录**：使用 GitHub 账户登录
3. **导入项目**：
   - 点击 "Add New..." → "Project"
   - 选择 "Import Git Repository"
   - 找到 `power-market-system` 仓库
   - 点击 "Import"

4. **配置项目**（自动检测）：
   - Framework Preset: `Next.js`
   - Root Directory: `./`
   - Build Command: `npm run build`
   - Output Directory: `.next`

5. **部署**：
   - 点击 "Deploy"
   - 等待 2-3 分钟
   - 获得在线 URL

---

## 📋 部署后的操作

### 1. 访问您的网站
```
https://power-market-system-xxx.vercel.app
```

### 2. 测试所有功能
- ✅ 数据库状态
- ✅ 历史数据查询
- ✅ 预测分析
- ✅ 投标优化

### 3. 分享给他人
直接复制 URL 发送给任何人，他们都可以访问！

---

## 🔄 更新已部署的项目

### 方法 1：使用批处理文件
双击 `部署到Vercel.bat`

### 方法 2：使用命令行
```bash
cd C:\Users\86182\Documents\augment-projects\assistance\power-market-system
vercel --prod
```

### 方法 3：通过 GitHub（如果使用了方法三）
```bash
git add .
git commit -m "更新说明"
git push
```
Vercel 会自动检测并重新部署

---

## ❓ 常见问题

### Q1: 提示 "vercel 不是内部或外部命令"
**解决**：
```bash
npm install -g vercel
```

### Q2: 部署失败
**检查**：
1. 网络连接是否正常
2. 是否已登录 Vercel
3. package.json 是否存在
4. node_modules 是否完整

**重试**：
```bash
npm install
vercel --prod
```

### Q3: 如何查看部署日志
访问：https://vercel.com/dashboard
- 找到您的项目
- 点击 "Deployments"
- 查看详细日志

### Q4: 如何绑定自定义域名
1. 访问 Vercel Dashboard
2. 选择项目 → Settings → Domains
3. 添加您的域名
4. 按照提示配置 DNS

---

## 📞 需要帮助？

- Vercel 文档：https://vercel.com/docs
- Next.js 文档：https://nextjs.org/docs
- Vercel 支持：https://vercel.com/support

---

## ✅ 快速命令参考

```bash
# 安装 Vercel CLI
npm install -g vercel

# 登录
vercel login

# 部署到生产环境
vercel --prod

# 部署到预览环境
vercel

# 查看部署列表
vercel ls

# 查看项目信息
vercel inspect
```

---

**祝您部署顺利！🎉**

