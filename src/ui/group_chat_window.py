# -*- coding: utf-8 -*-
"""
客户端 GUI —— 群聊 / 公共聊天室窗口 (美化版)
群消息收发、气泡式消息展示
成员 C（董鑫）负责
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import time

from src.core.protocol import GROUP_ID
from src.common.ui_utils import (
    COLORS, AVATAR_COLORS,
    get_avatar_color, get_initial, add_hover_effect,
    center_window, format_time, create_header_btn,
    setup_canvas_scroll, bind_mousewheel,
    add_system_msg, add_progress_msg,
    scroll_to_bottom,
)


class GroupChatWindow:
    """公共聊天室窗口 (气泡式现代化设计)"""

    def __init__(self, parent, client, main_window):
        self.client = client
        self.main_window = main_window
        self._history_loaded = False

        self.root = tk.Toplevel(parent)
        self.root.title("公共聊天室")
        self.root.geometry("600x600")
        self.root.minsize(450, 400)
        self.root.configure(bg=COLORS['bg'])

        self._setup_ui()
        center_window(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._load_history()

    def _setup_ui(self):
        # ── 顶部 Header ──
        header = tk.Frame(self.root, bg=COLORS['header_bg'], height=52)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Frame(header, bg=COLORS['border'], height=1).pack(side="bottom", fill="x")

        icon_label = tk.Label(
            header, text="\U0001f4e2",
            font=("Segoe UI Emoji", 16),
            bg=COLORS['header_bg']
        )
        icon_label.pack(side="left", padx=(12, 6), pady=8)

        tk.Label(
            header, text="公共聊天室",
            font=("微软雅黑", 12, "bold"),
            fg=COLORS['text'], bg=COLORS['header_bg'],
            anchor="w"
        ).pack(side="left", fill="y", pady=10)

        btn_frame = tk.Frame(header, bg=COLORS['header_bg'])
        btn_frame.pack(side="right", padx=4, pady=8)

        create_header_btn(btn_frame, "\U0001f4cb", self._load_history)

        # ── 消息区域 (Canvas) ──
        msg_container = tk.Frame(self.root, bg=COLORS['bg'])
        msg_container.pack(fill="both", expand=True, padx=0, pady=0)

        self.msg_canvas = tk.Canvas(
            msg_container, bg=COLORS['bg'],
            highlightthickness=0, bd=0
        )
        self.msg_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(msg_container, command=self.msg_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.msg_canvas.configure(yscrollcommand=scrollbar.set)

        self.msg_frame = tk.Frame(self.msg_canvas, bg=COLORS['bg'])
        self.canvas_window = setup_canvas_scroll(self.msg_canvas, self.msg_frame)
        bind_mousewheel(self.root, self.msg_canvas)

        # ── 输入区域 ──
        input_container = tk.Frame(self.root, bg=COLORS['card'])
        input_container.pack(fill="x")

        tk.Frame(input_container, bg=COLORS['border'], height=1).pack(fill="x")

        input_inner = tk.Frame(input_container, bg=COLORS['card'])
        input_inner.pack(fill="x", padx=10, pady=(8, 4))

        self.input_text = tk.Text(
            input_inner,
            font=("微软雅黑", 10),
            height=3,
            wrap=tk.WORD,
            bg=COLORS['input_bg'],
            fg=COLORS['text'],
            insertbackground=COLORS['primary'],
            relief="flat",
            bd=6,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['primary']
        )
        self.input_text.pack(fill="x")

        send_frame = tk.Frame(input_container, bg=COLORS['card'])
        send_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.send_btn = tk.Button(
            send_frame, text="发送",
            font=("微软雅黑", 10, "bold"),
            bg=COLORS['group_header'], fg="white",
            activebackground="#3DA012",
            activeforeground="white",
            relief="flat", bd=0,
            padx=24, pady=4,
            cursor="hand2",
            command=self._send_message
        )
        self.send_btn.pack(side="right")

        add_hover_effect(self.send_btn, COLORS['group_header'], "#3DA012")

        self.input_text.bind("<Return>", lambda e: self._send_message() or "break")
        self.input_text.focus_set()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def add_message(self, sender, content, timestamp=None):
        """添加气泡消息"""
        is_me = (sender == self.client.username)

        row = tk.Frame(self.msg_frame, bg=COLORS['bg'])
        row.pack(fill="x", padx=10, pady=2)

        if is_me:
            self._create_bubble(row, content, timestamp, is_me=True)
        else:
            self._create_bubble(row, content, timestamp, is_me=False, sender=sender)

        scroll_to_bottom(self.msg_canvas)

    def _create_bubble(self, parent, content, timestamp, is_me, sender=None):
        """创建单条气泡消息"""
        bubble_bg = COLORS['my_bubble'] if is_me else COLORS['other_bubble']
        text_color = COLORS['my_bubble_text'] if is_me else COLORS['other_bubble_text']
        time_str = format_time(timestamp)

        if is_me:
            time_label = tk.Label(
                parent, text=time_str,
                font=("微软雅黑", 7),
                fg=COLORS['text_secondary'], bg=COLORS['bg']
            )
            time_label.pack(side="right", padx=(4, 0), anchor="se")

            bubble = tk.Frame(parent, bg=bubble_bg)
            bubble.pack(side="right", anchor="e")

            bubble_inner = tk.Frame(bubble, bg=bubble_bg)
            bubble_inner.pack(padx=1, pady=1)

            msg_label = tk.Label(
                bubble_inner, text=content,
                font=("微软雅黑", 10),
                fg=text_color, bg=bubble_bg,
                wraplength=360,
                justify="left",
                padx=12, pady=8
            )
            msg_label.pack()
        else:
            avatar_color = get_avatar_color(sender)
            avatar = tk.Label(
                parent, text=get_initial(sender),
                font=("微软雅黑", 9, "bold"),
                fg="white", bg=avatar_color,
                width=2, height=1
            )
            avatar.pack(side="left", anchor="n", padx=(0, 6), pady=(2, 0))

            name_label = tk.Label(
                parent, text=sender,
                font=("微软雅黑", 8),
                fg=COLORS['text_secondary'], bg=COLORS['bg']
            )
            name_label.pack(side="left", anchor="sw", padx=(0, 4))

            bubble = tk.Frame(parent, bg=bubble_bg)
            bubble.pack(side="left", anchor="w")

            bubble_inner = tk.Frame(bubble, bg=bubble_bg)
            bubble_inner.pack(padx=1, pady=1)

            msg_label = tk.Label(
                bubble_inner, text=content,
                font=("微软雅黑", 10),
                fg=text_color, bg=bubble_bg,
                wraplength=360,
                justify="left",
                padx=12, pady=8
            )
            msg_label.pack()

            time_label = tk.Label(
                parent, text=time_str,
                font=("微软雅黑", 7),
                fg=COLORS['text_secondary'], bg=COLORS['bg']
            )
            time_label.pack(side="left", padx=(4, 0), anchor="sw")

    def _add_system_msg(self, content):
        add_system_msg(self.msg_frame, content)
        scroll_to_bottom(self.msg_canvas)

    def _add_progress_msg(self, content):
        add_progress_msg(self.msg_frame, content)
        scroll_to_bottom(self.msg_canvas)

    def _send_message(self):
        content = self.input_text.get("1.0", tk.END).strip()
        if not content:
            return

        if not self.client.is_connected():
            messagebox.showwarning("提示", "连接已断开，无法发送消息")
            return

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        if self.client.send_group_msg(content):
            self.add_message(self.client.username, content, timestamp)
            self.input_text.delete("1.0", tk.END)
        else:
            messagebox.showerror("发送失败", "消息发送失败，请检查网络连接")

    def _load_history(self):
        if not self.client.is_connected():
            return
        self.client.request_history(GROUP_ID)

    def show_history_records(self, records):
        if not self._history_loaded:
            for w in self.msg_frame.winfo_children():
                w.destroy()
            self._history_loaded = True

        if not records:
            self._add_system_msg("暂无聊天记录")
            return

        for m in records:
            sender = m.get("sender", "")
            content = m.get("content", "")
            timestamp = m.get("timestamp", "")
            self.add_message(sender, content, timestamp)

        self._add_system_msg("--- 以上为历史记录 ---")

    def _on_close(self):
        self.root.unbind("<MouseWheel>")
        self.main_window.set_group_chat_window(None)
        self.root.destroy()