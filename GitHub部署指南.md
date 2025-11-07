# 📦 通过 GitHub 部署到 Vercel 完整指南

## 🎯 部署流程概览

```
本地代码 → Git → GitHub → Vercel → 线上网站
```

---

## 第一步：安装 Git

### Windows 系统

1. **下载 Git**：
   - 访问：https://git-scm.com/download/win
   - 下载并安装（使用默认设置）

2. **验证安装**：
   ```bash
   git --version
   ```

---

## 第二步：初始化 Git 仓库

在 `power-market-system` 目录下打开命令行，执行：

```bash
# 1. 初始化 Git 仓库
git init

# 2. 配置用户信息（首次使用）
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"

# 3. 添加所有文件
git add .

# 4. 提交代码
git commit -m "feat: 完成电力市场预测系统美化升级"
```

---

## 第三步：创建 GitHub 仓库

1. **登录 GitHub**：https://github.com

2. **创建新仓库**：
   - 点击右上角 `+` → `New repository`
   - **Repository name**：`power-market-system`
   - **Description**：`电力市场预测与投标优化系统`
   - **Public** 或 **Private**：根据需要选择
   - **不要勾选** "Initialize this repository with a README"
   - 点击 `Create repository`

3. **复制仓库地址**：
   ```
   https://github.com/你的用户名/power-market-system.git
   ```

---

## 第四步：推送代码到 GitHub

```bash
# 1. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/power-market-system.git

# 2. 推送代码
git branch -M main
git push -u origin main
```

**注意**：首次推送需要 GitHub 身份验证

### GitHub 身份验证方式

**方式1：Personal Access Token（推荐）**

1. GitHub 设置 → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → 勾选 `repo` 权限
3. 复制生成的 token
4. 推送时使用 token 作为密码

**方式2：GitHub CLI**

```bash
# 安装 GitHub CLI
winget install --id GitHub.cli

# 登录
gh auth login
```

---

## 第五步：连接 Vercel

1. **登录 Vercel**：https://vercel.com

2. **使用 GitHub 登录**：
   - 点击 `Continue with GitHub`
   - 授权 Vercel 访问 GitHub

3. **导入项目**：
   - 点击 `Add New...` → `Project`
   - 找到 `power-market-system` 仓库
   - 点击 `Import`

---

## 第六步：配置和部署

### 配置项（通常使用默认值即可）

- **Framework Preset**：Next.js（自动检测）
- **Root Directory**：`.`
- **Build Command**：`npm run build`
- **Output Directory**：`.next`
- **Install Command**：`npm install`
- **Node.js Version**：18.x（自动选择）

### 点击 Deploy 🚀

等待 1-3 分钟，部署完成！

---

## 第七步：访问网站

部署成功后，Vercel 会提供：

- **生产环境 URL**：`https://power-market-system.vercel.app`
- **自定义域名**：可在设置中添加

点击 `Visit` 查看您的网站！

---

## 🔄 后续更新流程

每次修改代码后：

```bash
# 1. 查看修改状态
git status

# 2. 添加修改的文件
git add .

# 3. 提交修改
git commit -m "描述你的修改内容"

# 4. 推送到 GitHub
git push
```

**Vercel 会自动检测推送并重新部署！** ✨

---

## 🛠️ 常用 Git 命令

```bash
# 查看状态
git status

# 查看提交历史
git log --oneline

# 撤销未提交的修改
git checkout -- 文件名

# 查看远程仓库
git remote -v

# 拉取最新代码
git pull
```

---

## ❓ 常见问题

### 1. Git 推送失败：Authentication failed

**解决方案**：使用 Personal Access Token 代替密码

### 2. Vercel 构建失败

**检查**：
- `package.json` 中的依赖是否完整
- Node.js 版本是否兼容（需要 >=18.0.0）
- 构建命令是否正确

**查看日志**：Vercel 部署页面 → Deployment → Build Logs

### 3. 部署成功但页面显示错误

**检查**：
- API 路由是否正确
- 环境变量是否配置
- 浏览器控制台是否有错误信息

---

## 📊 项目文件结构

```
power-market-system/
├── pages/
│   ├── index.js          # 主页面
│   ├── _app.js           # App 配置
│   └── api/              # API 路由
│       ├── database/
│       ├── available-dates.js
│       ├── historical-prices.js
│       ├── predict.js
│       └── optimize.js
├── styles/
│   └── globals.css       # 全局样式
├── package.json          # 依赖配置
├── next.config.js        # Next.js 配置
├── vercel.json           # Vercel 配置
└── .gitignore            # Git 忽略文件
```

---

## 🎉 完成！

现在您的电力市场预测系统已经部署到 Vercel，可以通过互联网访问了！

**优势**：
- ✅ 全球 CDN 加速
- ✅ 自动 HTTPS
- ✅ 自动部署（推送代码即部署）
- ✅ 免费额度充足
- ✅ 性能监控和分析

---

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看 Vercel 部署日志
2. 检查 GitHub Actions（如果配置了）
3. 查看浏览器控制台错误信息

