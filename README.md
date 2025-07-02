# 数据库管理工具

本项目是一款基于 Python 3 和 PyQt5 开发的跨平台数据库管理工具，支持 MySQL、PostgreSQL、SQLite、Redis 等多种数据库的远程连接与管理，具备数据查询、结构管理、可视化分析等功能。

## 主要功能

- 多数据库类型支持（MySQL、PostgreSQL、SQLite、Redis 等）
- 远程连接与本地导入
- 数据库对象浏览与管理
- 数据增删改查与 SQL 编辑器
- 数据可视化与基础分析
- 连接信息加密存储
- 插件扩展机制

## 技术栈

- Python 3.x
- PyQt5（桌面图形界面）
- PyMySQL、psycopg2、sqlite3、redis-py（数据库驱动）
- matplotlib、PyQtGraph、pyecharts（可视化）

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 运行主程序：
   ```bash
   python src/main.py
   ```

## 目录结构

- docs/ 文档
- src/ 源代码
- tests/ 测试代码

## 许可证

MIT License
