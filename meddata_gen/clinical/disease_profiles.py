"""疾病画像定义：诊断驱动的医学一致性模型。

每个 DiseaseProfile 描述一种疾病在数据生成中的典型表现，包括：
- 患者画像约束（年龄范围、性别）
- 关联 ICD-10 编码
- 典型科室（住院/门诊）
- 医疗行为概率（检验/检查/开药/手术/ICU/ECG）
- 异常检验项及分布
- 典型用药、影像、手术
- 住院天数分布
- 预后概率
- 并发症概率映射

版本 2.0：新增规则引擎支持字段。
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ------------------------------------------------------------------
# 辅助类型
# ------------------------------------------------------------------

@dataclass
class LabAbnormality:
    """检验项异常模式。"""

    item_code: str  # LAB_ITEMS 中的 code，如 "WBC"
    direction: str  # "high" | "low" | "variable"
    # (概率, 相对于参考上限/下限的倍数分布)
    severity_dist: List[Tuple[float, float]] = field(default_factory=list)


# ------------------------------------------------------------------
# 疾病画像
# ------------------------------------------------------------------

@dataclass
class DiseaseProfile:
    """疾病临床画像（规则引擎版）。"""

    name: str
    icd10_codes: List[str]

    # --- 患者画像约束 ---
    age_range: Tuple[Optional[int], Optional[int]] = (0, None)  # (min, max), None = 无限制
    gender: str = "B"  # "M" | "F" | "B" (both)
    age_distribution: str = "uniform"  # "uniform" | "normal" | "skewed_young" | "skewed_old"

    # --- 科室映射 ---
    primary_departments: List[str] = field(default_factory=list)  # 住院主科室
    outpatient_departments: List[str] = field(default_factory=list)  # 门诊科室（空则默认同住院）

    # --- 医疗行为概率 (0.0 ~ 1.0) ---
    order_lab_prob: float = 0.95
    order_imaging_prob: float = 0.40
    order_medication_prob: float = 0.80
    surgery_prob: float = 0.0
    icu_prob: float = 0.0
    ecg_prob: float = 0.05
    outpatient_prob: float = 0.50  # 该疾病以门诊为主的比例（vs 住院）
    emergency_prob: float = 0.0  # 急诊就诊比例

    # --- 并发症：{disease_icd_prefix: probability} ---
    comorbidity_probs: Dict[str, float] = field(default_factory=dict)

    # --- 保留现有字段 ---
    lab_abnormalities: Dict[str, LabAbnormality] = field(default_factory=dict)
    typical_medications: Dict[str, List[str]] = field(default_factory=dict)
    typical_imaging: List[str] = field(default_factory=list)
    typical_surgeries: List[str] = field(default_factory=list)
    los_distribution: List[Tuple[int, float]] = field(
        default_factory=lambda: [(3, 20), (5, 30), (7, 25), (10, 15), (14, 10)]
    )
    outcome_probs: Dict[str, float] = field(
        default_factory=lambda: {"治愈": 0.50, "好转": 0.35, "未愈": 0.10, "死亡": 0.05}
    )

    def matches_patient(self, age: int, gender: str) -> bool:
        """检查患者（年龄+性别）是否符合该疾病画像。"""
        min_age, max_age = self.age_range
        if min_age is not None and age < min_age:
            return False
        if max_age is not None and age > max_age:
            return False
        if self.gender != "B" and gender != self.gender:
            return False
        return True

    def get_outpatient_depts(self) -> List[str]:
        """返回门诊科室，若未单独定义则回退到住院科室。"""
        return self.outpatient_departments if self.outpatient_departments else self.primary_departments

    def get_visit_type_probs(self) -> Tuple[float, float, float]:
        """返回 (emergency_prob, outpatient_prob, inpatient_prob) 三元组，保证和为1.0。"""
        e = self.emergency_prob
        o = self.outpatient_prob
        i = max(0.0, 1.0 - e - o)
        return e, o, i


# ==================================================================
# 疾病画像定义（按科室分组）
# ==================================================================

# ------------------------------------------------------------------
# 1. 心血管内科
# ------------------------------------------------------------------

HYPERTENSION = DiseaseProfile(
    name="原发性高血压",
    icd10_codes=["I10"],
    age_range=(35, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT001"],
    order_lab_prob=0.80,
    order_imaging_prob=0.30,
    order_medication_prob=0.95,
    surgery_prob=0.0,
    icu_prob=0.01,
    ecg_prob=0.15,
    outpatient_prob=0.90,
    emergency_prob=0.05,
    comorbidity_probs={
        "E11": 0.30,
        "E78": 0.25,
        "I25": 0.20,
        "N18": 0.15,
        "E05": 0.08,
    },
    lab_abnormalities={
        "GLU": LabAbnormality("GLU", "high", [(0.3, 1.2), (0.2, 1.5)]),
        "TC": LabAbnormality("TC", "high", [(0.3, 1.2), (0.25, 1.4)]),
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.4, 1.3), (0.3, 1.5)]),
        "TG": LabAbnormality("TG", "high", [(0.3, 1.5), (0.2, 2.0)]),
        "CREA": LabAbnormality("CREA", "high", [(0.1, 1.3), (0.05, 1.5)]),
    },
    typical_medications={
        "降压": ["氨氯地平片", "缬沙坦胶囊", "美托洛尔片", "贝那普利片", "厄贝沙坦片"],
        "调脂": ["阿托伐他汀钙片", "瑞舒伐他汀钙片"],
    },
    typical_imaging=["心脏彩超", "颈动脉超声", "眼底照相"],
    los_distribution=[(1, 5), (3, 15), (5, 30), (7, 30), (10, 15), (14, 5)],
)

HYPERTENSIVE_HEART_DISEASE = DiseaseProfile(
    name="高血压性心脏病",
    icd10_codes=["I11"],
    age_range=(50, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT001"],
    order_lab_prob=0.85,
    order_imaging_prob=0.50,
    order_medication_prob=0.95,
    surgery_prob=0.0,
    icu_prob=0.03,
    ecg_prob=0.50,
    outpatient_prob=0.70,
    emergency_prob=0.15,
    comorbidity_probs={
        "I10": 0.90,
        "E11": 0.35,
        "I50": 0.25,
        "N18": 0.20,
    },
    lab_abnormalities={
        "BNP": LabAbnormality("BNP", "high", [(0.4, 2.0), (0.3, 3.0), (0.2, 5.0)]),
        "NT-proBNP": LabAbnormality("NT-proBNP", "high", [(0.4, 2.0), (0.3, 3.0)]),
        "CREA": LabAbnormality("CREA", "high", [(0.15, 1.3), (0.1, 1.5)]),
    },
    typical_medications={
        "降压": ["氨氯地平片", "缬沙坦胶囊", "美托洛尔片"],
        "利尿": ["呋塞米片", "螺内酯片"],
    },
    typical_imaging=["心脏彩超", "胸部X线正侧位"],
)

ANGINA_PECTORIS = DiseaseProfile(
    name="心绞痛",
    icd10_codes=["I20"],
    age_range=(40, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT001"],
    order_lab_prob=0.90,
    order_imaging_prob=0.50,
    order_medication_prob=0.95,
    surgery_prob=0.15,
    icu_prob=0.05,
    ecg_prob=0.60,
    outpatient_prob=0.75,
    emergency_prob=0.15,
    comorbidity_probs={
        "I10": 0.50,
        "E11": 0.25,
        "E78": 0.30,
        "I25": 0.20,
    },
    lab_abnormalities={
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.4, 1.3), (0.3, 1.6)]),
        "TC": LabAbnormality("TC", "high", [(0.35, 1.2), (0.25, 1.5)]),
        "TG": LabAbnormality("TG", "high", [(0.3, 1.5), (0.2, 2.0)]),
        "GLU": LabAbnormality("GLU", "high", [(0.25, 1.2), (0.15, 1.5)]),
    },
    typical_medications={
        "抗血小板": ["阿司匹林肠溶片", "硫酸氢氯吡格雷片"],
        "调脂": ["阿托伐他汀钙片"],
        "扩冠": ["硝酸异山梨酯片", "单硝酸异山梨酯缓释片"],
        "降压": ["美托洛尔片", "氨氯地平片"],
    },
    typical_imaging=["冠状动脉CTA", "心脏彩超"],
    typical_surgeries=["经皮冠状动脉介入治疗"],
)

ACUTE_MYOCARDIAL_INFARCTION = DiseaseProfile(
    name="急性心肌梗死",
    icd10_codes=["I21.0", "I21.1", "I21.2", "I21.3", "I21.4"],
    age_range=(45, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT001", "DEPT029"],
    order_lab_prob=0.98,
    order_imaging_prob=0.70,
    order_medication_prob=0.98,
    surgery_prob=0.40,
    icu_prob=0.25,
    ecg_prob=0.90,
    outpatient_prob=0.02,
    emergency_prob=0.90,
    comorbidity_probs={
        "I10": 0.40,
        "E11": 0.30,
        "E78": 0.35,
        "I50": 0.15,
        "N18": 0.10,
    },
    lab_abnormalities={
        "CK-MB": LabAbnormality("CK-MB", "high", [(0.3, 2.0), (0.4, 3.0), (0.2, 5.0), (0.1, 8.0)]),
        "CK": LabAbnormality("CK", "high", [(0.3, 2.0), (0.4, 3.0), (0.2, 5.0), (0.1, 10.0)]),
        "LDH": LabAbnormality("LDH", "high", [(0.4, 1.5), (0.35, 2.0), (0.2, 3.0), (0.05, 4.0)]),
        "AST": LabAbnormality("AST", "high", [(0.4, 1.8), (0.35, 2.5), (0.2, 4.0), (0.05, 6.0)]),
        "Troponin": LabAbnormality("Troponin", "high", [(0.5, 5.0), (0.3, 10.0), (0.2, 20.0)]),
    },
    typical_medications={
        "抗血小板": ["阿司匹林肠溶片", "氯吡格雷片", "替格瑞洛片"],
        "调脂": ["阿托伐他汀钙片", "瑞舒伐他汀钙片"],
        "降压": ["美托洛尔片", "贝那普利片"],
        "扩冠": ["硝酸异山梨酯片"],
    },
    typical_imaging=["冠状动脉CTA", "心脏彩超", "胸部X线正侧位"],
    typical_surgeries=["经皮冠状动脉介入治疗", "冠状动脉搭桥术"],
    los_distribution=[(3, 10), (5, 20), (7, 30), (10, 20), (14, 15), (21, 5)],
    outcome_probs={"治愈": 0.50, "好转": 0.35, "未愈": 0.10, "死亡": 0.05},
)

CHRONIC_ISCHEMIC_HEART_DISEASE = DiseaseProfile(
    name="慢性缺血性心脏病",
    icd10_codes=["I25"],
    age_range=(50, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT001"],
    order_lab_prob=0.85,
    order_imaging_prob=0.50,
    order_medication_prob=0.95,
    surgery_prob=0.20,
    icu_prob=0.03,
    ecg_prob=0.40,
    outpatient_prob=0.80,
    emergency_prob=0.08,
    comorbidity_probs={
        "I10": 0.55,
        "I20": 0.30,
        "E11": 0.25,
        "E78": 0.35,
    },
    typical_medications={
        "抗血小板": ["阿司匹林肠溶片"],
        "调脂": ["阿托伐他汀钙片"],
        "扩冠": ["硝酸异山梨酯片"],
    },
    typical_imaging=["冠状动脉CTA", "心脏彩超"],
    typical_surgeries=["经皮冠状动脉介入治疗", "冠状动脉搭桥术"],
)

HEART_FAILURE = DiseaseProfile(
    name="心力衰竭",
    icd10_codes=["I50"],
    age_range=(55, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT001"],
    order_lab_prob=0.95,
    order_imaging_prob=0.60,
    order_medication_prob=0.95,
    surgery_prob=0.05,
    icu_prob=0.15,
    ecg_prob=0.60,
    outpatient_prob=0.50,
    emergency_prob=0.30,
    comorbidity_probs={
        "I10": 0.50,
        "I25": 0.35,
        "E11": 0.25,
        "N18": 0.20,
    },
    lab_abnormalities={
        "BNP": LabAbnormality("BNP", "high", [(0.5, 3.0), (0.3, 5.0), (0.2, 10.0)]),
        "CREA": LabAbnormality("CREA", "high", [(0.2, 1.3), (0.1, 1.6)]),
        "K": LabAbnormality("K", "high", [(0.15, 1.2), (0.1, 1.5)]),
    },
    typical_medications={
        "利尿": ["呋塞米片", "螺内酯片"],
        "降压": ["美托洛尔片", "缬沙坦胶囊"],
        "强心": ["地高辛片"],
    },
    typical_imaging=["心脏彩超", "胸部X线正侧位"],
    los_distribution=[(5, 15), (7, 25), (10, 30), (14, 20), (21, 10)],
)

ATRIAL_FIBRILLATION = DiseaseProfile(
    name="心房颤动",
    icd10_codes=["I48"],
    age_range=(50, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT001"],
    order_lab_prob=0.85,
    order_imaging_prob=0.40,
    order_medication_prob=0.90,
    surgery_prob=0.10,
    icu_prob=0.03,
    ecg_prob=0.95,
    outpatient_prob=0.80,
    emergency_prob=0.12,
    comorbidity_probs={
        "I10": 0.45,
        "I25": 0.20,
        "E11": 0.20,
    },
    typical_medications={
        "抗凝": ["华法林钠片", "利伐沙班片"],
        "控制心室率": ["美托洛尔片", "地高辛片"],
    },
    typical_imaging=["心脏彩超", "胸部X线正侧位"],
    typical_surgeries=["射频消融术"],
)

# ------------------------------------------------------------------
# 2. 呼吸内科
# ------------------------------------------------------------------

ACUTE_UPPER_RESPIRATORY_INFECTION = DiseaseProfile(
    name="急性上呼吸道感染",
    icd10_codes=["J06"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT002"],
    order_lab_prob=0.40,
    order_imaging_prob=0.10,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.01,
    outpatient_prob=0.95,
    emergency_prob=0.03,
    comorbidity_probs={
        "J18": 0.05,
        "J45": 0.10,
    },
    typical_medications={
        "解热镇痛": ["对乙酰氨基酚片", "布洛芬缓释胶囊"],
        "抗组胺": ["氯雷他定片"],
    },
    los_distribution=[(1, 50), (2, 30), (3, 15), (5, 5)],
)

COMMUNITY_ACQUIRED_PNEUMONIA = DiseaseProfile(
    name="社区获得性肺炎",
    icd10_codes=["J18.9", "J15.9", "J12.9"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT002", "DEPT010"],
    order_lab_prob=0.95,
    order_imaging_prob=0.90,
    order_medication_prob=0.95,
    surgery_prob=0.0,
    icu_prob=0.05,
    ecg_prob=0.05,
    outpatient_prob=0.20,
    emergency_prob=0.30,
    comorbidity_probs={
        "I10": 0.25,
        "E11": 0.15,
        "J44": 0.20,
        "E78": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.4, 1.5), (0.35, 2.0), (0.2, 3.0), (0.05, 4.0)]),
        "NEUT%": LabAbnormality("NEUT%", "high", [(0.5, 1.2), (0.3, 1.5), (0.15, 1.8), (0.05, 2.0)]),
        "PLT": LabAbnormality("PLT", "high", [(0.3, 1.1), (0.2, 1.3)]),
        "CRP": LabAbnormality("CRP", "high", [(0.5, 3.0), (0.3, 5.0), (0.2, 10.0)]),
        "PCT": LabAbnormality("PCT", "high", [(0.4, 2.0), (0.3, 5.0), (0.2, 10.0)]),
    },
    typical_medications={
        "抗菌药物": ["头孢曲松", "头孢噻肟", "左氧氟沙星", "莫西沙星"],
        "化痰": ["氨溴索", "乙酰半胱氨酸"],
    },
    typical_imaging=["胸部CT平扫", "胸部X线正侧位"],
    los_distribution=[(3, 10), (5, 20), (7, 25), (10, 20), (14, 15), (21, 10)],
    outcome_probs={"治愈": 0.60, "好转": 0.30, "未愈": 0.07, "死亡": 0.03},
)

COPD = DiseaseProfile(
    name="慢性阻塞性肺疾病",
    icd10_codes=["J44"],
    age_range=(45, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT002"],
    order_lab_prob=0.90,
    order_imaging_prob=0.60,
    order_medication_prob=0.95,
    surgery_prob=0.0,
    icu_prob=0.08,
    ecg_prob=0.15,
    outpatient_prob=0.70,
    emergency_prob=0.15,
    comorbidity_probs={
        "I10": 0.30,
        "E11": 0.15,
        "I25": 0.15,
        "J18": 0.20,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.2, 1.2), (0.15, 1.5)]),
        "RBC": LabAbnormality("RBC", "high", [(0.3, 1.1), (0.2, 1.2)]),
        "HGB": LabAbnormality("HGB", "high", [(0.25, 1.1), (0.15, 1.2)]),
    },
    typical_medications={
        "支气管扩张": ["沙丁胺醇气雾剂", "布地奈德福莫特罗粉吸入剂", "噻托溴铵粉吸入剂"],
        "化痰": ["氨溴索"],
    },
    typical_imaging=["胸部CT平扫", "胸部X线正侧位"],
    los_distribution=[(5, 15), (7, 25), (10, 30), (14, 20), (21, 10)],
)

ASTHMA = DiseaseProfile(
    name="支气管哮喘",
    icd10_codes=["J45"],
    age_range=(5, 65),
    gender="B",
    primary_departments=["DEPT002"],
    order_lab_prob=0.70,
    order_imaging_prob=0.40,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.03,
    ecg_prob=0.05,
    outpatient_prob=0.85,
    emergency_prob=0.10,
    comorbidity_probs={
        "J06": 0.20,
        "J44": 0.10,
    },
    typical_medications={
        "支气管扩张": ["沙丁胺醇气雾剂", "布地奈德福莫特罗粉吸入剂"],
        "抗组胺": ["孟鲁司特钠片", "氯雷他定片"],
    },
    typical_imaging=["胸部X线正侧位"],
)

PNEUMOTHORAX = DiseaseProfile(
    name="气胸",
    icd10_codes=["J93"],
    age_range=(15, 45),
    gender="M",
    primary_departments=["DEPT002", "DEPT012"],
    order_lab_prob=0.80,
    order_imaging_prob=0.95,
    order_medication_prob=0.70,
    surgery_prob=0.20,
    icu_prob=0.05,
    ecg_prob=0.10,
    outpatient_prob=0.15,
    emergency_prob=0.75,
    comorbidity_probs={
        "J44": 0.15,
        "J45": 0.10,
    },
    typical_imaging=["胸部X线正侧位", "胸部CT平扫"],
    typical_surgeries=["胸腔闭式引流术", "胸腔镜手术"],
)

# ------------------------------------------------------------------
# 3. 消化内科
# ------------------------------------------------------------------

GASTRIC_ULCER = DiseaseProfile(
    name="胃溃疡",
    icd10_codes=["K25"],
    age_range=(25, None),
    gender="B",
    primary_departments=["DEPT003"],
    order_lab_prob=0.85,
    order_imaging_prob=0.50,
    order_medication_prob=0.90,
    surgery_prob=0.05,
    icu_prob=0.01,
    ecg_prob=0.02,
    outpatient_prob=0.80,
    emergency_prob=0.10,
    comorbidity_probs={
        "K29": 0.30,
        "I10": 0.15,
        "E11": 0.10,
    },
    lab_abnormalities={
        "Hb": LabAbnormality("Hb", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.85), (0.2, 0.75)]),
    },
    typical_medications={
        "抑酸": ["奥美拉唑肠溶胶囊", "雷贝拉唑钠肠溶片"],
        "胃黏膜保护": ["铝碳酸镁片", "瑞巴派特片"],
    },
    typical_imaging=["腹部CT", "上消化道造影"],
    los_distribution=[(3, 20), (5, 30), (7, 25), (10, 15), (14, 10)],
)

GASTRITIS_DUODENITIS = DiseaseProfile(
    name="胃炎和十二指肠炎",
    icd10_codes=["K29"],
    age_range=(18, None),
    gender="B",
    primary_departments=["DEPT003"],
    order_lab_prob=0.70,
    order_imaging_prob=0.30,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.01,
    outpatient_prob=0.90,
    emergency_prob=0.05,
    comorbidity_probs={
        "K25": 0.15,
        "I10": 0.10,
    },
    typical_medications={
        "抑酸": ["奥美拉唑肠溶胶囊", "泮托拉唑钠肠溶片"],
        "促动力": ["莫沙必利片"],
    },
    typical_imaging=["腹部超声", "胃镜"],
)

ACUTE_APPENDICITIS = DiseaseProfile(
    name="急性阑尾炎",
    icd10_codes=["K35"],
    age_range=(5, 65),
    gender="B",
    primary_departments=["DEPT011", "DEPT003"],
    order_lab_prob=0.90,
    order_imaging_prob=0.80,
    order_medication_prob=0.80,
    surgery_prob=0.85,
    icu_prob=0.01,
    ecg_prob=0.02,
    outpatient_prob=0.05,
    emergency_prob=0.80,
    comorbidity_probs={
        "J18": 0.10,
        "I10": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.5, 1.5), (0.3, 2.0), (0.15, 3.0)]),
        "NEUT%": LabAbnormality("NEUT%", "high", [(0.5, 1.2), (0.3, 1.5)]),
        "CRP": LabAbnormality("CRP", "high", [(0.4, 3.0), (0.3, 5.0)]),
    },
    typical_medications={
        "抗菌": ["头孢曲松", "甲硝唑"],
        "镇痛": ["布洛芬缓释胶囊"],
    },
    typical_imaging=["腹部CT", "腹部超声"],
    typical_surgeries=["阑尾切除术"],
    los_distribution=[(2, 30), (3, 40), (5, 25), (7, 5)],
)

CHOLELITHIASIS = DiseaseProfile(
    name="胆石症",
    icd10_codes=["K80"],
    age_range=(30, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT003", "DEPT011"],
    order_lab_prob=0.85,
    order_imaging_prob=0.90,
    order_medication_prob=0.75,
    surgery_prob=0.30,
    icu_prob=0.02,
    ecg_prob=0.02,
    outpatient_prob=0.50,
    emergency_prob=0.30,
    comorbidity_probs={
        "K85": 0.20,
        "E11": 0.15,
        "I10": 0.15,
    },
    lab_abnormalities={
        "ALT": LabAbnormality("ALT", "high", [(0.3, 1.5), (0.2, 2.0)]),
        "AST": LabAbnormality("AST", "high", [(0.3, 1.5), (0.2, 2.0)]),
        "TBIL": LabAbnormality("TBIL", "high", [(0.3, 1.5), (0.2, 2.5)]),
        "DBIL": LabAbnormality("DBIL", "high", [(0.3, 1.8), (0.2, 3.0)]),
    },
    typical_medications={
        "解痉": ["山莨菪碱"],
        "抗菌": ["头孢曲松"],
        "利胆": ["熊去氧胆酸胶囊"],
    },
    typical_imaging=["腹部超声", "腹部CT", "MRCP"],
    typical_surgeries=["腹腔镜胆囊切除术"],
    los_distribution=[(2, 20), (3, 40), (5, 30), (7, 10)],
)

ACUTE_PANCREATITIS = DiseaseProfile(
    name="急性胰腺炎",
    icd10_codes=["K85"],
    age_range=(25, None),
    gender="B",
    primary_departments=["DEPT003", "DEPT029"],
    order_lab_prob=0.95,
    order_imaging_prob=0.80,
    order_medication_prob=0.85,
    surgery_prob=0.10,
    icu_prob=0.15,
    ecg_prob=0.05,
    outpatient_prob=0.05,
    emergency_prob=0.85,
    comorbidity_probs={
        "E11": 0.25,
        "E78": 0.20,
        "K80": 0.30,
        "I10": 0.15,
    },
    lab_abnormalities={
        "AMY": LabAbnormality("AMY", "high", [(0.4, 3.0), (0.3, 5.0), (0.2, 10.0)]),
        "LPS": LabAbnormality("LPS", "high", [(0.4, 3.0), (0.3, 5.0), (0.2, 10.0)]),
        "GLU": LabAbnormality("GLU", "high", [(0.3, 1.5), (0.2, 2.0)]),
        "CA": LabAbnormality("CA", "low", [(0.2, 0.85), (0.1, 0.75)]),
    },
    typical_medications={
        "抑酸": ["奥美拉唑肠溶胶囊"],
        "抑制胰酶": ["生长抑素"],
        "抗菌": ["头孢曲松", "甲硝唑"],
    },
    typical_imaging=["腹部CT", "腹部超声"],
    los_distribution=[(5, 10), (7, 25), (10, 30), (14, 20), (21, 10), (28, 5)],
)

UPPER_GI_BLEEDING = DiseaseProfile(
    name="上消化道出血",
    icd10_codes=["K92"],
    age_range=(25, None),
    gender="B",
    primary_departments=["DEPT003", "DEPT029"],
    order_lab_prob=0.95,
    order_imaging_prob=0.60,
    order_medication_prob=0.90,
    surgery_prob=0.10,
    icu_prob=0.10,
    ecg_prob=0.10,
    outpatient_prob=0.02,
    emergency_prob=0.90,
    comorbidity_probs={
        "K25": 0.35,
        "K29": 0.20,
        "I10": 0.20,
        "N18": 0.10,
    },
    lab_abnormalities={
        "Hb": LabAbnormality("Hb", "low", [(0.5, 0.75), (0.3, 0.60), (0.15, 0.45)]),
        "HGB": LabAbnormality("HGB", "low", [(0.5, 0.75), (0.3, 0.60), (0.15, 0.45)]),
        "BUN": LabAbnormality("BUN", "high", [(0.3, 1.5), (0.2, 2.0)]),
    },
    typical_medications={
        "抑酸": ["奥美拉唑肠溶胶囊"],
        "止血": ["氨甲环酸"],
    },
    typical_imaging=["腹部CT", "胃镜"],
    typical_surgeries=["胃镜下止血术"],
    los_distribution=[(3, 15), (5, 30), (7, 30), (10, 20), (14, 5)],
)

# ------------------------------------------------------------------
# 4. 内分泌科
# ------------------------------------------------------------------

TYPE_2_DIABETES = DiseaseProfile(
    name="2型糖尿病",
    icd10_codes=["E11.9", "E11.0", "E11.1", "E11.2"],
    age_range=(30, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT004"],
    order_lab_prob=0.85,
    order_imaging_prob=0.40,
    order_medication_prob=0.95,
    surgery_prob=0.0,
    icu_prob=0.02,
    ecg_prob=0.05,
    outpatient_prob=0.85,
    emergency_prob=0.03,
    comorbidity_probs={
        "I10": 0.50,
        "E78": 0.40,
        "I25": 0.25,
        "N18": 0.30,
        "E05": 0.08,
    },
    lab_abnormalities={
        "GLU": LabAbnormality("GLU", "high", [(0.5, 1.3), (0.3, 1.6), (0.15, 2.0), (0.05, 3.0)]),
        "HbA1c": LabAbnormality("HbA1c", "high", [(0.4, 1.2), (0.35, 1.4), (0.2, 1.6), (0.05, 2.0)]),
        "TG": LabAbnormality("TG", "high", [(0.4, 1.5), (0.3, 2.0), (0.2, 3.0), (0.1, 4.0)]),
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.4, 1.3), (0.35, 1.5), (0.2, 1.8), (0.05, 2.2)]),
        "CREA": LabAbnormality("CREA", "high", [(0.15, 1.2), (0.1, 1.4)]),
        "UA": LabAbnormality("UA", "high", [(0.3, 1.3), (0.2, 1.6)]),
    },
    typical_medications={
        "降糖": ["二甲双胍片", "格列美脲片", "阿卡波糖片", "西格列汀片", "门冬胰岛素注射液"],
        "调脂": ["阿托伐他汀钙片"],
    },
    typical_imaging=["眼底照相", "颈动脉超声", "下肢动脉超声"],
    los_distribution=[(3, 15), (5, 25), (7, 30), (10, 20), (14, 10)],
    outcome_probs={"治愈": 0.10, "好转": 0.70, "未愈": 0.18, "死亡": 0.02},
)

THYROTOXICOSIS = DiseaseProfile(
    name="甲状腺毒症",
    icd10_codes=["E05"],
    age_range=(20, 65),
    gender="F",
    primary_departments=["DEPT004"],
    order_lab_prob=0.85,
    order_imaging_prob=0.70,
    order_medication_prob=0.85,
    surgery_prob=0.10,
    icu_prob=0.01,
    ecg_prob=0.20,
    outpatient_prob=0.80,
    emergency_prob=0.05,
    comorbidity_probs={
        "E11": 0.10,
        "I10": 0.10,
        "I48": 0.08,
    },
    lab_abnormalities={
        "TSH": LabAbnormality("TSH", "low", [(0.5, 0.1), (0.3, 0.05)]),
        "FT3": LabAbnormality("FT3", "high", [(0.4, 1.5), (0.3, 2.0)]),
        "FT4": LabAbnormality("FT4", "high", [(0.4, 1.5), (0.3, 2.0)]),
    },
    typical_medications={
        "抗甲状腺": ["甲巯咪唑片", "丙硫氧嘧啶片"],
        "对症": ["美托洛尔片"],
    },
    typical_imaging=["甲状腺超声", "甲状腺核素扫描"],
    typical_surgeries=["甲状腺次全切除术"],
)

HYPOTHYROIDISM = DiseaseProfile(
    name="甲状腺功能减退",
    icd10_codes=["E03"],
    age_range=(30, None),
    gender="F",
    age_distribution="skewed_old",
    primary_departments=["DEPT004"],
    order_lab_prob=0.80,
    order_imaging_prob=0.30,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.05,
    outpatient_prob=0.90,
    emergency_prob=0.02,
    comorbidity_probs={
        "E11": 0.15,
        "E78": 0.15,
    },
    lab_abnormalities={
        "TSH": LabAbnormality("TSH", "high", [(0.5, 2.0), (0.3, 3.0), (0.15, 5.0)]),
        "FT3": LabAbnormality("FT3", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "FT4": LabAbnormality("FT4", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "TC": LabAbnormality("TC", "high", [(0.3, 1.2), (0.2, 1.4)]),
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.3, 1.2), (0.2, 1.4)]),
    },
    typical_medications={
        "替代": ["左甲状腺素钠片"],
    },
    typical_imaging=["甲状腺超声"],
)

OBESITY = DiseaseProfile(
    name="肥胖症",
    icd10_codes=["E66"],
    age_range=(18, 60),
    gender="B",
    primary_departments=["DEPT004"],
    order_lab_prob=0.70,
    order_imaging_prob=0.20,
    order_medication_prob=0.60,
    surgery_prob=0.02,
    icu_prob=0.0,
    ecg_prob=0.05,
    outpatient_prob=0.95,
    emergency_prob=0.01,
    comorbidity_probs={
        "E11": 0.35,
        "I10": 0.25,
        "E78": 0.30,
        "E05": 0.05,
    },
    lab_abnormalities={
        "GLU": LabAbnormality("GLU", "high", [(0.3, 1.2), (0.2, 1.4)]),
        "TG": LabAbnormality("TG", "high", [(0.4, 1.5), (0.3, 2.0)]),
        "TC": LabAbnormality("TC", "high", [(0.3, 1.2), (0.2, 1.5)]),
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.35, 1.3), (0.25, 1.6)]),
        "ALT": LabAbnormality("ALT", "high", [(0.3, 1.3), (0.2, 1.6)]),
    },
    typical_medications={
        "降糖": ["二甲双胍片"],
        "降脂": ["阿托伐他汀钙片"],
    },
    typical_imaging=["腹部超声"],
)

DYSLIPIDEMIA = DiseaseProfile(
    name="血脂异常",
    icd10_codes=["E78"],
    age_range=(30, None),
    gender="B",
    primary_departments=["DEPT004"],
    order_lab_prob=0.80,
    order_imaging_prob=0.20,
    order_medication_prob=0.80,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.05,
    outpatient_prob=0.95,
    emergency_prob=0.01,
    comorbidity_probs={
        "I10": 0.45,
        "E11": 0.30,
        "I25": 0.25,
    },
    lab_abnormalities={
        "TG": LabAbnormality("TG", "high", [(0.3, 1.5), (0.2, 2.0)]),
        "TC": LabAbnormality("TC", "high", [(0.3, 1.3), (0.2, 1.6)]),
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.4, 1.5), (0.3, 2.0)]),
        "HDL-C": LabAbnormality("HDL-C", "low", [(0.3, 0.6), (0.2, 0.5)]),
    },
    typical_medications={
        "降脂": ["阿托伐他汀钙片", "瑞舒伐他汀钙片", "非诺贝特胶囊"],
    },
    typical_imaging=["颈动脉超声"],
)

# ------------------------------------------------------------------
# 5. 神经内科
# ------------------------------------------------------------------

CEREBRAL_INFARCTION = DiseaseProfile(
    name="脑梗死",
    icd10_codes=["I63.9", "I63.0", "I63.1", "I63.2", "I63.3"],
    age_range=(45, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT008", "DEPT013"],
    order_lab_prob=0.95,
    order_imaging_prob=0.90,
    order_medication_prob=0.95,
    surgery_prob=0.10,
    icu_prob=0.15,
    ecg_prob=0.30,
    outpatient_prob=0.05,
    emergency_prob=0.80,
    comorbidity_probs={
        "I10": 0.55,
        "E11": 0.25,
        "E78": 0.35,
        "I25": 0.20,
        "I48": 0.15,
    },
    lab_abnormalities={
        "D-Dimer": LabAbnormality("D-Dimer", "high", [(0.3, 1.5), (0.3, 2.0), (0.2, 3.0), (0.2, 5.0)]),
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.4, 1.2), (0.3, 1.5), (0.2, 1.8), (0.1, 2.2)]),
        "TC": LabAbnormality("TC", "high", [(0.4, 1.2), (0.3, 1.5), (0.2, 1.8), (0.1, 2.0)]),
        "GLU": LabAbnormality("GLU", "high", [(0.25, 1.2), (0.15, 1.5)]),
    },
    typical_medications={
        "抗血小板": ["阿司匹林肠溶片", "氯吡格雷片"],
        "调脂": ["阿托伐他汀钙片", "瑞舒伐他汀钙片"],
        "改善循环": ["丁苯酞", "银杏叶提取物"],
    },
    typical_imaging=["头颅CT平扫", "头颅MRI", "颈动脉CTA"],
    typical_surgeries=["颈动脉内膜剥脱术"],
    los_distribution=[(5, 10), (7, 20), (10, 25), (14, 25), (21, 15), (28, 5)],
    outcome_probs={"治愈": 0.25, "好转": 0.45, "未愈": 0.22, "死亡": 0.08},
)

CEREBRAL_HEMORRHAGE = DiseaseProfile(
    name="脑出血",
    icd10_codes=["I61.9", "I61.0", "I61.1", "I61.2"],
    age_range=(45, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT008", "DEPT013", "DEPT029"],
    order_lab_prob=0.95,
    order_imaging_prob=0.95,
    order_medication_prob=0.90,
    surgery_prob=0.30,
    icu_prob=0.80,
    ecg_prob=0.40,
    outpatient_prob=0.02,
    emergency_prob=0.90,
    comorbidity_probs={
        "I10": 0.60,
        "E11": 0.20,
        "I63": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.4, 1.3), (0.3, 1.8), (0.2, 2.5), (0.1, 3.5)]),
        "GLU": LabAbnormality("GLU", "high", [(0.4, 1.2), (0.3, 1.5), (0.2, 2.0), (0.1, 2.5)]),
        "D-Dimer": LabAbnormality("D-Dimer", "high", [(0.3, 2.0), (0.3, 3.0), (0.2, 5.0), (0.2, 8.0)]),
    },
    typical_medications={
        "脱水": ["甘露醇", "呋塞米"],
        "降压": ["乌拉地尔", "尼莫地平"],
        "止血": ["氨甲环酸"],
    },
    typical_imaging=["头颅CT平扫", "头颅CT增强", "头颅MRI"],
    typical_surgeries=["开颅术", "脑室穿刺引流术"],
    los_distribution=[(7, 10), (14, 25), (21, 30), (28, 20), (35, 10), (42, 5)],
    outcome_probs={"治愈": 0.20, "好转": 0.40, "未愈": 0.25, "死亡": 0.15},
)

PARKINSON_DISEASE = DiseaseProfile(
    name="帕金森病",
    icd10_codes=["G20"],
    age_range=(55, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT008"],
    order_lab_prob=0.70,
    order_imaging_prob=0.40,
    order_medication_prob=0.90,
    surgery_prob=0.05,
    icu_prob=0.01,
    ecg_prob=0.05,
    outpatient_prob=0.85,
    emergency_prob=0.03,
    comorbidity_probs={
        "I10": 0.25,
        "E11": 0.15,
        "I63": 0.10,
    },
    typical_medications={
        "多巴胺": ["左旋多巴", "普拉克索"],
    },
    typical_imaging=["头颅MRI", "头颅CT平扫"],
)

EPILEPSY = DiseaseProfile(
    name="癫痫",
    icd10_codes=["G40"],
    age_range=(5, None),
    gender="B",
    primary_departments=["DEPT008"],
    order_lab_prob=0.80,
    order_imaging_prob=0.60,
    order_medication_prob=0.90,
    surgery_prob=0.05,
    icu_prob=0.05,
    ecg_prob=0.30,
    outpatient_prob=0.80,
    emergency_prob=0.15,
    comorbidity_probs={
        "G43": 0.10,
        "E11": 0.08,
    },
    lab_abnormalities={
        "K": LabAbnormality("K", "low", [(0.1, 0.85)]),
        "NA": LabAbnormality("NA", "low", [(0.1, 0.90)]),
    },
    typical_medications={
        "抗癫痫": ["丙戊酸钠缓释片", "左乙拉西坦片", "卡马西平片"],
    },
    typical_imaging=["头颅MRI", "头颅CT平扫"],
)

MIGRAINE = DiseaseProfile(
    name="偏头痛",
    icd10_codes=["G43"],
    age_range=(15, 60),
    gender="B",
    primary_departments=["DEPT008"],
    order_lab_prob=0.40,
    order_imaging_prob=0.30,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.02,
    outpatient_prob=0.95,
    emergency_prob=0.03,
    comorbidity_probs={
        "G40": 0.05,
        "E11": 0.05,
    },
    typical_medications={
        "镇痛": ["布洛芬缓释胶囊", "曲马多缓释片"],
        "预防": ["氟桂利嗪胶囊", "普萘洛尔"],
    },
    typical_imaging=["头颅CT平扫", "头颅MRI"],
)

# ------------------------------------------------------------------
# 6. 肾脏内科
# ------------------------------------------------------------------

CHRONIC_KIDNEY_DISEASE = DiseaseProfile(
    name="慢性肾脏病",
    icd10_codes=["N18"],
    age_range=(35, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT005"],
    order_lab_prob=0.90,
    order_imaging_prob=0.40,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.05,
    ecg_prob=0.15,
    outpatient_prob=0.70,
    emergency_prob=0.10,
    comorbidity_probs={
        "I10": 0.55,
        "E11": 0.40,
        "E78": 0.25,
        "I25": 0.15,
        "I48": 0.10,
    },
    lab_abnormalities={
        "CREA": LabAbnormality("CREA", "high", [(0.5, 1.5), (0.3, 2.0), (0.15, 3.0), (0.05, 5.0)]),
        "UREA": LabAbnormality("UREA", "high", [(0.4, 1.5), (0.3, 2.0), (0.2, 2.5)]),
        "UA": LabAbnormality("UA", "high", [(0.3, 1.3), (0.2, 1.6)]),
        "K": LabAbnormality("K", "high", [(0.3, 1.2), (0.2, 1.4)]),
        "HGB": LabAbnormality("HGB", "low", [(0.4, 0.85), (0.3, 0.75), (0.2, 0.65)]),
        "CA": LabAbnormality("CA", "low", [(0.2, 0.90), (0.1, 0.85)]),
        "P": LabAbnormality("P", "high", [(0.3, 1.2), (0.2, 1.4)]),
    },
    typical_medications={
        "降压": ["缬沙坦胶囊", "氨氯地平片"],
        "纠正贫血": ["重组人促红素注射液"],
        "降磷": ["碳酸镧"],
    },
    typical_imaging=["腹部超声", "肾脏CT"],
)

NEPHROLITHIASIS = DiseaseProfile(
    name="肾结石",
    icd10_codes=["N20"],
    age_range=(20, 65),
    gender="M",
    primary_departments=["DEPT005", "DEPT015"],
    order_lab_prob=0.85,
    order_imaging_prob=0.90,
    order_medication_prob=0.80,
    surgery_prob=0.30,
    icu_prob=0.01,
    ecg_prob=0.02,
    outpatient_prob=0.50,
    emergency_prob=0.40,
    comorbidity_probs={
        "N18": 0.15,
        "I10": 0.15,
        "E11": 0.10,
    },
    lab_abnormalities={
        "CREA": LabAbnormality("CREA", "high", [(0.2, 1.2), (0.1, 1.4)]),
        "UA": LabAbnormality("UA", "high", [(0.3, 1.3), (0.2, 1.5)]),
        "WBC": LabAbnormality("WBC", "high", [(0.3, 1.2), (0.2, 1.5)]),
    },
    typical_medications={
        "解痉": ["山莨菪碱"],
        "镇痛": ["布洛芬缓释胶囊", "曲马多缓释片"],
    },
    typical_imaging=["腹部超声", "泌尿系CTU", "腹部X线"],
    typical_surgeries=["输尿管镜碎石术", "经皮肾镜取石术"],
)

URINARY_TRACT_INFECTION = DiseaseProfile(
    name="尿路感染",
    icd10_codes=["N39"],
    age_range=(0, None),
    gender="F",
    primary_departments=["DEPT005"],
    order_lab_prob=0.90,
    order_imaging_prob=0.30,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.01,
    ecg_prob=0.01,
    outpatient_prob=0.85,
    emergency_prob=0.10,
    comorbidity_probs={
        "E11": 0.15,
        "N18": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.4, 1.3), (0.3, 1.6)]),
        "NEUT%": LabAbnormality("NEUT%", "high", [(0.4, 1.2), (0.3, 1.4)]),
    },
    typical_medications={
        "抗菌": ["左氧氟沙星", "头孢曲松", "阿莫西林"],
    },
    typical_imaging=["腹部超声"],
)

# ------------------------------------------------------------------
# 7. 风湿免疫科
# ------------------------------------------------------------------

RHEUMATOID_ARTHRITIS = DiseaseProfile(
    name="类风湿关节炎",
    icd10_codes=["M06"],
    age_range=(30, 75),
    gender="F",
    primary_departments=["DEPT007"],
    order_lab_prob=0.80,
    order_imaging_prob=0.50,
    order_medication_prob=0.90,
    surgery_prob=0.05,
    icu_prob=0.0,
    ecg_prob=0.02,
    outpatient_prob=0.85,
    emergency_prob=0.03,
    comorbidity_probs={
        "E11": 0.15,
        "I10": 0.15,
        "M32": 0.05,
    },
    lab_abnormalities={
        "CRP": LabAbnormality("CRP", "high", [(0.4, 2.0), (0.3, 3.0)]),
        "ESR": LabAbnormality("ESR", "high", [(0.5, 2.0), (0.3, 3.0), (0.2, 5.0)]),
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.90), (0.2, 0.85)]),
    },
    typical_medications={
        "免疫抑制": ["甲氨蝶呤", "来氟米特"],
        "生物制剂": ["阿达木单抗"],
        "镇痛": ["布洛芬缓释胶囊"],
    },
    typical_imaging=["关节X线", "关节超声", "关节MRI"],
)

SYSTEMIC_LUPUS = DiseaseProfile(
    name="系统性红斑狼疮",
    icd10_codes=["M32"],
    age_range=(15, 50),
    gender="F",
    primary_departments=["DEPT007"],
    order_lab_prob=0.90,
    order_imaging_prob=0.40,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.05,
    ecg_prob=0.10,
    outpatient_prob=0.80,
    emergency_prob=0.10,
    comorbidity_probs={
        "N18": 0.20,
        "I10": 0.15,
        "E11": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "PLT": LabAbnormality("PLT", "low", [(0.3, 0.80), (0.2, 0.70)]),
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "CREA": LabAbnormality("CREA", "high", [(0.2, 1.2), (0.1, 1.4)]),
    },
    typical_medications={
        "激素": ["泼尼松片", "甲泼尼龙片"],
        "免疫抑制": ["环磷酰胺", "霉酚酸酯"],
    },
    typical_imaging=["肾脏超声", "胸部X线"],
)

GOUT = DiseaseProfile(
    name="痛风",
    icd10_codes=["M10"],
    age_range=(30, None),
    gender="M",
    primary_departments=["DEPT007"],
    order_lab_prob=0.80,
    order_imaging_prob=0.40,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.02,
    outpatient_prob=0.90,
    emergency_prob=0.05,
    comorbidity_probs={
        "E11": 0.25,
        "I10": 0.20,
        "E78": 0.20,
        "N18": 0.15,
    },
    lab_abnormalities={
        "UA": LabAbnormality("UA", "high", [(0.5, 1.5), (0.3, 2.0), (0.15, 2.5)]),
        "CREA": LabAbnormality("CREA", "high", [(0.15, 1.2), (0.1, 1.4)]),
        "CRP": LabAbnormality("CRP", "high", [(0.4, 2.0), (0.3, 3.0)]),
    },
    typical_medications={
        "降尿酸": ["别嘌醇", "非布司他"],
        "镇痛": ["布洛芬缓释胶囊", "秋水仙碱"],
    },
    typical_imaging=["关节X线", "关节超声"],
)

# ------------------------------------------------------------------
# 8. 血液内科
# ------------------------------------------------------------------

ANEMIA = DiseaseProfile(
    name="贫血",
    icd10_codes=["D64"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT006"],
    order_lab_prob=0.90,
    order_imaging_prob=0.20,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.01,
    ecg_prob=0.10,
    outpatient_prob=0.80,
    emergency_prob=0.05,
    comorbidity_probs={
        "N18": 0.15,
        "E11": 0.10,
        "K25": 0.08,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.5, 0.80), (0.3, 0.65), (0.15, 0.50)]),
        "RBC": LabAbnormality("RBC", "low", [(0.4, 0.85), (0.3, 0.75)]),
        "MCV": LabAbnormality("MCV", "low", [(0.3, 0.90), (0.2, 0.85)]),
        "MCH": LabAbnormality("MCH", "low", [(0.3, 0.90), (0.2, 0.85)]),
        "FE": LabAbnormality("FE", "low", [(0.4, 0.75), (0.3, 0.60)]),
    },
    typical_medications={
        "补铁": ["蔗糖铁注射液", "叶酸片", "维生素B12片"],
        "促红": ["重组人促红素注射液"],
    },
    typical_imaging=["腹部超声"],
)

LEUKEMIA = DiseaseProfile(
    name="急性白血病",
    icd10_codes=["C91", "C92"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT006"],
    order_lab_prob=0.98,
    order_imaging_prob=0.30,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.15,
    ecg_prob=0.10,
    outpatient_prob=0.05,
    emergency_prob=0.30,
    comorbidity_probs={
        "D64": 0.40,
        "J18": 0.25,
        "N18": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "variable", [(0.3, 0.2), (0.3, 3.0), (0.2, 5.0), (0.2, 10.0)]),
        "HGB": LabAbnormality("HGB", "low", [(0.5, 0.70), (0.3, 0.55), (0.15, 0.40)]),
        "PLT": LabAbnormality("PLT", "low", [(0.4, 0.65), (0.3, 0.50), (0.2, 0.35)]),
    },
    typical_medications={
        "化疗": ["注射用环磷酰胺", "注射用阿糖胞苷"],
    },
    typical_imaging=["胸部X线", "腹部超声", "头颅CT"],
    los_distribution=[(7, 10), (14, 25), (21, 30), (28, 20), (35, 10), (42, 5)],
)

# ------------------------------------------------------------------
# 9. 普通外科
# ------------------------------------------------------------------

INGUINAL_HERNIA = DiseaseProfile(
    name="腹股沟疝",
    icd10_codes=["K40"],
    age_range=(0, None),
    gender="M",
    primary_departments=["DEPT011"],
    order_lab_prob=0.70,
    order_imaging_prob=0.60,
    order_medication_prob=0.60,
    surgery_prob=0.90,
    icu_prob=0.0,
    ecg_prob=0.02,
    outpatient_prob=0.20,
    emergency_prob=0.15,
    comorbidity_probs={
        "I10": 0.15,
        "E11": 0.10,
    },
    typical_medications={
        "镇痛": ["布洛芬缓释胶囊"],
    },
    typical_imaging=["腹部超声", "腹部CT"],
    typical_surgeries=["疝修补术", "腹腔镜疝修补术"],
    los_distribution=[(1, 30), (2, 40), (3, 25), (5, 5)],
)

BOWEL_OBSTRUCTION = DiseaseProfile(
    name="麻痹性肠梗阻",
    icd10_codes=["K56"],
    age_range=(20, None),
    gender="B",
    primary_departments=["DEPT011", "DEPT003"],
    order_lab_prob=0.90,
    order_imaging_prob=0.90,
    order_medication_prob=0.80,
    surgery_prob=0.30,
    icu_prob=0.08,
    ecg_prob=0.05,
    outpatient_prob=0.02,
    emergency_prob=0.85,
    comorbidity_probs={
        "K35": 0.10,
        "I10": 0.15,
        "E11": 0.10,
    },
    lab_abnormalities={
        "K": LabAbnormality("K", "high", [(0.3, 1.2), (0.2, 1.4)]),
        "K": LabAbnormality("K", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "WBC": LabAbnormality("WBC", "high", [(0.3, 1.3), (0.2, 1.6)]),
    },
    typical_medications={
        "胃肠减压": [],
        "抗菌": ["头孢曲松"],
    },
    typical_imaging=["腹部X线", "腹部CT"],
    typical_surgeries=["肠粘连松解术", "肠切除术"],
    los_distribution=[(3, 15), (5, 30), (7, 30), (10, 20), (14, 5)],
)

# ------------------------------------------------------------------
# 10. 骨科
# ------------------------------------------------------------------

HUMERUS_FRACTURE = DiseaseProfile(
    name="肱骨骨折",
    icd10_codes=["S42"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT014"],
    order_lab_prob=0.70,
    order_imaging_prob=0.95,
    order_medication_prob=0.80,
    surgery_prob=0.40,
    icu_prob=0.01,
    ecg_prob=0.05,
    outpatient_prob=0.15,
    emergency_prob=0.70,
    comorbidity_probs={
        "I10": 0.15,
        "E11": 0.10,
        "M16": 0.05,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.2, 0.90), (0.1, 0.85)]),
    },
    typical_medications={
        "镇痛": ["布洛芬缓释胶囊", "曲马多缓释片"],
        "抗凝": ["低分子肝素钙注射液"],
    },
    typical_imaging=["X光", "CT"],
    typical_surgeries=["骨折内固定术"],
    los_distribution=[(2, 20), (3, 40), (5, 30), (7, 10)],
)

FEMUR_FRACTURE = DiseaseProfile(
    name="股骨骨折",
    icd10_codes=["S72"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT014"],
    order_lab_prob=0.80,
    order_imaging_prob=0.95,
    order_medication_prob=0.85,
    surgery_prob=0.80,
    icu_prob=0.05,
    ecg_prob=0.15,
    outpatient_prob=0.02,
    emergency_prob=0.85,
    comorbidity_probs={
        "I10": 0.20,
        "E11": 0.15,
        "N18": 0.10,
        "M16": 0.10,
    },
    lab_abnormalities={
        "D-Dimer": LabAbnormality("D-Dimer", "high", [(0.4, 2.0), (0.3, 3.0)]),
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.90), (0.2, 0.85)]),
    },
    typical_medications={
        "镇痛": ["曲马多缓释片", "吗啡注射液"],
        "抗凝": ["低分子肝素钙注射液"],
    },
    typical_imaging=["X光", "CT", "MRI"],
    typical_surgeries=["骨折内固定术", "髋关节置换术"],
    los_distribution=[(7, 15), (10, 25), (14, 30), (21, 20), (28, 10)],
)

SPINE_FRACTURE = DiseaseProfile(
    name="脊柱骨折",
    icd10_codes=["S32"],
    age_range=(20, None),
    gender="B",
    primary_departments=["DEPT014"],
    order_lab_prob=0.80,
    order_imaging_prob=0.95,
    order_medication_prob=0.80,
    surgery_prob=0.50,
    icu_prob=0.10,
    ecg_prob=0.10,
    outpatient_prob=0.05,
    emergency_prob=0.80,
    comorbidity_probs={
        "I10": 0.15,
        "E11": 0.10,
    },
    typical_medications={
        "镇痛": ["曲马多缓释片"],
        "抗凝": ["低分子肝素钙注射液"],
    },
    typical_imaging=["X光", "CT", "MRI"],
    typical_surgeries=["脊柱融合术", "椎体成形术"],
    los_distribution=[(5, 15), (7, 25), (10, 30), (14, 20), (21, 10)],
)

HIP_ARTHROSIS = DiseaseProfile(
    name="髋关节病",
    icd10_codes=["M16"],
    age_range=(50, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT014"],
    order_lab_prob=0.60,
    order_imaging_prob=0.80,
    order_medication_prob=0.75,
    surgery_prob=0.25,
    icu_prob=0.0,
    ecg_prob=0.05,
    outpatient_prob=0.75,
    emergency_prob=0.03,
    comorbidity_probs={
        "I10": 0.25,
        "E11": 0.15,
        "M17": 0.10,
    },
    typical_medications={
        "镇痛": ["布洛芬缓释胶囊", "塞来昔布"],
        "关节保护": ["硫酸氨基葡萄糖"],
    },
    typical_imaging=["X光", "CT", "MRI"],
    typical_surgeries=["髋关节置换术"],
)

KNEE_ARTHROSIS = DiseaseProfile(
    name="膝关节病",
    icd10_codes=["M17"],
    age_range=(45, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT014"],
    order_lab_prob=0.60,
    order_imaging_prob=0.80,
    order_medication_prob=0.75,
    surgery_prob=0.20,
    icu_prob=0.0,
    ecg_prob=0.02,
    outpatient_prob=0.80,
    emergency_prob=0.02,
    comorbidity_probs={
        "I10": 0.20,
        "E11": 0.15,
        "M16": 0.10,
    },
    typical_medications={
        "镇痛": ["布洛芬缓释胶囊", "塞来昔布"],
        "关节保护": ["硫酸氨基葡萄糖"],
    },
    typical_imaging=["X光", "MRI"],
    typical_surgeries=["膝关节置换术", "关节镜手术"],
)

# ------------------------------------------------------------------
# 11. 心胸外科
# ------------------------------------------------------------------

LUNG_CANCER = DiseaseProfile(
    name="支气管和肺恶性肿瘤",
    icd10_codes=["C34"],
    age_range=(40, None),
    gender="M",
    age_distribution="skewed_old",
    primary_departments=["DEPT009", "DEPT012"],
    order_lab_prob=0.95,
    order_imaging_prob=0.90,
    order_medication_prob=0.85,
    surgery_prob=0.35,
    icu_prob=0.10,
    ecg_prob=0.20,
    outpatient_prob=0.30,
    emergency_prob=0.10,
    comorbidity_probs={
        "I10": 0.25,
        "E11": 0.15,
        "J44": 0.20,
        "J18": 0.15,
        "I25": 0.10,
    },
    lab_abnormalities={
        "CEA": LabAbnormality("CEA", "high", [(0.4, 2.0), (0.3, 3.0), (0.2, 5.0)]),
        "CYFRA21-1": LabAbnormality("CYFRA21-1", "high", [(0.3, 2.0), (0.2, 3.0)]),
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.90), (0.2, 0.85)]),
    },
    typical_medications={
        "化疗": ["注射用顺铂", "注射用紫杉醇"],
        "靶向": ["吉非替尼片"],
        "镇痛": ["吗啡注射液"],
    },
    typical_imaging=["胸部CT", "PET-CT", "头颅MRI", "腹部CT"],
    typical_surgeries=["肺叶切除术", "肺癌根治术"],
    los_distribution=[(7, 15), (10, 25), (14, 30), (21, 20), (28, 10)],
)

ESOPHAGEAL_CANCER = DiseaseProfile(
    name="食管恶性肿瘤",
    icd10_codes=["C15"],
    age_range=(45, None),
    gender="M",
    age_distribution="skewed_old",
    primary_departments=["DEPT012", "DEPT009"],
    order_lab_prob=0.95,
    order_imaging_prob=0.90,
    order_medication_prob=0.80,
    surgery_prob=0.40,
    icu_prob=0.10,
    ecg_prob=0.15,
    outpatient_prob=0.15,
    emergency_prob=0.20,
    comorbidity_probs={
        "I10": 0.20,
        "E11": 0.10,
        "N18": 0.10,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.4, 0.85), (0.3, 0.75), (0.2, 0.65)]),
        "ALB": LabAbnormality("ALB", "low", [(0.3, 0.85), (0.2, 0.75)]),
    },
    typical_medications={
        "化疗": ["注射用顺铂", "注射用紫杉醇"],
        "营养": ["肠外营养"],
    },
    typical_imaging=["胸部CT", "上消化道造影", "PET-CT"],
    typical_surgeries=["食管癌根治术", "胃代食管术"],
    los_distribution=[(7, 10), (10, 20), (14, 30), (21, 25), (28, 15)],
)

CONGENITAL_HEART_DISEASE = DiseaseProfile(
    name="先天性心脏病",
    icd10_codes=["Q21"],
    age_range=(0, 18),
    gender="B",
    primary_departments=["DEPT012", "DEPT022"],
    order_lab_prob=0.85,
    order_imaging_prob=0.90,
    order_medication_prob=0.70,
    surgery_prob=0.40,
    icu_prob=0.20,
    ecg_prob=0.80,
    outpatient_prob=0.30,
    emergency_prob=0.20,
    comorbidity_probs={
        "J18": 0.20,
        "J45": 0.10,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "high", [(0.3, 1.1), (0.2, 1.2)]),
    },
    typical_medications={
        "强心": ["地高辛片"],
        "利尿": ["呋塞米片"],
    },
    typical_imaging=["心脏彩超", "胸部X线"],
    typical_surgeries=["房间隔缺损修补术", "室间隔缺损修补术"],
    los_distribution=[(5, 15), (7, 30), (10, 30), (14, 20), (21, 5)],
)

# ------------------------------------------------------------------
# 12. 泌尿外科
# ------------------------------------------------------------------

BENIGN_PROSTATIC_HYPERPLASIA = DiseaseProfile(
    name="前列腺增生",
    icd10_codes=["N40"],
    age_range=(50, None),
    gender="M",
    age_distribution="skewed_old",
    primary_departments=["DEPT015"],
    order_lab_prob=0.75,
    order_imaging_prob=0.70,
    order_medication_prob=0.80,
    surgery_prob=0.20,
    icu_prob=0.0,
    ecg_prob=0.05,
    outpatient_prob=0.70,
    emergency_prob=0.10,
    comorbidity_probs={
        "I10": 0.25,
        "E11": 0.15,
        "N18": 0.10,
    },
    lab_abnormalities={
        "CREA": LabAbnormality("CREA", "high", [(0.15, 1.2), (0.1, 1.4)]),
        "PSA": LabAbnormality("PSA", "high", [(0.4, 2.0), (0.3, 3.0)]),
    },
    typical_medications={
        "α受体阻滞": ["坦索罗辛"],
        "5α还原酶抑制": ["非那雄胺"],
    },
    typical_imaging=["腹部超声", "泌尿系超声"],
    typical_surgeries=["经尿道前列腺电切术"],
)

# ------------------------------------------------------------------
# 13. 神经外科
# ------------------------------------------------------------------

TRAUMATIC_BRAIN_INJURY = DiseaseProfile(
    name="脑外伤",
    icd10_codes=["S06"],
    age_range=(0, None),
    gender="M",
    primary_departments=["DEPT013", "DEPT029"],
    order_lab_prob=0.90,
    order_imaging_prob=0.95,
    order_medication_prob=0.80,
    surgery_prob=0.30,
    icu_prob=0.40,
    ecg_prob=0.30,
    outpatient_prob=0.05,
    emergency_prob=0.90,
    comorbidity_probs={
        "S42": 0.15,
        "S72": 0.10,
        "I10": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.3, 1.3), (0.2, 1.5)]),
        "D-Dimer": LabAbnormality("D-Dimer", "high", [(0.3, 1.5), (0.2, 2.0)]),
    },
    typical_medications={
        "脱水": ["甘露醇", "呋塞米"],
        "镇痛": ["地佐辛注射液"],
        "镇静": ["丙泊酚"],
    },
    typical_imaging=["头颅CT平扫", "头颅MRI"],
    typical_surgeries=["开颅血肿清除术", "去骨瓣减压术"],
    los_distribution=[(7, 15), (14, 25), (21, 30), (28, 20), (35, 10)],
)

INTRACRANIAL_INJURY = DiseaseProfile(
    name="颅内损伤",
    icd10_codes=["S02", "S06"],
    age_range=(0, None),
    gender="M",
    primary_departments=["DEPT013", "DEPT029"],
    order_lab_prob=0.90,
    order_imaging_prob=0.95,
    order_medication_prob=0.80,
    surgery_prob=0.25,
    icu_prob=0.30,
    ecg_prob=0.25,
    outpatient_prob=0.02,
    emergency_prob=0.92,
    comorbidity_probs={
        "I61": 0.10,
        "S42": 0.10,
        "I10": 0.10,
    },
    typical_medications={
        "脱水": ["甘露醇"],
        "镇痛": ["地佐辛注射液"],
    },
    typical_imaging=["头颅CT平扫", "头颅MRI"],
    typical_surgeries=["开颅血肿清除术"],
    los_distribution=[(7, 15), (14, 25), (21, 30), (28, 20), (35, 10)],
)

# ------------------------------------------------------------------
# 14. 妇科
# ------------------------------------------------------------------

UTERINE_FIBROID = DiseaseProfile(
    name="子宫肌瘤",
    icd10_codes=["D25"],
    age_range=(30, 55),
    gender="F",
    primary_departments=["DEPT019"],
    order_lab_prob=0.70,
    order_imaging_prob=0.80,
    order_medication_prob=0.60,
    surgery_prob=0.30,
    icu_prob=0.01,
    ecg_prob=0.02,
    outpatient_prob=0.85,
    emergency_prob=0.05,
    comorbidity_probs={
        "I10": 0.20,
        "E11": 0.15,
        "N39": 0.10,
    },
    typical_medications={
        "止血": ["氨甲环酸"],
        "激素": ["GnRH激动剂"],
    },
    typical_imaging=["妇科超声", "盆腔MRI"],
    typical_surgeries=["子宫肌瘤剔除术", "子宫切除术"],
)

OVARIAN_CYST = DiseaseProfile(
    name="卵巢囊肿",
    icd10_codes=["N83"],
    age_range=(18, 55),
    gender="F",
    primary_departments=["DEPT019"],
    order_lab_prob=0.70,
    order_imaging_prob=0.85,
    order_medication_prob=0.50,
    surgery_prob=0.25,
    icu_prob=0.0,
    ecg_prob=0.01,
    outpatient_prob=0.90,
    emergency_prob=0.03,
    comorbidity_probs={
        "D25": 0.15,
        "I10": 0.10,
    },
    typical_medications={
        "激素": ["短效避孕药"],
    },
    typical_imaging=["妇科超声", "盆腔CT"],
    typical_surgeries=["卵巢囊肿剥除术"],
)

ECTOPIC_PREGNANCY = DiseaseProfile(
    name="异位妊娠",
    icd10_codes=["O00"],
    age_range=(18, 45),
    gender="F",
    primary_departments=["DEPT019", "DEPT020"],
    order_lab_prob=0.90,
    order_imaging_prob=0.90,
    order_medication_prob=0.70,
    surgery_prob=0.40,
    icu_prob=0.05,
    ecg_prob=0.05,
    outpatient_prob=0.05,
    emergency_prob=0.90,
    comorbidity_probs={
        "I10": 0.10,
        "E11": 0.08,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.90), (0.2, 0.85)]),
    },
    typical_medications={
        "化疗": ["甲氨蝶呤"],
    },
    typical_imaging=["妇科超声"],
    typical_surgeries=["腹腔镜探查术", "输卵管切除术"],
    los_distribution=[(3, 20), (5, 40), (7, 30), (10, 10)],
)

CERVICITIS = DiseaseProfile(
    name="宫颈炎",
    icd10_codes=["N72"],
    age_range=(18, 55),
    gender="F",
    primary_departments=["DEPT019"],
    order_lab_prob=0.80,
    order_imaging_prob=0.20,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.0,
    outpatient_prob=0.95,
    emergency_prob=0.01,
    comorbidity_probs={
        "N39": 0.15,
        "E11": 0.05,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.3, 1.2), (0.2, 1.4)]),
    },
    typical_medications={
        "抗菌": ["阿奇霉素", "多西环素"],
    },
    typical_imaging=["妇科超声"],
)

# ------------------------------------------------------------------
# 15. 产科
# ------------------------------------------------------------------

NORMAL_DELIVERY = DiseaseProfile(
    name="正常分娩",
    icd10_codes=["O80"],
    age_range=(20, 40),
    gender="F",
    primary_departments=["DEPT020"],
    order_lab_prob=0.90,
    order_imaging_prob=0.30,
    order_medication_prob=0.70,
    surgery_prob=0.05,
    icu_prob=0.01,
    ecg_prob=0.05,
    outpatient_prob=0.10,
    emergency_prob=0.90,
    comorbidity_probs={
        "E11": 0.10,
        "I10": 0.08,
    },
    typical_medications={
        "缩宫": ["缩宫素"],
        "镇痛": ["哌替啶"],
    },
    typical_imaging=["产科超声"],
    typical_surgeries=["会阴侧切术", "剖宫产术"],
    los_distribution=[(2, 50), (3, 35), (5, 15)],
)

CESAREAN_SECTION = DiseaseProfile(
    name="剖宫产",
    icd10_codes=["O82"],
    age_range=(20, 42),
    gender="F",
    primary_departments=["DEPT020"],
    order_lab_prob=0.90,
    order_imaging_prob=0.20,
    order_medication_prob=0.80,
    surgery_prob=1.0,
    icu_prob=0.02,
    ecg_prob=0.10,
    outpatient_prob=0.05,
    emergency_prob=0.40,
    comorbidity_probs={
        "E11": 0.12,
        "I10": 0.10,
        "D25": 0.08,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.90), (0.2, 0.85)]),
    },
    typical_medications={
        "缩宫": ["缩宫素"],
        "镇痛": ["哌替啶", "地佐辛注射液"],
        "抗菌": ["头孢呋辛"],
    },
    typical_imaging=["产科超声"],
    typical_surgeries=["子宫下段剖宫产术"],
    los_distribution=[(3, 40), (5, 40), (7, 20)],
)

GESTATIONAL_DIABETES = DiseaseProfile(
    name="妊娠期糖尿病",
    icd10_codes=["O24"],
    age_range=(20, 42),
    gender="F",
    primary_departments=["DEPT020", "DEPT004"],
    order_lab_prob=0.90,
    order_imaging_prob=0.30,
    order_medication_prob=0.80,
    surgery_prob=0.0,
    icu_prob=0.01,
    ecg_prob=0.05,
    outpatient_prob=0.70,
    emergency_prob=0.05,
    comorbidity_probs={
        "I10": 0.15,
        "E11": 0.20,
    },
    lab_abnormalities={
        "GLU": LabAbnormality("GLU", "high", [(0.4, 1.3), (0.3, 1.6)]),
        "HbA1c": LabAbnormality("HbA1c", "high", [(0.3, 1.15), (0.2, 1.25)]),
    },
    typical_medications={
        "降糖": ["胰岛素", "二甲双胍"],
    },
    typical_imaging=["产科超声"],
)

# ------------------------------------------------------------------
# 16. 儿科
# ------------------------------------------------------------------

NEONATAL_JAUNDICE = DiseaseProfile(
    name="新生儿黄疸",
    icd10_codes=["P59"],
    age_range=(0, 0),
    gender="B",
    primary_departments=["DEPT023"],
    order_lab_prob=0.90,
    order_imaging_prob=0.10,
    order_medication_prob=0.60,
    surgery_prob=0.0,
    icu_prob=0.05,
    ecg_prob=0.0,
    outpatient_prob=0.20,
    emergency_prob=0.50,
    comorbidity_probs={
        "P23": 0.10,
    },
    lab_abnormalities={
        "TBIL": LabAbnormality("TBIL", "high", [(0.4, 1.5), (0.3, 2.0), (0.2, 3.0)]),
        "DBIL": LabAbnormality("DBIL", "high", [(0.3, 1.3), (0.2, 1.6)]),
    },
    typical_medications={
        "退黄": ["苯巴比妥", "益生菌"],
    },
    typical_imaging=["腹部超声"],
    los_distribution=[(2, 30), (3, 40), (5, 25), (7, 5)],
)

NEONATAL_PNEUMONIA = DiseaseProfile(
    name="新生儿肺炎",
    icd10_codes=["P23"],
    age_range=(0, 0),
    gender="B",
    primary_departments=["DEPT023"],
    order_lab_prob=0.95,
    order_imaging_prob=0.80,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.15,
    outpatient_prob=0.10,
    emergency_prob=0.80,
    comorbidity_probs={},
    typical_medications={
        "抗菌": ["头孢曲松", "青霉素"],
    },
    typical_imaging=["胸部X线"],
    los_distribution=[(5, 20), (7, 35), (10, 30), (14, 15)],
)

PEDIATRIC_DIARRHEA = DiseaseProfile(
    name="小儿腹泻",
    icd10_codes=["A09"],
    age_range=(0, 5),
    gender="B",
    primary_departments=["DEPT022"],
    order_lab_prob=0.80,
    order_imaging_prob=0.10,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.02,
    ecg_prob=0.0,
    outpatient_prob=0.90,
    emergency_prob=0.07,
    comorbidity_probs={
        "J18": 0.10,
        "E11": 0.02,
    },
    lab_abnormalities={
        "K": LabAbnormality("K", "low", [(0.3, 0.90), (0.2, 0.85)]),
        "NA": LabAbnormality("NA", "low", [(0.3, 0.92), (0.2, 0.88)]),
    },
    typical_medications={
        "止泻": ["蒙脱石散", "益生菌"],
        "补液": ["口服补液盐"],
    },
    typical_imaging=["腹部超声"],
)

PEDIATRIC_PNEUMONIA = DiseaseProfile(
    name="儿童肺炎",
    icd10_codes=["J18"],
    age_range=(0, 14),
    gender="B",
    primary_departments=["DEPT022"],
    order_lab_prob=0.90,
    order_imaging_prob=0.70,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.05,
    ecg_prob=0.02,
    outpatient_prob=0.60,
    emergency_prob=0.30,
    comorbidity_probs={
        "J45": 0.15,
        "A09": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.4, 1.4), (0.3, 1.8), (0.2, 2.2)]),
        "NEUT%": LabAbnormality("NEUT%", "high", [(0.3, 1.15), (0.2, 1.25)]),
        "CRP": LabAbnormality("CRP", "high", [(0.4, 2.0), (0.3, 3.0)]),
    },
    typical_medications={
        "抗菌": ["阿莫西林克拉维酸钾", "头孢曲松"],
    },
    typical_imaging=["胸部X线"],
)

# ------------------------------------------------------------------
# 17. 肿瘤科（补充）
# ------------------------------------------------------------------

GASTRIC_CANCER = DiseaseProfile(
    name="胃恶性肿瘤",
    icd10_codes=["C16"],
    age_range=(40, None),
    gender="M",
    age_distribution="skewed_old",
    primary_departments=["DEPT009", "DEPT012"],
    order_lab_prob=0.95,
    order_imaging_prob=0.90,
    order_medication_prob=0.85,
    surgery_prob=0.50,
    icu_prob=0.08,
    ecg_prob=0.15,
    outpatient_prob=0.20,
    emergency_prob=0.15,
    comorbidity_probs={
        "I10": 0.20,
        "E11": 0.10,
        "N18": 0.10,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.4, 0.85), (0.3, 0.75), (0.2, 0.65)]),
        "ALB": LabAbnormality("ALB", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "CEA": LabAbnormality("CEA", "high", [(0.4, 2.0), (0.3, 3.0)]),
    },
    typical_medications={
        "化疗": ["注射用奥沙利铂", "注射用紫杉醇"],
        "靶向": ["曲妥珠单抗"],
    },
    typical_imaging=["腹部CT", "胃镜", "PET-CT"],
    typical_surgeries=["胃癌根治术", "胃大部切除术"],
    los_distribution=[(7, 15), (10, 25), (14, 30), (21, 20), (28, 10)],
)

COLORECTAL_CANCER = DiseaseProfile(
    name="结肠直肠恶性肿瘤",
    icd10_codes=["C18", "C20"],
    age_range=(45, None),
    gender="M",
    age_distribution="skewed_old",
    primary_departments=["DEPT009", "DEPT012"],
    order_lab_prob=0.95,
    order_imaging_prob=0.90,
    order_medication_prob=0.85,
    surgery_prob=0.55,
    icu_prob=0.08,
    ecg_prob=0.15,
    outpatient_prob=0.25,
    emergency_prob=0.15,
    comorbidity_probs={
        "I10": 0.20,
        "E11": 0.15,
        "N18": 0.10,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.4, 0.85), (0.3, 0.75)]),
        "ALB": LabAbnormality("ALB", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "CEA": LabAbnormality("CEA", "high", [(0.4, 2.0), (0.3, 3.0)]),
    },
    typical_medications={
        "化疗": ["注射用奥沙利铂", "注射用紫杉醇"],
        "靶向": ["贝伐珠单抗"],
    },
    typical_imaging=["腹部CT", "肠镜", "PET-CT"],
    typical_surgeries=["结肠癌根治术", "直肠癌根治术"],
    los_distribution=[(7, 15), (10, 25), (14, 30), (21, 20), (28, 10)],
)

LIVER_CANCER = DiseaseProfile(
    name="肝恶性肿瘤",
    icd10_codes=["C22"],
    age_range=(40, None),
    gender="M",
    age_distribution="skewed_old",
    primary_departments=["DEPT009", "DEPT003"],
    order_lab_prob=0.95,
    order_imaging_prob=0.90,
    order_medication_prob=0.80,
    surgery_prob=0.30,
    icu_prob=0.10,
    ecg_prob=0.15,
    outpatient_prob=0.30,
    emergency_prob=0.15,
    comorbidity_probs={
        "N18": 0.15,
        "I10": 0.15,
        "E11": 0.10,
    },
    lab_abnormalities={
        "ALB": LabAbnormality("ALB", "low", [(0.4, 0.85), (0.3, 0.75)]),
        "ALT": LabAbnormality("ALT", "high", [(0.4, 2.0), (0.3, 3.0), (0.2, 5.0)]),
        "AST": LabAbnormality("AST", "high", [(0.4, 2.0), (0.3, 3.0), (0.2, 5.0)]),
        "AFP": LabAbnormality("AFP", "high", [(0.5, 5.0), (0.3, 10.0), (0.2, 20.0)]),
    },
    typical_medications={
        "靶向": ["索拉非尼", "仑伐替尼"],
        "化疗": ["注射用奥沙利铂"],
    },
    typical_imaging=["腹部CT", "腹部MRI", "PET-CT"],
    typical_surgeries=["肝部分切除术", "肝移植术"],
    los_distribution=[(7, 15), (10, 25), (14, 30), (21, 20), (28, 10)],
)

PROSTATE_CANCER = DiseaseProfile(
    name="前列腺恶性肿瘤",
    icd10_codes=["C61"],
    age_range=(55, None),
    gender="M",
    age_distribution="skewed_old",
    primary_departments=["DEPT015", "DEPT009"],
    order_lab_prob=0.90,
    order_imaging_prob=0.85,
    order_medication_prob=0.80,
    surgery_prob=0.40,
    icu_prob=0.03,
    ecg_prob=0.10,
    outpatient_prob=0.40,
    emergency_prob=0.05,
    comorbidity_probs={
        "I10": 0.20,
        "E11": 0.15,
        "N18": 0.10,
    },
    lab_abnormalities={
        "PSA": LabAbnormality("PSA", "high", [(0.4, 3.0), (0.3, 5.0), (0.2, 10.0)]),
        "ALB": LabAbnormality("ALB", "low", [(0.2, 0.90), (0.1, 0.85)]),
    },
    typical_medications={
        "内分泌": ["亮丙瑞林", "比卡鲁胺"],
        "化疗": ["注射用多西他赛"],
    },
    typical_imaging=["前列腺MRI", "骨扫描", "PET-CT"],
    typical_surgeries=["前列腺癌根治术"],
    los_distribution=[(5, 15), (7, 30), (10, 30), (14, 20), (21, 5)],
)

BREAST_CANCER = DiseaseProfile(
    name="乳腺恶性肿瘤",
    icd10_codes=["C50"],
    age_range=(35, None),
    gender="F",
    age_distribution="skewed_old",
    primary_departments=["DEPT009", "DEPT012"],
    order_lab_prob=0.90,
    order_imaging_prob=0.90,
    order_medication_prob=0.85,
    surgery_prob=0.50,
    icu_prob=0.03,
    ecg_prob=0.10,
    outpatient_prob=0.30,
    emergency_prob=0.05,
    comorbidity_probs={
        "I10": 0.15,
        "E11": 0.10,
        "M32": 0.05,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.90), (0.2, 0.85)]),
        "ALB": LabAbnormality("ALB", "low", [(0.2, 0.90), (0.1, 0.85)]),
        "CA153": LabAbnormality("CA153", "high", [(0.3, 2.0), (0.2, 3.0)]),
        "CEA": LabAbnormality("CEA", "high", [(0.3, 1.5), (0.2, 2.0)]),
    },
    typical_medications={
        "化疗": ["注射用紫杉醇", "注射用多柔比星"],
        "靶向": ["曲妥珠单抗"],
        "内分泌": ["他莫昔芬", "来曲唑"],
    },
    typical_imaging=["乳腺钼靶", "乳腺超声", "胸部CT", "PET-CT"],
    typical_surgeries=["乳腺癌根治术", "保乳手术"],
    los_distribution=[(3, 20), (5, 35), (7, 30), (10, 15)],
)

LYMPHOMA = DiseaseProfile(
    name="淋巴瘤",
    icd10_codes=["C81", "C82", "C83", "C85"],
    age_range=(15, None),
    gender="B",
    primary_departments=["DEPT009", "DEPT006"],
    order_lab_prob=0.95,
    order_imaging_prob=0.80,
    order_medication_prob=0.85,
    surgery_prob=0.05,
    icu_prob=0.05,
    ecg_prob=0.10,
    outpatient_prob=0.40,
    emergency_prob=0.10,
    comorbidity_probs={
        "D64": 0.25,
        "J18": 0.15,
        "N18": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "variable", [(0.3, 0.3), (0.3, 2.0), (0.2, 5.0)]),
        "HGB": LabAbnormality("HGB", "low", [(0.4, 0.85), (0.3, 0.75), (0.2, 0.65)]),
        "PLT": LabAbnormality("PLT", "low", [(0.3, 0.80), (0.2, 0.70)]),
        "LDH": LabAbnormality("LDH", "high", [(0.4, 1.5), (0.3, 2.0), (0.2, 3.0)]),
    },
    typical_medications={
        "化疗": ["注射用环磷酰胺", "注射用多柔比星", "注射用长春新碱"],
        "靶向": ["利妥昔单抗"],
    },
    typical_imaging=["全身CT", "PET-CT", "骨髓穿刺"],
    los_distribution=[(7, 15), (10, 25), (14, 30), (21, 20), (28, 10)],
)

# ------------------------------------------------------------------
# 18. 眼科 / 耳鼻喉 / 口腔
# ------------------------------------------------------------------

CATARACT = DiseaseProfile(
    name="老年性白内障",
    icd10_codes=["H25"],
    age_range=(50, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT024"],
    order_lab_prob=0.50,
    order_imaging_prob=0.20,
    order_medication_prob=0.40,
    surgery_prob=0.80,
    icu_prob=0.0,
    ecg_prob=0.05,
    outpatient_prob=0.90,
    emergency_prob=0.01,
    comorbidity_probs={
        "I10": 0.25,
        "E11": 0.15,
    },
    typical_medications={
        "眼药水": ["左氧氟沙星滴眼液", "妥布霉素地塞米松滴眼液"],
    },
    typical_imaging=["眼部超声"],
    typical_surgeries=["白内障超声乳化术"],
    los_distribution=[(1, 70), (2, 25), (3, 5)],
)

GLAUCOMA = DiseaseProfile(
    name="青光眼",
    icd10_codes=["H40"],
    age_range=(40, None),
    gender="B",
    age_distribution="skewed_old",
    primary_departments=["DEPT024"],
    order_lab_prob=0.60,
    order_imaging_prob=0.40,
    order_medication_prob=0.85,
    surgery_prob=0.15,
    icu_prob=0.0,
    ecg_prob=0.02,
    outpatient_prob=0.90,
    emergency_prob=0.05,
    comorbidity_probs={
        "I10": 0.15,
        "E11": 0.10,
    },
    typical_medications={
        "降眼压": ["噻吗洛尔滴眼液", "拉坦前列素滴眼液", "布林佐胺滴眼液"],
    },
    typical_imaging=["眼底照相", "OCT", "视野检查"],
    typical_surgeries=["小梁切除术", "青光眼引流阀植入术"],
)

REFRACTIVE_ERROR = DiseaseProfile(
    name="屈光不正",
    icd10_codes=["H52"],
    age_range=(5, None),
    gender="B",
    primary_departments=["DEPT024"],
    order_lab_prob=0.10,
    order_imaging_prob=0.10,
    order_medication_prob=0.05,
    surgery_prob=0.05,
    icu_prob=0.0,
    ecg_prob=0.0,
    outpatient_prob=0.98,
    emergency_prob=0.0,
    comorbidity_probs={},
    typical_medications={},
    typical_imaging=["验光", "角膜地形图"],
    typical_surgeries=["LASIK", "ICL植入术"],
)

SINUSITIS = DiseaseProfile(
    name="鼻窦炎",
    icd10_codes=["J32"],
    age_range=(5, None),
    gender="B",
    primary_departments=["DEPT025"],
    order_lab_prob=0.50,
    order_imaging_prob=0.70,
    order_medication_prob=0.85,
    surgery_prob=0.10,
    icu_prob=0.0,
    ecg_prob=0.0,
    outpatient_prob=0.90,
    emergency_prob=0.03,
    comorbidity_probs={
        "J45": 0.15,
        "J18": 0.08,
    },
    typical_medications={
        "抗菌": ["阿莫西林克拉维酸钾"],
        "鼻喷": ["布地奈德鼻喷雾剂", "糠酸莫米松鼻喷雾剂"],
    },
    typical_imaging=["鼻窦CT", "鼻窦X线"],
    typical_surgeries=["鼻内镜手术"],
)

TONSILLITIS = DiseaseProfile(
    name="扁桃体炎",
    icd10_codes=["J03"],
    age_range=(3, 35),
    gender="B",
    primary_departments=["DEPT025"],
    order_lab_prob=0.80,
    order_imaging_prob=0.10,
    order_medication_prob=0.90,
    surgery_prob=0.05,
    icu_prob=0.0,
    ecg_prob=0.01,
    outpatient_prob=0.90,
    emergency_prob=0.07,
    comorbidity_probs={
        "J18": 0.10,
        "J32": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.4, 1.3), (0.3, 1.6)]),
        "NEUT%": LabAbnormality("NEUT%", "high", [(0.3, 1.1), (0.2, 1.2)]),
    },
    typical_medications={
        "抗菌": ["阿莫西林", "头孢呋辛"],
        "退热": ["布洛芬缓释胶囊"],
    },
    typical_imaging=["颈部X线"],
    typical_surgeries=["扁桃体切除术"],
)

PERIODONTITIS = DiseaseProfile(
    name="牙周炎",
    icd10_codes=["K05"],
    age_range=(18, None),
    gender="B",
    primary_departments=["DEPT026"],
    order_lab_prob=0.30,
    order_imaging_prob=0.60,
    order_medication_prob=0.70,
    surgery_prob=0.10,
    icu_prob=0.0,
    ecg_prob=0.0,
    outpatient_prob=0.95,
    emergency_prob=0.03,
    comorbidity_probs={
        "E11": 0.15,
        "I10": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.2, 1.1), (0.1, 1.2)]),
    },
    typical_medications={
        "抗菌": ["甲硝唑", "阿莫西林"],
    },
    typical_imaging=["牙片", "口腔全景片"],
    typical_surgeries=["牙周翻瓣术", "牙龈切除术"],
)

# ------------------------------------------------------------------
# 19. 急诊科
# ------------------------------------------------------------------

MULTIPLE_TRAUMA = DiseaseProfile(
    name="多发伤",
    icd10_codes=["T07"],
    age_range=(0, None),
    gender="M",
    primary_departments=["DEPT029", "DEPT014", "DEPT013"],
    order_lab_prob=0.98,
    order_imaging_prob=0.95,
    order_medication_prob=0.90,
    surgery_prob=0.50,
    icu_prob=0.40,
    ecg_prob=0.40,
    outpatient_prob=0.0,
    emergency_prob=1.0,
    comorbidity_probs={
        "S42": 0.20,
        "S72": 0.15,
        "S06": 0.10,
        "I61": 0.05,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.4, 0.85), (0.3, 0.75), (0.2, 0.65)]),
        "D-Dimer": LabAbnormality("D-Dimer", "high", [(0.4, 2.0), (0.3, 3.0)]),
    },
    typical_medications={
        "镇痛": ["吗啡注射液", "地佐辛注射液"],
        "抗凝": ["低分子肝素钙注射液"],
    },
    typical_imaging=["全身CT", "X光", "超声FAST"],
    typical_surgeries=["清创缝合术", "骨折内固定术", "开颅术"],
    los_distribution=[(3, 10), (5, 20), (7, 30), (10, 25), (14, 15)],
)

ACUTE_POISONING = DiseaseProfile(
    name="急性中毒",
    icd10_codes=["T36-T65"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT029", "DEPT003"],
    order_lab_prob=0.95,
    order_imaging_prob=0.30,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.20,
    ecg_prob=0.30,
    outpatient_prob=0.05,
    emergency_prob=0.90,
    comorbidity_probs={
        "N18": 0.10,
        "I10": 0.10,
    },
    lab_abnormalities={
        "CREA": LabAbnormality("CREA", "high", [(0.2, 1.2), (0.1, 1.5)]),
        "ALT": LabAbnormality("ALT", "high", [(0.2, 1.5), (0.1, 2.0)]),
        "AST": LabAbnormality("AST", "high", [(0.2, 1.5), (0.1, 2.0)]),
    },
    typical_medications={
        "解毒": ["纳洛酮", "阿托品"],
        "保肝": ["谷胱甘肽", "异甘草酸镁"],
    },
    typical_imaging=["腹部超声", "头颅CT"],
    los_distribution=[(1, 30), (2, 35), (3, 25), (5, 10)],
)

SHOCK = DiseaseProfile(
    name="休克",
    icd10_codes=["R57"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT029", "DEPT030"],
    order_lab_prob=0.98,
    order_imaging_prob=0.50,
    order_medication_prob=0.95,
    surgery_prob=0.20,
    icu_prob=0.80,
    ecg_prob=0.60,
    outpatient_prob=0.0,
    emergency_prob=1.0,
    comorbidity_probs={
        "I21": 0.10,
        "S06": 0.10,
        "J18": 0.10,
    },
    lab_abnormalities={
        "HGB": LabAbnormality("HGB", "low", [(0.3, 0.85), (0.2, 0.75)]),
        "CREA": LabAbnormality("CREA", "high", [(0.3, 1.3), (0.2, 1.6)]),
        "LAC": LabAbnormality("LAC", "high", [(0.5, 2.0), (0.3, 3.0), (0.2, 5.0)]),
    },
    typical_medications={
        "升压": ["去甲肾上腺素", "多巴胺"],
        "扩容": ["乳酸林格", "羟乙基淀粉"],
    },
    typical_imaging=["超声FAST", "胸部X线", "ECG"],
    los_distribution=[(1, 20), (2, 30), (3, 30), (5, 15), (7, 5)],
)

CHEST_PAIN_UNDIAGNOSED = DiseaseProfile(
    name="胸痛待查",
    icd10_codes=["R07"],
    age_range=(18, None),
    gender="B",
    primary_departments=["DEPT029", "DEPT001"],
    order_lab_prob=0.90,
    order_imaging_prob=0.80,
    order_medication_prob=0.70,
    surgery_prob=0.05,
    icu_prob=0.10,
    ecg_prob=0.90,
    outpatient_prob=0.10,
    emergency_prob=0.85,
    comorbidity_probs={
        "I21": 0.15,
        "I20": 0.10,
        "I10": 0.10,
    },
    lab_abnormalities={
        "TnI": LabAbnormality("TnI", "high", [(0.2, 1.5), (0.1, 3.0)]),
        "D-Dimer": LabAbnormality("D-Dimer", "high", [(0.2, 1.5), (0.1, 2.0)]),
    },
    typical_medications={
        "镇痛": ["地佐辛注射液"],
        "抗凝": ["低分子肝素钙注射液"],
    },
    typical_imaging=["胸部CT", "心脏彩超", "ECG"],
    los_distribution=[(1, 40), (2, 35), (3, 20), (5, 5)],
)

ACUTE_ABDOMEN = DiseaseProfile(
    name="急腹症",
    icd10_codes=["R10"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT029", "DEPT011", "DEPT003"],
    order_lab_prob=0.90,
    order_imaging_prob=0.90,
    order_medication_prob=0.75,
    surgery_prob=0.30,
    icu_prob=0.08,
    ecg_prob=0.05,
    outpatient_prob=0.02,
    emergency_prob=0.93,
    comorbidity_probs={
        "K35": 0.15,
        "K80": 0.10,
        "K56": 0.10,
    },
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.4, 1.3), (0.3, 1.6)]),
        "CRP": LabAbnormality("CRP", "high", [(0.4, 2.0), (0.3, 3.0)]),
    },
    typical_medications={
        "镇痛": ["地佐辛注射液"],
        "抗菌": ["头孢曲松"],
    },
    typical_imaging=["腹部CT", "腹部超声", "腹部X线"],
    typical_surgeries=["阑尾切除术", "胆囊切除术"],
    los_distribution=[(1, 20), (2, 30), (3, 30), (5, 15), (7, 5)],
)

# ------------------------------------------------------------------
# 20. 皮肤科
# ------------------------------------------------------------------

ECZEMA = DiseaseProfile(
    name="湿疹",
    icd10_codes=["L20"],
    age_range=(0, None),
    gender="B",
    primary_departments=["DEPT027"],
    order_lab_prob=0.40,
    order_imaging_prob=0.05,
    order_medication_prob=0.80,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.0,
    outpatient_prob=0.95,
    emergency_prob=0.02,
    comorbidity_probs={
        "J45": 0.15,
        "E11": 0.05,
    },
    lab_abnormalities={
        "IgE": LabAbnormality("IgE", "high", [(0.4, 1.5), (0.3, 2.0)]),
    },
    typical_medications={
        "外用": ["糠酸莫米松乳膏", "他克莫司软膏"],
        "口服": ["氯雷他定片", "西替利嗪片"],
    },
    typical_imaging=[],
)

PSORIASIS = DiseaseProfile(
    name="银屑病",
    icd10_codes=["L40"],
    age_range=(15, None),
    gender="B",
    primary_departments=["DEPT027"],
    order_lab_prob=0.50,
    order_imaging_prob=0.05,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.0,
    outpatient_prob=0.95,
    emergency_prob=0.01,
    comorbidity_probs={
        "E11": 0.10,
        "I10": 0.10,
        "M06": 0.08,
    },
    lab_abnormalities={
        "CRP": LabAbnormality("CRP", "high", [(0.3, 1.5), (0.2, 2.0)]),
        "ESR": LabAbnormality("ESR", "high", [(0.3, 1.5), (0.2, 2.0)]),
    },
    typical_medications={
        "外用": ["卡泊三醇软膏", "他扎罗汀凝胶"],
        "生物制剂": ["阿达木单抗", "司库奇尤单抗"],
    },
    typical_imaging=[],
)

# ------------------------------------------------------------------
# 21. 精神科
# ------------------------------------------------------------------

DEPRESSION = DiseaseProfile(
    name="抑郁症",
    icd10_codes=["F32"],
    age_range=(18, None),
    gender="B",
    primary_departments=["DEPT028"],
    order_lab_prob=0.50,
    order_imaging_prob=0.10,
    order_medication_prob=0.85,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.05,
    outpatient_prob=0.90,
    emergency_prob=0.05,
    comorbidity_probs={
        "I10": 0.15,
        "E11": 0.10,
        "F41": 0.20,
    },
    lab_abnormalities={},
    typical_medications={
        "抗抑郁": ["舍曲林", "帕罗西汀", "文拉法辛"],
        "镇静": ["劳拉西泮", "阿普唑仑"],
    },
    typical_imaging=["头颅MRI"],
)

ANXIETY_DISORDER = DiseaseProfile(
    name="焦虑障碍",
    icd10_codes=["F41"],
    age_range=(18, None),
    gender="B",
    primary_departments=["DEPT028"],
    order_lab_prob=0.40,
    order_imaging_prob=0.05,
    order_medication_prob=0.80,
    surgery_prob=0.0,
    icu_prob=0.0,
    ecg_prob=0.10,
    outpatient_prob=0.92,
    emergency_prob=0.06,
    comorbidity_probs={
        "F32": 0.25,
        "I10": 0.10,
    },
    lab_abnormalities={},
    typical_medications={
        "抗焦虑": ["劳拉西泮", "丁螺环酮"],
        "抗抑郁": ["舍曲林", "帕罗西汀"],
    },
    typical_imaging=[],
)

SCHIZOPHRENIA = DiseaseProfile(
    name="精神分裂症",
    icd10_codes=["F20"],
    age_range=(18, 55),
    gender="B",
    primary_departments=["DEPT028"],
    order_lab_prob=0.60,
    order_imaging_prob=0.20,
    order_medication_prob=0.90,
    surgery_prob=0.0,
    icu_prob=0.02,
    ecg_prob=0.10,
    outpatient_prob=0.70,
    emergency_prob=0.25,
    comorbidity_probs={
        "F32": 0.15,
        "F41": 0.10,
        "E11": 0.10,
    },
    lab_abnormalities={
        "PROL": LabAbnormality("PROL", "high", [(0.3, 1.5), (0.2, 2.0)]),
    },
    typical_medications={
        "抗精神病": ["奥氮平", "利培酮", "阿立哌唑", "喹硫平"],
    },
    typical_imaging=["头颅MRI", "头颅CT平扫"],
    los_distribution=[(7, 20), (14, 30), (21, 30), (28, 15), (35, 5)],
)

# ------------------------------------------------------------------
# 注册表与辅助函数
# ------------------------------------------------------------------

DISEASE_PROFILES: Dict[str, DiseaseProfile] = {
    # 心血管
    "I10": HYPERTENSION,
    "I20": ANGINA_PECTORIS,
    "I21": ACUTE_MYOCARDIAL_INFARCTION,
    "I50": HEART_FAILURE,
    "I48": ATRIAL_FIBRILLATION,
    "I25": CHRONIC_ISCHEMIC_HEART_DISEASE,
    "I63": CEREBRAL_INFARCTION,
    "I61": CEREBRAL_HEMORRHAGE,
    # 呼吸
    "J06": ACUTE_UPPER_RESPIRATORY_INFECTION,
    "J18": COMMUNITY_ACQUIRED_PNEUMONIA,
    "J44": COPD,
    "J45": ASTHMA,
    "J32": SINUSITIS,
    "J03": TONSILLITIS,
    # 消化
    "K25": GASTRIC_ULCER,
    "K29": GASTRITIS_DUODENITIS,
    "K35": ACUTE_APPENDICITIS,
    "K80": CHOLELITHIASIS,
    "K85": ACUTE_PANCREATITIS,
    "K40": INGUINAL_HERNIA,
    "K56": BOWEL_OBSTRUCTION,
    "K05": PERIODONTITIS,
    # 内分泌
    "E11": TYPE_2_DIABETES,
    "E05": THYROTOXICOSIS,
    "E66": OBESITY,
    "E78": DYSLIPIDEMIA,
    "E03": HYPOTHYROIDISM,
    "O24": GESTATIONAL_DIABETES,
    # 神经
    "G20": PARKINSON_DISEASE,
    "G40": EPILEPSY,
    "G43": MIGRAINE,
    # 肾脏
    "N18": CHRONIC_KIDNEY_DISEASE,
    "N20": NEPHROLITHIASIS,
    "N39": URINARY_TRACT_INFECTION,
    "N40": BENIGN_PROSTATIC_HYPERPLASIA,
    # 风湿
    "M06": RHEUMATOID_ARTHRITIS,
    "M32": SYSTEMIC_LUPUS,
    "M10": GOUT,
    "M16": HIP_ARTHROSIS,
    "M17": KNEE_ARTHROSIS,
    # 血液
    "D64": ANEMIA,
    "C91": LEUKEMIA,
    "C92": LEUKEMIA,
    # 骨科
    "S42": HUMERUS_FRACTURE,
    "S72": FEMUR_FRACTURE,
    "S32": SPINE_FRACTURE,
    # 心胸
    "C34": LUNG_CANCER,
    "C15": ESOPHAGEAL_CANCER,
    "Q21": CONGENITAL_HEART_DISEASE,
    # 泌尿
    "C61": PROSTATE_CANCER,
    # 神经外
    "S06": TRAUMATIC_BRAIN_INJURY,
    "S02": INTRACRANIAL_INJURY,
    # 妇科
    "D25": UTERINE_FIBROID,
    "N83": OVARIAN_CYST,
    "N72": CERVICITIS,
    # 产科
    "O80": NORMAL_DELIVERY,
    "O82": CESAREAN_SECTION,
    # 儿科
    "P59": NEONATAL_JAUNDICE,
    "P23": NEONATAL_PNEUMONIA,
    "A09": PEDIATRIC_DIARRHEA,
    # 肿瘤（补充）
    "C16": GASTRIC_CANCER,
    "C18": COLORECTAL_CANCER,
    "C20": COLORECTAL_CANCER,
    "C22": LIVER_CANCER,
    "C50": BREAST_CANCER,
    "C81": LYMPHOMA,
    "C82": LYMPHOMA,
    "C83": LYMPHOMA,
    "C85": LYMPHOMA,
    # 眼耳鼻喉口腔
    "H25": CATARACT,
    "H40": GLAUCOMA,
    "H52": REFRACTIVE_ERROR,
    # 急诊
    "T07": MULTIPLE_TRAUMA,
    "T36": ACUTE_POISONING,
    "R57": SHOCK,
    "R07": CHEST_PAIN_UNDIAGNOSED,
    "R10": ACUTE_ABDOMEN,
    # 皮肤
    "L20": ECZEMA,
    "L40": PSORIASIS,
    # 精神
    "F32": DEPRESSION,
    "F41": ANXIETY_DISORDER,
    "F20": SCHIZOPHRENIA,
}


# 反向查找：通过疾病名称找编码
def icd_for_name(name: str) -> Optional[str]:
    """通过疾病名称查找其主 ICD-10 编码。"""
    for code, profile in DISEASE_PROFILES.items():
        if profile.name == name:
            return code
    return None


def select_profile_for_icd(icd_code: str) -> Optional[DiseaseProfile]:
    """通过 ICD-10 编码获取疾病画像。"""
    return DISEASE_PROFILES.get(icd_code)


def random_disease_profile() -> Tuple[str, DiseaseProfile]:
    """随机选择一个疾病画像，返回 (icd_code, profile)。"""
    code = random.choice(list(DISEASE_PROFILES.keys()))
    return code, DISEASE_PROFILES[code]


def profiles_matching_patient(age: int, gender: str) -> List[DiseaseProfile]:
    """筛选符合患者画像约束的所有疾病。"""
    return [p for p in DISEASE_PROFILES.values() if p.matches_patient(age, gender)]


def random_profile_for_patient(age: int, gender: str) -> Optional[DiseaseProfile]:
    """随机选择一个符合患者画像约束的疾病。"""
    matching = profiles_matching_patient(age, gender)
    if matching:
        return random.choice(matching)
    return None
