@echo off
echo ========================================
echo PDF和图像处理工具集 - 一键打包脚本
echo ========================================
echo.

echo [1/4] 创建处理打印图片背景的虚拟环境...
python -m venv venv_image_processor
call venv_image_processor\Scripts\activate.bat
pip install --upgrade pip
pip install opencv-python==4.8.1.78 numpy==1.24.3 Pillow==10.0.0 tkinterdnd2==0.4.3 pyinstaller==6.18.0
echo.

echo [2/4] 创建PDF广告移除工具的虚拟环境...
python -m venv venv_pdf_ad_remover
call venv_pdf_ad_remover\Scripts\activate.bat
pip install --upgrade pip
pip install opencv-python==4.8.1.78 numpy==1.24.3 Pillow==10.0.0 pymupdf==1.23.8 pyinstaller==6.18.0
echo.

echo [3/4] 打包处理打印图片背景...
call venv_image_processor\Scripts\activate.bat
pyinstaller pack_image_processor.spec --clean
echo.

echo [4/4] 打包PDF广告移除工具...
call venv_pdf_ad_remover\Scripts\activate.bat
pyinstaller pack_pdf_ad_remover.spec --clean
echo.

echo ========================================
echo 打包完成!
echo ========================================
echo 输出文件位置: dist/
dir dist\
echo.
echo 按任意键退出...
pause > nul
