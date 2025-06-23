import os
import sys
import shutil
from subprocess import run
import site

def create_exe():
    # 确保dist目录为空
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # VLC路径
    vlc_dir = "D:\\VLC"
    
    if not os.path.exists(vlc_dir):
        print(f"错误: 未找到VLC目录: {vlc_dir}")
        sys.exit(1)
        
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onedir',
        '--windowed',
        '--icon=icons/logo.ico',
        f'--add-binary={vlc_dir}\\*.dll;.',  # 添加所有VLC动态库到根目录
        f'--add-binary={vlc_dir}\\plugins;plugins',  # 添加VLC插件目录
        '--add-data=icons;icons',  # 添加图标资源
        '--name=PlanetBoy Wallpaper',
        'main.py'
    ]
    
    print(f"正在使用VLC目录: {vlc_dir}")
    # 运行打包命令
    run(cmd)

if __name__ == '__main__':
    create_exe() 