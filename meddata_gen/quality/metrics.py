"""质量指标数据结构。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QualityMetric:
    """单个质量指标。"""

    name: str
    category: str                    # statistical / temporal / linkage / clinical / defect
    value: Any
    unit: str = ""
    threshold: Optional[float] = None
    passed: Optional[bool] = None
    details: Dict[str, Any] = field(default_factory=dict)
