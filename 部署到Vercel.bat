@echo off
chcp 65001 >nul
echo ========================================
echo   🚀 电力市场预测系统 - Vercel 部署
echo ========================================
echo.

cd /d "%~dp0"

echo 项目位置: %~dp0
echo.
echo 正在部署到 Vercel...
echo.
echo 💡 提示:
echo    - 首次部署需要登录 Vercel 账户
echo    - 部署完成后会获得一个在线 URL
echo    - 可以分享给任何人访问
echo.
echo ========================================
echo.

call vercel --prod

echo.
echo ========================================
echo.
echo ✅ 部署完成！
echo.
echo 📱 请复制上面的 URL 在浏览器中访问
echo.
echo 💡 下次更新只需再次运行此脚本
echo.
echo ========================================
echo.

pause

