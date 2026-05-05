"""BaseGenerator: 数据库连接、状态保持、缺陷注入工具方法。

所有子系统 Mixin 共用本类提供的：
- 数据库连接 (connect/close/commit/rollback)
- SQL 文件执行
- 状态共享 (patients/inpatients/outpatients/staff/departments/drugs)
- 缺陷注入工具 (_should_null/_should_link/_format_inconsistent_date/_maybe_logic_error)
- 批量插入 (_batch_insert)
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional

import psycopg2

from meddata_gen import config


class BaseGenerator:
    """数据生成器基类——状态、连接、缺陷注入工具。"""

    def __init__(self, db_config: dict, seed: Optional[int] = None):
        self.db_config = db_config
        self.conn = None
        self.cur = None
        # 跨子系统共享的对象列表
        self.patients: List[dict] = []
        self.inpatients: List[dict] = []
        self.outpatients: List[dict] = []
        self.staff: List[dict] = []
        self.departments: List[dict] = []
        self.drugs: List[dict] = []
        self.diagnoses: List[dict] = []

        # 随机种子：None 表示不固定
        if seed is None:
            seed = getattr(config, "RANDOM_SEED", None)
        if seed is not None:
            random.seed(seed)
        self.seed = seed

    # ----- 连接管理 -----

    def connect(self, database: Optional[str] = None) -> "BaseGenerator":
        """连接到指定数据库；返回 self 以便链式调用。"""
        cfg = self.db_config.copy()
        if database:
            cfg["database"] = database
        self.conn = psycopg2.connect(**cfg)
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        return self

    def close(self) -> None:
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def commit(self) -> None:
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        if self.conn:
            self.conn.rollback()

    def execute_sql_file(self, filepath: str) -> None:
        """执行 SQL 文件（一次性 execute，依赖 PostgreSQL 多语句执行）。"""
        with open(filepath, "r", encoding="utf-8") as f:
            sql = f.read()
        self.cur.execute(sql)
        self.commit()

    # ----- 缺陷注入 -----

    def _null_rate(self, base_rate: float, system: str) -> float:
        adjust = config.QUALITY["system_null_adjust"].get(system, 0.05)
        rate = base_rate + adjust
        min_r, max_r = config.QUALITY["null_rate_range"]
        return max(min_r, min(max_r, rate))

    def _should_null(self, system: str, field_importance: str = "normal") -> bool:
        """按系统 + 字段重要性决定是否置空。"""
        importance_map = {"critical": 0.02, "normal": 0.05, "optional": 0.10}
        base = importance_map.get(field_importance, 0.05)
        rate = self._null_rate(base, system)
        return random.random() < rate

    def _should_link(self, system: str) -> bool:
        """按系统的关联率决定是否建立跨系统外联。"""
        link_rate = config.QUALITY["system_link_rate"].get(system, 0.85)
        return random.random() < link_rate

    def _format_inconsistent_date(self, dt: datetime) -> str:
        """按比例返回不一致格式日期，模拟脏数据。"""
        if random.random() < config.QUALITY["format_inconsistency_rate"]:
            formats = [
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M:%S",
                "%Y年%m月%d日 %H时%M分",
            ]
            fmt = random.choice(formats)
            return dt.strftime(fmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _maybe_logic_error(self, value, error_type: str = "date_swap"):
        """按比例返回错乱值——时间倒挂/负值/极端放大。"""
        if random.random() < config.QUALITY["logic_error_rate"]:
            if error_type == "date_swap" and isinstance(value, datetime):
                return value - timedelta(days=random.randint(1, 30))
            if error_type == "negative" and isinstance(value, (int, float)) and value > 0:
                return -abs(value)
            if error_type == "extreme" and isinstance(value, (int, float)):
                return value * random.choice([10, 100])
        return value

    # ----- 批量入库 -----

    def _batch_insert(
        self,
        table: str,
        columns: List[str],
        rows: List[tuple],
        batch_size: int = 1000,
    ) -> None:
        if not rows:
            return
        placeholders = ",".join(["%s"] * len(columns))
        sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            self.cur.executemany(sql, batch)
        self.commit()
