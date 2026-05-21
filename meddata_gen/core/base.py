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
from meddata_gen.dict_io.schemas import DICT_TABLES


# 字典表 → 回退 seed_data 常量的映射（字典为空时的兜底）
_FALLBACK_SEED = {
    "diagnosis_dict": "ICD10_DIAGNOSES",
    "surgery_dict": None,       # 无对应常量，需内置
    "order_items_dict": None,
    "charge_items_dict": None,
    "lab_items_dict": "LAB_ITEMS",
    "organism_dict": "MICRO_ORGANISMS",
    "antibiotic_dict": "ANTIBIOTICS",
    "exam_items_dict": "RIS_EXAM_TYPES",
}


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
        self._dict_cache: dict = {}  # {table_name: [rows]}

        # 随机种子：None 表示不固定
        if seed is None:
            seed = getattr(config, "RANDOM_SEED", None)
        if seed is not None:
            random.seed(seed)
        self.seed = seed

    # ----- 连接管理 -----

    def connect(self, database: Optional[str] = None) -> "BaseGenerator":
        """连接到指定数据库；返回 self 以便链式调用。"""
        import time
        t0 = time.perf_counter()
        cfg = self.db_config.copy()
        if database:
            cfg["database"] = database
        self.conn = psycopg2.connect(**cfg)
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"      [计时-Base] psycopg2.connect('{database or cfg.get('database')}'): {elapsed:.1f} ms")
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
        import time
        t0 = time.perf_counter()
        with open(filepath, "r", encoding="utf-8") as f:
            sql = f.read()
        t1 = time.perf_counter()
        self.cur.execute(sql)
        t2 = time.perf_counter()
        self.commit()
        t3 = time.perf_counter()
        print(f"      [计时-Base] 读取 SQL 文件: {(t1 - t0) * 1000:.1f} ms")
        print(f"      [计时-Base] 执行 SQL: {(t2 - t1) * 1000:.1f} ms")
        print(f"      [计时-Base] commit: {(t3 - t2) * 1000:.1f} ms")

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

    # ----- 字典缓存 -----

    def _load_dict_cache(self) -> None:
        """从各数据库字典表加载数据到内存缓存。

        若字典表不存在或为空，则尝试回退到 seed_data.py 常量（向后兼容）。
        在 ``generate`` 或 ``run`` 调用前执行一次即可。
        """
        if self._dict_cache:
            return  # 已加载，跳过

        # 先尝试从数据库读取
        for table in DICT_TABLES:
            db_name = table.database
            try:
                # 复用已有连接或新建
                if self.conn is None or self.conn.closed:
                    self.connect(db_name)
                else:
                    # 切换数据库需要重连
                    self.close()
                    self.connect(db_name)
                self.cur.execute(
                    "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public' AND tablename=%s",
                    (table.name,),
                )
                if self.cur.fetchone()[0] == 0:
                    continue
                self.cur.execute(f"SELECT * FROM {table.name}")
                rows = self.cur.fetchall()
                if rows:
                    self._dict_cache[table.name] = rows
            except Exception:
                pass  # 表不存在或连接失败，继续尝试回退

        # 回退：用 seed_data 常量填充未加载的字典
        from meddata_gen import seed_data as sd

        for table in DICT_TABLES:
            if table.name in self._dict_cache:
                continue
            fallback = _FALLBACK_SEED.get(table.name)
            if fallback is None:
                continue
            raw = getattr(sd, fallback, None)
            if raw is None:
                continue
            # 统一转换为 tuple list，顺序与 schema 对齐
            self._dict_cache[table.name] = self._normalize_seed(table.name, raw)

    def _normalize_seed(self, table_name: str, raw_data) -> list:
        """将 seed_data 常量规范化成与字典表列顺序一致的 tuple 列表。"""
        rows: list = []
        if table_name == "diagnosis_dict":
            # raw: [(code, name), ...]
            for code, name in raw_data:
                rows.append((code, name, None, None, None))
        elif table_name == "lab_items_dict":
            # raw: {"routine": [(code,name,unit,low,high), ...], ...}
            for category, items in raw_data.items():
                for item in items:
                    code, name, unit, ref_low, ref_high = item
                    rows.append((
                        code, name, category, None, unit,
                        float(ref_low) if ref_low else None,
                        float(ref_high) if ref_high else None,
                        None, None,
                    ))
        elif table_name == "organism_dict":
            # raw: [(code, name), ...]
            for code, name in raw_data:
                rows.append((code, name, None, None))
        elif table_name == "antibiotic_dict":
            # raw: [(code, name), ...]
            for code, name in raw_data:
                rows.append((code, name, None))
        elif table_name == "exam_items_dict":
            # raw: {"X光": [name, ...], ...}
            idx = 1
            for modality, items in raw_data.items():
                for name in items:
                    rows.append((
                        f"EX{idx:03d}", name, modality, None, None, None, None,
                    ))
                    idx += 1
        return rows

    def _sample_dict(self, table_name: str, count: int = 1):
        """从指定字典缓存中随机抽样。返回 tuple 或 tuple 列表。"""
        cache = self._dict_cache.get(table_name, [])
        if not cache:
            return None
        if count == 1:
            return random.choice(cache)
        return [random.choice(cache) for _ in range(count)]

    def _sample_dict_by_filter(self, table_name: str, col_idx: int, value):
        """按指定列值过滤后随机抽样。"""
        cache = self._dict_cache.get(table_name, [])
        filtered = [r for r in cache if len(r) > col_idx and r[col_idx] == value]
        if not filtered:
            return self._sample_dict(table_name)
        return random.choice(filtered)

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
