"""临床规则引擎：驱动所有基于规则的决策。

包括：
- 疾病选择（基础病 vs 新发疾病）
- 科室选择（按画像 vs 随机错误）
- 就诊率检查（实际就诊 / 退号 / 爽约 / 取消）
- 事件概率决策（检验/检查/开药/手术/ICU/ECG）
- 就诊类型选择（门诊/急诊/住院）
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from meddata_gen.clinical.disease_profiles import DiseaseProfile, DISEASE_PROFILES
from meddata_gen.clinical.patient_health import PatientHealthProfile


@dataclass
class RuleEngineConfig:
    """规则引擎全局配置。"""

    # 合理性阈值
    patient_disease_match_rate: float = 0.90      # 患者绑定合理疾病的比例
    encounter_department_match_rate: float = 0.95  # 就诊挂对科室的比例

    # 混合绑定模型
    base_disease_rate: float = 0.80               # 看基础病的比例
    new_disease_rate: float = 0.20                # 看新发疾病的比例

    # 就诊率
    outpatient_visit_rate: float = 0.92           # 门诊就诊率
    inpatient_admission_rate: float = 0.95        # 住院入院率

    # 退号/取消率（在未就诊/未入院的人中）
    outpatient_refund_rate: float = 0.70          # 未就诊门诊中退号的比例
    inpatient_cancel_rate: float = 0.60           # 未入院中取消的比例


class ClinicalRuleEngine:
    """临床规则引擎。"""

    def __init__(
        self,
        profiles: Optional[Dict[str, DiseaseProfile]] = None,
        config: Optional[RuleEngineConfig] = None,
    ) -> None:
        self.profiles = profiles if profiles is not None else DISEASE_PROFILES
        self.config = config if config is not None else RuleEngineConfig()

    # ------------------------------------------------------------------
    # 疾病选择
    # ------------------------------------------------------------------

    def select_encounter_disease(
        self,
        patient_health: PatientHealthProfile,
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
    ) -> Tuple[str, DiseaseProfile]:
        """为一次就诊选择诊断。80% 基础病，20% 随机新发疾病。

        新发疾病选择时会尽量匹配患者年龄和性别（如果提供），
        避免男性患者分配到妇科疾病等明显不合理场景。
        """
        if random.random() < self.config.base_disease_rate:
            return patient_health.primary_icd, patient_health.primary_profile

        # 新发疾病：优先选择符合患者画像的疾病
        if patient_age is not None and patient_gender is not None:
            from meddata_gen.clinical.disease_profiles import profiles_matching_patient
            matching = profiles_matching_patient(patient_age, patient_gender)
            if matching:
                profile = random.choice(matching)
                # 找到对应的 ICD 编码
                new_icd = next(
                    (code for code, p in self.profiles.items() if p is profile),
                    random.choice(list(self.profiles.keys())),
                )
                return new_icd, profile

        # 回退：完全随机
        new_icd = random.choice(list(self.profiles.keys()))
        return new_icd, self.profiles[new_icd]

    # ------------------------------------------------------------------
    # 科室选择
    # ------------------------------------------------------------------

    def select_department(
        self,
        profile: DiseaseProfile,
        visit_type: str,
        patient_gender: str,
        patient_age: int,
        departments: List[dict],
    ) -> str:
        """选择科室。95% 按疾病画像，5% 随机（模拟挂错号）。"""
        if random.random() < self.config.encounter_department_match_rate:
            if visit_type == "outpatient" and profile.outpatient_departments:
                candidates = profile.outpatient_departments
            else:
                candidates = profile.primary_departments
            # 过滤出实际存在的科室 ID
            valid = [
                d for d in candidates
                if any(dept.get("id") == d for dept in departments)
            ]
            if valid:
                return random.choice(valid)

        # 回退：随机选择符合条件的科室
        return self._pick_random_dept(visit_type, departments)

    def _pick_random_dept(self, visit_type: str, departments: List[dict]) -> str:
        """随机选择一个符合条件的科室。"""
        if visit_type == "outpatient":
            depts = [d["id"] for d in departments if d.get("outpatient") == "Y"]
        else:
            depts = [d["id"] for d in departments if d.get("ward") == "Y"]
        if depts:
            return random.choice(depts)
        # 最终回退
        return random.choice([d["id"] for d in departments])

    # ------------------------------------------------------------------
    # 就诊类型选择
    # ------------------------------------------------------------------

    def select_visit_type(self, profile: DiseaseProfile) -> str:
        """根据疾病画像决定就诊类型。"""
        r = random.random()
        if r < profile.emergency_prob:
            return "emergency"
        elif r < profile.emergency_prob + profile.outpatient_prob:
            return "outpatient"
        else:
            return "inpatient"

    # ------------------------------------------------------------------
    # 就诊率
    # ------------------------------------------------------------------

    def check_visit_rate(self, visit_type: str) -> Tuple[bool, Optional[str]]:
        """检查就诊率。

        返回: (是否实际就诊, 未就诊原因)
        未就诊原因: "refunded" | "no_show" | "cancelled" | "absent"
        """
        if visit_type == "outpatient":
            rate = self.config.outpatient_visit_rate
            refund_rate = self.config.outpatient_refund_rate
        else:
            rate = self.config.inpatient_admission_rate
            refund_rate = self.config.inpatient_cancel_rate

        if random.random() < rate:
            return True, None

        # 未就诊
        if random.random() < refund_rate:
            reason = "refunded" if visit_type == "outpatient" else "cancelled"
        else:
            reason = "no_show" if visit_type == "outpatient" else "absent"
        return False, reason

    # ------------------------------------------------------------------
    # 事件概率决策
    # ------------------------------------------------------------------

    def should_generate_event(
        self,
        event_type: str,
        profile: Optional[DiseaseProfile] = None,
    ) -> bool:
        """根据疾病画像决定是否生成某类医疗事件。"""
        if profile is None:
            return self._default_event_probability(event_type)

        prob_map = {
            "order_lab": profile.order_lab_prob,
            "order_imaging": profile.order_imaging_prob,
            "order_medication": profile.order_medication_prob,
            "surgery": profile.surgery_prob,
            "icu_admission": profile.icu_prob,
            "ecg_exam": profile.ecg_prob,
        }
        prob = prob_map.get(event_type, 0.5)
        return random.random() < prob

    def _default_event_probability(self, event_type: str) -> float:
        """默认事件概率（无疾病画像时回退）。"""
        defaults = {
            "order_lab": 0.95,
            "order_imaging": 0.40,
            "order_medication": 0.80,
            "surgery": 0.30,
            "icu_admission": 0.08,
            "ecg_exam": 0.05,
        }
        return defaults.get(event_type, 0.5)
