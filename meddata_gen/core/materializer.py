"""Materializer: 将事件序列转换为数据库行并批量写入。

设计要点:
- 事件处理器返回行数据，但不直接写入数据库
- Materializer 按 (database, table) 缓冲行数据
- 最后通过 OutputWriter 统一写入（PostgreSQL / CSV / FHIR 等）
- 与现有 7-database 架构完全兼容
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

from meddata_gen.core.events import EventContext, MedicalEvent
from meddata_gen.output.base import OutputWriter
from meddata_gen.output.postgres import PostgresWriter
from meddata_gen.quality.defect_engine import ScenarioDefectEngine


# 处理器签名: (event, ctx) -> 单个结果 或 结果列表
SingleResult = Tuple[str, str, List[str], List[tuple]]
EventHandler = Callable[
    [MedicalEvent, EventContext],
    Optional[SingleResult | List[SingleResult]],
]


class Materializer:
    """事件物化层：事件 → 行数据 → 批量入库。"""

    def __init__(
        self,
        writer: Optional[OutputWriter] = None,
        defect_engine: Optional[ScenarioDefectEngine] = None,
    ) -> None:
        # registry: (source_system, event_type) -> handler
        self._handlers: Dict[Tuple[str, str], EventHandler] = {}
        # buffers: (database, table) -> (columns, list_of_rows)
        self._buffers: Dict[Tuple[str, str], Tuple[List[str], List[tuple]]] = defaultdict(
            lambda: (None, [])
        )
        self.writer = writer
        self.defect_engine = defect_engine

    # ------------------------------------------------------------------
    # 注册
    # ------------------------------------------------------------------

    def register(self, source_system: str, event_type: str, handler: EventHandler) -> None:
        """为特定系统+事件类型注册处理器。"""
        self._handlers[(source_system, event_type)] = handler

    # ------------------------------------------------------------------
    # 物化
    # ------------------------------------------------------------------

    def materialize(self, events: List[MedicalEvent], ctx: EventContext) -> None:
        """遍历事件，分发到处理器，缓冲行数据。"""
        for event in events:
            handler = self._handlers.get((event.source_system, event.event_type))
            if handler is None:
                continue
            result = handler(event, ctx)
            if result is None:
                continue
            # 支持单个结果或结果列表
            results = result if isinstance(result, list) else [result]
            for db, table, columns, rows in results:
                self._append(db, table, columns, rows)

    def _append(self, db: str, table: str, columns: List[str], rows: List[tuple]) -> None:
        """将行数据追加到对应缓冲。"""
        if not rows:
            return
        key = (db, table)
        existing = self._buffers[key]
        if existing[0] is None:
            self._buffers[key] = (columns, list(rows))
        else:
            # 列名必须一致
            if existing[0] != columns:
                raise ValueError(
                    f"列名不一致 for {db}.{table}: "
                    f"已有 {existing[0]}, 新传入 {columns}"
                )
            existing[1].extend(rows)

    # ------------------------------------------------------------------
    # 写入
    # ------------------------------------------------------------------

    def flush(self, db_config: dict, batch_size: int = 1000) -> None:
        """将所有缓冲数据通过 OutputWriter 写入。

        兼容旧接口：若未传入 writer，则默认使用 PostgresWriter。
        """
        writer = self.writer
        if writer is None:
            writer = PostgresWriter(db_config, batch_size=batch_size)

        for (db, table), (columns, rows) in self._buffers.items():
            # 应用场景化缺陷注入
            if self.defect_engine is not None:
                rows = self._apply_defects(rows, columns, db, table)
            writer.write_rows(db, table, columns, rows)

        writer.finalize()

    def _apply_defects(
        self,
        rows: List[tuple],
        columns: List[str],
        db_name: str,
        table: str,
    ) -> List[tuple]:
        """对所有行应用缺陷引擎。"""
        from datetime import datetime

        # 启发式查找时间戳列（用于 time_range 过滤）
        time_idx = None
        for i, col in enumerate(columns):
            if "time" in col.lower():
                time_idx = i
                break

        result = []
        for row in rows:
            row_timestamp = None
            if time_idx is not None:
                ts = row[time_idx]
                if isinstance(ts, datetime):
                    row_timestamp = ts
            result.append(self.defect_engine.apply(row, columns, db_name, table, row_timestamp))
        return result

    def clear(self) -> None:
        """清空所有缓冲。"""
        self._buffers.clear()
