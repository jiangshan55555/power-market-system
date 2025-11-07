# 📦 使用 GitHub Desktop 部署到 Vercel 完整指南

## 🎯 部署流程概览

```
本地代码 → GitHub Desktop → GitHub → Vercel → 线上网站
```

**优势**：图形化界面，操作简单，无需记忆命令！

---

## 第一步：安装 GitHub Desktop

### 1. 下载 GitHub Desktop

- **官方网站**：https://desktop.github.com
- **直接下载**：https://central.github.com/deployments/desktop/desktop/latest/win32
- 下载后运行安装程序

### 2. 登录 GitHub 账号

1. 打开 GitHub Desktop
2. 点击 `File` → `Options` → `Accounts`
3. 点击 `Sign in` 登录 GitHub 账号
4. 在浏览器中完成授权

**如果没有 GitHub 账号**：
- 访问 https://github.com/signup
- 注册一个免费账号

---

## 第二步：将项目添加到 GitHub Desktop

### 方式一：添加现有本地仓库（推荐）

1. **打开 GitHub Desktop**

2. **添加仓库**：
   - 点击 `File` → `Add local repository`
   - 或点击左上角 `Current Repository` → `Add` → `Add Existing Repository`

3. **选择项目文件夹**：
   - 点击 `Choose...` 按钮
   - 浏览到：`C:\Users\86182\Documents\augment-projects\assistance\power-market-system`
   - 点击 `选择文件夹`

4. **初始化仓库**（如果提示）：
   - 如果显示 "This directory does not appear to be a Git repository"
   - 点击 `create a repository` 链接
   - 或点击 `Initialize Git Repository`

### 方式二：创建新仓库

1. 点击 `File` → `New repository`
2. **Name**：`power-market-system`
3. **Local path**：选择项目所在的**父目录**
   - 例如：`C:\Users\86182\Documents\augment-projects\assistance`
4. **Git ignore**：选择 `Node`
5. 点击 `Create repository`

---

## 第三步：配置 .gitignore（确保已存在）

GitHub Desktop 会自动识别项目中的 `.gitignore` 文件。

**确认 `.gitignore` 内容**（已存在，无需修改）：
```
/node_modules
/.next/
/out/
.env*.local
.vercel
```

---

## 第四步：提交代码

### 1. 查看更改

在 GitHub Desktop 左侧 `Changes` 标签页，您会看到所有文件：
- ✅ 勾选的文件会被提交
- 默认全部勾选

### 2. 填写提交信息

在左下角：
- **Summary（必填）**：`feat: 完成电力市场预测系统美化升级`
- **Description（可选）**：
  ```
  - 升级配色方案为能源行业专业配色
  - 优化视觉层次和交互体验
  - 添加响应式设计和可访问性支持
  - 完善数据展示和加载动画
  ```

### 3. 提交

点击左下角蓝色按钮 `Commit to main`

---

## 第五步：发布到 GitHub

### 1. 发布仓库

提交后，顶部会显示 `Publish repository` 按钮：

1. **点击 `Publish repository`**

2. **配置仓库信息**：
   - **Name**：`power-market-system`（保持默认）
   - **Description**：`电力市场预测与投标优化系统`
   - **Keep this code private**：
     - ✅ 勾选 = 私有仓库（只有你能看到）
     - ❌ 不勾选 = 公开仓库（所有人可见）
   - **Organization**：选择 `None`（个人仓库）

3. **点击 `Publish repository`**

### 2. 等待上传

GitHub Desktop 会自动上传所有文件到 GitHub。

上传完成后，顶部会显示：
- `View on GitHub` - 点击可在浏览器中查看仓库

---

## 第六步：连接 Vercel 并部署

### 1. 登录 Vercel

1. **访问**：https://vercel.com
2. **点击 `Sign Up` 或 `Log In`**
3. **选择 `Continue with GitHub`**（用 GitHub 账号登录）
4. **授权 Vercel** 访问您的 GitHub 账号

### 2. 导入项目

1. **点击 `Add New...`** → **`Project`**

2. **在 "Import Git Repository" 页面**：
   - 找到 `power-market-system` 仓库
   - 如果看不到，点击 `Adjust GitHub App Permissions` 授权更多仓库
   - 点击仓库右侧的 `Import` 按钮

### 3. 配置项目

**Configure Project** 页面（通常使用默认值）：

- **Project Name**：`power-market-system`
- **Framework Preset**：`Next.js`（自动检测）
- **Root Directory**：`./`（保持默认）
- **Build and Output Settings**：
  - Build Command：`npm run build`
  - Output Directory：`.next`
  - Install Command：`npm install`

**Environment Variables**（暂时不需要）：
- 如果以后需要数据库等配置，可以在这里添加

### 4. 开始部署

**点击 `Deploy` 按钮** 🚀

---

## 第七步：等待部署完成

Vercel 会自动执行：

1. ✅ **Building**：安装依赖并构建项目（1-2分钟）
2. ✅ **Deploying**：部署到全球 CDN
3. ✅ **Ready**：部署完成！

部署成功后会显示：
- 🎉 **Congratulations!**
- 🌐 **域名**：`https://power-market-system.vercel.app`（或类似）

---

## 第八步：访问您的网站

1. **点击预览图** 或 **`Visit`** 按钮
2. **测试所有功能**：
   - 数据库状态查询
   - 历史数据查看
   - 预测分析
   - 投标优化

---

## 🔄 后续更新流程（超级简单！）

每次修改代码后，在 GitHub Desktop 中：

### 1. 查看更改
- 打开 GitHub Desktop
- 左侧 `Changes` 会显示所有修改的文件

### 2. 提交更改
- 填写 **Summary**：描述你的修改
- 点击 `Commit to main`

### 3. 推送到 GitHub
- 点击顶部的 `Push origin` 按钮
- 或按快捷键 `Ctrl + P`

### 4. 自动部署
- **Vercel 会自动检测到推送**
- **自动重新构建和部署**
- **1-2分钟后更新生效**

**就这么简单！** ✨

---

## 📊 GitHub Desktop 界面说明

```
┌─────────────────────────────────────────────────────────┐
│  File  Edit  View  Repository  Branch  Help             │
├─────────────────────────────────────────────────────────┤
│  Current Repository: power-market-system    Push origin │
├──────────────┬──────────────────────────────────────────┤
│              │                                           │
│  Changes (5) │  文件差异对比                              │
│              │                                           │
│  ☑ file1.js  │  + 新增的代码（绿色）                      │
│  ☑ file2.css │  - 删除的代码（红色）                      │
│  ☑ file3.md  │                                           │
│              │                                           │
│  History     │                                           │
│              │                                           │
├──────────────┴──────────────────────────────────────────┤
│  Summary (required)                                      │
│  ┌────────────────────────────────────────────────┐    │
│  │ 输入提交信息                                     │    │
│  └────────────────────────────────────────────────┘    │
│  Description                                             │
│  ┌────────────────────────────────────────────────┐    │
│  │ 详细描述（可选）                                 │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│              [ Commit to main ]                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 关键操作快捷键

| 操作 | 快捷键 |
|------|--------|
| 提交 | `Ctrl + Enter` |
| 推送 | `Ctrl + P` |
| 拉取 | `Ctrl + Shift + P` |
| 切换仓库 | `Ctrl + T` |
| 查看历史 | `Ctrl + 2` |
| 查看更改 | `Ctrl + 1` |

---

## ❓ 常见问题

### 1. GitHub Desktop 中看不到我的仓库

**解决方案**：
- 点击 `File` → `Add local repository`
- 手动选择项目文件夹

### 2. 提交时提示 "Please tell me who you are"

**解决方案**：
- GitHub Desktop 会自动使用你的 GitHub 账号信息
- 如果仍有问题，在 `File` → `Options` → `Git` 中配置

### 3. 推送失败：Authentication failed

**解决方案**：
- 在 GitHub Desktop 中重新登录
- `File` → `Options` → `Accounts` → `Sign out` → `Sign in`

### 4. Vercel 构建失败

**检查**：
1. 在 Vercel 部署页面查看 `Build Logs`
2. 确认 `package.json` 中的依赖完整
3. 确认 Node.js 版本兼容（需要 >=18.0.0）

### 5. 部署成功但页面显示错误

**检查**：
1. 浏览器控制台（F12）查看错误信息
2. Vercel 部署页面查看 `Function Logs`
3. 确认 API 路由是否正常

---

## 🎉 完成！

现在您已经掌握了使用 GitHub Desktop 部署的完整流程！

**优势总结**：
- ✅ 图形化界面，操作直观
- ✅ 无需记忆 Git 命令
- ✅ 自动同步，一键推送
- ✅ 可视化查看代码差异
- ✅ 完美集成 GitHub 和 Vercel

---

## 📞 需要帮助？

如果遇到问题，请告诉我：
1. 具体的错误信息
2. 操作到哪一步
3. 截图（如果可能）

我会立即帮您解决！🚀

