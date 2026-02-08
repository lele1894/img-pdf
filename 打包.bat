@echo off
chcp 65001 > nul
echo ========================================
echo PDF广告移除工具 - 打包脚本
echo ========================================
echo.

echo [1/4] 清理旧的打包文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo ✓ 清理完成
echo.

echo [2/4] 检查ico.ico文件...
if not exist "ico.ico" (
    echo ✗ 错误: 找不到ico.ico文件!
    echo   请确保ico.ico文件在当前目录下
    pause
    exit /b 1
)
echo ✓ 找到ico.ico文件
echo.

echo [3/4] 开始打包...
echo   这可能需要几分钟时间,请耐心等待...
echo.

pyinstaller --onefile --windowed --icon=ico.ico --name="PDF广告移除工具" --version-file=version_info.txt interactive_ad_remover.py

if %errorlevel% neq 0 (
    echo.
    echo ✗ 打包失败!
    echo   请检查错误信息
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成!
echo.

if exist "dist\PDF广告移除工具.exe" (
    echo ✓ exe文件已生成: dist\PDF广告移除工具.exe
    
    REM 显示文件大小
    for %%F in ("dist\PDF广告移除工具.exe") do (
        set size=%%~zF
        set /a sizeMB=!size! / 1048576
        echo   文件大小: !sizeMB! MB
    )
    
    echo.
    echo ========================================
    echo 打包成功! 可以在dist文件夹中找到exe文件
    echo ========================================
) else (
    echo ✗ 错误: 未找到生成的exe文件
)

echo.
pause
