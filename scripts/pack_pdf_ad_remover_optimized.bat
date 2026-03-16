@echo off
echo 在优化虚拟环境中打包PDF广告移除工具.py...
call venv_pdf_ad_remover\Scripts\activate.bat

echo 清理旧的打包文件...
if exist build\pack_pdf_ad_remover rmdir /s /q build\pack_pdf_ad_remover
if exist dist\PDF广告移除工具.exe del /q dist\PDF广告移除工具.exe

echo 开始打包...
pyinstaller pack_pdf_ad_remover.spec --clean

echo 打包完成!
echo 输出文件: dist\PDF广告移除工具.exe
dir dist\PDF广告移除工具.exe

pause
