"""RIS 事件处理器：影像申请与报告。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from meddata_gen.core.events import EventContext, MedicalEvent
from meddata_gen.core.handlers._common import maybe, next_id
from meddata_gen.seed_data import ICD10_DIAGNOSES, RIS_EXAM_TYPES


def register_ris_handlers(materializer) -> None:
    materializer.register("ris", "order_imaging", _handle_order_imaging)
    materializer.register("ris", "imaging_report", _handle_imaging_report)


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


def _infer_modality(exam_name: str) -> str:
    """根据检查名称推断影像模态。"""
    name = exam_name.lower()
    if "ct" in name or "ct" in exam_name:
        return "ct"
    if "mri" in name or "核磁" in exam_name or "磁共振" in exam_name:
        return "mri"
    if "超声" in exam_name or "b超" in name or "彩超" in exam_name:
        return "ultrasound"
    if "x线" in exam_name or "x光" in exam_name or "dr" in name:
        return "xray"
    return random.choice(list(RIS_EXAM_TYPES.keys()))


# ------------------------------------------------------------------
# 影像申请
# ------------------------------------------------------------------

def _handle_order_imaging(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    counter = ctx.state.setdefault("ris_order_counter", [0])
    order_id = next_id("EO", counter)
    order_time = event.timestamp

    # 选择影像类型和具体项目
    exam_item_code = None
    exam_item_name = None
    modality = None

    if ctx.disease_profile and ctx.disease_profile.typical_imaging:
        exam_item_name = random.choice(ctx.disease_profile.typical_imaging)
        modality = _infer_modality(exam_item_name)
    else:
        exam_row = _sample_from_ctx(ctx, "exam_items_dict")
        if exam_row:
            exam_item_code = exam_row[0]
            exam_item_name = exam_row[1]
            modality = exam_row[2]
        else:
            modality = random.choice(list(RIS_EXAM_TYPES.keys()))
            exam_item_name = random.choice(RIS_EXAM_TYPES[modality])

    if exam_item_code is None:
        exam_item_code = f"ITEM{random.randint(100, 999)}"

    diagnosis = ctx.primary_diagnosis or random.choice(ICD10_DIAGNOSES)
    diagnosis_name = diagnosis[1] if isinstance(diagnosis, tuple) else diagnosis

    row = (
        order_id,
        ctx.patient_id,
        ctx.visit_id,
        "住院" if ctx.visit_type == "inpatient" else "门诊",
        f"EX{random.randint(1000000, 9999999)}",
        order_time,
        ctx.department_id,
        ctx.attending_doctor_id,
        None,
        modality,
        exam_item_code,
        exam_item_name,
        maybe(random.choice(["头部", "胸部", "腹部", "盆腔", "脊柱", "四肢", "心脏", "甲状腺", "乳腺"]), 0.10),
        maybe("平扫+增强", 0.35),
        maybe(diagnosis_name, 0.20),
        maybe("进一步明确诊断", 0.30),
        random.choice(["普通", "紧急"]),
        random.choice(["Y", "N"]),
        maybe("无", 0.40),
        maybe("碘海醇", 0.50) if modality in ["CT", "MRI", "ct", "mri"] else None,
        random.choice(["已申请", "已预约", "已检查", "已报告"]),
        maybe(f"DV{random.randint(1, 15)}", 0.25),
        maybe(order_time + timedelta(hours=random.randint(1, 48)), 0.30),
        maybe(order_time + timedelta(hours=random.randint(2, 72)), 0.35),
        round(random.uniform(50, 5000), 2),
        datetime.now(),
        None,
    )

    # 记录 order_id 供 report 使用
    seq = event.payload.get("seq", 0)
    ctx.record_id(f"imaging_order_{seq}", order_id)

    cols = [
        "order_id", "patient_id", "visit_id", "visit_type", "order_no",
        "order_time", "order_dept_id", "order_doctor_id", "order_doctor_name",
        "exam_type", "exam_item_code", "exam_item_name", "exam_part", "exam_method",
        "clinical_diagnosis", "purpose", "priority", "pregnancy_status",
        "allergy_history", "contrast_agent", "order_status", "device_id",
        "appointment_time", "exam_time", "fee", "create_time", "update_time",
    ]
    return ("ris_db", "exam_orders", cols, [row])


# ------------------------------------------------------------------
# 影像报告
# ------------------------------------------------------------------

def _handle_imaging_report(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    seq = event.payload.get("seq", 0)
    order_id = ctx.get_id(f"imaging_order_{seq}")
    if not order_id:
        order_id = f"EO{random.randint(1, 9999999)}"

    report_time = event.timestamp

    # 报告模板
    findings_templates = [
        "{part}见{lesion}，大小约{size}，边界{edge}，密度{density}。",
        "{part}显示{lesion}，伴周围组织{change}。",
        "{part}未见明显异常密度影。",
        "{part}见多发{lesion}，最大径约{size}。",
    ]
    impressions = [
        "考虑{diagnosis}，建议进一步检查。",
        "{diagnosis}可能性大。",
        "{part}未见明显异常。",
        "符合{diagnosis}表现。",
    ]

    parts = ["右肺下叶", "左肺上叶", "肝右叶", "胰腺", "头颅", "腰椎", "膝关节"]
    lesions = ["结节影", "斑片状影", "肿块影", "条索状影", "钙化灶"]
    diagnoses = ["肺炎", "肺结核", "肺癌", "肝血管瘤", "脑梗死"]

    finding = random.choice(findings_templates).format(
        part=random.choice(parts),
        lesion=random.choice(lesions),
        size=f"{random.randint(5, 50)}mm",
        edge=random.choice(["清", "不清", "模糊"]),
        density=random.choice(["均匀", "不均", "低密度", "高密度"]),
        change=random.choice(["水肿", "浸润", "受压移位"]),
    )
    impression = random.choice(impressions).format(
        diagnosis=random.choice(diagnoses),
        part=random.choice(parts),
    )

    modality = random.choice(["xray", "ct", "mri", "ultrasound"])
    table_map = {
        "xray": "xray_reports",
        "ct": "ct_reports",
        "mri": "mri_reports",
        "ultrasound": "ultrasound_reports",
    }
    table = table_map[modality]
    prefix = {"xray": "XR", "ct": "CT", "mri": "MRI", "ultrasound": "US"}[modality]
    counter = ctx.state.setdefault(f"{modality}_report_counter", [0])
    report_id = next_id(prefix, counter)

    reporter_id = maybe(ctx.attending_doctor_id, 0.20)
    audit_time = maybe(report_time + timedelta(hours=random.randint(1, 24)), 0.30)
    auditor_id = maybe(ctx.attending_doctor_id, 0.25)
    critical = random.choice(["Y", "N"])

    if modality == "xray":
        cols = [
            "report_id", "order_id", "patient_id", "visit_id", "exam_no",
            "device_id", "exam_part", "exam_method", "film_count", "image_count",
            "technique", "findings", "impression", "report_status", "reporter_id",
            "reporter_name", "report_time", "auditor_id", "auditor_name",
            "audit_time", "critical_value", "create_time",
        ]
        row = (
            report_id, order_id, ctx.patient_id, ctx.visit_id,
            f"EX{random.randint(100000, 999999)}",
            maybe(f"DV{random.randint(1, 15)}", 0.25),
            random.choice(parts),
            maybe("正侧位", 0.40),
            random.randint(1, 4),
            random.randint(1, 4),
            maybe("DR数字摄影", 0.30),
            finding,
            impression,
            random.choice(["草稿", "已提交", "已审核"]),
            reporter_id,
            maybe(ctx.patient_name, 0.15),
            report_time,
            auditor_id,
            maybe(ctx.patient_name, 0.15),
            audit_time,
            critical,
            datetime.now(),
        )
    elif modality == "ct":
        cols = [
            "report_id", "order_id", "patient_id", "visit_id", "exam_no",
            "device_id", "exam_part", "contrast_agent", "contrast_dose",
            "slice_thickness", "kv", "ma", "findings", "impression",
            "report_status", "reporter_id", "reporter_name", "report_time",
            "auditor_id", "auditor_name", "audit_time", "critical_value", "create_time",
        ]
        row = (
            report_id, order_id, ctx.patient_id, ctx.visit_id,
            f"EX{random.randint(100000, 999999)}",
            maybe(f"DV{random.randint(1, 15)}", 0.25),
            random.choice(parts),
            maybe("碘海醇", 0.60),
            maybe("80ml", 0.60),
            maybe("5mm", 0.50),
            maybe("120", 0.50),
            maybe("200", 0.50),
            finding,
            impression,
            random.choice(["草稿", "已提交", "已审核"]),
            reporter_id,
            maybe(ctx.patient_name, 0.15),
            report_time,
            auditor_id,
            maybe(ctx.patient_name, 0.15),
            audit_time,
            critical,
            datetime.now(),
        )
    elif modality == "mri":
        cols = [
            "report_id", "order_id", "patient_id", "visit_id", "exam_no",
            "device_id", "exam_part", "sequence", "contrast_agent", "findings",
            "impression", "report_status", "reporter_id", "reporter_name",
            "report_time", "auditor_id", "auditor_name", "audit_time",
            "critical_value", "create_time",
        ]
        row = (
            report_id, order_id, ctx.patient_id, ctx.visit_id,
            f"EX{random.randint(100000, 999999)}",
            maybe(f"DV{random.randint(1, 15)}", 0.25),
            random.choice(parts),
            maybe("T1WI/T2WI/FLAIR", 0.50),
            maybe("钆喷酸葡胺", 0.50),
            finding,
            impression,
            random.choice(["草稿", "已提交", "已审核"]),
            reporter_id,
            maybe(ctx.patient_name, 0.15),
            report_time,
            auditor_id,
            maybe(ctx.patient_name, 0.15),
            audit_time,
            critical,
            datetime.now(),
        )
    else:  # ultrasound
        cols = [
            "report_id", "order_id", "patient_id", "visit_id", "exam_no",
            "device_id", "exam_part", "exam_type", "probe_frequency",
            "ultrasound_findings", "ultrasound_diagnosis", "measurements",
            "images_count", "video_flag", "report_status", "reporter_id",
            "reporter_name", "report_time", "auditor_id", "auditor_name",
            "audit_time", "critical_value", "create_time",
        ]
        row = (
            report_id, order_id, ctx.patient_id, ctx.visit_id,
            f"EX{random.randint(100000, 999999)}",
            maybe(f"DV{random.randint(1, 15)}", 0.25),
            random.choice(["腹部", "心脏", "甲状腺", "乳腺", "妇科"]),
            random.choice(["B超", "彩超", "三维", "造影"]),
            maybe("5-12MHz", 0.40),
            finding,
            impression,
            maybe("左室舒张末径 52mm", 0.30),
            random.randint(1, 10),
            random.choice(["Y", "N"]),
            random.choice(["草稿", "已提交", "已审核"]),
            reporter_id,
            maybe(ctx.patient_name, 0.15),
            report_time,
            auditor_id,
            maybe(ctx.patient_name, 0.15),
            audit_time,
            critical,
            datetime.now(),
        )

    results = [("ris_db", table, cols, [row])]

    # 同时生成检查图像记录（1-3 张）
    img_counter = ctx.state.setdefault("img_counter", [0])
    img_rows = []
    for _ in range(random.randint(1, 3)):
        img_id = next_id("IMG", img_counter)
        img_rows.append((
            img_id,
            order_id,
            ctx.patient_id,
            ctx.visit_id,
            f"1.2.840.{random.randint(100000, 999999)}.{random.randint(100000, 999999)}",
            f"1.2.840.{random.randint(100000, 999999)}.{random.randint(100000, 999999)}",
            modality.upper(),
            random.randint(10, 500),
            maybe(f"/pacs/{modality}/{ctx.patient_id}/{img_id}.dcm", 0.10),
            round(random.uniform(0.5, 50.0), 2),
            maybe(report_time + timedelta(minutes=random.randint(5, 60)), 0.20),
            datetime.now(),
        ))
    img_cols = [
        "image_id", "order_id", "patient_id", "visit_id", "series_uid",
        "study_uid", "modality", "image_count", "storage_path", "file_size_mb",
        "upload_time", "create_time",
    ]
    results.append(("ris_db", "exam_images", img_cols, img_rows))

    return results
