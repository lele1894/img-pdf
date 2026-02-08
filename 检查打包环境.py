# -*- coding: utf-8 -*-
"""
检查打包环境
"""

import os
import sys

def check_environment():
    print("=" * 50)
    print("PDF广告移除工具 - 打包环境检查")
    print("=" * 50)
    print()
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    all_ok = True
    
    # 检查Python版本
    print("[1/6] 检查Python版本...")
    print(f"  Python版本: {sys.version}")
    if sys.version_info >= (3, 7):
        print("  ✓ Python版本符合要求 (3.7+)")
    else:
        print("  ✗ Python版本过低,需要3.7或更高")
        all_ok = False
    print()
    
    # 检查依赖包
    print("[2/6] 检查依赖包...")
    required_packages = {
        'cv2': 'opencv-python',
        'PIL': 'pillow',
        'fitz': 'pymupdf',
        'numpy': 'numpy',
        'tkinter': 'tkinter'
    }
    
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} 未安装")
            all_ok = False
    print()
    
    # 检查PyInstaller
    print("[3/6] 检查PyInstaller...")
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller 已安装")
    except ImportError:
        print("  ✗ PyInstaller 未安装")
        print("    请运行: pip install pyinstaller")
        all_ok = False
    print()
    
    # 检查主程序文件
    print("[4/6] 检查主程序文件...")
    main_script = 'interactive_ad_remover.py'
    if os.path.exists(main_script):
        print(f"  ✓ {main_script}")
    else:
        print(f"  ✗ {main_script} 不存在")
        all_ok = False
    print()
    
    # 检查图标文件
    print("[5/6] 检查图标文件...")
    icon_file = 'ico.ico'
    if os.path.exists(icon_file):
        file_size = os.path.getsize(icon_file)
        print(f"  ✓ {icon_file} ({file_size} bytes)")
    else:
        print(f"  ✗ {icon_file} 不存在")
        print("    请将ico.ico文件放在当前目录下")
        all_ok = False
    print()
    
    # 检查版本信息文件
    print("[6/6] 检查版本信息文件...")
    version_file = 'version_info.txt'
    if os.path.exists(version_file):
        print(f"  ✓ {version_file}")
    else:
        print(f"  ✗ {version_file} 不存在")
        all_ok = False
    print()
    
    # 总结
    print("=" * 50)
    if all_ok:
        print("✓ 所有检查通过! 可以开始打包")
        print()
        print("运行以下命令开始打包:")
        print("  python 打包.py")
    else:
        print("✗ 部分检查未通过,请先解决上述问题")
    print("=" * 50)
    print()
    
    return all_ok

if __name__ == '__main__':
    ok = check_environment()
    input("按回车键退出...")
    sys.exit(0 if ok else 1)
