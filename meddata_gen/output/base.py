"""OutputWriter: 数据输出抽象基类。

所有输出格式（PostgreSQL、CSV、FHIR）都继承此基类，
Materializer 在 flush 时统一调用 writer 的方法。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple


class OutputWriter(ABC):
    """抽象输出写入器。

    生命周期:
        1. Materializer 在构建时传入 writer
        2. 每次 materialize() 把行数据缓冲到内存
        3. flush() 时 Materializer 调用 writer.write_rows() 逐表写入
        4. 最后调用 writer.finalize() 完成收尾（关闭连接、写文件等）
    """

    @abstractmethod
    def write_rows(
        self,
        system: str,
        table: str,
        columns: List[str],
        rows: List[tuple],
    ) -> None:
        """写入一批行数据。

        Args:
            system: 子系统/数据库名，如 "his_db", "lis_db"。
            table: 表名。
            columns: 列名列表。
            rows: 行数据列表，每个元素是一个 tuple。
        """
        ...

    @abstractmethod
    def finalize(self) -> None:
        """完成所有写入操作，释放资源。"""
        ...
