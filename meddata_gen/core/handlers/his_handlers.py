"""HIS 事件处理器：入院、门诊、医嘱、收费。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from meddata_gen.core.events import EventContext, MedicalEvent
from meddata_gen.core.handlers._common import (
    compute_fee_breakdown,
    maybe,
    next_id,
    random_cost,
)
from meddata_gen.seed_data import ICD10_DIAGNOSES


# ------------------------------------------------------------------
# 注册入口
# ------------------------------------------------------------------

def register_his_handlers(materializer) -> None:
    """向 Materializer 注册 HIS 处理器。"""
    materializer.register("his", "admission", _handle_admission)
    materializer.register("his", "outpatient_visit", _handle_outpatient_visit)
    materializer.register("his", "daily_orders", _handle_daily_orders)
    materializer.register("his", "order_medication", _handle_order_medication)
    materializer.register("his", "discharge", _handle_discharge)


# ------------------------------------------------------------------
# 入院
# ------------------------------------------------------------------

def _handle_admission(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    # 取消入院：不生成住院记录
    if ctx.visit_status in ("cancelled", "absent"):
        return None

    total_cost = random_cost()
    fee = compute_fee_breakdown(total_cost)

    diagnosis = ctx.primary_diagnosis or random.choice(ICD10_DIAGNOSES)[1]
    days = (
        (ctx.discharge_time - ctx.admission_time).days
        if ctx.discharge_time and ctx.admission_time
        else random.randint(3, 14)
    )

    row = (
        ctx.visit_id,
        ctx.patient_id,
        maybe(f"MR{random.randint(100000, 999999)}", 0.05),
        maybe(random.choice(["急诊", "门诊", "转院", "其他"]), 0.08),
        ctx.admission_time,
        ctx.department_id,
        ctx.department_id,
        maybe(f"{random.randint(1, 30)}床", 0.05),
        maybe(diagnosis, 0.15),
        ctx.attending_doctor_id,
        maybe(ctx.attending_doctor_id, 0.20),
        maybe(ctx.attending_doctor_id, 0.30),
        ctx.discharge_time,
        maybe(ctx.department_id, 0.10) if ctx.discharge_time else None,
        maybe(ctx.department_id, 0.15) if ctx.discharge_time else None,
        maybe(diagnosis, 0.20) if ctx.discharge_time else None,
        maybe(random.choice(["治愈", "好转", "未愈", "死亡", "转科"]), 0.10)
        if ctx.discharge_time
        else None,
        days if ctx.discharge_time else (datetime.now() - ctx.admission_time).days,
        total_cost,
        fee["pre_payment"],
        fee["balance"],
        fee["insurance_pay"],
        fee["self_pay"],
        "出院" if ctx.discharge_time else "在院",
        datetime.now(),
        None,
    )

    columns = [
        "visit_id", "patient_id", "medical_record_no", "admission_type", "admission_time",
        "admission_dept_id", "admission_ward_id", "admission_bed_no", "admission_diagnosis",
        "attending_doctor_id", "resident_doctor_id", "chief_doctor_id", "discharge_time",
        "discharge_dept_id", "discharge_ward_id", "discharge_diagnosis", "discharge_status",
        "days", "total_cost", "pre_payment", "balance", "insurance_pay", "self_pay",
        "status", "create_time", "update_time",
    ]
    results = [("his_db", "inpatient_visits", columns, [row])]

    # 5% 概率生成转科记录
    if random.random() < 0.05:
        tr_counter = ctx.state.setdefault("tr_counter", [0])
        tr_id = next_id("TR", tr_counter)
        tr_row = (
            tr_id,
            ctx.visit_id,
            ctx.patient_id,
            ctx.department_id,
            ctx.department_id,
            ctx.admission_time + timedelta(days=random.randint(1, max(1, days - 1))) if days > 1 else ctx.admission_time,
            maybe(random.choice(["病情需要", "专科治疗", "手术需要", "床位调整"]), 0.20),
            maybe(f"{random.randint(1, 30)}床", 0.10),
            ctx.attending_doctor_id,
            datetime.now(),
        )
        tr_cols = [
            "transfer_id", "visit_id", "patient_id", "from_dept_id", "to_dept_id",
            "transfer_time", "transfer_reason", "bed_no", "doctor_id", "create_time",
        ]
        results.append(("his_db", "transfer_records", tr_cols, [tr_row]))

    return results


# ------------------------------------------------------------------
# 门诊
# ------------------------------------------------------------------

def _handle_outpatient_visit(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    # 退号/爽约：只生成挂号记录，不生成门诊就诊记录
    if ctx.visit_status == "refunded":
        reg_status = "退号"
    elif ctx.visit_status == "no_show":
        reg_status = "爽约"
    else:
        reg_status = random.choice(["已就诊"])

    # 挂号记录（所有情况都生成）
    reg_counter = ctx.state.setdefault("reg_counter", [0])
    reg_id = next_id("RG", reg_counter)
    reg_row = (
        reg_id,
        ctx.patient_id,
        ctx.visit_id,
        ctx.visit_time,
        random.choice(["现场", "预约", "急诊", "转诊"]),
        ctx.department_id,
        ctx.attending_doctor_id,
        random.choice(["普通", "专家", "特需", "急诊"]),
        random.randint(1, 200),
        reg_status,
        datetime.now(),
    )
    reg_cols = [
        "reg_id", "patient_id", "visit_id", "reg_time", "reg_type",
        "reg_dept_id", "reg_doctor_id", "fee_type", "sequence_no", "status", "create_time",
    ]
    results = [("his_db", "registrations", reg_cols, [reg_row])]

    # 非就诊状态：不生成 outpatient_visits
    if ctx.visit_status in ("refunded", "no_show"):
        return results

    # 正常就诊：生成 outpatient_visits
    diagnosis = ctx.primary_diagnosis or random.choice(ICD10_DIAGNOSES)
    fee = round(random.uniform(20, 2000), 2)

    visit_row = (
        ctx.visit_id,
        ctx.patient_id,
        ctx.visit_time.date() if ctx.visit_time else None,
        ctx.visit_time,
        ctx.department_id,
        ctx.attending_doctor_id,
        random.choice(["普通", "专家", "急诊", "复诊"]),
        maybe("发热伴咳嗽3天", 0.15),
        maybe("患者3天前受凉后出现发热...", 0.20),
        maybe(diagnosis[1] if isinstance(diagnosis, tuple) else diagnosis, 0.10),
        maybe(diagnosis[0] if isinstance(diagnosis, tuple) else None, 0.25),
        maybe("对症处理，随诊", 0.18),
        fee,
        "已结束",
        datetime.now(),
    )

    visit_cols = [
        "visit_id", "patient_id", "visit_date", "visit_time", "dept_id", "doctor_id",
        "visit_type", "chief_complaint", "present_illness", "diagnosis", "diagnosis_icd",
        "treatment", "fee_amount", "status", "create_time",
    ]
    results.append(("his_db", "outpatient_visits", visit_cols, [visit_row]))

    return results


# ------------------------------------------------------------------
# 每日医嘱
# ------------------------------------------------------------------

def _handle_daily_orders(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    """生成一条长期医嘱（如护理、膳食等）。"""
    counter = ctx.state.setdefault("order_counter", [0])
    order_id = next_id("OR", counter)

    categories = ["护理", "膳食", "药品", "检验", "检查"]
    category = random.choice(categories)
    order_type = random.choice(["长期", "临时"])

    start_time = event.timestamp
    stop_time = (
        start_time + timedelta(days=random.randint(1, 7))
        if order_type == "长期"
        else None
    )

    row = (
        order_id,
        ctx.visit_id,
        ctx.patient_id,
        order_type,
        category,
        start_time,
        stop_time,
        ctx.attending_doctor_id,
        None,
        ctx.department_id,
        "普通",
        random.choice(["新开", "审核", "执行", "停止"]),
        maybe(start_time + timedelta(minutes=random.randint(5, 60)), 0.25),
        None,
        datetime.now(),
        None,
    )

    columns = [
        "order_id", "visit_id", "patient_id", "order_type", "order_category",
        "start_time", "stop_time", "doctor_id", "nurse_id", "dept_id",
        "priority", "order_status", "verify_time", "verify_nurse_id", "create_time", "update_time",
    ]
    return ("his_db", "orders", columns, [row])


# ------------------------------------------------------------------
# 开药
# ------------------------------------------------------------------

def _handle_order_medication(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    """生成用药医嘱 + 对应的收费明细。"""
    order_counter = ctx.state.setdefault("order_counter", [0])
    fee_counter = ctx.state.setdefault("fee_counter", [0])

    order_id = next_id("OR", order_counter)
    fee_id = next_id("FE", fee_counter)

    start_time = event.timestamp
    qty = random.randint(1, 10)
    unit_price = round(random.uniform(5, 500), 4)
    total = round(qty * unit_price, 2)

    # 医嘱
    order_row = (
        order_id,
        ctx.visit_id,
        ctx.patient_id,
        random.choice(["长期", "临时"]),
        "药品",
        start_time,
        maybe(start_time + timedelta(days=random.randint(3, 14)), 0.30),
        ctx.attending_doctor_id,
        None,
        ctx.department_id,
        random.choice(["普通", "紧急"]),
        random.choice(["新开", "审核", "执行"]),
        maybe(start_time + timedelta(minutes=random.randint(5, 60)), 0.25),
        None,
        datetime.now(),
        None,
    )

    # 收费
    item_name = f"药品项目{random.randint(1, 999)}"
    if ctx.disease_profile and ctx.disease_profile.typical_medications:
        # 过滤掉空列表的类别
        valid_cats = {k: v for k, v in ctx.disease_profile.typical_medications.items() if v}
        if valid_cats:
            category = random.choice(list(valid_cats.keys()))
            item_name = random.choice(valid_cats[category])

    fee_row = (
        fee_id,
        ctx.visit_id,
        ctx.patient_id,
        "药品费",
        f"DRUG{random.randint(1000, 99999)}",
        item_name,
        maybe("0.5g*24片", 0.30),
        "盒",
        qty,
        unit_price,
        total,
        ctx.department_id,
        ctx.attending_doctor_id,
        start_time,
        "已收费",
        maybe(f"INV{random.randint(1000000, 9999999)}", 0.15),
        datetime.now(),
    )

    # 返回 orders 表
    order_cols = [
        "order_id", "visit_id", "patient_id", "order_type", "order_category",
        "start_time", "stop_time", "doctor_id", "nurse_id", "dept_id",
        "priority", "order_status", "verify_time", "verify_nurse_id", "create_time", "update_time",
    ]

    # Materializer 一次只能返回一个表，所以我们把 fee_items 也放在 HIS 里
    # 但 Materializer 支持只返回一个 (db, table)。
    # 解决方案：让 materialize 返回多个？不，Materializer 当前只接受一个结果。
    # 变通：order_medication 只返回 orders，fee_items 由另一个事件生成？
    # 或者：扩展 Materializer 让 handler 返回列表？

    fee_cols = [
        "fee_id", "visit_id", "patient_id", "fee_type", "item_code", "item_name",
        "specification", "unit", "quantity", "unit_price", "total_amount",
        "dept_id", "doctor_id", "fee_time", "pay_status", "invoice_no", "create_time",
    ]

    return [
        ("his_db", "orders", order_cols, [order_row]),
        ("his_db", "fee_items", fee_cols, [fee_row]),
    ]


# ------------------------------------------------------------------
# 出院（无单独表，信息已写入 inpatient_visits）
# ------------------------------------------------------------------

def _handle_discharge(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    # discharge 事件本身不写入 HIS 独立表，信息已在 admission 中
    # 但生成结算和预交金记录
    results = []

    st_counter = ctx.state.setdefault("st_counter", [0])
    st_id = next_id("ST", st_counter)
    total_amount = round(random.uniform(2000, 150000), 2)
    insurance_pay = round(total_amount * random.uniform(0.3, 0.8), 2)
    st_row = (
        st_id,
        ctx.visit_id,
        ctx.patient_id,
        random.choice(["出院结算", "中途结算", "门诊结算", "急诊结算"]),
        event.timestamp,
        total_amount,
        insurance_pay,
        round(total_amount - insurance_pay, 2),
        f"INV{random.randint(1000000, 9999999)}",
        random.choice(["已结算", "已结算", "已结算", "已作废", "已冲正"]),
        ctx.attending_doctor_id,
        datetime.now(),
    )
    st_cols = [
        "settlement_id", "visit_id", "patient_id", "settlement_type",
        "settlement_time", "total_amount", "insurance_pay", "self_pay",
        "invoice_no", "settlement_status", "cashier_id", "create_time",
    ]
    results.append(("his_db", "settlements", st_cols, [st_row]))

    # 1-3 条预交金记录
    pp_counter = ctx.state.setdefault("pp_counter", [0])
    pp_rows = []
    for _ in range(random.randint(1, 3)):
        pp_id = next_id("PP", pp_counter)
        amount = round(random.uniform(1000, 50000), 2)
        pp_rows.append((
            pp_id,
            ctx.visit_id,
            ctx.patient_id,
            event.timestamp - timedelta(days=random.randint(1, 10)),
            amount,
            random.choice(["现金", "银行卡", "微信", "支付宝", "医保卡"]),
            f"RC{random.randint(1000000, 9999999)}",
            round(amount + random.uniform(-5000, 20000), 2),
            ctx.attending_doctor_id,
            datetime.now(),
        ))
    pp_cols = [
        "prepay_id", "visit_id", "patient_id", "prepay_time", "amount",
        "pay_method", "receipt_no", "balance", "operator_id", "create_time",
    ]
    results.append(("his_db", "prepayments", pp_cols, pp_rows))

    return results
