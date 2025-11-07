@echo off
chcp 65001 >nul
echo ========================================
echo   电力市场预测系统 - 快速部署到 GitHub
echo ========================================
echo.

REM 检查 Git 是否安装
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到 Git
    echo.
    echo 请先安装 Git：
    echo 1. 访问 https://git-scm.com/download/win
    echo 2. 下载并安装 Git
    echo 3. 重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo ✅ Git 已安装
echo.

REM 检查是否已初始化 Git 仓库
if not exist .git (
    echo 📦 初始化 Git 仓库...
    git init
    echo ✅ Git 仓库初始化完成
    echo.
    
    echo ⚙️  配置 Git 用户信息...
    set /p username="请输入你的 Git 用户名: "
    set /p email="请输入你的 Git 邮箱: "
    git config --global user.name "%username%"
    git config --global user.email "%email%"
    echo ✅ Git 用户信息配置完成
    echo.
)

REM 检查是否已添加远程仓库
git remote -v | findstr "origin" >nul 2>&1
if %errorlevel% neq 0 (
    echo 🌐 添加 GitHub 远程仓库...
    echo.
    echo 请先在 GitHub 上创建仓库：
    echo 1. 访问 https://github.com/new
    echo 2. Repository name: power-market-system
    echo 3. 不要勾选 "Initialize this repository with a README"
    echo 4. 点击 Create repository
    echo.
    set /p repo_url="请输入你的 GitHub 仓库地址 (例如: https://github.com/username/power-market-system.git): "
    git remote add origin %repo_url%
    echo ✅ 远程仓库添加完成
    echo.
)

echo 📝 添加文件到暂存区...
git add .
echo ✅ 文件添加完成
echo.

echo 💬 提交代码...
set /p commit_msg="请输入提交信息 (直接回车使用默认信息): "
if "%commit_msg%"=="" set commit_msg=feat: 更新电力市场预测系统
git commit -m "%commit_msg%"
echo ✅ 代码提交完成
echo.

echo 🚀 推送到 GitHub...
git branch -M main
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✅ 代码已成功推送到 GitHub！
    echo ========================================
    echo.
    echo 📋 下一步：部署到 Vercel
    echo.
    echo 1. 访问 https://vercel.com
    echo 2. 使用 GitHub 账号登录
    echo 3. 点击 "Add New..." → "Project"
    echo 4. 导入 power-market-system 仓库
    echo 5. 点击 "Deploy"
    echo.
    echo 🎉 部署完成后，你将获得一个在线访问地址！
    echo.
) else (
    echo.
    echo ========================================
    echo   ❌ 推送失败
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 需要 GitHub 身份验证
    echo 2. 远程仓库地址错误
    echo 3. 网络连接问题
    echo.
    echo 💡 解决方案：
    echo 1. 使用 Personal Access Token 作为密码
    echo    - GitHub 设置 → Developer settings → Personal access tokens
    echo    - Generate new token → 勾选 repo 权限
    echo 2. 或安装 GitHub CLI: winget install --id GitHub.cli
    echo.
)

pause

