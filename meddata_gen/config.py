"""医院信息系统模拟数据生成器配置：连接、规模、质量、随机种子。"""
from __future__ import annotations

# ----- 数据库连接 -----

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "wbg",
    "password": "",
    "database": "postgres",
}

# 7 个子系统数据库
DATABASES = [
    "his_db",
    "emr_db",
    "bingan_db",
    "lis_db",
    "ris_db",
    "ecg_db",
    "icu_monitoring_db",
]

# 数据库注释（写入到 PostgreSQL 的 COMMENT ON DATABASE）
DATABASE_DESCRIPTIONS = {
    "his_db": "HIS 医院信息系统：患者主索引、住院/门诊就诊、医嘱、收费、药品、科室、人员等核心业务数据",
    "emr_db": "EMR 电子病历系统：病历文档、病程记录、入院/出院记录、手术记录、护理记录等病历类数据",
    "bingan_db": "病案系统：病案首页、诊断明细、手术明细、肿瘤登记，对接医保结算/DRG/质控",
    "lis_db": "LIS 检验信息系统：申请单/标本/临检/生化/血液/微生物/药敏等检验结果",
    "ris_db": "RIS 影像信息系统：检查申请、普放/CT/MRI/超声等影像报告及设备信息",
    "ecg_db": "ECG 心电信息系统：心电检查、波形参数、分析结果",
    "icu_monitoring_db": "ICU 监护系统：入科记录、监护仪时序数据、报警事件、血气分析",
}

# ----- 随机种子 -----
# 设为整数则生成可复现；None 表示每次随机
RANDOM_SEED: int | None = None

# ----- 数据规模配置 -----

SCALE = {
    "patients": 5000,
    "inpatient_visits": 8000,      # 住院人次
    "outpatient_visits": 20000,    # 门诊人次
    "physicians": 200,
    "departments": 50,
    "drugs": 500,
    "diagnoses_pool": 2000,
    "lab_items_pool": 400,
    "time_start": "2023-01-01",
    "time_end": "2024-12-31",
}

# ----- 数据质量配置（缺陷注入） -----

QUALITY = {
    # 字段空置率范围 (min, max)
    "null_rate_range": (0.0, 0.20),
    # 按系统区分的基础空置率调整
    "system_null_adjust": {
        "his_db": 0.05,
        "emr_db": 0.08,
        "bingan_db": 0.02,
        "lis_db": 0.03,
        "ris_db": 0.06,
        "ecg_db": 0.07,
        "icu_monitoring_db": 0.04,
    },
    # 跨系统关联率 (min, max)
    "link_rate_range": (0.70, 1.00),
    # 按系统区分的关联率
    "system_link_rate": {
        "emr_db": 0.85,
        "bingan_db": 0.95,
        "lis_db": 0.90,
        "ris_db": 0.85,
        "ecg_db": 0.80,
        "icu_monitoring_db": 0.90,
    },
    # 逻辑矛盾数据比例
    "logic_error_rate": 0.015,
    # 格式不一致比例
    "format_inconsistency_rate": 0.02,
    # 重复记录比例
    "duplicate_rate": 0.005,
}

# ----- 各子系统的具体生成数量 -----

SYSTEM_SCALE = {
    "his_db": {
        "patients": 5000,
        "inpatients": 8000,
        "outpatients": 20000,
        "orders": 120000,
        "fee_items": 300000,
        "departments": 50,
        "physicians": 200,
        "drugs": 500,
    },
    "emr_db": {
        "emr_documents": 30000,
        "progress_notes": 80000,
        "admission_records": 8000,
        "discharge_records": 7800,
        "surgery_records": 4000,
        "nursing_records": 150000,
    },
    "bingan_db": {
        "medical_records": 7800,
        "diagnoses": 25000,
        "surgeries": 4500,
        "tumors": 300,
    },
    "lis_db": {
        "lab_orders": 60000,
        "specimens": 58000,
        "routine_results": 200000,
        "biochem_results": 150000,
        "blood_results": 80000,
        "microbiology": 12000,
        "antibiotic_sensitivity": 8000,
    },
    "ris_db": {
        "exam_orders": 25000,
        "xray_reports": 10000,
        "ct_reports": 8000,
        "mri_reports": 4000,
        "ultrasound_reports": 6000,
        "devices": 30,
    },
    "ecg_db": {
        "ecg_exams": 15000,
        "waveforms": 15000,
        "analyses": 15000,
    },
    "icu_monitoring_db": {
        "icu_admissions": 2000,
        "monitoring_data": 500000,
        "alarms": 50000,
        "blood_gas": 15000,
    },
}

# ----- 规模档位（CLI --scale 选项使用，相对 SYSTEM_SCALE 的乘数） -----
SCALE_PROFILES = {
    "tiny": 0.01,    # 用于冒烟测试
    "small": 0.10,
    "medium": 0.50,
    "full": 1.00,
}
