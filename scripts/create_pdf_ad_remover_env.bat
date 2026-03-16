@echo off
echo 创建PDF广告移除工具.py的虚拟环境...
python -m venv venv_pdf_ad_remover
call venv_pdf_ad_remover\Scripts\activate.bat

echo 安装必要的依赖包...
pip install --upgrade pip
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3
pip install Pillow==10.0.0
pip install pymupdf==1.23.8
pip install pyinstaller==6.18.0

echo 虚拟环境创建完成!
echo 激活命令: venv_pdf_ad_remover\Scripts\activate.bat
pause
