# -*- coding: utf-8 -*-
"""
客户端 GUI —— 主界面 (美化版)
在线用户列表、消息接收与分发、功能入口
成员 B（侯皓骞）负责
"""

import tkinter as tk
from tkinter import messagebox

from src.core.protocol import GROUP_ID
from src.common.ui_utils import (
    COLORS, AVATAR_COLORS, get_avatar_color, get_initial, center_window,
)


class MainWindow:
    """客户端主界面 (现代化设计)"""

    def __init__(self, client, login_root, on_logout_callback):
        self.client = client
        self.login_root = login_root
        self.on_logout_callback = on_logout_callback

        self.root = tk.Toplevel()
        self.root.title(f"校园即时通信 - {client.username}")
        self.root.geometry("860x600")
        self.root.minsize(700, 450)
        self.root.configure(bg=COLORS['bg'])

        self.online_users = []
        self.chat_windows = {}
        self.group_chat_window = None
        self._history_target = None
        self._history_records = []

        self._setup_ui()
        self._setup_callbacks()
        center_window(self.root)

        if self.client._initial_online_list:
            self._update_user_list(self.client._initial_online_list)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        # ── 顶部导航栏 ──
        navbar = tk.Frame(self.root, bg=COLORS['navbar_bg'], height=50)
        navbar.pack(fill="x")
        navbar.pack_propagate(False)

        tk.Label(
            navbar, text="\U0001f4ac  校园即时通信",
            font=("微软雅黑", 13, "bold"),
            fg="white", bg=COLORS['navbar_bg']
        ).pack(side="left", padx=16, pady=10)

        nav_right = tk.Frame(navbar, bg=COLORS['navbar_bg'])
        nav_right.pack(side="right", padx=8)

        self._create_nav_btn(nav_right, "\U0001f4e2 公共聊天室", self._open_group_chat)
        self._create_nav_btn(nav_right, "\U0001f6aa 退出", self._logout)

        # ── 主内容区 ──
        main_container = tk.Frame(self.root, bg=COLORS['bg'])
        main_container.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        # ── 左侧边栏 ──
        sidebar = tk.Frame(main_container, bg=COLORS['sidebar_bg'], width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        sidebar_header = tk.Frame(sidebar, bg=COLORS['sidebar_bg'], height=44)
        sidebar_header.pack(fill="x", padx=12, pady=(8, 4))
        sidebar_header.pack_propagate(False)

        tk.Label(
            sidebar_header, text="在线用户",
            font=("微软雅黑", 11, "bold"),
            fg=COLORS['text'], bg=COLORS['sidebar_bg'],
            anchor="w"
        ).pack(side="left", fill="y")

        self.online_count_label = tk.Label(
            sidebar_header, text="0",
            font=("微软雅黑", 9, "bold"),
            fg="white", bg=COLORS['primary'],
            width=2
        )
        self.online_count_label.pack(side="right")

        tk.Frame(sidebar, bg=COLORS['border'], height=1).pack(fill="x", padx=12)

        list_container = tk.Frame(sidebar, bg=COLORS['sidebar_bg'])
        list_container.pack(fill="both", expand=True, padx=4, pady=4)

        self.user_listbox = tk.Listbox(
            list_container,
            font=("微软雅黑", 10),
            selectmode="single",
            bg=COLORS['sidebar_bg'],
            fg=COLORS['text'],
            selectbackground=COLORS['selected'],
            selectforeground=COLORS['text'],
            activestyle="none",
            relief="flat",
            highlightthickness=0,
            bd=0,
            height=20
        )
        self.user_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_container, bg=COLORS['sidebar_bg'])
        scrollbar.pack(side="right", fill="y")
        self.user_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.user_listbox.yview)

        self.user_listbox.bind("<Double-Button-1>", self._on_user_double_click)

        # ── 右侧欢迎区 ──
        self.right_frame = tk.Frame(main_container, bg=COLORS['bg'])
        self.right_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self._show_welcome()

        # ── 底部状态栏 ──
        self.status_bar = tk.Label(
            self.root, text="  \u25cf 已连接", font=("微软雅黑", 9),
            fg=COLORS['success'], bg=COLORS['bg'],
            anchor="w", padx=12, pady=4
        )
        self.status_bar.pack(side="bottom", fill="x")

    def _show_welcome(self):
        """显示欢迎界面"""
        for w in self.right_frame.winfo_children():
            w.destroy()

        welcome = tk.Frame(self.right_frame, bg=COLORS['bg'])
        welcome.pack(fill="both", expand=True)

        center = tk.Frame(welcome, bg=COLORS['bg'])
        center.place(relx=0.5, rely=0.45, anchor="center")

        avatar_color = get_avatar_color(self.client.username)
        avatar_circle = tk.Label(
            center, text=get_initial(self.client.username),
            font=("微软雅黑", 32, "bold"),
            fg="white", bg=avatar_color,
            width=4, height=2
        )
        avatar_circle.pack(pady=(0, 16))

        tk.Label(
            center, text=f"欢迎回来，{self.client.username}",
            font=("微软雅黑", 16, "bold"),
            fg=COLORS['text'], bg=COLORS['bg']
        ).pack(pady=(0, 8))

        tk.Label(
            center,
            text="双击左侧在线用户开始私聊\n通过顶部导航栏进入公共聊天室",
            font=("微软雅黑", 10),
            fg=COLORS['text_secondary'], bg=COLORS['bg'],
            justify="center"
        ).pack()

    def _create_nav_btn(self, parent, text, command):
        """创建导航栏按钮"""
        btn = tk.Label(
            parent, text=text,
            font=("微软雅黑", 9),
            fg="white", bg=COLORS['navbar_bg'],
            cursor="hand2", padx=10, pady=6
        )
        btn.pack(side="left")

        def on_enter(e):
            btn.config(bg=COLORS['primary_dark'])

        def on_leave(e):
            btn.config(bg=COLORS['navbar_bg'])

        def on_click(e):
            command()

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)

    def _setup_callbacks(self):
        self.client.set_callback('on_online_list', self._on_online_list)
        self.client.set_callback('on_user_online', self._on_user_online)
        self.client.set_callback('on_user_offline', self._on_user_offline)
        self.client.set_callback('on_private_msg', self._on_private_msg)
        self.client.set_callback('on_group_msg', self._on_group_msg)
        self.client.set_callback('on_file_request', self._on_file_request)
        self.client.set_callback('on_file_response', self._on_file_response)
        self.client.set_callback('on_file_progress', self._on_file_progress)
        self.client.set_callback('on_file_complete', self._on_file_complete)
        self.client.set_callback('on_history', self._on_history)
        self.client.set_callback('on_error', self._on_error)
        self.client.set_callback('on_disconnected', self._on_disconnected)

    def show(self):
        self.root.deiconify()

    def _update_user_list(self, usernames):
        self.online_users = sorted(usernames)
        self.user_listbox.delete(0, tk.END)
        for user in self.online_users:
            avatar_color = get_avatar_color(user)
            initial = get_initial(user)
            display = f"  {initial}  {user}"
            if user == self.client.username:
                display += " (我)"
            self.user_listbox.insert(tk.END, display)
        self.online_count_label.config(text=str(len(self.online_users)))

    def _refresh_user_list(self):
        self._update_user_list(self.online_users)

    def _on_online_list(self, usernames):
        self._update_user_list(usernames)

    def _on_user_online(self, username):
        if username not in self.online_users:
            self.online_users.append(username)
        self._update_user_list(self.online_users)
        self.status_bar.config(text=f"  \u25cf {username} 上线了", fg=COLORS['success'])

    def _on_user_offline(self, username):
        if username in self.online_users:
            self.online_users.remove(username)
        self._update_user_list(self.online_users)
        self.status_bar.config(text=f"  \u25cb {username} 下线了", fg=COLORS['text_secondary'])
        if username in self.chat_windows:
            self.chat_windows[username].set_offline()

    def _on_private_msg(self, sender, content, timestamp):
        from src.ui.chat_window import ChatWindow
        if sender in self.chat_windows:
            self.chat_windows[sender].add_message(sender, content, timestamp)
        else:
            cw = ChatWindow(self.root, self.client, sender, self)
            self.chat_windows[sender] = cw
            cw.show()
            cw.add_message(sender, content, timestamp)

    def _on_history(self, target, records):
        if target == GROUP_ID and self.group_chat_window is not None:
            self.group_chat_window.show_history_records(records)
        elif target in self.chat_windows:
            self.chat_windows[target].show_history_records(records)

    def _on_error(self, reason):
        self.status_bar.config(text=f"  \u26a0 {reason}", fg=COLORS['danger'])

    def _on_disconnected(self, reason):
        self.status_bar.config(text=f"  \u2715 连接已断开: {reason}", fg=COLORS['danger'])
        self.root.after(3000, self._try_reconnect)

    def _try_reconnect(self):
        if self.client._host and self.client._port:
            if self.client.connect(self.client._host, self.client._port):
                self.status_bar.config(text="  \u25cf 已重新连接", fg=COLORS['success'])
                self.client.login(self.client.username, "")

    def _on_user_double_click(self, event):
        selection = self.user_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx >= len(self.online_users):
            return
        target = self.online_users[idx]
        if target == self.client.username:
            return

        if target in self.chat_windows:
            self.chat_windows[target].root.lift()
            self.chat_windows[target].root.focus_force()
            return

        from src.ui.chat_window import ChatWindow
        cw = ChatWindow(self.root, self.client, target, self)
        self.chat_windows[target] = cw
        cw.show()

    def _open_group_chat(self, event=None):
        if self.group_chat_window is not None:
            self.group_chat_window.show()
            return

        from src.ui.group_chat_window import GroupChatWindow
        self.group_chat_window = GroupChatWindow(self.root, self.client, self)
        self.group_chat_window.show()

    def set_group_chat_window(self, window):
        self.group_chat_window = window

    def _on_group_msg(self, sender, content, timestamp):
        if self.group_chat_window is None:
            from src.ui.group_chat_window import GroupChatWindow
            self.group_chat_window = GroupChatWindow(self.root, self.client, self)
            self.group_chat_window.show()
        if sender == self.client.username:
            return
        self.group_chat_window.add_message(sender, content, timestamp)

    def _on_file_request(self, sender, filename, filesize):
        if sender in self.chat_windows:
            self.chat_windows[sender].handle_file_request(sender, filename, filesize)
        else:
            from src.ui.chat_window import ChatWindow
            cw = ChatWindow(self.root, self.client, sender, self)
            self.chat_windows[sender] = cw
            cw.show()
            cw.root.after(100, lambda: cw.handle_file_request(sender, filename, filesize))

    def _on_file_response(self, sender, filename, accepted):
        if sender in self.chat_windows:
            cw = self.chat_windows[sender]
            if accepted:
                cw._add_system_msg(f"对方接受了文件: {filename}，开始传输...")
                self.client.start_send_file(sender, filename)
            else:
                cw._add_system_msg(f"对方拒绝了文件: {filename}")
                cw._file_sending_info = None

    def _on_file_progress(self, filename, percent):
        for cw in self.chat_windows.values():
            if hasattr(cw, 'file_transfer_filename') and cw.file_transfer_filename == filename:
                cw.update_file_progress(filename, percent)
                return

    def _on_file_complete(self, filename, data_or_size):
        for cw in self.chat_windows.values():
            if hasattr(cw, 'file_transfer_filename') and cw.file_transfer_filename == filename:
                cw.handle_file_complete(filename, data_or_size)
                return

    def _logout(self, event=None):
        self._close_all_chat_windows()
        self.on_logout_callback()
        self.root.destroy()

    def _on_close(self):
        self._close_all_chat_windows()
        self.on_logout_callback()
        self.root.destroy()

    def _close_all_chat_windows(self):
        for cw in list(self.chat_windows.values()):
            try:
                cw.root.destroy()
            except Exception:
                pass
        self.chat_windows.clear()
        if self.group_chat_window is not None:
            try:
                self.group_chat_window.root.destroy()
            except Exception:
                pass
            self.group_chat_window = None

    def remove_chat_window(self, username):
        if username in self.chat_windows:
            del self.chat_windows[username]