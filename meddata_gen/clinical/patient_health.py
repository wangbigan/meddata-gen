"""患者健康档案：将患者与疾病画像绑定。

生成患者池时，每个患者会被分配一个主病画像 + 0-N 个并发症画像，
用于后续就诊决策和临床数据生成。
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from meddata_gen.clinical.disease_profiles import (
    DiseaseProfile,
    DISEASE_PROFILES,
    profiles_matching_patient,
    random_profile_for_patient,
)


@dataclass
class PatientHealthProfile:
    """患者健康档案（规则引擎版）。"""

    patient_id: str
    primary_icd: str                     # 主病 ICD 编码
    primary_profile: DiseaseProfile      # 主病画像
    comorbidities: List[Tuple[str, DiseaseProfile]] = field(default_factory=list)
    is_reasonable: bool = True           # 是否符合画像（90% 合理 / 10% 异常）
    assigned_at: datetime = field(default_factory=datetime.now)

    def get_all_icds(self) -> List[str]:
        """返回主病 + 所有并发症的 ICD 编码列表。"""
        return [self.primary_icd] + [icd for icd, _ in self.comorbidities]

    def get_all_profiles(self) -> List[DiseaseProfile]:
        """返回主病 + 所有并发症的画像列表。"""
        return [self.primary_profile] + [p for _, p in self.comorbidities]


def assign_health_profile(
    patient: tuple,
    match_rate: float = 0.90,
) -> PatientHealthProfile:
    """为患者分配健康档案。

    1. 以 match_rate 概率选择符合患者画像约束的疾病
    2. 以 (1-match_rate) 概率随机选择疾病（模拟异常数据）
    3. 根据主病的 comorbidity_probs 随机抽取并发症
    """
    patient_id = patient[0]
    gender = patient[3] if len(patient) > 3 else "B"
    birthday = patient[4] if len(patient) > 4 else datetime(1980, 1, 1)

    # 计算年龄
    if isinstance(birthday, datetime):
        age = (datetime.now() - birthday).days // 365
    else:
        age = (datetime.now().date() - birthday).days // 365

    # 选择主病
    if random.random() < match_rate:
        primary = random_profile_for_patient(age, gender)
        is_reasonable = True
        if primary is None:
            # 回退：随机选择
            primary_icd = random.choice(list(DISEASE_PROFILES.keys()))
            primary = DISEASE_PROFILES[primary_icd]
            is_reasonable = False
        else:
            primary_icd = next(
                (code for code, p in DISEASE_PROFILES.items() if p is primary),
                list(DISEASE_PROFILES.keys())[0],
            )
    else:
        # 10% 异常：完全随机
        primary_icd = random.choice(list(DISEASE_PROFILES.keys()))
        primary = DISEASE_PROFILES[primary_icd]
        is_reasonable = False

    # 抽取并发症
    comorbidities: List[Tuple[str, DiseaseProfile]] = []
    for icd, prob in primary.comorbidity_probs.items():
        if random.random() < prob:
            profile = DISEASE_PROFILES.get(icd)
            if profile:
                comorbidities.append((icd, profile))

    return PatientHealthProfile(
        patient_id=patient_id,
        primary_icd=primary_icd,
        primary_profile=primary,
        comorbidities=comorbidities,
        is_reasonable=is_reasonable,
    )


# 全局患者健康档案缓存（由 EventDrivenGenerator 填充）
PATIENT_HEALTH_MAP: Dict[str, PatientHealthProfile] = {}


def get_patient_health(patient_id: str) -> Optional[PatientHealthProfile]:
    """获取指定患者的健康档案。"""
    return PATIENT_HEALTH_MAP.get(patient_id)
