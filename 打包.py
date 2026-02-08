# -*- coding: utf-8 -*-
"""
PDF广告移除工具 - 打包脚本
"""

import os
import sys
import shutil
import subprocess

def main():
    print("=" * 40)
    print("PDF广告移除工具 - 打包脚本")
    print("=" * 40)
    print()
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    # [1/4] 清理旧的打包文件
    print("[1/4] 清理旧的打包文件...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  ✓ 已删除 {dir_name}")
            except Exception as e:
                print(f"  ✗ 删除 {dir_name} 失败: {e}")
    print("  ✓ 清理完成")
    print()
    
    # [2/4] 检查ico.ico文件
    print("[2/4] 检查ico.ico文件...")
    icon_path = os.path.join(current_dir, 'ico.ico')
    if not os.path.exists(icon_path):
        print("  ✗ 错误: 找不到ico.ico文件!")
        print("    请确保ico.ico文件在当前目录下")
        input("按回车键退出...")
        sys.exit(1)
    print("  ✓ 找到ico.ico文件")
    print()
    
    # [3/4] 检查主程序文件
    print("[3/4] 检查主程序文件...")
    main_script = 'interactive_ad_remover.py'
    if not os.path.exists(main_script):
        print(f"  ✗ 错误: 找不到 {main_script} 文件!")
        input("按回车键退出...")
        sys.exit(1)
    print(f"  ✓ 找到 {main_script} 文件")
    print()
    
    # [4/4] 开始打包
    print("[4/4] 开始打包...")
    print("  这可能需要几分钟时间,请耐心等待...")
    print()
    
    try:
        # 构建PyInstaller命令
        cmd = [
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--icon=ico.ico',
            '--name=PDF广告移除工具',
            '--version-file=version_info.txt',
            main_script
        ]
        
        print("  执行命令:")
        print("  " + " ".join(cmd))
        print()
        
        # 执行打包
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print()
            print("  ✗ 打包失败!")
            print()
            print("  错误信息:")
            print(result.stderr)
            input("按回车键退出...")
            sys.exit(1)
        
        print()
        print("  ✓ 打包完成!")
        print()
        
        # 检查生成的文件
        exe_path = os.path.join(current_dir, 'dist', 'PDF广告移除工具.exe')
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path)
            file_size_mb = file_size / (1024 * 1024)
            
            print("  ✓ exe文件已生成: dist\\PDF广告移除工具.exe")
            print(f"  文件大小: {file_size_mb:.2f} MB")
            print()
            print("=" * 40)
            print("打包成功! 可以在dist文件夹中找到exe文件")
            print("=" * 40)
        else:
            print("  ✗ 错误: 未找到生成的exe文件")
            input("按回车键退出...")
            sys.exit(1)
        
    except FileNotFoundError:
        print()
        print("  ✗ 错误: 未找到pyinstaller命令!")
        print("    请先安装pyinstaller: pip install pyinstaller")
        input("按回车键退出...")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"  ✗ 打包过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
        sys.exit(1)
    
    print()
    input("按回车键退出...")

if __name__ == '__main__':
    main()
