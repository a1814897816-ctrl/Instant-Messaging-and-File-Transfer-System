# -*- coding: utf-8 -*-
"""
GUI 公共工具模块
提供配色方案、头像工具函数、通用 UI 组件等跨窗口共享的资源。
"""

import time
import os

# ══════════════════════════════════════════════
#  现代配色方案
# ══════════════════════════════════════════════

COLORS = {
    # 主色调
    'primary': '#2AABEE',
    'primary_dark': '#0088CC',
    'primary_light': '#E8F6FD',

    # 背景
    'bg': '#F0F2F5',
    'card': '#FFFFFF',
    'sidebar_bg': '#FFFFFF',
    'header_bg': '#FFFFFF',
    'input_bg': '#FFFFFF',
    'input_focus': '#FFFFFF',
    'system_bg': '#F0F2F5',

    # 文字
    'text': '#1A1A1A',
    'text_secondary': '#8E8E93',
    'text_light': '#B0B0B0',

    # 功能色
    'success': '#34C759',
    'danger': '#FF3B30',
    'warning': '#FF9500',

    # 边框
    'border': '#E5E5EA',

    # 在线状态
    'online': '#34C759',
    'offline': '#C7C7CC',

    # 列表交互
    'hover': '#F5F7FA',
    'selected': '#E8F6FD',

    # 聊天气泡
    'my_bubble': '#2AABEE',
    'my_bubble_text': '#FFFFFF',
    'other_bubble': '#FFFFFF',
    'other_bubble_text': '#1A1A1A',

    # 群聊专用
    'group_header': '#52C41A',

    # 导航栏
    'navbar_bg': '#2AABEE',
}

# ══════════════════════════════════════════════
#  用户头像颜色池
# ══════════════════════════════════════════════

AVATAR_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
    '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA',
    '#F1948A', '#85C1E9', '#AED6F1', '#D2B4DE',
]


# ══════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════

def get_avatar_color(username):
    """根据用户名生成一致的颜角色"""
    if not username:
        return AVATAR_COLORS[0]
    idx = sum(ord(c) for c in username) % len(AVATAR_COLORS)
    return AVATAR_COLORS[idx]


def get_initial(username):
    """获取用户名首字符（大写）"""
    if not username:
        return "?"
    return username[0].upper()


def add_hover_effect(widget, normal_color, hover_color):
    """为 tkinter 控件添加鼠标悬停变色效果"""
    def on_enter(e):
        widget.config(bg=hover_color)

    def on_leave(e):
        widget.config(bg=normal_color)

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def center_window(window):
    """将窗口居中显示"""
    window.update_idletasks()
    try:
        w = window.winfo_width()
        h = window.winfo_height()
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        window.geometry(f"+{x}+{y}")
    except Exception:
        pass


def format_time(timestamp):
    """格式化时间戳为 HH:MM 显示"""
    if timestamp is None:
        return time.strftime("%H:%M")
    try:
        parts = timestamp.split()
        if len(parts) >= 2:
            t = parts[1]
            if len(t) >= 5:
                return t[:5]
            return t
        elif len(timestamp) >= 5:
            return timestamp[:5]
    except Exception:
        pass
    return timestamp if timestamp else time.strftime("%H:%M")


def create_header_btn(parent, icon, command, colors=None):
    """创建 Header 图标按钮"""
    if colors is None:
        colors = COLORS

    btn = __import__('tkinter').Label(
        parent, text=icon,
        font=("Segoe UI Emoji", 12),
        bg=colors['header_bg'], fg=colors['text_secondary'],
        cursor="hand2", padx=6, pady=2
    )
    btn.pack(side="left")

    def on_enter(e):
        btn.config(fg=colors['primary'])

    def on_leave(e):
        btn.config(fg=colors['text_secondary'])

    def on_click(e):
        command()

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.bind("<Button-1>", on_click)
    return btn


def setup_canvas_scroll(canvas, msg_frame):
    """为 Canvas 消息区域设置滚动配置"""
    canvas_window = canvas.create_window(
        (0, 0), window=msg_frame, anchor="nw", tags="msg_frame"
    )

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    msg_frame.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)

    return canvas_window


def bind_mousewheel(target_widget, canvas):
    """将鼠标滚轮绑定到指定窗口（避免 bind_all 全局污染）"""
    def on_mousewheel(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    target_widget.bind("<MouseWheel>", on_mousewheel)


def add_system_msg(msg_frame, content, colors=None):
    """在消息区域添加系统消息"""
    if colors is None:
        colors = COLORS

    import tkinter as tk
    row = tk.Frame(msg_frame, bg=colors['bg'])
    row.pack(fill="x", padx=10, pady=4)

    tk.Label(
        row, text=content,
        font=("微软雅黑", 8),
        fg=colors['text_secondary'], bg=colors['bg']
    ).pack()


def add_progress_msg(msg_frame, content, colors=None):
    """在消息区域添加进度消息"""
    if colors is None:
        colors = COLORS

    import tkinter as tk
    row = tk.Frame(msg_frame, bg=colors['bg'])
    row.pack(fill="x", padx=10, pady=2)

    tk.Label(
        row, text=f"  {content}",
        font=("微软雅黑", 8, "italic"),
        fg=colors['primary'], bg=colors['bg']
    ).pack()


def scroll_to_bottom(canvas):
    """将 Canvas 滚动到底部"""
    canvas.update_idletasks()
    canvas.yview_moveto(1.0)


def format_file_size(size):
    """格式化文件大小为可读字符串"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def get_project_root():
    """获取项目根目录路径"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))