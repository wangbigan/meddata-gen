"""疾病画像定义：诊断驱动的医学一致性模型。

每个 DiseaseProfile 描述一种疾病在数据生成中的典型表现，包括：
- 关联 ICD-10 编码
- 典型科室
- 异常检验项及分布
- 典型用药、影像、手术
- 住院天数分布
- 预后概率
- 共病概率
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class LabAbnormality:
    """检验项异常模式。"""

    item_code: str  # LAB_ITEMS 中的 code，如 "WBC"
    direction: str  # "high" | "low" | "variable"
    # (概率, 相对于参考上限/下限的倍数分布)
    severity_dist: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class DiseaseProfile:
    """疾病临床画像。"""

    name: str
    icd10_codes: List[str]
    typical_departments: List[str]
    lab_abnormalities: Dict[str, LabAbnormality]
    typical_medications: Dict[str, List[str]]
    typical_imaging: List[str]
    typical_surgeries: List[str]
    los_distribution: List[Tuple[int, float]]  # (天数, 权重)
    outcome_probs: Dict[str, float]
    comorbidity_probs: Dict[str, float]
    icu_prob: float = 0.0
    surgery_prob: float = 0.0
    outpatient_prob: float = 0.0  # 该疾病以门诊为主的比例


# ------------------------------------------------------------------
# 预定义疾病画像
# ------------------------------------------------------------------

COMMUNITY_ACQUIRED_PNEUMONIA = DiseaseProfile(
    name="社区获得性肺炎",
    icd10_codes=["J18.9", "J15.9", "J12.9"],
    typical_departments=["DEPT002", "DEPT010"],  # 呼吸内科, 感染科
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.4, 1.5), (0.35, 2.0), (0.2, 3.0), (0.05, 4.0)]),
        "NEUT%": LabAbnormality("NEUT%", "high", [(0.5, 1.2), (0.3, 1.5), (0.15, 1.8), (0.05, 2.0)]),
        "PLT": LabAbnormality("PLT", "high", [(0.3, 1.1), (0.2, 1.3)]),
    },
    typical_medications={
        "抗菌药物": ["头孢曲松", "头孢噻肟", "左氧氟沙星", "莫西沙星"],
        "化痰": ["氨溴索", "乙酰半胱氨酸"],
    },
    typical_imaging=["胸部CT平扫", "胸部X线正侧位"],
    typical_surgeries=[],
    los_distribution=[(3, 10), (5, 20), (7, 25), (10, 20), (14, 15), (21, 10)],
    outcome_probs={"治愈": 0.60, "好转": 0.30, "未愈": 0.07, "死亡": 0.03},
    comorbidity_probs={"2型糖尿病": 0.15, "慢性阻塞性肺病": 0.20},
    icu_prob=0.05,
    surgery_prob=0.0,
    outpatient_prob=0.20,
)

ACUTE_MYOCARDIAL_INFARCTION = DiseaseProfile(
    name="急性前壁心肌梗死",
    icd10_codes=["I21.0", "I21.1", "I21.2", "I21.3", "I21.4"],
    typical_departments=["DEPT001"],  # 心血管内科
    lab_abnormalities={
        "CK-MB": LabAbnormality("CK-MB", "high", [(0.3, 2.0), (0.4, 3.0), (0.2, 5.0), (0.1, 8.0)]),
        "CK": LabAbnormality("CK", "high", [(0.3, 2.0), (0.4, 3.0), (0.2, 5.0), (0.1, 10.0)]),
        "LDH": LabAbnormality("LDH", "high", [(0.4, 1.5), (0.35, 2.0), (0.2, 3.0), (0.05, 4.0)]),
        "AST": LabAbnormality("AST", "high", [(0.4, 1.8), (0.35, 2.5), (0.2, 4.0), (0.05, 6.0)]),
    },
    typical_medications={
        "抗血小板": ["阿司匹林", "氯吡格雷", "替格瑞洛"],
        "调脂": ["阿托伐他汀", "瑞舒伐他汀"],
        "降压": ["美托洛尔", "贝那普利"],
        "扩冠": ["硝酸异山梨酯", "单硝酸异山梨酯"],
    },
    typical_imaging=["冠状动脉CTA", "心脏彩超", "胸部X线正侧位"],
    typical_surgeries=["冠状动脉搭桥术", "经皮冠状动脉介入治疗"],
    los_distribution=[(3, 10), (5, 20), (7, 30), (10, 20), (14, 15), (21, 5)],
    outcome_probs={"治愈": 0.50, "好转": 0.35, "未愈": 0.10, "死亡": 0.05},
    comorbidity_probs={"2型糖尿病": 0.30, "高血压": 0.40, "高脂血症": 0.35},
    icu_prob=0.25,
    surgery_prob=0.40,
    outpatient_prob=0.05,
)

TYPE_2_DIABETES = DiseaseProfile(
    name="2型糖尿病",
    icd10_codes=["E11.9", "E11.0", "E11.1", "E11.2"],
    typical_departments=["DEPT004"],  # 内分泌科
    lab_abnormalities={
        "GLU": LabAbnormality("GLU", "high", [(0.5, 1.3), (0.3, 1.6), (0.15, 2.0), (0.05, 3.0)]),
        "HbA1c": LabAbnormality("HbA1c", "high", [(0.4, 1.2), (0.35, 1.4), (0.2, 1.6), (0.05, 2.0)]),
        "TG": LabAbnormality("TG", "high", [(0.4, 1.5), (0.3, 2.0), (0.2, 3.0), (0.1, 4.0)]),
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.4, 1.3), (0.35, 1.5), (0.2, 1.8), (0.05, 2.2)]),
    },
    typical_medications={
        "降糖": ["二甲双胍", "格列美脲", "阿卡波糖", "胰岛素"],
        "调脂": ["阿托伐他汀"],
    },
    typical_imaging=["眼底照相", "颈动脉超声", "下肢动脉超声"],
    typical_surgeries=[],
    los_distribution=[(3, 15), (5, 25), (7, 30), (10, 20), (14, 10)],
    outcome_probs={"治愈": 0.10, "好转": 0.70, "未愈": 0.18, "死亡": 0.02},
    comorbidity_probs={"高血压": 0.50, "高脂血症": 0.40, "冠心病": 0.25},
    icu_prob=0.02,
    surgery_prob=0.0,
    outpatient_prob=0.80,
)

CEREBRAL_HEMORRHAGE = DiseaseProfile(
    name="脑出血",
    icd10_codes=["I61.9", "I61.0", "I61.1", "I61.2"],
    typical_departments=["DEPT008", "DEPT013"],  # 神经内科, 神经外科
    lab_abnormalities={
        "WBC": LabAbnormality("WBC", "high", [(0.4, 1.3), (0.3, 1.8), (0.2, 2.5), (0.1, 3.5)]),
        "GLU": LabAbnormality("GLU", "high", [(0.4, 1.2), (0.3, 1.5), (0.2, 2.0), (0.1, 2.5)]),
        "D-Dimer": LabAbnormality("D-Dimer", "high", [(0.3, 2.0), (0.3, 3.0), (0.2, 5.0), (0.2, 8.0)]),
    },
    typical_medications={
        "脱水": ["甘露醇", "呋塞米"],
        "降压": ["乌拉地尔", "尼莫地平"],
        "止血": ["氨甲环酸", "酚磺乙胺"],
    },
    typical_imaging=["头颅CT平扫", "头颅CT增强", "头颅MRI"],
    typical_surgeries=["开颅术", "脑室穿刺引流术"],
    los_distribution=[(7, 10), (14, 25), (21, 30), (28, 20), (35, 10), (42, 5)],
    outcome_probs={"治愈": 0.20, "好转": 0.40, "未愈": 0.25, "死亡": 0.15},
    comorbidity_probs={"高血压": 0.60, "2型糖尿病": 0.20},
    icu_prob=0.80,
    surgery_prob=0.30,
    outpatient_prob=0.02,
)

CEREBRAL_INFARCTION = DiseaseProfile(
    name="脑梗死",
    icd10_codes=["I63.9", "I63.0", "I63.1", "I63.2", "I63.3"],
    typical_departments=["DEPT008", "DEPT013"],  # 神经内科, 神经外科
    lab_abnormalities={
        "D-Dimer": LabAbnormality("D-Dimer", "high", [(0.3, 1.5), (0.3, 2.0), (0.2, 3.0), (0.2, 5.0)]),
        "LDL-C": LabAbnormality("LDL-C", "high", [(0.4, 1.2), (0.3, 1.5), (0.2, 1.8), (0.1, 2.2)]),
        "TC": LabAbnormality("TC", "high", [(0.4, 1.2), (0.3, 1.5), (0.2, 1.8), (0.1, 2.0)]),
    },
    typical_medications={
        "抗血小板": ["阿司匹林", "氯吡格雷"],
        "调脂": ["阿托伐他汀", "瑞舒伐他汀"],
        "改善循环": ["丁苯酞", "银杏叶提取物"],
    },
    typical_imaging=["头颅CT平扫", "头颅MRI", "颈动脉CTA"],
    typical_surgeries=["颈动脉内膜剥脱术"],
    los_distribution=[(5, 10), (7, 20), (10, 25), (14, 25), (21, 15), (28, 5)],
    outcome_probs={"治愈": 0.25, "好转": 0.45, "未愈": 0.22, "死亡": 0.08},
    comorbidity_probs={"高血压": 0.55, "2型糖尿病": 0.25, "高脂血症": 0.35},
    icu_prob=0.15,
    surgery_prob=0.10,
    outpatient_prob=0.10,
)

# ------------------------------------------------------------------
# 疾病注册表
# ------------------------------------------------------------------

DISEASE_PROFILES: Dict[str, DiseaseProfile] = {
    "J18.9": COMMUNITY_ACQUIRED_PNEUMONIA,
    "J15.9": COMMUNITY_ACQUIRED_PNEUMONIA,
    "J12.9": COMMUNITY_ACQUIRED_PNEUMONIA,
    "I21.0": ACUTE_MYOCARDIAL_INFARCTION,
    "I21.1": ACUTE_MYOCARDIAL_INFARCTION,
    "I21.2": ACUTE_MYOCARDIAL_INFARCTION,
    "I21.3": ACUTE_MYOCARDIAL_INFARCTION,
    "I21.4": ACUTE_MYOCARDIAL_INFARCTION,
    "E11.9": TYPE_2_DIABETES,
    "E11.0": TYPE_2_DIABETES,
    "E11.1": TYPE_2_DIABETES,
    "E11.2": TYPE_2_DIABETES,
    "I61.9": CEREBRAL_HEMORRHAGE,
    "I61.0": CEREBRAL_HEMORRHAGE,
    "I61.1": CEREBRAL_HEMORRHAGE,
    "I61.2": CEREBRAL_HEMORRHAGE,
    "I63.9": CEREBRAL_INFARCTION,
    "I63.0": CEREBRAL_INFARCTION,
    "I63.1": CEREBRAL_INFARCTION,
    "I63.2": CEREBRAL_INFARCTION,
    "I63.3": CEREBRAL_INFARCTION,
}


def select_profile_for_icd(icd_code: str) -> Optional[DiseaseProfile]:
    """根据 ICD-10 编码查找疾病画像。"""
    # 先精确匹配
    if icd_code in DISEASE_PROFILES:
        return DISEASE_PROFILES[icd_code]
    # 再尝试前缀匹配（如 I21.01 匹配 I21.0）
    for key in sorted(DISEASE_PROFILES.keys(), key=len, reverse=True):
        if icd_code.startswith(key):
            return DISEASE_PROFILES[key]
    return None


def random_disease_profile() -> Tuple[str, DiseaseProfile]:
    """随机选择一个有画像的疾病。"""
    key = random.choice(list(DISEASE_PROFILES.keys()))
    return key, DISEASE_PROFILES[key]
