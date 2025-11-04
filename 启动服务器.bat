@echo off
chcp 65001 >nul
echo ========================================
echo   ⚡ 电力市场预测系统 - 启动脚本
echo ========================================
echo.
echo 正在启动开发服务器...
echo.
echo 项目位置: %~dp0
echo.

cd /d "%~dp0"

echo [1/2] 检查依赖...
if not exist "node_modules\" (
    echo 首次运行，正在安装依赖...
    call npm install
    echo.
)

echo [2/2] 启动服务器...
echo.
echo ✅ 服务器启动成功！
echo.
echo 📱 请在浏览器中访问: http://localhost:3000
echo.
echo 💡 提示:
echo    - 按 Ctrl+C 可以停止服务器
echo    - 修改代码后会自动刷新
echo.
echo ========================================
echo.

call npm run dev

pause

