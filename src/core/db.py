# -*- coding: utf-8 -*-
"""
数据库模块 —— SQLite 持久化
管理用户表、私聊消息表、群聊消息表的创建与 CRUD 操作。
"""

import sqlite3
import hashlib
import time
import os
import sys

# 数据库路径：项目根目录
if getattr(sys, 'frozen', False):
    _base_dir = os.path.dirname(sys.executable)
else:
    # 从 src/core/db.py 向上两级到项目根目录
    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_base_dir, 'chat.db')


def sha256(text):
    """SHA256 哈希（用于密码存储）"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# ══════════════════════════════════════════════
#  数据库初始化
# ══════════════════════════════════════════════

def get_connection():
    """获取数据库连接（自动创建文件）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持 dict 风格访问
    return conn


def init_db():
    """初始化数据库表（首次运行时创建）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            username  VARCHAR(32) PRIMARY KEY,
            password  VARCHAR(64) NOT NULL,
            nickname  VARCHAR(32),
            status    VARCHAR(16) DEFAULT 'offline'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_message (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sender     VARCHAR(32) NOT NULL,
            receiver   VARCHAR(32) NOT NULL,
            content    TEXT NOT NULL,
            timestamp  DATETIME NOT NULL,
            type       VARCHAR(16) DEFAULT 'text',
            FOREIGN KEY (sender)   REFERENCES user(username),
            FOREIGN KEY (receiver) REFERENCES user(username)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_message (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sender     VARCHAR(32) NOT NULL,
            group_id   VARCHAR(32) NOT NULL,
            content    TEXT NOT NULL,
            timestamp  DATETIME NOT NULL,
            FOREIGN KEY (sender) REFERENCES user(username)
        )
    ''')

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════
#  用户操作
# ══════════════════════════════════════════════

def register_user(username, password):
    """注册用户，返回 (success, message)"""
    conn = get_connection()
    try:
        conn.execute(
            'INSERT INTO user (username, password) VALUES (?, ?)',
            (username, sha256(password))
        )
        conn.commit()
        return True, '注册成功'
    except sqlite3.IntegrityError:
        return False, '用户名已存在'
    finally:
        conn.close()


def verify_user(username, password):
    """验证用户登录，返回 (success, message)"""
    conn = get_connection()
    row = conn.execute(
        'SELECT password FROM user WHERE username = ?', (username,)
    ).fetchone()
    conn.close()
    if row is None:
        return False, '用户名不存在'
    if row['password'] != sha256(password):
        return False, '密码错误'
    return True, '登录成功'


def set_user_online(username):
    """更新用户状态为在线"""
    conn = get_connection()
    conn.execute(
        "UPDATE user SET status = 'online' WHERE username = ?", (username,)
    )
    conn.commit()
    conn.close()


def set_user_offline(username):
    """更新用户状态为离线"""
    conn = get_connection()
    conn.execute(
        "UPDATE user SET status = 'offline' WHERE username = ?", (username,)
    )
    conn.commit()
    conn.close()


def get_all_online():
    """获取所有在线用户列表"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT username, nickname FROM user WHERE status = 'online'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════
#  消息操作
# ══════════════════════════════════════════════

def save_private_msg(sender, receiver, content, msg_type='text'):
    """保存一条私聊消息"""
    conn = get_connection()
    conn.execute(
        '''INSERT INTO private_message (sender, receiver, content, timestamp, type)
           VALUES (?, ?, ?, ?, ?)''',
        (sender, receiver, content, time.strftime('%Y-%m-%d %H:%M:%S'), msg_type)
    )
    conn.commit()
    conn.close()


def save_group_msg(sender, group_id, content):
    """保存一条群聊消息"""
    conn = get_connection()
    conn.execute(
        '''INSERT INTO group_message (sender, group_id, content, timestamp)
           VALUES (?, ?, ?, ?)''',
        (sender, group_id, content, time.strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()


def get_private_history(user_a, user_b, limit=100):
    """获取两人之间的私聊历史记录"""
    conn = get_connection()
    rows = conn.execute(
        '''SELECT sender, receiver, content, timestamp, type
           FROM private_message
           WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
           ORDER BY timestamp ASC
           LIMIT ?''',
        (user_a, user_b, user_b, user_a, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_group_history(group_id, limit=100):
    """获取群聊历史记录"""
    conn = get_connection()
    rows = conn.execute(
        '''SELECT sender, group_id, content, timestamp
           FROM group_message
           WHERE group_id = ?
           ORDER BY timestamp ASC
           LIMIT ?''',
        (group_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]