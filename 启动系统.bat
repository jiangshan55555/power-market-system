@echo off
chcp 65001 >nul
echo ========================================
echo    电力市场预测系统 - 启动脚本
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖包...
cd api
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [3/3] 启动服务...
echo.
echo ========================================
echo    🚀 系统启动成功！
echo ========================================
echo    📍 API 地址: http://localhost:5000
echo    🌐 前端页面: 请在浏览器中打开 index.html
echo ========================================
echo.

python app.py

