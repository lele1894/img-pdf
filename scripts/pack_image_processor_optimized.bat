@echo off
echo 在优化虚拟环境中打包处理打印图片背景.py...
call venv_image_processor\Scripts\activate.bat

echo 清理旧的打包文件...
if exist build\pack_image_processor rmdir /s /q build\pack_image_processor
if exist dist\处理打印图片背景.exe del /q dist\处理打印图片背景.exe

echo 开始打包...
pyinstaller pack_image_processor.spec --clean

echo 打包完成!
echo 输出文件: dist\处理打印图片背景.exe
dir dist\处理打印图片背景.exe

pause
