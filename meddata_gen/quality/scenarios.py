"""缺陷场景定义：模拟真实业务根因导致的数据质量问题。

与均匀随机缺陷不同，场景化缺陷模拟的是有明确业务根因的数据问题：
- 系统升级期间某字段批量缺失
- 接口切换导致外键映射错误
- 时钟漂移导致时间错乱
- 模板复制粘贴导致内容重复
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DefectScenario:
    """单个缺陷场景定义。"""

    name: str
    target_systems: List[str]      # e.g. ["lis_db", "his_db"]
    target_tables: List[str]       # e.g. ["microbiology", "lab_orders"]
    target_fields: List[str]       # e.g. ["culture_result", "patient_id"]
    defect_type: str               # "null" | "foreign_key_mismatch" | "format_error" | "logic_error" | "duplicate"
    rate: float                    # 0.0 ~ 1.0
    time_range: Optional[tuple] = None   # (start_iso, end_iso) — 可选
    event_filter: Optional[str] = None   # 可选的事件类型过滤
    description: str = ""


# ------------------------------------------------------------------
# 预定义缺陷场景
# ------------------------------------------------------------------

PREDEFINED_SCENARIOS = [
    DefectScenario(
        name="LIS 系统升级 outage",
        target_systems=["lis_db"],
        target_tables=["microbiology"],
        target_fields=["culture_result", "bacteria_name"],
        defect_type="null",
        rate=0.95,
        time_range=("2023-06-01", "2023-06-15"),
        description="2023年6月LIS系统升级期间，微生物培养结果字段批量为空",
    ),
    DefectScenario(
        name="RIS-HIS 接口切换映射错误",
        target_systems=["ris_db"],
        target_tables=["exam_orders"],
        target_fields=["patient_id"],
        defect_type="foreign_key_mismatch",
        rate=0.05,
        time_range=("2024-01-01", "2024-01-31"),
        description="2024年1月RIS与HIS接口切换，导致5%检查申请patient_id映射错误",
    ),
    DefectScenario(
        name="ICU 监护仪时钟漂移",
        target_systems=["icu_monitoring_db"],
        target_tables=["monitoring_data"],
        target_fields=["monitor_time"],
        defect_type="logic_error",
        rate=0.15,
        time_range=("2023-08-01", "2023-08-15"),
        description="2023年8月ICU部分监护仪时钟漂移，导致monitor_time时间错乱",
    ),
    DefectScenario(
        name="EMR 模板复制粘贴重复",
        target_systems=["emr_db"],
        target_tables=["progress_notes"],
        target_fields=["content"],
        defect_type="duplicate",
        rate=0.03,
        description="EMR病程记录因模板复制粘贴导致内容批量重复",
    ),
    DefectScenario(
        name="HIS 收费接口延迟",
        target_systems=["his_db"],
        target_tables=["fee_items"],
        target_fields=["fee_time"],
        defect_type="logic_error",
        rate=0.08,
        time_range=("2023-03-01", "2023-03-10"),
        description="2023年3月HIS收费接口延迟，部分fee_time晚于实际发生时间",
    ),
]


DEFAULT_SCENARIOS = PREDEFINED_SCENARIOS
