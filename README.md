# 校园即时通信与文件传输系统

## 技术规格

| 项目 | 版本 |
|------|------|
| **语言** | Python 3.10+ |
| **GUI 框架** | tkinter (Python 标准库) |
| **数据库** | SQLite 3 (Python 标准库 sqlite3) |
| **通信协议** | TCP Socket + JSON 消息封装 |
| **打包工具** | PyInstaller |

## 目录结构

```
├── src/                    # 源代码
│   ├── common/             # 公共工具模块
│   │   └── ui_utils.py     # GUI 配色、头像、工具函数
│   ├── core/               # 核心通信模块
│   │   ├── protocol.py     # 通信协议定义 (JSON 消息格式)
│   │   ├── db.py           # 数据库模块 (SQLite CRUD)
│   │   ├── server.py       # 服务端核心 (多线程 TCP)
│   │   └── client.py       # 客户端核心 (事件回调驱动)
│   └── ui/                 # GUI 界面模块
│       ├── login_window.py      # 登录/注册界面
│       ├── main_window.py       # 主界面 (在线用户列表)
│       ├── chat_window.py       # 私聊窗口 (气泡消息)
│       └── group_chat_window.py # 公共聊天室窗口
├── test/                   # 单元测试
│   ├── test_protocol.py    # 协议模块测试
│   └── test_db.py          # 数据库模块测试
├── scripts/                # 构建与运维脚本
│   ├── build_server.py     # 服务端打包脚本
│   ├── build_client.py     # 客户端打包脚本
│   └── manage_users.py     # 用户账号管理 CLI 工具
├── chat.db                 # 运行时数据库 (自动生成)
├── received_files/         # 接收文件目录 (自动生成)
├── .gitignore
└── README.md
```

## 快速开始

### 1. 启动服务端

```bash
cd "校园即时通信与文件传输系统"
python -m src.core.server
```

默认监听 `0.0.0.0:8888`，可通过命令行参数指定端口：

```bash
python -m src.core.server 9999
```

### 2. 启动客户端

```bash
python -m src.ui.login_window
```

### 3. 账号管理

```bash
# 列出所有用户
python scripts/manage_users.py list

# 添加用户
python scripts/manage_users.py add <用户名> <密码> [昵称]

# 删除用户
python scripts/manage_users.py del <用户名>

# 重置密码
python scripts/manage_users.py passwd <用户名> <新密码>
```

### 4. 打包为 EXE

```bash
# 打包服务端
python scripts/build_server.py

# 打包客户端
python scripts/build_client.py
```

打包产物输出到 `dist/` 目录。

## 功能特性

- 用户注册 / 登录 / 在线状态管理
- 在线用户列表实时更新
- 点对点私聊 (气泡式消息展示)
- 公共聊天室 (群聊)
- 文件传输 (Base64 编码，支持进度显示)
- 聊天历史记录查询
- 心跳保活与自动断线重连
- 密码 SHA256 哈希存储

## 提交前检查清单

1. 清理 `__pycache__/`、`*.pyc` 等编译缓存
2. 清理 `dist/`、`build/` 等打包产物
3. 清理 `.claude/`、`.vscode/`、`.idea/` 等 IDE 临时目录
4. 确认 `.gitignore` 已配置正确
5. 确认 `chat.db` 不包含敏感测试数据
6. 运行 `python -m unittest discover test/ -v` 确保测试通过