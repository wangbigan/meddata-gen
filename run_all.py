"""
医院信息系统测试数据库一键创建脚本

⚠  兼容入口：本脚本已重构为 `meddata_gen` 包的外壳。
推荐直接使用 CLI：``meddata-gen run-all``
"""
from __future__ import annotations

import sys

import psycopg2

from meddata_gen import config
from meddata_gen.config import DB_CONFIG
from meddata_gen.core import orchestrator


def main() -> None:
    print("\n" + "=" * 60)
    print("  医院信息系统测试数据库创建工具")
    print("  Hospital Information System Test Data Generator")
    print("=" * 60 + "\n")

    # 测试数据库连接
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print(f"[OK] 数据库连接成功: {DB_CONFIG['host']}:{DB_CONFIG['port']}\n")
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        sys.exit(1)

    o = orchestrator.Orchestrator(DB_CONFIG)

    # Phase 1–2: init
    print("=" * 60)
    print("Phase 1: 创建数据库")
    print("=" * 60)
    orchestrator.create_databases(DB_CONFIG)

    print("\n" + "=" * 60)
    print("Phase 2: 初始化表结构")
    print("=" * 60)
    for db in config.DATABASES:
        orchestrator.init_schema(DB_CONFIG, db)

    # Phase 3–9: generate
    o.run(orchestrator.all_modules())

    # Phase 10: verify
    print("\n" + "=" * 60)
    print("Phase 10: 数据质量验证")
    print("=" * 60)
    # 复用 CLI verify 逻辑
    from meddata_gen.cli import cmd_verify
    cmd_verify()

    print("=" * 60)
    print("  全部完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
