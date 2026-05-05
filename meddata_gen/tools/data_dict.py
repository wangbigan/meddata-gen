"""数据字典生成工具。

从 PostgreSQL 的 ``information_schema`` 与 ``pg_description`` 读取表/字段元数据，
渲染为 markdown 文档。
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Tuple

import psycopg2

from meddata_gen import config

# (column_name, data_type, is_nullable, character_maximum_length, numeric_precision, comment)
ColumnInfo = Tuple[str, str, str, object, object, str]


def _fetch_table_meta(conn) -> Dict[str, str]:
    """返回 {table_name: comment}。"""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            c.relname AS table_name,
            COALESCE(obj_description(c.oid, 'pg_class'), '') AS comment
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind = 'r'
          AND n.nspname = 'public'
          AND c.relname NOT LIKE 'pg_%'
        ORDER BY c.relname
        """
    )
    result = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    return result


def _fetch_columns(conn, table: str) -> List[ColumnInfo]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            a.attname AS column_name,
            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
            CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END AS is_nullable,
            a.attlen AS char_max_len,
            NULL AS numeric_precision,
            COALESCE(col_description(a.attrelid, a.attnum), '') AS comment
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = %s
          AND n.nspname = 'public'
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum
        """,
        (table,),
    )
    cols = cur.fetchall()
    cur.close()
    return cols


def _fetch_row_count(conn, table: str) -> int:
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0]
    except Exception:
        return -1
    finally:
        cur.close()


def _render_db_section(db_name: str, description: str, conn) -> str:
    """渲染单个数据库的 markdown 内容。"""
    lines: List[str] = []
    lines.append(f"## {db_name}")
    lines.append("")
    if description:
        lines.append(f"> {description}")
        lines.append("")

    tables = _fetch_table_meta(conn)
    if not tables:
        lines.append("_（无数据表）_")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"共 {len(tables)} 张表：")
    lines.append("")
    for tname in tables:
        rc = _fetch_row_count(conn, tname)
        rc_str = f"{rc:,}" if rc >= 0 else "?"
        lines.append(f"- [`{tname}`](#{db_name}-{tname}) — {tables[tname]}（{rc_str} 行）")
    lines.append("")

    for tname, tcomment in tables.items():
        anchor = f"{db_name}-{tname}"
        lines.append(f"### <a id=\"{anchor}\"></a>`{tname}`")
        lines.append("")
        if tcomment:
            lines.append(f"_{tcomment}_")
            lines.append("")

        cols = _fetch_columns(conn, tname)
        if not cols:
            lines.append("_（无字段）_")
            lines.append("")
            continue

        lines.append("| 字段 | 类型 | 可空 | 注释 |")
        lines.append("|------|------|------|------|")
        for cname, ctype, cnull, _maxlen, _prec, ccomment in cols:
            comment_md = ccomment.replace("\n", " ").replace("|", "\\|") if ccomment else ""
            lines.append(f"| `{cname}` | `{ctype}` | {cnull} | {comment_md} |")
        lines.append("")

    return "\n".join(lines)


def write_data_dictionary(db_config: dict, output_path: str) -> None:
    """生成并写入 markdown 数据字典。"""
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    sections: List[str] = []
    sections.append("# 医院信息系统数据字典")
    sections.append("")
    sections.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sections.append("")
    sections.append("## 概览")
    sections.append("")
    for db_name in config.DATABASES:
        desc = config.DATABASE_DESCRIPTIONS.get(db_name, "")
        sections.append(f"- [`{db_name}`](#{db_name}) — {desc}")
    sections.append("")
    sections.append("---")
    sections.append("")

    for db_name in config.DATABASES:
        desc = config.DATABASE_DESCRIPTIONS.get(db_name, "")
        cfg = db_config.copy()
        cfg["database"] = db_name
        try:
            conn = psycopg2.connect(**cfg)
        except Exception as e:
            sections.append(f"## {db_name}\n\n> _连接失败：{e}_\n")
            continue
        try:
            sections.append(_render_db_section(db_name, desc, conn))
        finally:
            conn.close()
        sections.append("---")
        sections.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sections))
