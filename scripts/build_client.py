# -*- coding: utf-8 -*-
"""
客户端打包脚本
使用 PyInstaller 将客户端打包为单文件 EXE (无控制台窗口)。
"""

import PyInstaller.__main__
import os
import sys

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_project_root)

PyInstaller.__main__.run([
    '--name=ChatClient',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--clean',
    os.path.join('src', 'ui', 'login_window.py'),
])