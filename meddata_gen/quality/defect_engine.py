"""ScenarioDefectEngine: 按场景规则注入数据质量缺陷。

在 Materializer 写库前调用，遍历所有激活的场景，匹配则对行数据应用缺陷。
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from meddata_gen.quality.scenarios import DefectScenario


class ScenarioDefectEngine:
    """基于场景的缺陷注入引擎。"""

    def __init__(self, scenarios: Optional[List[DefectScenario]] = None) -> None:
        self.scenarios = scenarios or []

    def apply(
        self,
        row: tuple,
        columns: List[str],
        system: str,
        table: str,
        # timestamp 可选：如果传入，则用于 time_range 过滤
        row_timestamp: Optional[datetime] = None,
    ) -> tuple:
        """对单行数据应用所有匹配的场景缺陷。

        返回修改后的 row tuple。
        """
        row_list = list(row)
        modified = False

        for scenario in self.scenarios:
            if not self._scenario_matches(scenario, system, table, row_timestamp):
                continue

            # 按 rate 决定是否对该行应用缺陷
            if random.random() >= scenario.rate:
                continue

            # 对 target_fields 中的每个字段应用缺陷
            for field_name in scenario.target_fields:
                if field_name not in columns:
                    continue
                idx = columns.index(field_name)
                original = row_list[idx]
                defect_value = self._create_defect(original, scenario.defect_type)
                if defect_value != original:
                    row_list[idx] = defect_value
                    modified = True

        return tuple(row_list) if modified else row

    @staticmethod
    def _scenario_matches(
        scenario: DefectScenario,
        system: str,
        table: str,
        row_timestamp: Optional[datetime],
    ) -> bool:
        """检查场景是否匹配当前行。"""
        # system 匹配
        if system not in scenario.target_systems:
            return False

        # table 匹配
        if table not in scenario.target_tables:
            return False

        # time_range 匹配（如果有）
        if scenario.time_range and row_timestamp is not None:
            start = datetime.fromisoformat(scenario.time_range[0])
            end = datetime.fromisoformat(scenario.time_range[1])
            # 将 end 扩展到当天结束
            end = end + timedelta(days=1)
            if not (start <= row_timestamp <= end):
                return False

        return True

    @staticmethod
    def _create_defect(original, defect_type: str):
        """根据缺陷类型生成缺陷值。"""
        if original is None:
            return original

        if defect_type == "null":
            return None

        if defect_type == "foreign_key_mismatch":
            if isinstance(original, str) and original.startswith("P"):
                # 生成一个不存在的 patient_id
                return f"P{random.randint(900000, 999999):06d}"
            return f"UNKNOWN_{random.randint(10000, 99999)}"

        if defect_type == "format_error":
            if isinstance(original, datetime):
                # 返回不一致的日期格式字符串
                fmt = random.choice([
                    "%Y/%m/%d %H:%M:%S",
                    "%d/%m/%Y %H:%M:%S",
                    "%Y年%m月%d日 %H时%M分",
                ])
                return original.strftime(fmt)
            if isinstance(original, str):
                # 大小写混用
                return original.swapcase()
            return original

        if defect_type == "logic_error":
            if isinstance(original, datetime):
                # 时间倒挂：减去 1-30 天
                return original - timedelta(days=random.randint(1, 30))
            if isinstance(original, (int, float)) and original > 0:
                # 负值
                return -abs(original)
            return original

        if defect_type == "duplicate":
            if isinstance(original, str):
                # 返回原值的重复或截断版本
                if random.random() < 0.5:
                    return original + " " + original
                return original[: len(original) // 2] + "..."
            return original

        return original
