"""PostgresWriter: 将缓冲数据批量写入 PostgreSQL。"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

import psycopg2

from meddata_gen.output.base import OutputWriter


class PostgresWriter(OutputWriter):
    """按数据库分批建立连接、批量插入。"""

    def __init__(self, db_config: dict, batch_size: int = 1000) -> None:
        self.db_config = db_config
        self.batch_size = batch_size
        # buffers: db_name -> [(table, columns, rows), ...]
        self._buffers: Dict[str, List[Tuple[str, List[str], List[tuple]]]] = defaultdict(list)

    def write_rows(
        self,
        system: str,
        table: str,
        columns: List[str],
        rows: List[tuple],
    ) -> None:
        """缓冲行数据，等待 finalize 时统一写入。"""
        if rows:
            self._buffers[system].append((table, columns, rows))

    def finalize(self) -> None:
        """按数据库分批写入所有缓冲数据。"""
        for db_name, tables in self._buffers.items():
            conn = None
            cur = None
            try:
                cfg = self.db_config.copy()
                cfg["database"] = db_name
                conn = psycopg2.connect(**cfg)
                conn.autocommit = False
                cur = conn.cursor()

                for table, columns, rows in tables:
                    self._write_table(cur, table, columns, rows)

                conn.commit()
                total_rows = sum(len(r) for _, _, r in tables)
                print(f"  [PostgresWriter] {db_name}: {total_rows} rows across {len(tables)} tables")
            except Exception as e:
                if conn:
                    conn.rollback()
                raise RuntimeError(f"写入 {db_name} 失败: {e}") from e
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()

        self._buffers.clear()

    def _write_table(
        self,
        cur,
        table: str,
        columns: List[str],
        rows: List[tuple],
    ) -> None:
        """对单表执行批量插入。"""
        if not rows:
            return
        placeholders = ",".join(["%s"] * len(columns))
        sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
        for i in range(0, len(rows), self.batch_size):
            batch = rows[i : i + self.batch_size]
            for idx, row in enumerate(batch):
                if len(row) != len(columns):
                    raise RuntimeError(
                        f"表 {table} 第 {idx} 行列数不匹配: "
                        f"期望 {len(columns)} 列, 实际 {len(row)} 列. "
                        f"columns={columns}, row={row}"
                    )
            cur.executemany(sql, batch)
