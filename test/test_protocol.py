# -*- coding: utf-8 -*-
"""
协议模块单元测试
"""

import unittest
import json
import sys
import os

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.protocol import (
    MsgType, GROUP_ID, build_message, parse_message, get_field,
    make_login, make_register, make_private_msg, make_group_msg,
    make_file_request, make_file_response, make_file_data,
    make_file_complete, make_history_request, make_heartbeat,
    make_error, make_success,
)


class TestMsgType(unittest.TestCase):
    """测试消息类型枚举"""

    def test_enum_values(self):
        self.assertEqual(MsgType.LOGIN, 'LOGIN')
        self.assertEqual(MsgType.REGISTER, 'REGISTER')
        self.assertEqual(MsgType.GROUP_MSG, 'GROUP_MSG')
        self.assertEqual(MsgType.HEARTBEAT, 'HEARTBEAT')

    def test_group_id(self):
        self.assertEqual(GROUP_ID, 'PUBLIC_ROOM')


class TestBuildMessage(unittest.TestCase):
    """测试消息构建"""

    def test_basic_message(self):
        msg = build_message(MsgType.LOGIN, 'testuser', password='123456')
        parsed = json.loads(msg)
        self.assertEqual(parsed['type'], 'LOGIN')
        self.assertEqual(parsed['from'], 'testuser')
        self.assertEqual(parsed['password'], '123456')
        self.assertIn('timestamp', parsed)


class TestParseMessage(unittest.TestCase):
    """测试消息解析"""

    def test_valid_json(self):
        msg = json.dumps({'type': 'LOGIN', 'from': 'user'})
        result = parse_message(msg)
        self.assertEqual(result['type'], 'LOGIN')
        self.assertEqual(result['from'], 'user')

    def test_bytes_input(self):
        msg = json.dumps({'type': 'LOGIN', 'from': 'user'}).encode('utf-8')
        result = parse_message(msg)
        self.assertEqual(result['type'], 'LOGIN')

    def test_invalid_json(self):
        self.assertIsNone(parse_message('not json'))
        self.assertIsNone(parse_message(None))


class TestGetField(unittest.TestCase):
    """测试字段提取"""

    def test_get_field(self):
        msg = {'key': 'value'}
        self.assertEqual(get_field(msg, 'key'), 'value')
        self.assertEqual(get_field(msg, 'missing'), None)
        self.assertEqual(get_field(msg, 'missing', 'default'), 'default')
        self.assertIsNone(get_field(None, 'key'))


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷构建函数"""

    def test_make_login(self):
        msg = json.loads(make_login('alice', 'pass123'))
        self.assertEqual(msg['type'], 'LOGIN')
        self.assertEqual(msg['from'], 'alice')
        self.assertEqual(msg['password'], 'pass123')

    def test_make_register(self):
        msg = json.loads(make_register('bob', 'pass456'))
        self.assertEqual(msg['type'], 'REGISTER')

    def test_make_private_msg(self):
        msg = json.loads(make_private_msg('alice', 'bob', 'Hello'))
        self.assertEqual(msg['type'], 'PRIVATE_MSG')
        self.assertEqual(msg['receiver'], 'bob')
        self.assertEqual(msg['content'], 'Hello')

    def test_make_group_msg(self):
        msg = json.loads(make_group_msg('alice', 'Hi all'))
        self.assertEqual(msg['type'], 'GROUP_MSG')
        self.assertEqual(msg['receiver'], GROUP_ID)

    def test_make_file_request(self):
        msg = json.loads(make_file_request('alice', 'bob', 'test.pdf', 1024))
        self.assertEqual(msg['type'], 'FILE_REQUEST')
        self.assertEqual(msg['filename'], 'test.pdf')
        self.assertEqual(msg['filesize'], 1024)

    def test_make_error(self):
        msg = json.loads(make_error('server', 'Something wrong'))
        self.assertEqual(msg['type'], 'ERROR')
        self.assertEqual(msg['reason'], 'Something wrong')

    def test_make_success(self):
        msg = json.loads(make_success('server'))
        self.assertEqual(msg['type'], 'SUCCESS')
        self.assertEqual(msg['message'], 'ok')

    def test_make_heartbeat(self):
        msg = json.loads(make_heartbeat('alice'))
        self.assertEqual(msg['type'], 'HEARTBEAT')


if __name__ == '__main__':
    unittest.main()