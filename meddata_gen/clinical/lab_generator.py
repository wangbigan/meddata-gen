"""疾病感知的检验值生成器。

根据疾病画像生成有医学意义的检验结果：
- 正常患者：结果在参考范围内，带生物学变异
- 患病患者：对应检验项有较高概率体现异常，且异常程度有分布
"""
from __future__ import annotations

import random
from typing import Optional, Tuple

from meddata_gen.clinical.disease_profiles import DiseaseProfile, LabAbnormality
from meddata_gen.seed_data import LAB_ITEMS


def generate_lab_value(
    item_code: str,
    disease_profile: Optional[DiseaseProfile] = None,
    severity: Optional[str] = None,
) -> Tuple[str, float, str]:
    """生成单个检验项的结果。

    返回: (result_value_str, result_num, abnormal_flag)
    """
    # 查找参考范围
    ref = _find_reference(item_code)
    if ref is None:
        # 未知项目，返回随机正常值
        return ("0.00", 0.0, "N")

    ref_low, ref_high = ref
    normal_mid = (ref_low + ref_high) / 2
    normal_range = ref_high - ref_low

    # 检查疾病画像
    abnormality = None
    if disease_profile and item_code in disease_profile.lab_abnormalities:
        abnormality = disease_profile.lab_abnormalities[item_code]

    if abnormality and random.random() < 0.85:
        # 生成异常值
        value = _compute_abnormal(ref_low, ref_high, abnormality)
        flag = _abnormal_flag(value, ref_low, ref_high, abnormality.direction)
    else:
        # 生成正常值（带生物学变异）
        value = _compute_normal(normal_mid, normal_range)
        flag = "N"

    # 格式化
    value_str = _format_value(value)
    return (value_str, round(value, 3), flag)


def _find_reference(item_code: str) -> Optional[Tuple[float, float]]:
    """在 LAB_ITEMS 中查找检验项的参考范围。"""
    for category in LAB_ITEMS.values():
        for item in category:
            if item[0] == item_code:
                return (float(item[3]), float(item[4]))
    return None


def _compute_normal(normal_mid: float, normal_range: float) -> float:
    """生成带生物学变异的正常值（高斯分布，95% 落在参考范围内）。"""
    value = random.gauss(normal_mid, normal_range / 6)
    # 软截断：允许少量落在参考范围边缘外
    value = max(normal_mid - normal_range * 0.8, min(normal_mid + normal_range * 0.8, value))
    return value


def _compute_abnormal(ref_low: float, ref_high: float, abnormality: LabAbnormality) -> float:
    """根据异常模式生成异常值。"""
    # 从 severity_dist 中按概率选择倍数
    weights = [w for w, _ in abnormality.severity_dist]
    multipliers = [m for _, m in abnormality.severity_dist]
    multiplier = random.choices(multipliers, weights=weights)[0]

    if abnormality.direction == "high":
        # 高于参考上限
        value = ref_high * multiplier
        # 加一些随机扰动
        value = value * random.uniform(0.9, 1.1)
    elif abnormality.direction == "low":
        # 低于参考下限
        value = ref_low / multiplier
        value = value * random.uniform(0.9, 1.1)
    else:
        # variable：随机高或低
        if random.random() < 0.5:
            value = ref_high * multiplier * random.uniform(0.9, 1.1)
        else:
            value = ref_low / multiplier * random.uniform(0.9, 1.1)

    return value


def _abnormal_flag(value: float, ref_low: float, ref_high: float, direction: str) -> str:
    """根据数值判断异常标志。"""
    if ref_low <= value <= ref_high:
        return "N"
    if value < ref_low:
        return "L"
    return "H"


def _format_value(value: float) -> str:
    """格式化数值为字符串。"""
    if abs(value) >= 100:
        return f"{value:.1f}"
    if abs(value) >= 1:
        return f"{value:.2f}"
    return f"{value:.3f}"
