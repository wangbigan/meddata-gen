"""ICU 事件处理器：入科、监护数据、报警、血气。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from meddata_gen.core.events import EventContext, MedicalEvent
from meddata_gen.core.handlers._common import maybe, next_id


def register_icu_handlers(materializer) -> None:
    materializer.register("icu", "icu_admission", _handle_icu_admission)
    materializer.register("icu", "monitoring_data", _handle_monitoring_data)
    materializer.register("icu", "alarm", _handle_alarm)
    materializer.register("icu", "blood_gas", _handle_blood_gas)


# ------------------------------------------------------------------
# ICU 入科
# ------------------------------------------------------------------

def _handle_icu_admission(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    counter = ctx.state.setdefault("icu_adm_counter", [0])
    icu_adm_id = next_id("IA", counter)
    admission_time = event.timestamp

    los = random.randint(1, 7)
    discharge_time = admission_time + timedelta(days=los)

    # icu_admissions（对齐 schema 26列）
    row = (
        icu_adm_id,
        ctx.patient_id,
        ctx.visit_id,
        ctx.visit_id,
        maybe(f"ICU-B{random.randint(1, 20)}", 0.05),
        maybe(f"{random.randint(1, 20)}", 0.05),
        admission_time,
        random.choice(["急诊", "手术室", "病房", "外院转入"]),
        random.choice(["计划入ICU", "抢救入ICU", "术后入ICU"]),
        ctx.primary_diagnosis or "重症肺炎",
        maybe("合并多器官功能障碍", 0.20),
        random.randint(5, 30),
        random.randint(0, 15),
        random.randint(3, 15),
        round(random.uniform(50, 90), 2),
        round(random.uniform(160, 185), 1),
        round(random.uniform(18, 30), 2),
        round(los * 1.5, 1),
        discharge_time,
        random.choice(["转病房", "死亡", "自动出院", "转院"]),
        random.choice(["内科", "外科", "急诊", "其他医院"]),
        los,
        random.choice(["Y", "N"]),
        datetime.now(),
    )

    ctx.record_id("icu_admission_id", icu_adm_id)

    cols = [
        "icu_admission_id", "patient_id", "visit_id", "hospital_visit_id", "bed_id",
        "bed_no", "admission_time", "admission_source", "admission_type",
        "primary_diagnosis", "secondary_diagnosis", "apacheii_score", "sofa_score",
        "gcs_score", "admission_weight", "height", "bmi", "expected_los",
        "discharge_time", "discharge_status", "discharge_destination", "actual_los",
        "death_flag", "create_time",
    ]
    results = [("icu_monitoring_db", "icu_admissions", cols, [row])]

    # 呼吸机设置
    vs_counter = ctx.state.setdefault("vs_counter", [0])
    vs_id = next_id("VS", vs_counter)
    vs_row = (
        vs_id,
        icu_adm_id,
        ctx.patient_id,
        ctx.visit_id,
        admission_time,
        random.choice(["SIMV", "PSV", "PRVC", "AC", "CPAP"]),
        random.randint(400, 600),
        random.randint(10, 30),
        round(random.uniform(0.30, 1.00), 2),
        random.randint(5, 15),
        random.randint(10, 20),
        random.choice(["1:2", "1:1.5", "1:1"]),
        round(random.uniform(-2.0, -0.5), 1),
        random.randint(20, 35),
        random.randint(25, 40),
        ctx.attending_doctor_id,
        datetime.now(),
    )
    vs_cols = [
        "setting_id", "icu_admission_id", "patient_id", "visit_id", "setting_time",
        "vent_mode", "tv_set", "rr_set", "fio2_set", "peep_set", "pressure_support",
        "ie_ratio", "trigger_sensitivity", "plateau_pressure", "pip", "operator_id", "create_time",
    ]
    results.append(("icu_monitoring_db", "ventilator_settings", vs_cols, [vs_row]))

    # 50% 概率生成气管插管记录
    if random.random() < 0.50:
        it_counter = ctx.state.setdefault("it_counter", [0])
        it_id = next_id("IT", it_counter)
        intubation_time = admission_time + timedelta(minutes=random.randint(5, 60))
        extubation_time = intubation_time + timedelta(days=random.randint(1, 7)) if random.random() < 0.7 else None
        it_row = (
            it_id,
            icu_adm_id,
            ctx.patient_id,
            ctx.visit_id,
            random.choice(["气管插管", "气管切开", "喉罩"]),
            intubation_time,
            extubation_time,
            random.choice(["7.0", "7.5", "8.0", "8.5"]),
            round(random.uniform(20.0, 24.0), 1),
            maybe("呼吸衰竭", 0.20),
            maybe("病情好转，撤离呼吸机", 0.20) if extubation_time else None,
            random.choice(["成功", "再插管", "拔管失败"]) if extubation_time else None,
            ctx.attending_doctor_id,
            datetime.now(),
        )
        it_cols = [
            "record_id", "icu_admission_id", "patient_id", "visit_id", "tube_type",
            "intubation_time", "extubation_time", "tube_size", "depth_cm", "intubation_reason",
            "extubation_reason", "extubation_outcome", "doctor_id", "create_time",
        ]
        results.append(("icu_monitoring_db", "intubation_records", it_cols, [it_row]))

    return results


# ------------------------------------------------------------------
# 监护数据
# ------------------------------------------------------------------

def _handle_monitoring_data(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    monitor_time = event.timestamp
    icu_adm_id = ctx.get_id("icu_admission_id") or f"IA{random.randint(1, 9999)}"

    hr = random.randint(50, 140)
    sbp = random.randint(90, 170)
    dbp = random.randint(50, 100)
    map_val = int(round((sbp + 2 * dbp) / 3))
    spo2 = round(random.uniform(88.0, 100.0), 2)
    temp = round(random.uniform(35.5, 39.5), 1)
    rr = random.randint(10, 40)

    # monitoring_data（对齐 schema 39列，data_id 自增不插）
    row = (
        ctx.patient_id,
        icu_adm_id,
        ctx.visit_id,
        maybe(f"ICU-B{random.randint(1, 20)}", 0.05),
        monitor_time,
        hr,
        sbp,
        dbp,
        map_val,
        spo2,
        rr,
        temp,
        maybe(random.randint(5, 20), 0.40),
        maybe(random.randint(20, 50), 0.20),
        maybe(random.randint(8, 25), 0.20),
        maybe(round(random.uniform(4.0, 8.0), 2), 0.20),
        maybe(round(random.uniform(2.5, 4.5), 2), 0.20),
        maybe(round(random.uniform(60.0, 100.0), 1), 0.20),
        maybe(round(random.uniform(5.0, 15.0), 2), 0.20),
        maybe(round(random.uniform(5.0, 15.0), 2), 0.20),
        maybe(random.randint(25, 45), 0.60),
        round(random.uniform(0.30, 1.00), 2),
        random.randint(5, 15),
        random.randint(15, 35),
        random.randint(15, 30),
        random.randint(400, 600),
        random.randint(380, 620),
        round(random.uniform(5.0, 15.0), 2),
        random.choice(["1:2", "1:1.5", "1:1"]),
        maybe(random.randint(5, 20), 0.15),
        maybe(random.randint(40, 80), 0.15),
        maybe(round(random.uniform(40.0, 80.0), 1), 0.15),
        maybe(round(random.uniform(50.0, 300.0), 1), 0.40),
        random.choice(["监护仪", "呼吸机", "血气"]),
        maybe(f"DEV{random.randint(1, 20)}", 0.30),
        random.choice(["Y", "N"]),
        datetime.now(),
    )

    cols = [
        "patient_id", "icu_admission_id", "visit_id", "bed_id", "monitor_time",
        "hr", "sbp", "dbp", "map", "spo2", "rr", "temp",
        "cvp", "pap_systolic", "pap_diastolic", "co", "ci", "sv", "svv", "pvp",
        "etco2", "fio2", "peep", "pip", "plateau_pressure", "tv_set", "tv_actual",
        "mv", "ie_ratio", "icp", "cpp", "bis", "urine_output",
        "data_source", "device_id", "alarm_flag", "create_time",
    ]
    results = [("icu_monitoring_db", "monitoring_data", cols, [row])]

    # 20% 概率生成出入量记录
    if random.random() < 0.20:
        fb_counter = ctx.state.setdefault("fb_counter", [0])
        fb_id = next_id("FB", fb_counter)
        oral = round(random.uniform(0, 1500), 1)
        iv = round(random.uniform(500, 3000), 1)
        urine = round(random.uniform(500, 2500), 1)
        fb_row = (
            fb_id,
            icu_adm_id,
            ctx.patient_id,
            ctx.visit_id,
            monitor_time.date(),
            oral,
            iv,
            round(random.uniform(0, 500), 1),
            urine,
            round(random.uniform(0, 500), 1),
            round(random.uniform(0, 300), 1),
            round(oral + iv - urine, 1),
            maybe(ctx.attending_doctor_id, 0.30),
            datetime.now(),
        )
        fb_cols = [
            "balance_id", "icu_admission_id", "patient_id", "visit_id", "record_date",
            "intake_oral", "intake_iv", "intake_other", "output_urine", "output_drainage",
            "output_other", "balance_total", "nurse_id", "create_time",
        ]
        results.append(("icu_monitoring_db", "fluid_balance", fb_cols, [fb_row]))

    # 30% 概率生成镇静镇痛记录
    if random.random() < 0.30:
        sr_counter = ctx.state.setdefault("sr_counter", [0])
        sr_id = next_id("SR", sr_counter)
        sr_row = (
            sr_id,
            icu_adm_id,
            ctx.patient_id,
            ctx.visit_id,
            monitor_time,
            random.randint(-5, 4),
            random.randint(0, 8),
            random.randint(1, 6),
            maybe(random.choice(["丙泊酚", "咪达唑仑", "右美托咪定"]), 0.20),
            maybe(f"{random.uniform(1, 5):.1f}mg/h", 0.25),
            maybe(random.choice(["芬太尼", "舒芬太尼", "瑞芬太尼"]), 0.30),
            maybe(f"{random.uniform(5, 20):.1f}ug/h", 0.35),
            maybe(random.choice(["罗库溴铵", "维库溴铵"]), 0.50),
            maybe(ctx.attending_doctor_id, 0.30),
            datetime.now(),
        )
        sr_cols = [
            "record_id", "icu_admission_id", "patient_id", "visit_id", "record_time",
            "rass_score", "cpot_score", "ramsay_score", "sedative_drug", "sedative_dose",
            "analgesic_drug", "analgesic_dose", "muscle_relaxant", "nurse_id", "create_time",
        ]
        results.append(("icu_monitoring_db", "sedation_records", sr_cols, [sr_row]))

    return results


# ------------------------------------------------------------------
# 报警
# ------------------------------------------------------------------

def _handle_alarm(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    counter = ctx.state.setdefault("alarm_counter", [0])
    alarm_id = next_id("AL", counter)
    alarm_time = event.timestamp
    icu_adm_id = ctx.get_id("icu_admission_id") or f"IA{random.randint(1, 9999)}"

    alarm_types = [
        ("心率过高", "高", "HR", "120", "145"),
        ("心率过低", "高", "HR", "35", "48"),
        ("血氧过低", "高", "SpO2", "85", "92"),
        ("血压过高", "中", "SBP", "160", "190"),
        ("血压过低", "高", "SBP", "70", "85"),
        ("呼吸频率过快", "中", "RR", "30", "40"),
        ("体温过高", "中", "Temp", "38.5", "40.0"),
    ]
    atype = random.choice(alarm_types)

    actual = random.randint(50, 150)
    if atype[0] in ("心率过高", "血氧过低", "血压过高"):
        actual = random.randint(int(atype[4]), int(atype[4]) + 20)

    row = (
        alarm_id,
        ctx.patient_id,
        icu_adm_id,
        ctx.visit_id,
        maybe(f"ICU-B{random.randint(1, 20)}", 0.05),
        alarm_time,
        atype[1],
        atype[0],
        atype[2],
        str(actual),
        atype[3],
        atype[4],
        maybe(f"{atype[0]}：{actual}", 0.20),
        random.randint(30, 600),
        random.choice(["Y", "N"]),
        maybe(ctx.attending_doctor_id, 0.30),
        maybe(ctx.patient_name, 0.15),
        maybe(alarm_time + timedelta(minutes=random.randint(1, 30)), 0.40),
        maybe("调整报警限/通知医生处理", 0.20),
        random.choice(["未处理", "已处理", "已确认"]),
        datetime.now(),
    )

    cols = [
        "alarm_id", "patient_id", "icu_admission_id", "visit_id", "bed_id",
        "alarm_time", "alarm_level", "alarm_type", "parameter_name", "parameter_value",
        "threshold_low", "threshold_high", "alarm_message", "duration_seconds",
        "handled_flag", "handler_id", "handler_name", "handle_time", "handle_action",
        "status", "create_time",
    ]
    return ("icu_monitoring_db", "alarms", cols, [row])


# ------------------------------------------------------------------
# 血气分析
# ------------------------------------------------------------------

def _handle_blood_gas(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    counter = ctx.state.setdefault("blood_gas_counter", [0])
    gas_id = next_id("BG", counter)
    sample_time = event.timestamp
    icu_adm_id = ctx.get_id("icu_admission_id") or f"IA{random.randint(1, 9999)}"

    ph = round(random.uniform(7.20, 7.55), 2)
    paco2 = round(random.uniform(25.0, 70.0), 1)
    pao2 = round(random.uniform(50.0, 350.0), 1)
    hco3 = round(random.uniform(15.0, 35.0), 1)
    be = round((hco3 - 24) * 1.2, 1)
    sao2 = round(random.uniform(85.0, 100.0), 2)
    lactate = round(random.uniform(0.5, 15.0), 1)
    fio2 = round(random.uniform(0.21, 1.00), 2)

    row = (
        gas_id,
        ctx.patient_id,
        icu_adm_id,
        ctx.visit_id,
        random.choice(["动脉血", "静脉血", "混合静脉血"]),
        sample_time,
        ph,
        paco2,
        pao2,
        hco3,
        be,
        sao2,
        lactate,
        round(random.uniform(3.5, 15.0), 1),
        round(random.uniform(3.0, 6.0), 1),
        round(random.uniform(130.0, 155.0), 1),
        round(random.uniform(95.0, 115.0), 1),
        round(random.uniform(1.0, 1.3), 2),
        round(random.uniform(8.0, 15.0), 1),
        round(random.uniform(25.0, 50.0), 2),
        fio2,
        round(random.uniform(35.0, 37.5), 1),
        random.choice(["SIMV", "PSV", "PRVC", "AC", "CPAP", "自主呼吸"]),
        ctx.attending_doctor_id,
        maybe(ctx.patient_name, 0.15),
        random.choice(["Y", "N"]),
        datetime.now(),
    )

    cols = [
        "gas_id", "patient_id", "icu_admission_id", "visit_id", "specimen_type",
        "collect_time", "ph", "pco2", "po2", "hco3", "be", "sao2", "lac",
        "glucose", "potassium", "sodium", "chloride", "calcium", "hemoglobin",
        "hct", "fio2", "temp", "vent_mode", "operator_id", "operator_name",
        "verify_flag", "create_time",
    ]
    results = [("icu_monitoring_db", "blood_gas", cols, [row])]

    # 5% 概率生成 CRRT 记录
    if random.random() < 0.05:
        cr_counter = ctx.state.setdefault("cr_counter", [0])
        cr_id = next_id("CR", cr_counter)
        start_time = sample_time
        end_time = start_time + timedelta(hours=random.randint(4, 24)) if random.random() < 0.7 else None
        cr_row = (
            cr_id,
            icu_adm_id,
            ctx.patient_id,
            ctx.visit_id,
            start_time,
            end_time,
            random.choice(["CVVH", "CVVHD", "CVVHDF", "SCUF"]),
            round(random.uniform(150, 250), 1),
            round(random.uniform(500, 2000), 1),
            round(random.uniform(1000, 4000), 1),
            random.choice(["肝素", "枸橼酸钠", "无抗凝"]),
            maybe(f"{random.uniform(5, 20):.1f}U/kg/h", 0.20),
            round(random.uniform(500, 3000), 1),
            round(random.uniform(1000, 5000), 1),
            maybe(f"Filter-{random.randint(100, 999)}", 0.30),
            random.randint(12, 72) if end_time else None,
            maybe(random.choice(["滤器凝血", "治疗完成", "患者转出"]), 0.20) if end_time else None,
            ctx.attending_doctor_id,
            datetime.now(),
        )
        cr_cols = [
            "crrt_id", "icu_admission_id", "patient_id", "visit_id", "start_time", "end_time",
            "treatment_mode", "blood_flow", "dialysate_flow", "replacement_flow", "anticoagulant",
            "anticoagulant_dose", "uf_volume", "replacement_volume", "filter_model",
            "filter_life_hours", "termination_reason", "operator_id", "create_time",
        ]
        results.append(("icu_monitoring_db", "crrt_records", cr_cols, [cr_row]))

    return results
