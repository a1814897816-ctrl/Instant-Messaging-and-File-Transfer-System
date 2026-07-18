# -*- coding: utf-8 -*-
"""
用户账号数据库管理工具
支持增删改查 user 表
"""

import sqlite3
import hashlib
import os
import sys

# 数据库路径：项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_project_root, 'chat.db')


def sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def get_conn():
    if not os.path.exists(DB_PATH):
        print(f'数据库不存在: {DB_PATH}')
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── 查询 ──

def list_all():
    """列出所有用户"""
    conn = get_conn()
    rows = conn.execute('SELECT * FROM user ORDER BY username').fetchall()
    conn.close()
    if not rows:
        print('(无用户)')
        return
    print(f'{"用户名":<16} {"昵称":<16} {"状态":<10}')
    print('-' * 44)
    for r in rows:
        nickname = r['nickname'] or '-'
        print(f'{r["username"]:<16} {nickname:<16} {r["status"]:<10}')
    print(f'\n共 {len(rows)} 个用户')


def search_user(keyword):
    """模糊搜索用户"""
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM user WHERE username LIKE ? OR nickname LIKE ? ORDER BY username',
        (f'%{keyword}%', f'%{keyword}%')
    ).fetchall()
    conn.close()
    if not rows:
        print(f'未找到匹配 "{keyword}" 的用户')
        return
    print(f'{"用户名":<16} {"昵称":<16} {"状态":<10}')
    print('-' * 44)
    for r in rows:
        nickname = r['nickname'] or '-'
        print(f'{r["username"]:<16} {nickname:<16} {r["status"]:<10}')
    print(f'\n共 {len(rows)} 个匹配')


# ── 增加 ──

def add_user(username, password, nickname=''):
    """添加用户"""
    conn = get_conn()
    try:
        conn.execute(
            'INSERT INTO user (username, password, nickname) VALUES (?, ?, ?)',
            (username, sha256(password), nickname)
        )
        conn.commit()
        print(f'用户 "{username}" 添加成功')
    except sqlite3.IntegrityError:
        print(f'用户名 "{username}" 已存在')
    finally:
        conn.close()


# ── 删除 ──

def del_user(username):
    """删除用户（同时删除相关消息）"""
    conn = get_conn()
    row = conn.execute('SELECT username FROM user WHERE username = ?', (username,)).fetchone()
    if not row:
        print(f'用户 "{username}" 不存在')
        conn.close()
        return

    conn.execute('DELETE FROM private_message WHERE sender = ? OR receiver = ?', (username, username))
    conn.execute('DELETE FROM group_message WHERE sender = ?', (username,))
    conn.execute('DELETE FROM user WHERE username = ?', (username,))
    conn.commit()
    conn.close()
    print(f'用户 "{username}" 及其相关消息已删除')


# ── 修改 ──

def update_user(username, field, value):
    """修改用户字段 (nickname / password / status)"""
    valid_fields = {'nickname', 'password', 'status'}
    if field not in valid_fields:
        print(f'可修改字段: {", ".join(valid_fields)}')
        return

    conn = get_conn()
    row = conn.execute('SELECT username FROM user WHERE username = ?', (username,)).fetchone()
    if not row:
        print(f'用户 "{username}" 不存在')
        conn.close()
        return

    val = sha256(value) if field == 'password' else value
    conn.execute(f'UPDATE user SET {field} = ? WHERE username = ?', (val, username))
    conn.commit()
    conn.close()
    print(f'用户 "{username}" 的 {field} 已更新')


def reset_password(username, new_password):
    """重置密码"""
    update_user(username, 'password', new_password)


# ── 批量操作 ──

def del_all():
    """删除所有用户及消息"""
    conn = get_conn()
    conn.execute('DELETE FROM private_message')
    conn.execute('DELETE FROM group_message')
    conn.execute('DELETE FROM user')
    conn.commit()
    conn.close()
    print('所有用户及相关消息已删除')


def del_batch(usernames):
    """批量删除指定用户"""
    conn = get_conn()
    deleted = 0
    for username in usernames:
        username = username.strip()
        if not username:
            continue
        row = conn.execute('SELECT username FROM user WHERE username = ?', (username,)).fetchone()
        if row:
            conn.execute('DELETE FROM private_message WHERE sender = ? OR receiver = ?', (username, username))
            conn.execute('DELETE FROM group_message WHERE sender = ?', (username,))
            conn.execute('DELETE FROM user WHERE username = ?', (username,))
            deleted += 1
            print(f'  已删除: {username}')
        else:
            print(f'  跳过: {username} (不存在)')
    conn.commit()
    conn.close()
    print(f'\n共删除 {deleted} 个用户')


# ── 主菜单 ──

def print_help():
    print("""
用户账号管理工具
──────────────────────────────────────
  python manage_users.py list             列出所有用户
  python manage_users.py search <关键词>    模糊搜索用户
  python manage_users.py add <用户名> <密码> [昵称]
  python manage_users.py del <用户名>       删除用户
  python manage_users.py del-batch <用户名1,用户名2,...>  批量删除
  python manage_users.py delall           删除所有用户
  python manage_users.py set <用户名> nickname <昵称>
  python manage_users.py set <用户名> status <online|offline>
  python manage_users.py passwd <用户名> <新密码>
""")


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args:
        print_help()
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == 'list':
        list_all()
    elif cmd == 'search':
        if len(args) < 2:
            print('用法: search <关键词>')
        else:
            search_user(args[1])
    elif cmd == 'add':
        if len(args) < 3:
            print('用法: add <用户名> <密码> [昵称]')
        else:
            add_user(args[1], args[2], args[3] if len(args) > 3 else '')
    elif cmd == 'del':
        if len(args) < 2:
            print('用法: del <用户名>')
        else:
            del_user(args[1])
    elif cmd == 'del-batch':
        if len(args) < 2:
            print('用法: del-batch <用户名1,用户名2,...>')
        else:
            del_batch(args[1].split(','))
    elif cmd == 'delall':
        del_all()
    elif cmd == 'set':
        if len(args) < 4:
            print('用法: set <用户名> <nickname|status> <值>')
        else:
            update_user(args[1], args[2], args[3])
    elif cmd == 'passwd':
        if len(args) < 3:
            print('用法: passwd <用户名> <新密码>')
        else:
            reset_password(args[1], args[2])
    else:
        print(f'未知命令: {cmd}')
        print_help()