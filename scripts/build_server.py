# -*- coding: utf-8 -*-
"""
服务端打包脚本
使用 PyInstaller 将服务端打包为单文件 EXE。
"""

import PyInstaller.__main__
import os
import sys

# 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_project_root)

PyInstaller.__main__.run([
    '--name=ChatServer',
    '--onefile',
    '--console',
    '--noconfirm',
    '--clean',
    '--add-data=chat.db;.',
    os.path.join('src', 'core', 'server.py'),
])