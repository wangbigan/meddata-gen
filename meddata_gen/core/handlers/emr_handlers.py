"""EMR 事件处理器：病历文档、病程记录、出入院记录、手术记录。"""
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


def register_emr_handlers(materializer) -> None:
    materializer.register("emr", "emr_admission_record", _handle_admission_record)
    materializer.register("emr", "daily_progress_note", _handle_progress_note)
    materializer.register("emr", "emr_discharge_record", _handle_discharge_record)
    materializer.register("emr", "surgery", _handle_surgery_record)
    materializer.register("emr", "emr_outpatient_record", _handle_outpatient_record)


# ------------------------------------------------------------------
# 入院记录
# ------------------------------------------------------------------

def _handle_admission_record(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    counter_doc = ctx.state.setdefault("emr_doc_counter", [0])
    counter_rec = ctx.state.setdefault("admission_rec_counter", [0])
    doc_id = next_id("EMR", counter_doc)
    rec_id = next_id("AR", counter_rec)
    write_time = event.timestamp

    diagnosis = ctx.primary_diagnosis or random.choice(ICD10_DIAGNOSES)
    diagnosis_name = diagnosis[1] if isinstance(diagnosis, tuple) else diagnosis
    diagnosis_code = diagnosis[0] if isinstance(diagnosis, tuple) else None

    # emr_documents
    doc_row = (
        doc_id,
        ctx.patient_id,
        ctx.visit_id,
        "住院",
        "入院记录",
        f"入院记录-{rec_id}",
        maybe(f"{diagnosis_name}入院记录内容...", 0.05),
        ctx.department_id,
        ctx.attending_doctor_id,
        maybe(ctx.patient_name if not ctx.attending_doctor_id else None, 0.10),
        write_time,
        maybe(write_time + timedelta(hours=random.randint(1, 24)), 0.30),
        random.choice(["0", "1"]),
        random.randint(0, 3),
        maybe(ctx.attending_doctor_id, 0.40),
        maybe(write_time + timedelta(days=random.randint(1, 3)), 0.50),
        random.choice(["甲", "乙", "丙", None]),
        random.randint(0, 3),
        random.choice(["完成", "归档"]),
        datetime.now(),
        None,
    )

    # admission_records（schema 无 document_id）
    rec_row = (
        rec_id,
        ctx.patient_id,
        ctx.visit_id,
        ctx.admission_time,
        maybe("发热伴咳嗽3天", 0.15),
        maybe("患者3天前受凉后出现发热...", 0.20),
        maybe("否认高血压、糖尿病等慢性病史", 0.18),
        maybe("无特殊", 0.30),
        maybe("无特殊", 0.35),
        maybe("否认药物及食物过敏史", 0.20),
        maybe("T 37.5C, P 85次/分, R 20次/分, BP 120/80mmHg", 0.15),
        maybe("心肺腹查体未见明显异常", 0.20),
        maybe("血常规示WBC 10.5x10^9/L", 0.20),
        maybe(diagnosis_name, 0.08),
        maybe(diagnosis_code, 0.25),
        maybe("抗感染对症支持治疗", 0.15),
        ctx.attending_doctor_id,
        maybe(ctx.patient_name, 0.15),
        write_time,
        maybe(write_time + timedelta(hours=random.randint(1, 24)), 0.30),
        datetime.now(),
    )

    doc_cols = [
        "document_id", "patient_id", "visit_id", "visit_type", "document_type",
        "document_title", "document_content", "dept_id", "author_id", "author_name",
        "write_time", "sign_time", "sign_status", "modify_count", "modifier_id",
        "modify_time", "quality_status", "print_count", "status", "create_time", "update_time",
    ]
    rec_cols = [
        "record_id", "patient_id", "visit_id", "admission_time",
        "chief_complaint", "present_illness", "past_history", "personal_history", "family_history",
        "allergy_history", "physical_exam", "vital_signs", "auxiliary_exam",
        "preliminary_diagnosis", "diagnosis_icd", "treatment_plan", "doctor_id",
        "doctor_name", "write_time", "sign_time", "create_time",
    ]

    results = [
        ("emr_db", "emr_documents", doc_cols, [doc_row]),
        ("emr_db", "admission_records", rec_cols, [rec_row]),
    ]

    # 同时生成 EMR 诊断明细（1-3 个）
    dx_counter = ctx.state.setdefault("emr_dx_counter", [0])
    dx_rows = []
    n_dx = random.randint(1, 3)
    comorbidities = ctx.patient_health.comorbidities if ctx.patient_health else []
    for i in range(n_dx):
        dx_id = next_id("ED", dx_counter)
        if i == 0:
            dx_name = diagnosis_name
            dx_code = diagnosis_code
        elif i - 1 < len(comorbidities):
            # 使用并发症作为次要诊断
            comorbidity = comorbidities[i - 1]
            dx_name = comorbidity[1].name
            dx_code = comorbidity[0]
        else:
            other = random.choice(ICD10_DIAGNOSES)
            dx_name = other[1]
            dx_code = other[0]
        dx_rows.append((
            dx_id,
            ctx.patient_id,
            ctx.visit_id,
            "入院诊断",
            i + 1,
            dx_name,
            dx_code,
            write_time,
            ctx.attending_doctor_id,
            "Y" if i == 0 else "N",
            datetime.now(),
        ))
    dx_cols = [
        "diagnosis_id", "patient_id", "visit_id", "diagnosis_type", "seq_no",
        "diagnosis_name", "diagnosis_icd", "diagnosis_time", "doctor_id", "is_principal", "create_time",
    ]
    results.append(("emr_db", "emr_diagnoses", dx_cols, dx_rows))

    return results


# ------------------------------------------------------------------
# 病程记录
# ------------------------------------------------------------------

def _handle_progress_note(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    counter = ctx.state.setdefault("progress_note_counter", [0])
    note_id = next_id("PN", counter)
    write_time = event.timestamp
    day = event.payload.get("day", 1)

    row = (
        note_id,
        ctx.patient_id,
        ctx.visit_id,
        write_time.date(),
        write_time,
        random.choice(["日常病程", "上级查房", "交接班", "抢救记录", "阶段小结"]),
        maybe(f"第{day}天病程记录：患者一般情况可...", 0.10),
        ctx.attending_doctor_id,
        maybe(ctx.patient_name, 0.15),
        maybe(write_time + timedelta(hours=random.randint(1, 12)), 0.30),
        write_time,
        datetime.now(),
    )

    cols = [
        "note_id", "patient_id", "visit_id", "note_date", "note_time",
        "note_type", "content", "author_id", "author_name", "sign_time",
        "record_time", "create_time",
    ]
    results = [("emr_db", "progress_notes", cols, [row])]

    # 2% 概率生成会诊记录
    if random.random() < 0.02:
        cs_counter = ctx.state.setdefault("cs_counter", [0])
        cs_id = next_id("CS", cs_counter)
        # requested_dept_id NOT NULL，确保有值（回退到当前科室）
        req_dept = maybe(ctx.department_id, 0.30) or ctx.department_id
        cs_row = (
            cs_id,
            ctx.patient_id,
            ctx.visit_id,
            random.choice(["院内会诊", "院外会诊", "急诊会诊", "MDT"]),
            ctx.department_id,
            ctx.attending_doctor_id,
            req_dept,
            maybe(ctx.attending_doctor_id, 0.30),
            write_time - timedelta(hours=random.randint(2, 24)),
            write_time,
            maybe("建议进一步完善检查，调整治疗方案", 0.20),
            random.choice(["普通", "紧急"]),
            random.choice(["待会诊", "已完成", "已取消"]),
            datetime.now(),
        )
        cs_cols = [
            "consultation_id", "patient_id", "visit_id", "consultation_type",
            "request_dept_id", "request_doctor_id", "requested_dept_id", "requested_doctor_id",
            "request_time", "consultation_time", "consultation_opinion", "urgency", "status", "create_time",
        ]
        results.append(("emr_db", "consultation_records", cs_cols, [cs_row]))

    return results


# ------------------------------------------------------------------
# 出院记录
# ------------------------------------------------------------------

def _handle_discharge_record(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    counter_doc = ctx.state.setdefault("emr_doc_counter", [0])
    counter_rec = ctx.state.setdefault("discharge_rec_counter", [0])
    doc_id = next_id("EMR", counter_doc)
    rec_id = next_id("DR", counter_rec)
    write_time = event.timestamp

    diagnosis = ctx.primary_diagnosis or random.choice(ICD10_DIAGNOSES)
    diagnosis_name = diagnosis[1] if isinstance(diagnosis, tuple) else diagnosis
    diagnosis_code = diagnosis[0] if isinstance(diagnosis, tuple) else None

    days = (
        (ctx.discharge_time - ctx.admission_time).days
        if ctx.discharge_time and ctx.admission_time
        else random.randint(3, 14)
    )

    # emr_documents
    doc_row = (
        doc_id,
        ctx.patient_id,
        ctx.visit_id,
        "住院",
        "出院记录",
        f"出院记录-{rec_id}",
        maybe(f"{diagnosis_name}出院记录...", 0.05),
        ctx.department_id,
        ctx.attending_doctor_id,
        None,
        write_time,
        maybe(write_time + timedelta(hours=random.randint(1, 12)), 0.30),
        "1",
        random.randint(0, 2),
        maybe(ctx.attending_doctor_id, 0.40),
        maybe(write_time + timedelta(days=1), 0.50),
        random.choice(["甲", "乙"]),
        random.randint(0, 2),
        "归档",
        datetime.now(),
        None,
    )

    # discharge_records（schema 无 document_id）
    rec_row = (
        rec_id,
        ctx.patient_id,
        ctx.visit_id,
        ctx.admission_time,
        ctx.discharge_time,
        days,
        maybe("发热待查", 0.15),
        maybe(diagnosis_name, 0.10),
        maybe(diagnosis_code, 0.25),
        maybe("入院后完善相关检查，给予抗感染等治疗...", 0.15),
        maybe(random.choice(["治愈", "好转", "未愈"]), 0.12),
        maybe("出院带药，定期复查", 0.18),
        maybe("1周后门诊复查", 0.30),
        ctx.attending_doctor_id,
        maybe(ctx.patient_name, 0.15),
        write_time,
        maybe(ctx.discharge_time, 0.30) if ctx.discharge_time else None,
        datetime.now(),
    )

    doc_cols = [
        "document_id", "patient_id", "visit_id", "visit_type", "document_type",
        "document_title", "document_content", "dept_id", "author_id", "author_name",
        "write_time", "sign_time", "sign_status", "modify_count", "modifier_id",
        "modify_time", "quality_status", "print_count", "status", "create_time", "update_time",
    ]
    rec_cols = [
        "record_id", "patient_id", "visit_id", "admission_time", "discharge_time",
        "hospital_days", "admission_diagnosis", "discharge_diagnosis", "diagnosis_icd",
        "treatment_summary", "discharge_status", "discharge_advice", "follow_up_plan",
        "doctor_id", "doctor_name", "write_time", "sign_time", "create_time",
    ]

    results = [
        ("emr_db", "emr_documents", doc_cols, [doc_row]),
        ("emr_db", "discharge_records", rec_cols, [rec_row]),
    ]

    # 如果 discharge_status 为死亡，生成死亡记录
    discharge_status = rec_row[11]  # discharge_status 列索引
    if discharge_status == "死亡":
        dr_counter = ctx.state.setdefault("death_rec_counter", [0])
        dr_id = next_id("DR", dr_counter)
        dr_row = (
            dr_id,
            ctx.patient_id,
            ctx.visit_id,
            ctx.discharge_time or write_time,
            maybe("多器官功能衰竭", 0.20),
            maybe(diagnosis_name, 0.10),
            maybe(diagnosis_code, 0.25),
            random.choice(["Y", "N"]),
            maybe("尸检结果待出具", 0.30) if random.random() < 0.1 else None,
            maybe(ctx.discharge_time + timedelta(hours=random.randint(1, 6)), 0.15) if ctx.discharge_time else None,
            ctx.attending_doctor_id,
            datetime.now(),
        )
        dr_cols = [
            "record_id", "patient_id", "visit_id", "death_time", "death_cause",
            "death_diagnosis", "death_icd", "autopsy_flag", "autopsy_result",
            "notify_family_time", "doctor_id", "create_time",
        ]
        results.append(("emr_db", "death_records", dr_cols, [dr_row]))

    return results


# ------------------------------------------------------------------
# 手术记录
# ------------------------------------------------------------------

def _handle_surgery_record(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    counter_doc = ctx.state.setdefault("emr_doc_counter", [0])
    counter_rec = ctx.state.setdefault("surgery_rec_counter", [0])
    doc_id = next_id("EMR", counter_doc)
    rec_id = next_id("SR", counter_rec)
    start_time = event.timestamp
    duration = random.randint(30, 360)
    end_time = start_time + timedelta(minutes=duration)

    surgery = _sample_from_ctx(ctx, "surgery_dict")
    if surgery is None:
        if ctx.disease_profile and ctx.disease_profile.typical_surgeries:
            surgery_name = random.choice(ctx.disease_profile.typical_surgeries)
            surgery = (surgery_name, "99.9", None, None, None, None)
        else:
            surgery_names = [
                ("阑尾切除术", "47.0"), ("胆囊切除术", "51.2"), ("胃大部切除术", "43.7"),
                ("肠切除术", "45.7"), ("脾切除术", "41.5"), ("肝部分切除术", "50.2"),
                ("甲状腺切除术", "06.4"), ("乳腺切除术", "85.4"), ("剖宫产术", "74.1"),
                ("子宫切除术", "68.4"), ("髋关节置换术", "81.5"), ("膝关节置换术", "81.5"),
                ("脊柱融合术", "81.0"), ("开颅术", "01.2"), ("冠状动脉搭桥术", "36.1"),
                ("心脏瓣膜置换术", "35.2"), ("肺叶切除术", "32.4"), ("肾切除术", "55.5"),
                ("前列腺切除术", "60.5"), ("骨折内固定术", "79.3"),
            ]
            s = random.choice(surgery_names)
            surgery = (s[1], s[0], None, None, None, None)
    # surgery: (surgery_code, surgery_name, surgery_level, dept_id, duration, anesthesia)
    surgery_name = surgery[1] if surgery[1] else "未知手术"
    surgery_code = surgery[0] if surgery[0] else "99.99"
    surgery_level = surgery[2] if surgery[2] else random.choice(["I级", "II级", "III级", "IV级"])

    # emr_documents
    doc_row = (
        doc_id,
        ctx.patient_id,
        ctx.visit_id,
        "住院",
        "手术记录",
        f"手术记录-{rec_id}",
        maybe(f"{surgery_name}手术记录...", 0.05),
        ctx.department_id,
        ctx.attending_doctor_id,
        None,
        start_time,
        maybe(start_time + timedelta(hours=random.randint(1, 6)), 0.30),
        "1",
        random.randint(0, 2),
        maybe(ctx.attending_doctor_id, 0.40),
        maybe(start_time + timedelta(days=1), 0.50),
        "甲",
        random.randint(0, 2),
        "归档",
        datetime.now(),
        None,
    )

    # surgery_records（对齐 schema）
    rec_row = (
        rec_id,
        ctx.patient_id,
        ctx.visit_id,
        None,  # surgery_id
        surgery_name,
        surgery_code,
        surgery_level,
        maybe(ctx.primary_diagnosis, 0.15),
        maybe(ctx.primary_diagnosis, 0.20),
        ctx.attending_doctor_id,
        maybe(ctx.patient_name, 0.15),
        maybe(ctx.attending_doctor_id, 0.20),
        maybe(ctx.attending_doctor_id, 0.30),
        maybe(ctx.attending_doctor_id, 0.10),
        random.choice(["全麻", "硬膜外麻醉", "腰麻", "局麻"]),
        start_time,
        end_time,
        duration,
        random.choice(["I类", "II类", "III类", "IV类"]),
        maybe("取常规体位，常规消毒铺巾...", 0.20),
        maybe("术中探查见病变组织...", 0.20),
        maybe(random.randint(50, 500), 0.20),
        maybe(random.randint(0, 400), 0.20),
        maybe("已送病理", 0.30),
        maybe("术后患者安返病房", 0.15),
        "已完成",
        datetime.now(),
    )

    doc_cols = [
        "document_id", "patient_id", "visit_id", "visit_type", "document_type",
        "document_title", "document_content", "dept_id", "author_id", "author_name",
        "write_time", "sign_time", "sign_status", "modify_count", "modifier_id",
        "modify_time", "quality_status", "print_count", "status", "create_time", "update_time",
    ]
    rec_cols = [
        "record_id", "patient_id", "visit_id", "surgery_id", "surgery_name",
        "surgery_code", "surgery_level", "pre_op_diagnosis", "post_op_diagnosis",
        "surgeon_id", "surgeon_name", "assistant1_id", "assistant2_id",
        "anesthesiologist_id", "anesthesia_type", "surgery_start_time",
        "surgery_end_time", "surgery_duration", "incision_type",
        "operative_procedure", "intraoperative_findings", "blood_loss",
        "blood_transfusion", "specimen", "post_op_advice", "status", "create_time",
    ]

    return [
        ("emr_db", "emr_documents", doc_cols, [doc_row]),
        ("emr_db", "surgery_records", rec_cols, [rec_row]),
    ]


# ------------------------------------------------------------------
# 门诊病历
# ------------------------------------------------------------------

def _handle_outpatient_record(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    counter = ctx.state.setdefault("emr_doc_counter", [0])
    doc_id = next_id("EMR", counter)
    write_time = event.timestamp

    diagnosis = ctx.primary_diagnosis or random.choice(ICD10_DIAGNOSES)
    diagnosis_name = diagnosis[1] if isinstance(diagnosis, tuple) else diagnosis

    row = (
        doc_id,
        ctx.patient_id,
        ctx.visit_id,
        "门诊",
        "门诊病历",
        f"门诊病历-{doc_id}",
        maybe(f"主诉：发热伴咳嗽3天。现病史：...诊断：{diagnosis_name}", 0.05),
        ctx.department_id,
        ctx.attending_doctor_id,
        None,
        write_time,
        maybe(write_time + timedelta(minutes=random.randint(5, 30)), 0.30),
        "1",
        0,
        None,
        None,
        random.choice(["甲", "乙"]),
        0,
        "完成",
        datetime.now(),
        None,
    )

    cols = [
        "document_id", "patient_id", "visit_id", "visit_type", "document_type",
        "document_title", "document_content", "dept_id", "author_id", "author_name",
        "write_time", "sign_time", "sign_status", "modify_count", "modifier_id",
        "modify_time", "quality_status", "print_count", "status", "create_time", "update_time",
    ]
    return ("emr_db", "emr_documents", cols, [row])
