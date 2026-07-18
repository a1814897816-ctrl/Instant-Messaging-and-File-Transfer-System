# -*- coding: utf-8 -*-
"""
客户端 GUI —— 登录/注册界面 (美化版)
成员 B（侯皓骞）负责
基于 ChatClient 核心框架构建
"""

import tkinter as tk
from tkinter import messagebox

from src.core.client import ChatClient
from src.common.ui_utils import COLORS, add_hover_effect, center_window


class LoginWindow:
    """登录/注册窗口 (现代化设计)"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("校园即时通信系统 - 登录")
        self.root.geometry("420x520")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['bg'])

        self.client = ChatClient()
        self.main_window = None
        self._logged_in = False

        self._setup_ui()
        self._setup_client_callbacks()
        center_window(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_rounded_frame(self, parent, bg=COLORS['card'], padx=20, pady=15):
        """创建带圆角效果的卡片框架"""
        outer = tk.Frame(parent, bg=COLORS['border'], highlightthickness=0)
        inner = tk.Frame(outer, bg=bg, highlightthickness=0)
        inner.pack(padx=1, pady=1, fill="both", expand=True)
        content = tk.Frame(inner, bg=bg)
        content.pack(fill="both", expand=True, padx=padx, pady=pady)
        return outer, content

    def _setup_ui(self):
        # ── 顶部 Header ──
        header = tk.Frame(self.root, bg=COLORS['primary'], height=160)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="\U0001f4ac", font=("Segoe UI Emoji", 36),
            bg=COLORS['primary']
        ).pack(pady=(25, 0))

        tk.Label(
            header, text="校园即时通信",
            font=("微软雅黑", 18, "bold"),
            fg="white", bg=COLORS['primary']
        ).pack(pady=(2, 0))

        tk.Label(
            header, text="Campus IM",
            font=("Segoe UI", 10),
            fg="#B0DDF5", bg=COLORS['primary']
        ).pack()

        # ── 主卡片区域 ──
        card_outer, card = self._create_rounded_frame(
            self.root, bg=COLORS['card'], padx=24, pady=20
        )
        card_outer.pack(fill="x", padx=20, pady=(20, 10))

        # 服务器设置 (可折叠)
        self._server_collapsed = True
        self._server_toggle_frame = tk.Frame(card, bg=COLORS['card'], cursor="hand2")
        self._server_toggle_frame.pack(fill="x", pady=(0, 6))

        self._server_arrow = tk.Label(
            self._server_toggle_frame, text="\u25b6",
            font=("微软雅黑", 8),
            fg=COLORS['text_secondary'], bg=COLORS['card']
        )
        self._server_arrow.pack(side="left")

        server_label = tk.Label(
            self._server_toggle_frame, text=" 服务器设置",
            font=("微软雅黑", 10, "bold"),
            fg=COLORS['text'], bg=COLORS['card'], cursor="hand2"
        )
        server_label.pack(side="left")

        tk.Label(
            self._server_toggle_frame, text="127.0.0.1:8888",
            font=("微软雅黑", 8),
            fg=COLORS['text_light'], bg=COLORS['card']
        ).pack(side="right")

        self._server_toggle_frame.bind("<Button-1>", lambda e: self._toggle_server())
        server_label.bind("<Button-1>", lambda e: self._toggle_server())
        self._server_arrow.bind("<Button-1>", lambda e: self._toggle_server())

        # 服务器设置内容 (默认隐藏)
        self._server_content = tk.Frame(card, bg=COLORS['card'])

        ip_row = tk.Frame(self._server_content, bg=COLORS['card'])
        ip_row.pack(fill="x", pady=(0, 8))
        self._create_input_field(ip_row, "IP 地址", is_ip=True)

        port_row = tk.Frame(self._server_content, bg=COLORS['card'])
        port_row.pack(fill="x", pady=(0, 6))
        self._create_input_field(port_row, "端口号", is_port=True)

        # 分隔线
        self._server_sep = tk.Frame(card, bg=COLORS['border'], height=1)
        self._server_sep.pack(fill="x", pady=(0, 12))

        # 账号信息
        account_label = tk.Label(
            card, text="账号信息",
            font=("微软雅黑", 10, "bold"),
            fg=COLORS['text'], bg=COLORS['card'], anchor="w"
        )
        account_label.pack(fill="x", pady=(0, 10))

        # 用户名输入
        user_row = tk.Frame(card, bg=COLORS['card'])
        user_row.pack(fill="x", pady=(0, 8))
        self._create_input_field(user_row, "用户名", is_user=True)

        # 密码输入
        pass_row = tk.Frame(card, bg=COLORS['card'])
        pass_row.pack(fill="x", pady=(0, 12))
        self._create_input_field(pass_row, "密码", is_pass=True)

        # 按钮
        btn_frame = tk.Frame(card, bg=COLORS['card'])
        btn_frame.pack(fill="x", pady=(4, 0))

        self.login_btn = tk.Button(
            btn_frame, text="登  录", height=2,
            font=("微软雅黑", 11, "bold"),
            bg=COLORS['primary'], fg="white",
            activebackground=COLORS['primary_dark'],
            activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            command=self._do_login
        )
        self.login_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        add_hover_effect(self.login_btn, COLORS['primary'], COLORS['primary_dark'])

        self.register_btn = tk.Button(
            btn_frame, text="注  册", height=2,
            font=("微软雅黑", 11, "bold"),
            bg=COLORS['success'], fg="white",
            activebackground="#2DB84D",
            activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            command=self._do_register
        )
        self.register_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        add_hover_effect(self.register_btn, COLORS['success'], "#2DB84D")

        # 状态标签
        self.status_label = tk.Label(
            self.root, text="",
            font=("微软雅黑", 9), fg=COLORS['text_secondary'],
            bg=COLORS['bg']
        )
        self.status_label.pack(pady=(5, 10))

        # 回车触发登录
        self.root.bind("<Return>", lambda e: self._do_login())

    def _create_input_field(self, parent, placeholder, is_ip=False, is_port=False,
                            is_user=False, is_pass=False):
        """创建带图标和占位符的输入框"""
        icon_char = "\U0001f310" if is_ip else "\U0001f50c" if is_port else "\U0001f464" if is_user else "\U0001f512"

        icon_label = tk.Label(
            parent, text=icon_char,
            font=("Segoe UI Emoji", 11),
            bg=COLORS['card'], fg=COLORS['text_secondary']
        )
        icon_label.pack(side="left", padx=(0, 8))

        field_frame = tk.Frame(
            parent, bg=COLORS['input_bg'],
            highlightthickness=1, highlightbackground=COLORS['border'],
            highlightcolor=COLORS['primary']
        )
        field_frame.pack(side="left", fill="x", expand=True)

        entry = tk.Entry(
            field_frame, font=("微软雅黑", 10),
            bg=COLORS['input_bg'], fg=COLORS['text'],
            insertbackground=COLORS['primary'],
            relief="flat", bd=5,
            insertwidth=2
        )
        entry.pack(fill="x", expand=True)

        if is_ip:
            entry.insert(0, "127.0.0.1")
            self.ip_entry = entry
        elif is_port:
            entry.insert(0, "8888")
            self.port_entry = entry
        elif is_user:
            self.user_entry = entry
        elif is_pass:
            entry.config(show="\u25cf")
            self.pass_entry = entry

        def on_focus_in(e):
            field_frame.config(bg=COLORS['input_focus'], highlightbackground=COLORS['primary'])
            entry.config(bg=COLORS['input_focus'])

        def on_focus_out(e):
            field_frame.config(bg=COLORS['input_bg'], highlightbackground=COLORS['border'])
            entry.config(bg=COLORS['input_bg'])

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def _toggle_server(self):
        """切换服务器设置折叠/展开"""
        if self._server_collapsed:
            self._server_content.pack(fill="x", after=self._server_toggle_frame, pady=(0, 4))
            self._server_arrow.config(text="\u25bc")
        else:
            self._server_content.pack_forget()
            self._server_arrow.config(text="\u25b6")
        self._server_collapsed = not self._server_collapsed

    def _setup_client_callbacks(self):
        """注册客户端回调"""
        self.client.set_callback('on_login_result', self._on_login_result)
        self.client.set_callback('on_register_result', self._on_register_result)
        self.client.set_callback('on_error', self._on_error)
        self.client.set_callback('on_disconnected', self._on_disconnected)

    def _set_status(self, text, color=None):
        if color is None:
            color = COLORS['text_secondary']
        self.status_label.config(text=text, fg=color)
        self.root.update()

    def _get_connection_params(self):
        host = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        try:
            port = int(port_str)
        except ValueError:
            return None, None, "端口号格式不正确"
        return host, port, None

    # ── 登录 ──

    def _do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("提示", "请输入用户名和密码")
            return

        host, port, err = self._get_connection_params()
        if err:
            messagebox.showwarning("提示", err)
            return

        self._set_status("正在连接服务端...", COLORS['primary'])

        if not self.client.connect(host, port):
            self._set_status("连接失败，请检查服务端是否启动", COLORS['danger'])
            return

        self._set_status("正在登录...", COLORS['primary'])
        self.client.login(username, password)

    def _on_login_result(self, success, message):
        if success:
            self._set_status("登录成功", COLORS['success'])
            self._logged_in = True
            self._open_main_window()
        else:
            self._set_status(message, COLORS['danger'])
            messagebox.showerror("登录失败", message)
            self.client.disconnect()

    # ── 注册 ──

    def _do_register(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("提示", "请输入用户名和密码")
            return

        host, port, err = self._get_connection_params()
        if err:
            messagebox.showwarning("提示", err)
            return

        self._set_status("正在连接服务端...", COLORS['primary'])

        if not self.client.connect(host, port):
            self._set_status("连接失败，请检查服务端是否启动", COLORS['danger'])
            return

        self._set_status("正在注册...", COLORS['primary'])
        self.client.register(username, password)

    def _on_register_result(self, success, message):
        if success:
            self._set_status("注册成功，请点击登录", COLORS['success'])
            messagebox.showinfo("注册成功", "账号注册成功，请点击登录按钮登录")
        else:
            self._set_status(message, COLORS['danger'])
            messagebox.showerror("注册失败", message)
        self.client.disconnect()

    # ── 错误与断连 ──

    def _on_error(self, reason):
        if not self._logged_in:
            self._set_status(f"错误: {reason}", COLORS['danger'])

    def _on_disconnected(self, reason):
        if not self._logged_in:
            self._set_status(f"连接断开: {reason}", COLORS['danger'])

    # ── 打开主界面 ──

    def _open_main_window(self):
        from src.ui.main_window import MainWindow
        self.root.withdraw()
        self.main_window = MainWindow(
            self.client, self.root, self._on_return_to_login
        )
        self.main_window.show()

    def _on_return_to_login(self):
        """从主界面退出，回到登录窗口"""
        self._logged_in = False
        self.client.disconnect()
        self.root.deiconify()

    def _on_close(self):
        if self.client.is_connected():
            self.client.disconnect()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    LoginWindow().run()