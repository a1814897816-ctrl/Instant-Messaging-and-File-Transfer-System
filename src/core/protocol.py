# -*- coding: utf-8 -*-
"""
通信协议定义模块
所有客户端与服务端之间的消息统一采用 JSON 格式封装。
"""

import json
import time
from enum import Enum


# ── 消息类型枚举 ──
class MsgType(str, Enum):
    """消息类型常量，所有消息字段 type 必须使用此处定义的值"""
    # 认证
    REGISTER = 'REGISTER'           # 注册请求
    LOGIN = 'LOGIN'                 # 登录请求
    LOGOUT = 'LOGOUT'               # 登出通知

    # 在线用户
    ONLINE_LIST = 'ONLINE_LIST'     # 在线用户列表（服务端 → 客户端）
    USER_ONLINE = 'USER_ONLINE'     # 用户上线广播
    USER_OFFLINE = 'USER_OFFLINE'   # 用户下线广播

    # 聊天
    PRIVATE_MSG = 'PRIVATE_MSG'     # 点对点私聊消息
    GROUP_MSG = 'GROUP_MSG'         # 群聊/公共聊天室消息

    # 文件传输
    FILE_REQUEST = 'FILE_REQUEST'   # 文件传输请求（发送方 → 接收方）
    FILE_RESPONSE = 'FILE_RESPONSE' # 文件传输响应（接收方接受/拒绝）
    FILE_DATA = 'FILE_DATA'         # 文件数据块
    FILE_COMPLETE = 'FILE_COMPLETE' # 文件传输完成通知

    # 聊天记录
    HISTORY_REQUEST = 'HISTORY_REQUEST'   # 请求聊天历史
    HISTORY_RESPONSE = 'HISTORY_RESPONSE' # 聊天历史响应（多条记录）

    # 系统
    HEARTBEAT = 'HEARTBEAT'         # 心跳保活
    ERROR = 'ERROR'                 # 错误响应
    SUCCESS = 'SUCCESS'             # 操作成功响应
    QUIT = 'QUIT'                   # 客户端主动退出

    # 通用
    PROGRESS = 'PROGRESS'           # 进度通知


# ── 群聊固定标识 ──
GROUP_ID = 'PUBLIC_ROOM'


# ── 协议构建 ──

def build_message(msg_type, sender, **kwargs):
    """
    构建一条标准 JSON 消息
    :param msg_type: 消息类型（MsgType 枚举值）
    :param sender: 发送者用户名
    :param kwargs: 额外字段（receiver, content, filename 等）
    :return: JSON 字符串
    """
    msg = {
        'type': msg_type,
        'from': sender,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    msg.update(kwargs)
    return json.dumps(msg, ensure_ascii=False)


def parse_message(raw_data):
    """
    解析收到的原始数据为 Python dict
    :param raw_data: 收到的原始字节或字符串
    :return: dict 或 None（解析失败时）
    """
    if isinstance(raw_data, bytes):
        raw_data = raw_data.decode('utf-8')
    try:
        return json.loads(raw_data)
    except (json.JSONDecodeError, TypeError):
        return None


# ── 便捷构建函数 ──

def make_login(username, password):
    return build_message(MsgType.LOGIN, username, password=password)


def make_register(username, password):
    return build_message(MsgType.REGISTER, username, password=password)


def make_private_msg(sender, receiver, content):
    return build_message(MsgType.PRIVATE_MSG, sender, receiver=receiver, content=content)


def make_group_msg(sender, content):
    return build_message(MsgType.GROUP_MSG, sender, receiver=GROUP_ID, content=content)


def make_file_request(sender, receiver, filename, filesize):
    return build_message(MsgType.FILE_REQUEST, sender, receiver=receiver,
                         filename=filename, filesize=filesize)


def make_file_response(sender, receiver, filename, accepted):
    return build_message(MsgType.FILE_RESPONSE, sender, receiver=receiver,
                         filename=filename, accepted=accepted)


def make_file_data(sender, receiver, filename, offset, total, data):
    return build_message(MsgType.FILE_DATA, sender, receiver=receiver,
                         filename=filename, offset=offset, total=total, data=data)


def make_file_complete(sender, receiver, filename, filesize):
    return build_message(MsgType.FILE_COMPLETE, sender, receiver=receiver,
                         filename=filename, filesize=filesize)


def make_history_request(sender, target):
    return build_message(MsgType.HISTORY_REQUEST, sender, target=target)


def make_heartbeat(sender):
    return build_message(MsgType.HEARTBEAT, sender)


def make_error(sender, reason):
    return build_message(MsgType.ERROR, sender, reason=reason)


def make_success(sender, message='ok'):
    return build_message(MsgType.SUCCESS, sender, message=message)


# ── 消息字段提取辅助 ──

def get_field(msg, key, default=None):
    """安全获取消息字段"""
    return msg.get(key, default) if msg else default