# -*- coding: utf-8 -*-
"""
数据库模块单元测试
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.db import (
    init_db, get_connection, sha256,
    register_user, verify_user,
    set_user_online, set_user_offline, get_all_online,
    save_private_msg, save_group_msg,
    get_private_history, get_group_history,
    DB_PATH,
)


class TestDB(unittest.TestCase):
    """数据库模块测试"""

    @classmethod
    def setUpClass(cls):
        """初始化测试数据库"""
        # 备份原数据库路径，使用测试数据库
        cls._original_db_path = DB_PATH
        import src.core.db as db_module
        # 使用临时测试数据库
        test_db = os.path.join(os.path.dirname(DB_PATH), 'test_chat.db')
        db_module.DB_PATH = test_db
        # 重新初始化
        if os.path.exists(test_db):
            os.remove(test_db)
        init_db()

    @classmethod
    def tearDownClass(cls):
        """清理测试数据库"""
        import src.core.db as db_module
        test_db = db_module.DB_PATH
        if os.path.exists(test_db):
            os.remove(test_db)
        db_module.DB_PATH = cls._original_db_path

    def test_sha256(self):
        """测试 SHA256 哈希"""
        result = sha256('hello')
        self.assertEqual(len(result), 64)
        self.assertEqual(sha256('hello'), sha256('hello'))
        self.assertNotEqual(sha256('hello'), sha256('world'))

    def test_register_user(self):
        """测试用户注册"""
        success, msg = register_user('testuser1', 'password123')
        self.assertTrue(success)
        self.assertEqual(msg, '注册成功')

        # 重复注册
        success, msg = register_user('testuser1', 'password123')
        self.assertFalse(success)
        self.assertEqual(msg, '用户名已存在')

    def test_verify_user(self):
        """测试用户验证"""
        register_user('testuser2', 'mypassword')

        success, msg = verify_user('testuser2', 'mypassword')
        self.assertTrue(success)
        self.assertEqual(msg, '登录成功')

        success, msg = verify_user('testuser2', 'wrongpassword')
        self.assertFalse(success)
        self.assertEqual(msg, '密码错误')

        success, msg = verify_user('nonexistent', 'password')
        self.assertFalse(success)
        self.assertEqual(msg, '用户名不存在')

    def test_online_status(self):
        """测试在线状态管理"""
        register_user('testuser3', 'password')

        set_user_online('testuser3')
        online = get_all_online()
        self.assertTrue(any(u['username'] == 'testuser3' for u in online))

        set_user_offline('testuser3')
        online = get_all_online()
        self.assertFalse(any(u['username'] == 'testuser3' for u in online))

    def test_save_and_get_private_msg(self):
        """测试私聊消息存储与查询"""
        register_user('alice', 'pass')
        register_user('bob', 'pass')

        save_private_msg('alice', 'bob', 'Hello Bob')
        save_private_msg('bob', 'alice', 'Hi Alice')

        history = get_private_history('alice', 'bob')
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['sender'], 'alice')
        self.assertEqual(history[0]['content'], 'Hello Bob')
        self.assertEqual(history[1]['sender'], 'bob')
        self.assertEqual(history[1]['content'], 'Hi Alice')

    def test_save_and_get_group_msg(self):
        """测试群聊消息存储与查询"""
        register_user('charlie', 'pass')

        save_group_msg('charlie', 'PUBLIC_ROOM', 'Hello everyone')
        save_group_msg('charlie', 'PUBLIC_ROOM', 'How are you?')

        history = get_group_history('PUBLIC_ROOM')
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['content'], 'Hello everyone')
        self.assertEqual(history[1]['content'], 'How are you?')


if __name__ == '__main__':
    unittest.main()