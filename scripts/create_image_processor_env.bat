@echo off
echo 创建处理打印图片背景.py的虚拟环境...
python -m venv venv_image_processor
call venv_image_processor\Scripts\activate.bat

echo 安装必要的依赖包...
pip install --upgrade pip
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3
pip install Pillow==10.0.0
pip install tkinterdnd2==0.4.3
pip install pyinstaller==6.18.0

echo 虚拟环境创建完成!
echo 激活命令: venv_image_processor\Scripts\activate.bat
pause
