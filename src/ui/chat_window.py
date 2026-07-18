# -*- coding: utf-8 -*-
"""
客户端 GUI —— 私聊窗口 (美化版)
点对点文本聊天、消息收发、气泡式消息展示
成员 B（侯皓骞）负责
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import os
import time

from src.common.ui_utils import (
    COLORS, AVATAR_COLORS,
    get_avatar_color, get_initial, add_hover_effect,
    center_window, format_time, create_header_btn,
    setup_canvas_scroll, bind_mousewheel,
    add_system_msg, add_progress_msg,
    scroll_to_bottom, format_file_size,
)


class ChatWindow:
    """点对点私聊窗口 (气泡式现代化设计)"""

    def __init__(self, parent, client, target_user, main_window):
        self.client = client
        self.target_user = target_user
        self.main_window = main_window
        self.target_online = True
        self._history_loaded = False
        self._file_request_info = None
        self._file_sending_info = None
        self._file_receiving_info = None

        self.root = tk.Toplevel(parent)
        self.root.title(f"与 {target_user} 私聊")
        self.root.geometry("550x600")
        self.root.minsize(400, 400)
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

        avatar_color = get_avatar_color(self.target_user)
        avatar = tk.Label(
            header, text=get_initial(self.target_user),
            font=("微软雅黑", 12, "bold"),
            fg="white", bg=avatar_color,
            width=2
        )
        avatar.pack(side="left", padx=(12, 8), pady=8)

        info_frame = tk.Frame(header, bg=COLORS['header_bg'])
        info_frame.pack(side="left", fill="y", pady=6)

        tk.Label(
            info_frame, text=self.target_user,
            font=("微软雅黑", 11, "bold"),
            fg=COLORS['text'], bg=COLORS['header_bg'],
            anchor="w"
        ).pack(fill="x")

        self.status_label = tk.Label(
            info_frame, text="在线",
            font=("微软雅黑", 8),
            fg=COLORS['online'], bg=COLORS['header_bg'],
            anchor="w"
        )
        self.status_label.pack(fill="x")

        btn_frame = tk.Frame(header, bg=COLORS['header_bg'])
        btn_frame.pack(side="right", padx=4, pady=8)

        create_header_btn(btn_frame, "\U0001f4ce", self._send_file)
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
            bg=COLORS['primary'], fg="white",
            activebackground=COLORS['primary_dark'],
            activeforeground="white",
            relief="flat", bd=0,
            padx=24, pady=4,
            cursor="hand2",
            command=self._send_message
        )
        self.send_btn.pack(side="right")

        add_hover_effect(self.send_btn, COLORS['primary'], COLORS['primary_dark'])

        self.input_text.bind("<Return>", lambda e: self._send_message() or "break")
        self.input_text.focus_set()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def set_offline(self):
        self.target_online = False
        self.status_label.config(text="离线", fg=COLORS['offline'])
        self.send_btn.config(state="disabled")
        self._add_system_msg(f"{self.target_user} 已离线")

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
                wraplength=320,
                justify="left",
                padx=12, pady=8
            )
            msg_label.pack()
        else:
            avatar_color = get_avatar_color(sender or self.target_user)
            avatar = tk.Label(
                parent, text=get_initial(sender or self.target_user),
                font=("微软雅黑", 9, "bold"),
                fg="white", bg=avatar_color,
                width=2, height=1
            )
            avatar.pack(side="left", anchor="n", padx=(0, 6), pady=(2, 0))

            bubble = tk.Frame(parent, bg=bubble_bg)
            bubble.pack(side="left", anchor="w")

            bubble_inner = tk.Frame(bubble, bg=bubble_bg)
            bubble_inner.pack(padx=1, pady=1)

            msg_label = tk.Label(
                bubble_inner, text=content,
                font=("微软雅黑", 10),
                fg=text_color, bg=bubble_bg,
                wraplength=320,
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

        if self.client.send_private_msg(self.target_user, content):
            self.add_message(self.client.username, content, timestamp)
            self.input_text.delete("1.0", tk.END)
        else:
            messagebox.showerror("发送失败", "消息发送失败，请检查网络连接")

    def _load_history(self):
        if not self.client.is_connected():
            return
        self.client.request_history(self.target_user)

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

    # ── 文件传输 ──

    @property
    def file_transfer_filename(self):
        if self._file_request_info:
            return self._file_request_info['filename']
        if self._file_sending_info:
            return self._file_sending_info['filename']
        if self._file_receiving_info:
            return self._file_receiving_info['filename']
        return None

    def _send_file(self):
        if not self.target_online:
            messagebox.showwarning("提示", "对方已离线，无法发送文件")
            return

        filepath = filedialog.askopenfilename(
            title="选择要发送的文件",
            parent=self.root
        )
        if not filepath:
            return

        if not self.client.is_connected():
            messagebox.showwarning("提示", "连接已断开，无法发送文件")
            return

        filesize = os.path.getsize(filepath)
        filename = os.path.basename(filepath)

        if not self.client.send_file_request(self.target_user, filepath):
            messagebox.showerror("发送失败", "文件请求发送失败")
            return

        self._file_sending_info = {
            'filename': filename,
            'filesize': filesize
        }
        self._add_progress_msg(
            f"文件发送请求已发出: {filename} ({format_file_size(filesize)})，等待对方接受..."
        )

    def handle_file_request(self, sender, filename, filesize):
        accept = messagebox.askyesno(
            "文件传输请求",
            f"{sender} 想向你发送文件:\n\n"
            f"文件名: {filename}\n"
            f"大小: {format_file_size(filesize)}\n\n"
            f"是否接受？"
        )
        self.client.send_file_response(sender, filename, accept)

        if accept:
            self._file_receiving_info = {
                'filename': filename,
                'total': filesize,
                'received': 0
            }
            self._add_progress_msg(
                f"正在接收文件: {filename} ({format_file_size(filesize)})..."
            )
        else:
            self._add_system_msg(f"已拒绝接收文件: {filename}")

    def update_file_progress(self, filename, percent):
        if self._file_receiving_info and self._file_receiving_info['filename'] == filename:
            self._file_receiving_info['received'] = int(
                self._file_receiving_info['total'] * percent / 100
            )
            self._add_progress_msg(
                f"接收文件 {filename}: {percent}% "
                f"({format_file_size(self._file_receiving_info['received'])}/"
                f"{format_file_size(self._file_receiving_info['total'])})"
            )

    def handle_file_complete(self, filename, data_or_size):
        if isinstance(data_or_size, bytes):
            self._save_received_file(filename, data_or_size)
            self._file_receiving_info = None
            self._add_system_msg(f"文件接收完成: {filename}")
        elif self._file_sending_info and self._file_sending_info['filename'] == filename:
            self._file_sending_info = None
            self._add_system_msg(f"文件发送完成: {filename}")

    def _save_received_file(self, filename, data):
        import os as _os
        # 保存到项目根目录的 received_files/
        base_dir = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        save_dir = _os.path.join(base_dir, 'received_files')
        _os.makedirs(save_dir, exist_ok=True)
        save_path = _os.path.join(save_dir, filename)
        base, ext = _os.path.splitext(filename)
        counter = 1
        while _os.path.exists(save_path):
            save_path = _os.path.join(save_dir, f"{base}({counter}){ext}")
            counter += 1
        with open(save_path, 'wb') as f:
            f.write(data)
        self._add_system_msg(f"文件已保存到: received_files/{_os.path.basename(save_path)}")

    def _on_close(self):
        self.root.unbind("<MouseWheel>")
        self.main_window.remove_chat_window(self.target_user)
        self.root.destroy()