"""事件模型：MedicalEvent, EventContext, TimelineEngine。

所有事件驱动生成的基石。一个 MedicalEvent 代表医疗流程中的一个原子步骤，
JourneyBuilder 负责按临床逻辑编排事件序列，TimelineEngine 保证时间因果顺序。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class MedicalEvent:
    """医疗流程原子事件。"""

    event_type: str
    timestamp: datetime
    source_system: str
    patient_id: str
    visit_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: f"EV-{uuid.uuid4().hex[:12]}")
    parent_event_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def with_payload(self, **kwargs) -> "MedicalEvent":
        """返回携带额外 payload 的事件副本（不可变更新）。"""
        new_payload = dict(self.payload)
        new_payload.update(kwargs)
        return MedicalEvent(
            event_type=self.event_type,
            timestamp=self.timestamp,
            source_system=self.source_system,
            patient_id=self.patient_id,
            visit_id=self.visit_id,
            event_id=self.event_id,
            parent_event_id=self.parent_event_id,
            payload=new_payload,
        )


@dataclass
class EventContext:
    """单次患者就诊的上下文，贯穿整个旅程。"""

    # 患者信息
    patient_id: str
    patient_name: str
    gender: str
    birthday: datetime

    # 就诊信息
    visit_id: str
    visit_type: str  # "inpatient" | "outpatient"

    # 时间
    admission_time: Optional[datetime] = None
    discharge_time: Optional[datetime] = None
    visit_time: Optional[datetime] = None  # 门诊用

    # 医疗信息
    department_id: Optional[str] = None
    attending_doctor_id: Optional[str] = None
    primary_diagnosis: Optional[str] = None
    primary_icd: Optional[str] = None

    # 旅程状态
    disease_profile: Optional[Any] = None
    patient_health: Optional[Any] = None   # PatientHealthProfile
    generated_ids: Dict[str, str] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    visit_status: str = "visited"          # "visited" | "refunded" | "no_show" | "cancelled" | "absent"
    no_show_reason: Optional[str] = None

    # 字典缓存（由 EventDrivenGenerator 传入，供 handlers 抽样）
    dict_cache: Dict[str, list] = field(default_factory=dict)

    def record_id(self, key: str, value: str) -> None:
        """记录本次旅程生成的业务 ID（如 order_id -> lab_order_id）。"""
        self.generated_ids[key] = value

    def get_id(self, key: str) -> Optional[str]:
        """获取已记录的业务 ID。"""
        return self.generated_ids.get(key)


class TimelineEngine:
    """保证事件时间因果顺序的调度引擎。"""

    @staticmethod
    def schedule_after(
        parent_time: datetime,
        min_hours: float = 0.0,
        max_hours: float = 24.0,
    ) -> datetime:
        """在 parent_time 之后随机偏移 [min_hours, max_hours] 小时。"""
        import random

        offset_seconds = random.uniform(min_hours * 3600, max_hours * 3600)
        return parent_time + timedelta(seconds=offset_seconds)

    @staticmethod
    def schedule_within(
        start: datetime,
        end: datetime,
        min_hours_after_start: float = 0.0,
    ) -> datetime:
        """在 [start+min_hours, end] 区间内随机选择一个时间点。"""
        import random

        earliest = start + timedelta(hours=min_hours_after_start)
        if earliest >= end:
            return end
        span = (end - earliest).total_seconds()
        return earliest + timedelta(seconds=random.uniform(0, span))

    @staticmethod
    def schedule_daily(
        start: datetime,
        end: datetime,
        hour_range: tuple = (8, 18),
    ) -> List[datetime]:
        """在区间内每天生成一个时间点（用于每日病程、每日医嘱等）。"""
        import random

        days = []
        current = start.date()
        end_date = end.date()
        while current <= end_date:
            h = random.randint(*hour_range)
            m = random.randint(0, 59)
            dt = datetime.combine(current, datetime.min.time().replace(hour=h, minute=m))
            if start <= dt <= end:
                days.append(dt)
            current += timedelta(days=1)
        return days
