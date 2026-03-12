# pip install pyinstaller
"""
打包脚本 - 将手势答题系统打包成EXE
使用方法：python build_exe.py
"""

import PyInstaller.__main__
import os
import shutil
import site

# 清理之前的构建文件
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

# 获取mediapipe的路径（用于数据文件）
import mediapipe as mp
mediapipe_path = os.path.dirname(mp.__file__)

# PyInstaller参数
PyInstaller.__main__.run([
    '版本五(优化加载卡顿).py',  # 你的主程序文件名（请将原代码保存为main.py）
    '--name=手势答题系统',
    '--onefile',  # 打包成单个exe文件
    '--windowed',  # 不显示控制台窗口（如果不需要调试信息）
    '--icon=icon.ico',  # 如果有图标文件可以添加
    '--add-data', f'{mediapipe_path}{os.pathsep}mediapipe',  # 添加mediapipe数据文件
    '--hidden-import=mediapipe',
    '--hidden-import=pygame',
    '--hidden-import=cv2',
    '--hidden-import=queue',
    '--hidden-import=threading',
    '--hidden-import=datetime',
    '--hidden-import=csv',
    '--hidden-import=math',
    '--hidden-import=random',
    '--hidden-import=time',
    '--collect-all=mediapipe',  # 收集mediapipe所有文件
    '--collect-all=cv2',
    '--collect-all=pygame',
])