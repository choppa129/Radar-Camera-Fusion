@echo off
chcp 65001 >nul
REM Fusion 启动脚本：激活 conda 环境并运行主程序
call "F:\anaconda3\Scripts\activate.bat" "F:\anaconda3\envs\fusion"
cd /d "%~dp0"
echo 启动 Fusion 主程序...
python "%~dp0src\detect.py"
if errorlevel 1 (
    echo.
    echo 程序异常退出。可先运行自检:  python "%~dp0tools\check_env.py"
    pause
)
