"""病案事件处理器：病案首页、诊断、手术、肿瘤登记。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from meddata_gen.core.events import EventContext, MedicalEvent
from meddata_gen.core.handlers._common import maybe, next_id
from meddata_gen.seed_data import ICD10_DIAGNOSES


def _sample_from_ctx(ctx: EventContext, table_name: str, col_idx: int = None, value = None):
    """从 ctx.dict_cache 中随机抽样。支持按列过滤。"""
    cache = ctx.dict_cache.get(table_name, [])
    if not cache:
        return None
    if col_idx is not None and value is not None:
        filtered = [r for r in cache if len(r) > col_idx and r[col_idx] == value]
        if filtered:
            return random.choice(filtered)
    return random.choice(cache)


def register_bingan_handlers(materializer) -> None:
    materializer.register("bingan", "bingan_record", _handle_bingan_record)


# ------------------------------------------------------------------
# 病案首页
# ------------------------------------------------------------------

def _handle_bingan_record(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    counter_mr = ctx.state.setdefault("bingan_mr_counter", [0])
    counter_dx = ctx.state.setdefault("bingan_dx_counter", [0])
    counter_sx = ctx.state.setdefault("bingan_sx_counter", [0])

    mr_id = next_id("MR", counter_mr)
    record_time = event.timestamp

    diagnosis = ctx.primary_diagnosis or random.choice(ICD10_DIAGNOSES)
    diagnosis_name = diagnosis[1] if isinstance(diagnosis, tuple) else diagnosis
    diagnosis_code = diagnosis[0] if isinstance(diagnosis, tuple) else None

    days = (
        (ctx.discharge_time - ctx.admission_time).days
        if ctx.discharge_time and ctx.admission_time
        else random.randint(3, 14)
    )

    total_cost = round(random.uniform(2000, 150000), 2)

    # medical_records 行（对齐 schema 所有列）
    drug_cost = round(total_cost * random.uniform(0.2, 0.4), 2)
    surgery_cost = round(total_cost * random.uniform(0.05, 0.2), 2)
    mr_row = (
        mr_id,
        ctx.patient_id,
        ctx.visit_id,
        f"MR{random.randint(100000, 999999)}",  # medical_record_no
        ctx.admission_time,
        ctx.discharge_time,
        days,
        ctx.department_id,
        ctx.department_id,
        maybe("未转科", 0.80),
        1,
        random.choice(["急诊", "门诊", "其他医疗机构转入"]),
        random.choice(["医嘱离院", "医嘱转院", "非医嘱离院", "死亡", "其他"]),
        random.choice(["治愈", "好转", "未愈", "死亡", "其他"]),
        diagnosis_name,
        diagnosis_code,
        maybe(diagnosis_code, 0.10),  # principal_diagnosis_code
        maybe("高血压、糖尿病", 0.30),
        None,                       # external_cause
        None,                       # external_cause_icd
        maybe("病理诊断待完善", 0.20),
        maybe("", 0.20),            # pathological_code
        random.randint(0, 3),       # surgery_count
        total_cost,
        round(total_cost * random.uniform(0.2, 0.5), 2),  # self_pay
        drug_cost,
        round(total_cost * random.uniform(0.1, 0.25), 2), # material_cost
        round(total_cost * random.uniform(0.05, 0.15), 2),# exam_cost
        round(total_cost * random.uniform(0.05, 0.2), 2), # lab_cost
        surgery_cost,
        round(total_cost * random.uniform(0.02, 0.1), 2), # anesthesia_cost
        round(total_cost * random.uniform(0.05, 0.15), 2),# nursing_cost
        random.randint(18, 85),     # age
        None,                       # age_month
        round(random.uniform(50, 90), 2),  # weight
        None,                       # birth_weight
        maybe(f"DRG{random.randint(100, 999)}", 0.15),   # drg_code
        maybe("未分组", 0.15),      # drg_name
        maybe(f"MDC{random.randint(1, 26)}", 0.15),      # mdc_code
        random.choice(["甲", "乙", "丙"]),  # quality_control
        random.choice(["Y", "N"]),  # teaching_case
        random.choice(["Y", "N"]),  # research_case
        maybe(ctx.patient_name, 0.15),  # coding_doctor
        maybe(record_time + timedelta(days=random.randint(1, 14)), 0.25),  # coding_time
        maybe(record_time + timedelta(days=random.randint(3, 30)), 0.30),  # archive_time
        random.choice(["未归档", "已归档", "借阅中"]),  # archive_status
        datetime.now(),
        None,
    )

    # diagnoses 行（1-3 个诊断，对齐 schema 12列）
    dx_rows = []
    n_dx = random.randint(1, 3)
    for i in range(n_dx):
        dx_id = next_id("DI", counter_dx)
        if i == 0:
            dx_name = diagnosis_name
            dx_code = diagnosis_code
            dx_type = "主要诊断"
        else:
            other = random.choice(ICD10_DIAGNOSES)
            dx_name = other[1]
            dx_code = other[0]
            dx_type = random.choice(["其他诊断", "并发症", "院内感染"])

        dx_row = (
            dx_id,
            mr_id,
            ctx.patient_id,
            ctx.visit_id,
            i + 1,
            dx_type,
            dx_name,
            dx_code,
            "ICD-10",
            random.choice(["有", "临床未确定", "情况不明", "无"]),
            random.choice(["治愈", "好转", "未愈", "死亡", "其他"]),
            ctx.attending_doctor_id,
            datetime.now(),
        )
        dx_rows.append(dx_row)

    # surgeries 行（30% 有病案手术记录，对齐 schema 21列）
    sx_rows = []
    if random.random() < 0.30:
        sx_id = next_id("BGS", counter_sx)
        surgery_row = _sample_from_ctx(ctx, "surgery_dict")
        if surgery_row:
            # row: (surgery_code, surgery_name, surgery_level, department_id, duration_min, anesthesia_type)
            surgery_name = surgery_row[1]
            surgery_code = surgery_row[0]
            surgery_level = surgery_row[2] or random.choice(["I级", "II级", "III级", "IV级"])
            anesthesia_type = surgery_row[5] or random.choice(["全麻", "硬膜外麻醉", "腰麻", "局麻"])
        else:
            surgery_names = [
                ("阑尾切除术", "47.0"), ("胆囊切除术", "51.2"), ("胃大部切除术", "43.7"),
                ("冠状动脉搭桥术", "36.1"), ("心脏瓣膜置换术", "35.2"), ("肺叶切除术", "32.4"),
                ("髋关节置换术", "81.5"), ("剖宫产术", "74.1"), ("子宫切除术", "68.4"),
            ]
            surgery = random.choice(surgery_names)
            surgery_name = surgery[0]
            surgery_code = surgery[1]
            surgery_level = random.choice(["I级", "II级", "III级", "IV级"])
            anesthesia_type = random.choice(["全麻", "硬膜外麻醉", "腰麻", "局麻"])
        sx_date = ctx.admission_time + timedelta(days=random.randint(1, max(1, days - 1))) if ctx.admission_time else record_time
        sx_row = (
            sx_id,
            mr_id,
            ctx.patient_id,
            ctx.visit_id,
            1,
            surgery_name,
            surgery_code,
            sx_date.date(),
            surgery_level,
            maybe(ctx.patient_name, 0.15),
            maybe(ctx.patient_name, 0.25),
            maybe(ctx.patient_name, 0.25),
            anesthesia_type,
            maybe(ctx.patient_name, 0.15),
            random.choice(["甲", "乙", "丙"]),
            random.choice(["I", "II", "III", "IV", "V"]),
            random.choice(["Y", "N"]),
            random.choice(["Y", "N"]),
            random.choice(["Y", "N"]),
            random.choice(["Y", "N"]),
            datetime.now(),
        )
        sx_rows.append(sx_row)

    mr_cols = [
        "record_id", "patient_id", "visit_id", "medical_record_no", "admission_time",
        "discharge_time", "hospital_days", "admission_dept", "discharge_dept", "transfer_dept",
        "dept_count", "admission_type", "discharge_type", "discharge_status", "principal_diagnosis",
        "principal_diagnosis_icd", "principal_diagnosis_code", "other_diagnoses", "external_cause",
        "external_cause_icd", "pathological_diagnosis", "pathological_code", "surgery_count",
        "total_cost", "self_pay", "drug_cost", "material_cost", "exam_cost", "lab_cost",
        "surgery_cost", "anesthesia_cost", "nursing_cost", "age", "age_month", "weight",
        "birth_weight", "drg_code", "drg_name", "mdc_code", "quality_control", "teaching_case",
        "research_case", "coding_doctor", "coding_time", "archive_time", "archive_status",
        "create_time", "update_time",
    ]
    dx_cols = [
        "diagnosis_id", "record_id", "patient_id", "visit_id", "seq_no",
        "diagnosis_type", "diagnosis_name", "diagnosis_icd", "diagnosis_version",
        "in_condition", "discharge_status", "doctor_id", "create_time",
    ]
    sx_cols = [
        "surgery_id", "record_id", "patient_id", "visit_id", "seq_no",
        "surgery_name", "surgery_icd", "surgery_date", "surgery_level", "surgeon_name",
        "assistant1_name", "assistant2_name", "anesthesia_type", "anesthesia_doctor",
        "incision_healing", "anesthesia_level", "is_emergency", "is_sterile",
        "is_microscope", "is_reoperation", "create_time",
    ]

    results = [("bingan_db", "medical_records", mr_cols, [mr_row])]
    if dx_rows:
        results.append(("bingan_db", "diagnoses", dx_cols, dx_rows))
    if sx_rows:
        results.append(("bingan_db", "surgeries", sx_cols, sx_rows))

    # 20% 概率生成质控缺陷记录
    if random.random() < 0.20:
        qd_counter = ctx.state.setdefault("qd_counter", [0])
        qd_id = next_id("QD", qd_counter)
        qd_row = (
            qd_id,
            mr_id,
            ctx.patient_id,
            random.choice(["首页", "病程", "医嘱", "知情同意", "签名", "其他"]),
            maybe(random.choice(["缺项", "逻辑错误", "填写不规范", "未及时完成"]), 0.15),
            random.choice(["甲", "乙", "丙", "单项否决"]),
            maybe("病案首页填写不完整", 0.20),
            maybe(ctx.attending_doctor_id, 0.30),
            maybe(record_time + timedelta(days=random.randint(1, 7)), 0.25),
            random.choice(["Y", "N"]),
            maybe(record_time + timedelta(days=random.randint(3, 14)), 0.20),
            datetime.now(),
        )
        qd_cols = [
            "defect_id", "record_id", "patient_id", "defect_type", "defect_item",
            "severity", "description", "qc_doctor_id", "qc_time", "is_rectified", "rectify_time", "create_time",
        ]
        results.append(("bingan_db", "qc_defects", qd_cols, [qd_row]))

    return results
