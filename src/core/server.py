# -*- coding: utf-8 -*-
"""
服务端核心框架
负责：监听端口、接受客户端连接、认证用户、消息路由转发、在线状态管理。

成员 A（组长）负责本模块的完整实现。
"""

import json
import socket
import threading
import time
import sys
import traceback

from src.core.protocol import (
    MsgType, GROUP_ID, parse_message, get_field,
    make_success, make_error, build_message,
)
from src.core.db import (
    init_db, register_user, verify_user,
    set_user_online, set_user_offline, get_all_online,
    save_private_msg, save_group_msg,
    get_private_history, get_group_history,
)


# ══════════════════════════════════════════════
#  ClientManager —— 在线客户端管理器
# ══════════════════════════════════════════════

class ClientManager:
    """
    线程安全地管理所有在线客户端的连接。
    key = username, value = socket 对象
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._clients = {}   # {username: socket}

    def add(self, username, conn):
        with self._lock:
            self._clients[username] = conn

    def remove(self, username):
        with self._lock:
            return self._clients.pop(username, None)

    def get(self, username):
        with self._lock:
            return self._clients.get(username)

    def get_all_usernames(self):
        with self._lock:
            return list(self._clients.keys())

    def _to_bytes(self, message):
        """将消息（str 或 dict）转换为待发送的字节串"""
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False)
        return (message + '\n').encode('utf-8')

    def send_to(self, username, message):
        """向指定用户发送消息"""
        conn = self.get(username)
        if conn is None:
            return False
        try:
            data = self._to_bytes(message)
            conn.sendall(data)
            return True
        except OSError:
            self.remove(username)
            return False

    def broadcast(self, message, exclude=None):
        """向所有在线用户广播消息（可排除某个用户）"""
        with self._lock:
            data = self._to_bytes(message)
            for username, conn in list(self._clients.items()):
                if username == exclude:
                    continue
                try:
                    conn.sendall(data)
                except OSError:
                    pass  # 发送失败的用户将在下次检测时被清理

    def clean_dead_connections(self):
        """清理已断开的连接"""
        with self._lock:
            dead = []
            for username, conn in self._clients.items():
                try:
                    conn.sendall(b'')
                except OSError:
                    dead.append(username)
            for u in dead:
                del self._clients[u]
                set_user_offline(u)


# ══════════════════════════════════════════════
#  MessageRouter —— 消息路由引擎
# ══════════════════════════════════════════════

class MessageRouter:
    """
    根据消息 type 字段将消息分发到对应的处理函数。
    每个处理函数接收 (sender_username, parsed_msg_dict) 并返回响应消息（或 None）。
    """

    def __init__(self, manager: ClientManager):
        self.manager = manager
        self._handlers = {
            MsgType.REGISTER:      self.handle_register,
            MsgType.LOGIN:         self.handle_login,
            MsgType.LOGOUT:        self.handle_logout,
            MsgType.PRIVATE_MSG:   self.handle_private_msg,
            MsgType.GROUP_MSG:     self.handle_group_msg,
            MsgType.FILE_REQUEST:  self.handle_file_request,
            MsgType.FILE_RESPONSE: self.handle_file_response,
            MsgType.FILE_DATA:     self.handle_file_data,
            MsgType.FILE_COMPLETE: self.handle_file_complete,
            MsgType.HISTORY_REQUEST: self.handle_history_request,
            MsgType.HEARTBEAT:     self.handle_heartbeat,
            MsgType.QUIT:          self.handle_quit,
        }

    def route(self, sender, msg):
        """根据消息类型路由到对应处理器"""
        msg_type = get_field(msg, 'type')
        handler = self._handlers.get(msg_type)
        if handler:
            return handler(sender, msg)
        else:
            return make_error('server', f'未知消息类型: {msg_type}')

    # ── 认证 ──

    def handle_register(self, sender, msg):
        username = get_field(msg, 'from')
        password = get_field(msg, 'password')
        success, reason = register_user(username, password)
        if success:
            return make_success('server', reason)
        else:
            return make_error('server', reason)

    def handle_login(self, sender, msg):
        username = get_field(msg, 'from')
        password = get_field(msg, 'password')
        success, reason = verify_user(username, password)
        if not success:
            return make_error('server', reason)

        # 检查是否已在线（防止重复登录）
        if self.manager.get(username) is not None:
            return make_error('server', '该账号已在其他设备登录')

        set_user_online(username)
        self.manager.add(username, sender)

        # 广播上线通知
        online_broadcast = build_message(MsgType.USER_ONLINE, username)
        self.manager.broadcast(online_broadcast, exclude=username)

        # 返回在线用户列表
        online_list = self.manager.get_all_usernames()
        return build_message(MsgType.SUCCESS, 'server',
                             message=reason, online_list=online_list)

    def handle_logout(self, sender, msg):
        username = get_field(msg, 'from')
        return self._perform_logout(username)

    def handle_quit(self, sender, msg):
        username = get_field(msg, 'from')
        return self._perform_logout(username)

    def _perform_logout(self, username):
        """执行用户下线流程"""
        self.manager.remove(username)
        set_user_offline(username)
        offline_broadcast = build_message(MsgType.USER_OFFLINE, username)
        self.manager.broadcast(offline_broadcast)
        return None

    # ── 聊天 ──

    def handle_private_msg(self, sender, msg):
        receiver = get_field(msg, 'receiver')
        content = get_field(msg, 'content', '')
        if not receiver:
            return make_error('server', '接收者不能为空')

        save_private_msg(get_field(msg, 'from'), receiver, content)

        if not self.manager.send_to(receiver, msg):
            return make_error('server', f'用户 {receiver} 已离线')
        return None

    def handle_group_msg(self, sender, msg):
        content = get_field(msg, 'content', '')
        save_group_msg(get_field(msg, 'from'), GROUP_ID, content)
        self.manager.broadcast(msg, exclude=get_field(msg, 'from'))
        return None

    # ── 文件传输 ──

    def handle_file_request(self, sender, msg):
        """转发文件传输请求给接收方"""
        receiver = get_field(msg, 'receiver')
        if not self.manager.send_to(receiver, msg):
            return make_error('server', f'用户 {receiver} 已离线')
        return None

    def handle_file_response(self, sender, msg):
        """转发文件传输响应给原发送方"""
        receiver = get_field(msg, 'receiver')
        self.manager.send_to(receiver, msg)
        return None

    def handle_file_data(self, sender, msg):
        """转发文件数据块"""
        receiver = get_field(msg, 'receiver')
        if not self.manager.send_to(receiver, msg):
            return make_error('server', '文件传输中断：接收方已离线')
        return None

    def handle_file_complete(self, sender, msg):
        """转发文件传输完成通知"""
        receiver = get_field(msg, 'receiver')
        self.manager.send_to(receiver, msg)
        return None

    # ── 历史记录 ──

    def handle_history_request(self, sender, msg):
        target = get_field(msg, 'target')
        username = get_field(msg, 'from')

        if target == GROUP_ID:
            records = get_group_history(GROUP_ID)
        else:
            records = get_private_history(username, target)

        return build_message(
            MsgType.HISTORY_RESPONSE, 'server',
            target=target, records=json.dumps(records, ensure_ascii=False)
        )

    # ── 心跳 ──

    def handle_heartbeat(self, sender, msg):
        return None


# ══════════════════════════════════════════════
#  ClientHandler —— 单客户端处理线程
# ══════════════════════════════════════════════

class ClientHandler(threading.Thread):
    """每个客户端连接对应一个 Handler 线程"""

    def __init__(self, conn, addr, router: MessageRouter, manager: ClientManager):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.router = router
        self.manager = manager
        self.username = None

    def run(self):
        print(f'[连接] {self.addr}')
        buffer = ''
        try:
            while True:
                data = self.conn.recv(4096)
                if not data:
                    break

                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    msg = parse_message(line)
                    if msg is None:
                        self._reply(make_error('server', '消息格式错误'))
                        continue

                    msg_type = get_field(msg, 'type')
                    try:
                        response = self.router.route(self.conn, msg)
                        if response:
                            self._reply(response)
                        # 登录成功后设置用户名，确保 _cleanup 能正确清理
                        if msg_type == MsgType.LOGIN and response:
                            resp = parse_message(response)
                            if resp and get_field(resp, 'type') == MsgType.SUCCESS:
                                self.username = get_field(msg, 'from')
                    except Exception as e:
                        print(f'[错误] 处理消息时发生异常: {e}')
                        traceback.print_exc()
                        self._reply(make_error('server', f'服务器内部错误'))

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            self._cleanup()
            print(f'[断开] {self.addr}')

    def _reply(self, message):
        """向当前客户端回复消息"""
        try:
            data = (message + '\n').encode('utf-8')
            self.conn.sendall(data)
        except OSError:
            pass

    def _cleanup(self):
        """当前客户端断开后的清理"""
        if self.username:
            self.manager.remove(self.username)
            set_user_offline(self.username)
            offline_broadcast = build_message(MsgType.USER_OFFLINE, self.username)
            self.manager.broadcast(offline_broadcast)
        try:
            self.conn.close()
        except OSError:
            pass


# ══════════════════════════════════════════════
#  ChatServer —— 服务端主入口
# ══════════════════════════════════════════════

class ChatServer:
    """校园即时通信服务端"""

    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.manager = ClientManager()
        self.router = MessageRouter(self.manager)

    def start(self):
        init_db()
        print(f'[服务端] SQLite 数据库初始化完成')

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(50)
        print(f'[服务端] 正在监听 {self.host}:{self.port} ...')

        try:
            while True:
                conn, addr = server_socket.accept()
                handler = ClientHandler(conn, addr, self.router, self.manager)
                handler.start()
        except KeyboardInterrupt:
            print('\n[服务端] 正在关闭...')
        finally:
            server_socket.close()
            print('[服务端] 已关闭')


# ── 入口 ──
if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    ChatServer(port=port).start()