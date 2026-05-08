"""ECG 事件处理器：心电检查与分析。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from meddata_gen.core.events import EventContext, MedicalEvent
from meddata_gen.core.handlers._common import maybe, next_id
from meddata_gen.seed_data import ECG_DIAGNOSES


def register_ecg_handlers(materializer) -> None:
    materializer.register("ecg", "ecg_exam", _handle_ecg_exam)
    materializer.register("ecg", "ecg_analysis", _handle_ecg_analysis)


# ------------------------------------------------------------------
# 心电检查
# ------------------------------------------------------------------

def _handle_ecg_exam(
    event: MedicalEvent, ctx: EventContext
) -> Optional[Tuple[str, str, List[str], List[tuple]]]:
    counter = ctx.state.setdefault("ecg_exam_counter", [0])
    exam_id = next_id("ECG", counter)
    exam_time = event.timestamp
    exam_type = random.choice(["常规12导联", "18导联", "动态心电图", "运动平板", "心电监护"])

    # ecg_exams（对齐 schema 22列）
    row = (
        exam_id,
        ctx.patient_id,
        ctx.visit_id,
        "住院" if ctx.visit_type == "inpatient" else "门诊",
        f"EC{random.randint(100000, 999999)}",
        None,
        exam_type,
        maybe(f"DEV{random.randint(1, 20)}", 0.25),
        maybe(f"ECG-{random.randint(100, 999)}", 0.25),
        random.choice(["心电图室", "病房", "急诊", "ICU"]),
        exam_time,
        maybe(ctx.attending_doctor_id, 0.20),
        ctx.department_id,
        maybe(ctx.attending_doctor_id, 0.30),
        maybe(ctx.patient_name, 0.15),
        random.choice(["静息", "运动后", "吸氧中", "疼痛发作"]),
        random.randint(45, 150),
        500,
        0.05,
        150.0,
        random.choice(["标准12导联", "18导联", "Mason-Likar"]),
        random.randint(5, 30),
        random.choice(["已采集", "分析中", "已完成", "已审核"]),
        datetime.now(),
        None,
    )

    ctx.record_id("ecg_exam_id", exam_id)

    cols = [
        "exam_id", "patient_id", "visit_id", "visit_type", "exam_no",
        "order_id", "exam_type", "device_id", "device_model", "exam_location",
        "exam_time", "request_doctor", "request_dept", "operator_id", "operator_name",
        "patient_state", "heart_rate", "sampling_rate", "filter_low", "filter_high",
        "lead_system", "duration", "status", "create_time", "update_time",
    ]
    results = [("ecg_db", "ecg_exams", cols, [row])]

    # 动态心电图 → holter_records
    if exam_type == "动态心电图":
        hl_counter = ctx.state.setdefault("hl_counter", [0])
        hl_id = next_id("HL", hl_counter)
        avg_hr = random.randint(55, 95)
        hl_row = (
            hl_id,
            ctx.patient_id,
            ctx.visit_id,
            exam_time.date(),
            24,
            random.randint(80000, 120000),
            avg_hr,
            random.randint(40, avg_hr - 5),
            random.randint(avg_hr + 5, 160),
            maybe(exam_time + timedelta(hours=random.randint(2, 22)), 0.20),
            maybe(exam_time + timedelta(hours=random.randint(2, 22)), 0.20),
            random.randint(0, 10),
            random.randint(1000, 5000),
            round(random.uniform(0, 30), 2),
            random.randint(0, 50),
            random.randint(100, 5000),
            random.randint(50, 2000),
            random.randint(0, 20),
            random.randint(0, 10),
            random.choice(["Y", "N"]),
            random.choice(["草稿", "已提交", "已审核"]),
            ctx.attending_doctor_id,
            maybe(exam_time + timedelta(hours=random.randint(2, 48)), 0.30),
            datetime.now(),
        )
        hl_cols = [
            "holter_id", "patient_id", "visit_id", "record_date", "total_hours", "total_beats",
            "avg_hr", "min_hr", "max_hr", "min_hr_time", "max_hr_time", "pauses_count",
            "longest_pause_ms", "af_burden", "af_episodes", "ve_count", "sv_count",
            "vt_episodes", "svt_episodes", "st_deviation_flag", "report_status",
            "reporter_id", "report_time", "create_time",
        ]
        results.append(("ecg_db", "holter_records", hl_cols, [hl_row]))
        ctx.record_id("holter_id", hl_id)

    # 运动平板 → stress_test_records
    elif exam_type == "运动平板":
        st_counter = ctx.state.setdefault("st_counter", [0])
        st_id = next_id("ST", st_counter)
        max_hr = random.randint(120, 180)
        duration = random.randint(180, 900)
        st_row = (
            st_id,
            ctx.patient_id,
            ctx.visit_id,
            random.choice(["Bruce", "Modified Bruce", "Balke", "Naughton"]),
            round(random.uniform(3.0, 8.0), 1),
            round(random.uniform(5.0, 20.0), 1),
            max_hr,
            random.randint(140, 170),
            f"{random.randint(90, 180)}/{random.randint(60, 110)}",
            duration,
            round(duration / 60 * random.uniform(3.0, 6.0), 1),
            random.choice(["阳性", "阴性", "可疑", "未完成"]),
            maybe(random.choice(["达到目标心率", "出现ST段压低", "患者要求停止", "出现心律失常"]), 0.20),
            round(random.uniform(-0.2, 0.5), 2),
            maybe(random.choice(["室性早搏", "房性早搏", "短阵室速"]), 0.30),
            maybe(random.choice(["无", "轻度", "中度", "重度"]), 0.40),
            ctx.attending_doctor_id,
            maybe(exam_time + timedelta(minutes=random.randint(10, 60)), 0.30),
            datetime.now(),
        )
        st_cols = [
            "test_id", "patient_id", "visit_id", "protocol", "max_speed", "max_grade",
            "max_hr", "target_hr", "max_bp", "test_duration", "max_mets", "test_result",
            "termination_reason", "st_deviation_max", "arrhythmia", "chest_pain",
            "reporter_id", "report_time", "create_time",
        ]
        results.append(("ecg_db", "stress_test_records", st_cols, [st_row]))

    return results


# ------------------------------------------------------------------
# 心电分析
# ------------------------------------------------------------------

def _handle_ecg_analysis(
    event: MedicalEvent, ctx: EventContext
) -> Optional[List[Tuple[str, str, List[str], List[tuple]]]]:
    counter_ana = ctx.state.setdefault("ecg_analysis_counter", [0])
    counter_wf = ctx.state.setdefault("ecg_waveform_counter", [0])
    analysis_id = next_id("EA", counter_ana)
    analysis_time = event.timestamp

    exam_id = ctx.get_id("ecg_exam_id") or f"ECG{random.randint(1, 9999999)}"

    diagnosis = random.choice(ECG_DIAGNOSES)
    hr = random.randint(45, 150)
    rhythm = random.choice(["窦性心律", "房颤", "房扑", "室上速", "室速", "窦缓", "窦速"])
    pr = round(random.uniform(120, 220), 1)
    qrs = round(random.uniform(60, 120), 1)
    qt = round(random.uniform(320, 480), 1)
    qtc = round(random.uniform(350, 520), 1)

    # ecg_analyses（对齐 schema 28列）
    ana_row = (
        analysis_id,
        exam_id,
        ctx.patient_id,
        rhythm,
        hr,
        random.randint(30, 90),      # p_axis
        random.randint(-30, 120),    # qrs_axis
        random.randint(0, 90),       # t_axis
        pr,
        qrs,
        qt,
        qtc,
        diagnosis,
        maybe(f"ECG{random.randint(100, 999)}", 0.10),
        maybe("ST-T改变", 0.30),
        random.choice(["正常", "异常", "危急"]),
        maybe("建议心内科进一步评估", 0.30),
        maybe("无明显变化", 0.40),
        None,
        maybe(round(random.uniform(0.70, 0.99), 2), 0.10),
        ctx.attending_doctor_id,
        maybe(ctx.patient_name, 0.15),
        analysis_time,
        maybe(ctx.attending_doctor_id, 0.25),
        maybe(ctx.patient_name, 0.15),
        maybe(analysis_time + timedelta(minutes=random.randint(10, 120)), 0.30),
        random.choice(["草稿", "已提交", "已审核"]),
        datetime.now(),
    )

    # ecg_waveforms（对齐 schema 18列，12导联中随机生成 1-3 个）
    wf_rows = []
    leads = random.sample(
        ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"],
        k=random.randint(1, 3),
    )
    for lead in leads:
        wf_id = next_id("WF", counter_wf)
        wf_row = (
            wf_id,
            exam_id,
            ctx.patient_id,
            lead,
            round(random.uniform(-0.1, 0.1), 2),
            round(random.uniform(-1.0, 0.5), 2),
            round(random.uniform(0.5, 2.5), 2),
            round(random.uniform(0.05, 0.25), 2),
            round(random.uniform(60, 120), 1),
            round(random.uniform(0.5, 2.0), 2),
            round(random.uniform(60, 110), 1),
            round(random.uniform(0.1, 0.6), 2),
            round(random.uniform(120, 220), 1),
            round(random.uniform(-0.5, 0.5), 2),
            round(random.uniform(120, 220), 1),
            round(random.uniform(320, 480), 1),
            round(random.uniform(350, 520), 1),
            random.randint(60, 100),
            random.choice(["Y", "N"]),
            datetime.now(),
        )
        wf_rows.append(wf_row)

    ana_cols = [
        "analysis_id", "exam_id", "patient_id", "rhythm", "heart_rate",
        "p_axis", "qrs_axis", "t_axis", "pr_interval", "qrs_duration",
        "qt_interval", "qtc_interval", "diagnosis", "diagnosis_codes",
        "abnormalities", "severity", "interpretation", "comparison_result",
        "comparison_exam_id", "ai_score", "reporter_id", "reporter_name",
        "report_time", "auditor_id", "auditor_name", "audit_time",
        "report_status", "create_time",
    ]
    wf_cols = [
        "waveform_id", "exam_id", "patient_id", "lead_name", "baseline",
        "amplitude_min", "amplitude_max", "p_wave_amplitude", "p_wave_duration",
        "qrs_amplitude", "qrs_duration", "t_wave_amplitude", "t_wave_duration",
        "st_segment", "pr_interval", "qt_interval", "qtc_interval",
        "quality_score", "artifact_flag", "create_time",
    ]

    results = [("ecg_db", "ecg_analyses", ana_cols, [ana_row])]
    if wf_rows:
        results.append(("ecg_db", "ecg_waveforms", wf_cols, wf_rows))

    # 如果关联了 Holter 记录，生成 Holter 事件
    holter_id = ctx.get_id("holter_id")
    if holter_id:
        he_counter = ctx.state.setdefault("he_counter", [0])
        he_rows = []
        for _ in range(random.randint(1, 5)):
            he_id = next_id("HE", he_counter)
            he_rows.append((
                he_id,
                holter_id,
                analysis_time + timedelta(hours=random.randint(0, 23)),
                random.choice(["室早", "房早", "室速", "房颤", "ST改变", "停搏"]),
                random.randint(1, 300),
                random.randint(40, 100),
                random.randint(80, 180),
                random.randint(60, 140),
                maybe("心悸", 0.30),
                maybe(random.choice(["静息", "活动", "睡眠"]), 0.40),
                datetime.now(),
            ))
        he_cols = [
            "event_id", "holter_id", "event_time", "event_type", "duration_seconds",
            "min_hr", "max_hr", "avg_hr", "symptom", "activity", "create_time",
        ]
        results.append(("ecg_db", "holter_events", he_cols, he_rows))

    return results
