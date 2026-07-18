# -*- coding: utf-8 -*-
"""
客户端核心框架
负责：连接服务端、收发消息、断线重连、回调通知。

成员 B 和成员 C 基于本框架开发具体 GUI 界面。
B 负责：登录界面、在线列表、主界面框架、点对点私聊
C 负责：群聊/公共聊天室、文件传输界面

设计说明：
  - 通信层与 UI 层分离，通过回调函数解耦
  - 所有 UI 逻辑通过 set_callback() 注册的回调触发
  - 支持自动重连和心跳保活
"""

import json
import socket
import threading
import time
import base64

from src.core.protocol import (
    MsgType, GROUP_ID, parse_message, get_field,
    make_login, make_register,
    make_private_msg, make_group_msg,
    make_file_request, make_file_response,
    make_file_data, make_file_complete,
    make_history_request, make_heartbeat,
)
from src.core.protocol import build_message


# ══════════════════════════════════════════════
#  ChatClient —— 客户端核心
# ══════════════════════════════════════════════

class ChatClient:
    """
    校园即时通信客户端核心类（与 UI 无关）

    使用方式：
        client = ChatClient()
        client.set_callback('on_private_msg', my_handler_func)
        client.connect('127.0.0.1', 8888)
        client.login('myuser', 'mypass')
        client.send_private_msg('target_user', 'Hello')
    """

    # ── 支持的回调事件名 ──
    CALLBACK_EVENTS = [
        'on_connected',
        'on_disconnected',
        'on_login_result',
        'on_register_result',
        'on_online_list',
        'on_user_online',
        'on_user_offline',
        'on_private_msg',
        'on_group_msg',
        'on_file_request',
        'on_file_response',
        'on_file_progress',
        'on_file_complete',
        'on_history',
        'on_error',
        'on_progress',
    ]

    def __init__(self):
        self._socket = None
        self._listener_thread = None
        self._heartbeat_thread = None
        self._running = False
        self._username = None
        self._host = None
        self._port = None

        self._callbacks = {event: [] for event in self.CALLBACK_EVENTS}
        self._file_buffers = {}
        self._initial_online_list = []

    # ── 回调管理 ──

    def set_callback(self, event, handler):
        """注册回调函数（覆盖方式，每个事件只保留一个 handler）"""
        if event in self._callbacks:
            self._callbacks[event] = [handler]

    def add_callback(self, event, handler):
        """追加回调函数（允许多个监听者）"""
        if event in self._callbacks:
            self._callbacks[event].append(handler)

    def _fire(self, event, *args):
        """触发指定事件的所有回调"""
        for handler in self._callbacks.get(event, []):
            try:
                handler(*args)
            except Exception as e:
                print(f'[客户端] 回调异常 ({event}): {e}')

    # ── 连接管理 ──

    def connect(self, host='127.0.0.1', port=8888):
        """
        连接到服务端（阻塞直到连接成功或失败）
        连接成功后自动启动消息监听线程和心跳线程
        """
        self._host = host
        self._port = port
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5)
            self._socket.connect((host, port))
            self._socket.settimeout(None)
            self._running = True

            self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._listener_thread.start()

            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

            self._fire('on_connected')
            return True
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self._fire('on_error', f'连接失败: {e}')
            return False

    def disconnect(self):
        """主动断开连接"""
        self._running = False
        if self._socket:
            try:
                msg = build_message(MsgType.QUIT, self.username or '')
                data = (msg + '\n').encode('utf-8')
                self._socket.sendall(data)
            except OSError:
                pass
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
        self._fire('on_disconnected', '主动断开')

    def is_connected(self):
        return self._socket is not None and self._running

    @property
    def username(self):
        return self._username

    # ── 发送消息 ──

    def _send_raw(self, message):
        """发送原始 JSON 消息字符串"""
        if not self._socket or not self._running:
            return False
        try:
            data = (message + '\n').encode('utf-8')
            self._socket.sendall(data)
            return True
        except OSError as e:
            self._fire('on_error', f'发送失败: {e}')
            self.disconnect()
            return False

    # ── 认证 ──

    def login(self, username, password):
        """发送登录请求"""
        self._username = username
        return self._send_raw(make_login(username, password))

    def register(self, username, password):
        """发送注册请求"""
        return self._send_raw(make_register(username, password))

    # ── 聊天 ──

    def send_private_msg(self, receiver, content):
        """发送私聊消息"""
        sender = self._username or ''
        return self._send_raw(make_private_msg(sender, receiver, content))

    def send_group_msg(self, content):
        """发送群聊消息"""
        sender = self._username or ''
        return self._send_raw(make_group_msg(sender, content))

    # ── 文件传输 ──

    def send_file_request(self, receiver, filepath):
        """发送文件传输请求"""
        import os
        if not os.path.exists(filepath):
            self._fire('on_error', f'文件不存在: {filepath}')
            return
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        self._file_buffers[filename] = {'path': filepath, 'total': filesize}
        sender = self._username or ''
        return self._send_raw(make_file_request(sender, receiver, filename, filesize))

    def send_file_response(self, sender, filename, accepted):
        """响应文件传输请求（接受或拒绝）"""
        me = self._username or ''
        return self._send_raw(make_file_response(me, sender, filename, accepted))

    def start_send_file(self, receiver, filename, chunk_size=64 * 1024):
        """
        分块发送文件数据（在收到对方接受响应后调用）
        :param chunk_size: 每块大小，默认 64KB
        """
        info = self._file_buffers.get(filename)
        if not info:
            self._fire('on_error', f'文件信息丢失: {filename}')
            return

        filepath = info['path']
        total = info['total']
        sender = self._username or ''
        offset = 0

        try:
            with open(filepath, 'rb') as f:
                while offset < total:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    data_b64 = base64.b64encode(chunk).decode('ascii')
                    msg = make_file_data(sender, receiver, filename, offset, total, data_b64)
                    self._send_raw(msg)
                    offset += len(chunk)
                    percent = int(offset / total * 100)
                    self._fire('on_file_progress', filename, percent)
        except IOError as e:
            self._fire('on_error', f'读取文件失败: {e}')
            return

        self._send_raw(make_file_complete(sender, receiver, filename, total))
        self._file_buffers.pop(filename, None)

    # ── 聊天记录 ──

    def request_history(self, target):
        """请求聊天历史（target 为用户名或 GROUP_ID）"""
        sender = self._username or ''
        return self._send_raw(make_history_request(sender, target))

    # ── 消息监听线程 ──

    def _listen_loop(self):
        """持续监听服务端消息"""
        buffer = ''
        while self._running and self._socket:
            try:
                data = self._socket.recv(4096)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                self._running = False
                self._fire('on_disconnected', '连接断开')
                break

            if not data:
                self._running = False
                self._fire('on_disconnected', '服务端关闭了连接')
                break

            buffer += data.decode('utf-8')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                self._dispatch(parse_message(line))

    # ── 心跳线程 ──

    def _heartbeat_loop(self):
        """每 30 秒发送心跳包"""
        while self._running:
            time.sleep(30)
            if self._running and self._socket:
                self._send_raw(make_heartbeat(self._username or ''))

    # ── 消息分发 ──

    def _dispatch(self, msg):
        """根据消息类型触发对应的回调"""
        if msg is None:
            return

        msg_type = get_field(msg, 'type')

        if msg_type == MsgType.SUCCESS:
            online_list = get_field(msg, 'online_list', [])
            if online_list:
                self._fire('on_login_result', True, get_field(msg, 'message', 'ok'))
                self._initial_online_list = online_list
                self._fire('on_online_list', online_list)
            else:
                self._fire('on_register_result', True, get_field(msg, 'message', 'ok'))

        elif msg_type == MsgType.ERROR:
            error_text = get_field(msg, 'reason', '未知错误')
            if '用户名不存在' in error_text or '密码错误' in error_text:
                self._fire('on_login_result', False, error_text)
            elif '用户名已存在' in error_text:
                self._fire('on_register_result', False, error_text)
            else:
                self._fire('on_error', error_text)

        elif msg_type == MsgType.USER_ONLINE:
            self._fire('on_user_online', get_field(msg, 'from'))

        elif msg_type == MsgType.USER_OFFLINE:
            self._fire('on_user_offline', get_field(msg, 'from'))

        elif msg_type == MsgType.PRIVATE_MSG:
            self._fire('on_private_msg',
                       get_field(msg, 'from'),
                       get_field(msg, 'content', ''),
                       get_field(msg, 'timestamp', ''))

        elif msg_type == MsgType.GROUP_MSG:
            self._fire('on_group_msg',
                       get_field(msg, 'from'),
                       get_field(msg, 'content', ''),
                       get_field(msg, 'timestamp', ''))

        elif msg_type == MsgType.FILE_REQUEST:
            self._fire('on_file_request',
                       get_field(msg, 'from'),
                       get_field(msg, 'filename', ''),
                       get_field(msg, 'filesize', 0))

        elif msg_type == MsgType.FILE_RESPONSE:
            self._fire('on_file_response',
                       get_field(msg, 'from'),
                       get_field(msg, 'filename', ''),
                       get_field(msg, 'accepted', False))

        elif msg_type == MsgType.FILE_DATA:
            filename = get_field(msg, 'filename', '')
            total = get_field(msg, 'total', 0)
            offset = get_field(msg, 'offset', 0)
            data_b64 = get_field(msg, 'data', '')
            if filename not in self._file_buffers:
                self._file_buffers[filename] = {'data': bytearray(), 'total': total, 'received': 0}
            buf = self._file_buffers[filename]
            if not isinstance(buf['data'], bytearray):
                buf['data'] = bytearray()
            chunk = base64.b64decode(data_b64)
            buf['data'].extend(chunk)
            buf['received'] += len(chunk)
            percent = int(buf['received'] / total * 100) if total > 0 else 0
            self._fire('on_file_progress', filename, percent)

        elif msg_type == MsgType.FILE_COMPLETE:
            filename = get_field(msg, 'filename', '')
            filesize = get_field(msg, 'filesize', 0)
            buf = self._file_buffers.pop(filename, None)
            if buf:
                self._fire('on_file_complete', filename, bytes(buf['data']))
            else:
                self._fire('on_file_complete', filename, filesize)

        elif msg_type == MsgType.HISTORY_RESPONSE:
            target = get_field(msg, 'target', '')
            records_str = get_field(msg, 'records', '[]')
            try:
                records = json.loads(records_str)
            except json.JSONDecodeError:
                records = []
            self._fire('on_history', target, records)

        elif msg_type == MsgType.PROGRESS:
            self._fire('on_progress', get_field(msg, 'message', ''))