"""LIS 事件处理器：检验申请、标本、结果。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from meddata_gen.core.events import EventContext, MedicalEvent
from meddata_gen.core.handlers._common import maybe, next_id
from meddata_gen.seed_data import ICD10_DIAGNOSES, LAB_ITEMS
from meddata_gen.clinical.lab_generator import generate_lab_value


def register_lis_handlers(materializer) -> None:
    materializer.register("lis", "order_lab", _handle_order_lab)
    materializer.register("lis", "lab_result", _handle_lab_result)


# ------------------------------------------------------------------
# 检验申请
# ------------------------------------------------------------------

def _handle_order_lab(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    counter = ctx.state.setdefault("lab_order_counter", [0])
    specimen_counter = ctx.state.setdefault("specimen_counter", [0])

    order_id = next_id("LO", counter)
    specimen_id = next_id("SP", specimen_counter)
    order_time = event.timestamp

    diagnosis = ctx.primary_diagnosis or random.choice(ICD10_DIAGNOSES)
    diagnosis_name = diagnosis[1] if isinstance(diagnosis, tuple) else diagnosis

    # 根据申请原因选择标本类型
    specimen_types = ["血清", "血浆", "全血", "尿液"]
    specimen_type = random.choice(specimen_types)

    # lab_orders 行
    order_row = (
        order_id,
        ctx.patient_id,
        ctx.visit_id,
        "住院" if ctx.visit_type == "inpatient" else "门诊",
        f"LAB{random.randint(1000000, 9999999)}",
        order_time,
        ctx.department_id,
        ctx.attending_doctor_id,
        None,
        random.choice(["普通", "紧急", "抢救"]),
        maybe(diagnosis_name, 0.20),
        maybe("请查血常规、生化全套", 0.30),
        specimen_type,
        maybe("空腹采血", 0.40),
        random.choice(["已申请", "已采样", "检验中", "已完成"]),
        maybe(order_time + timedelta(hours=random.randint(1, 48)), 0.25),
        ctx.attending_doctor_id,
        maybe(ctx.attending_doctor_id, 0.35),
        maybe(f"INST{random.randint(1, 50)}", 0.20),
        datetime.now(),
        None,
    )

    # specimens 行
    collect_time = order_time + timedelta(minutes=random.randint(10, 60))
    receive_time = collect_time + timedelta(minutes=random.randint(5, 120))
    specimen_row = (
        specimen_id,
        order_id,
        ctx.patient_id,
        ctx.visit_id,
        f"BAR{random.randint(100000000, 999999999)}",
        specimen_type,
        maybe(random.choice(["促凝管", "EDTA管", "肝素管", "枸橼酸钠管"]), 0.15),
        collect_time,
        maybe(f"ST{random.randint(1, 200)}", 0.20),
        random.choice(["病房", "门诊", "急诊", "ICU"]),
        receive_time,
        maybe(f"ST{random.randint(1, 200)}", 0.25),
        random.choice(["合格", "合格", "合格", "不合格", "溶血", "脂血"]),
        maybe("标本量不足", 0.70),
        maybe(f"{random.randint(1, 10)}ml", 0.15),
        maybe(random.choice(["真空采血管", "尿管", "便盒"]), 0.20),
        maybe("常温", 0.30),
        maybe(f"{random.randint(1, 50)}床", 0.40),
        datetime.now(),
    )

    # 记录 order_id 供 lab_result 使用
    seq = event.payload.get("seq", 0)
    ctx.record_id(f"lab_order_{seq}", order_id)

    order_cols = [
        "order_id", "patient_id", "visit_id", "visit_type", "order_no",
        "order_time", "order_dept_id", "order_doctor_id", "order_doctor_name",
        "priority", "diagnosis", "clinical_note", "specimen_type",
        "specimen_requirements", "order_status", "report_time",
        "reporter_id", "verifier_id", "instrument_code", "create_time", "update_time",
    ]
    specimen_cols = [
        "specimen_id", "order_id", "patient_id", "visit_id", "barcode",
        "specimen_type", "specimen_sub_type", "collect_time", "collector_id",
        "collect_location", "receive_time", "receiver_id", "receive_status",
        "reject_reason", "volume", "container", "transport_temp", "bed_no", "create_time",
    ]

    return [
        ("lis_db", "lab_orders", order_cols, [order_row]),
        ("lis_db", "specimens", specimen_cols, [specimen_row]),
    ]


# ------------------------------------------------------------------
# 检验结果
# ------------------------------------------------------------------

def _handle_lab_result(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    seq = event.payload.get("seq", 0)
    order_id = ctx.get_id(f"lab_order_{seq}")
    if not order_id:
        order_id = f"LO{random.randint(1, 9999999)}"

    result_time = event.timestamp

    # 随机选择检验类别和项目数
    category = random.choice(["routine", "biochem", "blood"])
    items = LAB_ITEMS.get(category, [])
    if not items:
        return None

    # 每个申请生成 3-8 个结果项
    n_results = random.randint(3, 8)
    selected = random.choices(items, k=min(n_results, len(items)))

    rows = []
    counter = ctx.state.setdefault(f"lab_result_counter_{category}", [0])

    for item in selected:
        # item: (code, name, unit, ref_low, ref_high)
        code, name, unit, ref_low, ref_high = item
        result_str, result_num, abnormal_flag = generate_lab_value(code, ctx.disease_profile)

        counter[0] += 1
        prefix = {"routine": "RR", "blood": "BR", "biochem": "BLR"}[category]
        result_id = f"{prefix}{str(counter[0]).zfill(7)}"

        # 结果表 schema 列（20列，对齐 routine_results / biochem_results / blood_results）
        row = (
            result_id,
            order_id,
            None,                       # specimen_id
            ctx.patient_id,
            ctx.visit_id,
            code,                       # item_code
            name,                       # item_name
            None,                       # item_loinc
            result_str,                 # result_value
            result_num,                 # result_num
            unit,
            f"{ref_low}-{ref_high}",    # reference_range
            float(ref_low) if ref_low is not None else None,   # ref_low
            float(ref_high) if ref_high is not None else None, # ref_high
            abnormal_flag,
            maybe("仪器法", 0.30),      # test_method
            maybe(f"INST{random.randint(1, 50)}", 0.20),  # instrument_code
            result_time,                # test_time
            maybe(result_time + timedelta(minutes=random.randint(10, 120)), 0.30),  # report_time
            datetime.now(),
        )
        rows.append(row)

    cols = [
        "result_id", "order_id", "specimen_id", "patient_id", "visit_id",
        "item_code", "item_name", "item_loinc", "result_value", "result_num",
        "unit", "reference_range", "ref_low", "ref_high", "abnormal_flag",
        "test_method", "instrument_code", "test_time", "report_time", "create_time",
    ]

    table_map = {
        "routine": "routine_results",
        "biochem": "biochem_results",
        "blood": "blood_results",
    }
    table = table_map.get(category, "routine_results")
    results = [("lis_db", table, cols, rows)]

    # 15% 概率生成检验报告主表
    if random.random() < 0.15:
        rm_counter = ctx.state.setdefault("rm_counter", [0])
        rm_id = next_id("RM", rm_counter)
        is_critical = "Y" if any(r[6] != "N" for r in rows) else "N"
        rm_row = (
            rm_id,
            order_id,
            ctx.patient_id,
            ctx.visit_id,
            f"RPT{random.randint(1000000, 9999999)}",
            result_time,
            maybe(result_time + timedelta(minutes=random.randint(10, 120)), 0.30),
            ctx.attending_doctor_id,
            maybe(ctx.attending_doctor_id, 0.35),
            random.choice(["草稿", "已提交", "已审核", "已发布"]),
            is_critical,
            "Y" if is_critical == "Y" and random.random() > 0.3 else "N",
            random.choice(["血清", "血浆", "全血", "尿液"]),
            random.choice(["合格", "合格", "合格", "溶血", "脂血"]),
            maybe(f"INST{random.randint(1, 50)}", 0.20),
            datetime.now(),
            None,
        )
        rm_cols = [
            "report_id", "order_id", "patient_id", "visit_id", "report_no",
            "report_time", "verify_time", "reporter_id", "verifier_id",
            "report_status", "critical_value_flag", "critical_value_handled",
            "specimen_type", "specimen_status", "instrument_code", "create_time", "update_time",
        ]
        results.append(("lis_db", "lab_report_master", rm_cols, [rm_row]))

        # 如果有异常结果，20% 概率生成危急值记录
        if is_critical == "Y" and random.random() < 0.20:
            cv_counter = ctx.state.setdefault("cv_counter", [0])
            cv_id = next_id("CV", cv_counter)
            abnormal_row = next(r for r in rows if r[6] != "N")
            cv_row = (
                cv_id,
                order_id,
                rm_id,
                ctx.patient_id,
                ctx.visit_id,
                abnormal_row[2],  # test_item
                abnormal_row[3],  # result_value
                abnormal_row[5],  # reference_range
                result_time,
                ctx.attending_doctor_id,
                maybe(result_time + timedelta(minutes=random.randint(1, 30)), 0.15),
                maybe(result_time + timedelta(minutes=random.randint(5, 60)), 0.25),
                maybe(ctx.attending_doctor_id, 0.30),
                maybe(random.choice(["立即处理", "复查确认", "调整用药", "转入ICU"]), 0.20),
                random.choice(["已通知", "已确认", "已处理", "已关闭"]),
                datetime.now(),
            )
            cv_cols = [
                "cv_id", "order_id", "report_id", "patient_id", "visit_id",
                "item_name", "result_value", "reference_range", "cv_time",
                "notified_doctor_id", "notification_time", "confirmation_time",
                "handler_id", "handle_action", "status", "create_time",
            ]
            results.append(("lis_db", "critical_values", cv_cols, [cv_row]))

    return results


def _generate_result_value(ref_low, ref_high):
    """生成检验结果值：90% 正常，10% 异常。"""
    ref_low = float(ref_low)
    ref_high = float(ref_high)
    normal_mid = (ref_low + ref_high) / 2
    normal_range = ref_high - ref_low

    if random.random() < 0.90:
        # 正常值：在参考范围内带生物变异
        value = random.gauss(normal_mid, normal_range / 6)
        value = max(ref_low * 0.95, min(ref_high * 1.05, value))
        flag = "N"
    else:
        # 异常值
        if random.random() < 0.5:
            value = ref_low * random.uniform(0.3, 0.95)
            flag = "L"
        else:
            value = ref_high * random.uniform(1.05, 3.0)
            flag = "H"

    # 格式化：整数或 1-2 位小数
    if value >= 100:
        value = round(value, 1)
    elif value >= 1:
        value = round(value, 2)
    else:
        value = round(value, 3)
    return value, flag
