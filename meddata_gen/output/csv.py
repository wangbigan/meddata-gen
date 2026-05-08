"""CSVWriter: 将数据输出为 CSV 文件。"""
from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Tuple

from meddata_gen.output.base import OutputWriter


class CSVWriter(OutputWriter):
    """按 (system, table) 输出到 ``output_dir/{system}/{table}.csv``。"""

    def __init__(self, output_dir: str = "output/csv") -> None:
        self.output_dir = output_dir
        # buffers: (system, table) -> (columns, rows)
        self._buffers: Dict[Tuple[str, str], Tuple[List[str], List[tuple]]] = {}

    def write_rows(
        self,
        system: str,
        table: str,
        columns: List[str],
        rows: List[tuple],
    ) -> None:
        key = (system, table)
        if key not in self._buffers:
            self._buffers[key] = (columns, list(rows))
        else:
            existing_cols, existing_rows = self._buffers[key]
            if existing_cols != columns:
                raise ValueError(
                    f"列名不一致 for {system}.{table}: "
                    f"已有 {existing_cols}, 新传入 {columns}"
                )
            existing_rows.extend(rows)

    def finalize(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        for (system, table), (columns, rows) in self._buffers.items():
            if not rows:
                continue
            dir_path = os.path.join(self.output_dir, system)
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, f"{table}.csv")
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in rows:
                    writer.writerow(_serialize(row))
            print(f"  [CSVWriter] {system}.{table}: {len(rows)} rows -> {file_path}")
        self._buffers.clear()


def _serialize(row: tuple) -> list:
    """将 row tuple 中的非基本类型序列化为字符串。"""
    result = []
    for val in row:
        if val is None:
            result.append("")
        elif isinstance(val, (datetime, date)):
            result.append(val.isoformat())
        else:
            result.append(str(val))
    return result
