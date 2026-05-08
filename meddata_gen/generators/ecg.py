"""ECG 模块生成器：心电检查/波形/分析。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from meddata_gen.seed_data import (
    ECG_DIAGNOSES,
    generate_name,
    random_datetime,
    maybe_null,
)


class ECGMixin:
    """ECG（心电信息系统）数据生成。"""

    def generate_ecg_exams(self, count: int = 15000):
        """生成心电检查"""
        rows = []
        exam_types = ["常规12导联", "18导联", "动态心电图", "运动平板", "心电监护"]
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("ecg_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            exam_time = random_datetime("2023-01-01", "2024-12-31")
            exam_type = random.choice(exam_types)

            rows.append((
                f"EC{str(i+1).zfill(6)}", patient_id,
                f"IV{random.randint(1, 8000)}",
                random.choice(["住院", "门诊", "急诊", "体检"]),
                f"ECG{random.randint(100000, 999999)}",
                maybe_null(f"OR{random.randint(1, 120000)}", 0.45),
                exam_type,
                maybe_null(f"ECG{random.randint(1, 20)}", 0.20),
                random.choice(["MAC 2000", "PageWriter TC50", "SE-18", "ECG-2350"]),
                random.choice(["心电图室", "病房", "急诊", "ICU"]),
                exam_time,
                maybe_null(generate_name(), 0.25),
                random.choice([d["name"] for d in self.departments]),
                maybe_null(f"ST{random.randint(1, 200)}", 0.30),
                maybe_null(generate_name(), 0.35),
                random.choice(["静息", "运动后", "吸氧中", "疼痛发作"]),
                random.randint(60, 120),
                1000 if exam_type == "常规12导联" else 500,
                0.05, 150.0,
                "标准12导联" if exam_type == "常规12导联" else "18导联",
                random.randint(10, 300),
                random.choice(["已采集", "分析中", "已完成", "已审核"]),
                datetime.now(), None,
                maybe_null(random.choice(["V1", "V2", "V3", "II", "III", "aVR"]), 0.35),
                maybe_null(random.choice(["无", "轻度", "中度", "重度"]), 0.30),
                maybe_null(random.choice(["I期", "II期", "III期", "恢复期"]), 0.50) if exam_type == "运动平板" else None,
            ))

        self._batch_insert("ecg_exams",
            ["exam_id", "patient_id", "visit_id", "visit_type", "exam_no", "order_id",
             "exam_type", "device_id", "device_model", "exam_location", "exam_time",
             "request_doctor", "request_dept", "operator_id", "operator_name",
             "patient_state", "heart_rate", "sampling_rate", "filter_low", "filter_high",
             "lead_system", "duration", "status", "create_time", "update_time",
             "lead_off_info", "baseline_drift", "exercise_stage"],
            rows)
        print(f"  [ECG] ecg_exams: {len(rows)} rows")

    def generate_ecg_waveforms(self, count: int = 15000):
        """生成心电波形数据"""
        rows = []
        leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

        for i in range(count):
            if self._should_link("ecg_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            lead = random.choice(leads)
            qrs_dur = random.uniform(60, 120)

            rows.append((
                f"EW{str(i+1).zfill(7)}",
                f"EC{random.randint(1, 15000)}",
                patient_id,
                lead,
                round(random.uniform(-0.5, 0.5), 2),
                round(random.uniform(-2.0, -0.1), 2),
                round(random.uniform(0.5, 3.0), 2),
                round(random.uniform(0.05, 0.25), 2),
                round(random.uniform(80, 160), 1),
                round(random.uniform(-2.0, -0.5), 2),
                qrs_dur,
                round(random.uniform(0.1, 0.8), 2),
                round(random.uniform(100, 300), 1),
                round(random.uniform(-0.5, 0.5), 2),
                round(random.uniform(120, 220), 1),
                round(qrs_dur + random.uniform(200, 400), 1),
                round(qrs_dur + random.uniform(200, 400) / (random.uniform(0.8, 1.2)), 1),
                random.randint(60, 100),
                random.choice(["Y", "N"]),
                datetime.now()
            ))

        self._batch_insert("ecg_waveforms",
            ["waveform_id", "exam_id", "patient_id", "lead_name", "baseline",
             "amplitude_min", "amplitude_max", "p_wave_amplitude", "p_wave_duration",
             "qrs_amplitude", "qrs_duration", "t_wave_amplitude", "t_wave_duration",
             "st_segment", "pr_interval", "qt_interval", "qtc_interval",
             "quality_score", "artifact_flag", "create_time"],
            rows)
        print(f"  [ECG] ecg_waveforms: {len(rows)} rows")

    def generate_ecg_analyses(self, count: int = 15000):
        """生成心电分析结果"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("ecg_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            report_time = random_datetime("2023-01-01", "2024-12-31")
            reporter = random.choice(doctor_ids) if doctor_ids else None
            diagnosis = random.choice(ECG_DIAGNOSES)

            rows.append((
                f"EA{str(i+1).zfill(6)}",
                f"EC{random.randint(1, 15000)}",
                patient_id,
                random.choice(ECG_DIAGNOSES),
                random.randint(45, 130),
                maybe_null(random.randint(-30, 90), 0.20),
                maybe_null(random.randint(-30, 120), 0.20),
                maybe_null(random.randint(0, 90), 0.20),
                round(random.uniform(120, 220), 1),
                round(random.uniform(60, 120), 1),
                round(random.uniform(300, 450), 1),
                round(random.uniform(350, 500), 1),
                diagnosis,
                maybe_null(f"{diagnosis}", 0.30),
                maybe_null("窦性心律不齐", 0.40),
                random.choice(["正常", "异常", "危急"]),
                maybe_null("请结合临床", 0.35),
                random.choice(["无明显变化", "改善", "加重", "新出现"]),
                maybe_null(f"EC{random.randint(1, 15000)}", 0.50),
                round(random.uniform(0.7, 0.99), 2),
                reporter,
                maybe_null(generate_name(), 0.15),
                report_time,
                maybe_null(reporter, 0.30),
                maybe_null(generate_name(), 0.35),
                maybe_null(report_time + timedelta(hours=random.randint(1, 12)), 0.30),
                random.choice(["草稿", "已提交", "已审核"]),
                datetime.now()
            ))

        self._batch_insert("ecg_analyses",
            ["analysis_id", "exam_id", "patient_id", "rhythm", "heart_rate",
             "p_axis", "qrs_axis", "t_axis", "pr_interval", "qrs_duration",
             "qt_interval", "qtc_interval", "diagnosis", "diagnosis_codes",
             "abnormalities", "severity", "interpretation", "comparison_result",
             "comparison_exam_id", "ai_score", "reporter_id", "reporter_name",
             "report_time", "auditor_id", "auditor_name", "audit_time",
             "report_status", "create_time"],
            rows)
        print(f"  [ECG] ecg_analyses: {len(rows)} rows")

    def generate_holter_records(self, count: int = 3000):
        """生成动态心电图(Holter)记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("ecg_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            record_date = random_datetime("2023-01-01", "2024-12-31")
            total_hours = random.randint(20, 48)
            total_beats = random.randint(60000, 150000)
            avg_hr = random.randint(55, 95)
            min_hr = random.randint(35, 55)
            max_hr = random.randint(110, 180)
            reporter = random.choice(doctor_ids) if doctor_ids else None
            report_time = record_date + timedelta(hours=random.randint(12, 48))

            rows.append((
                f"HO{str(i+1).zfill(5)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                record_date.date(),
                total_hours,
                total_beats,
                avg_hr,
                min_hr,
                max_hr,
                record_date + timedelta(hours=random.randint(1, total_hours)),
                record_date + timedelta(hours=random.randint(1, total_hours)),
                random.randint(0, 20),
                random.randint(0, 3000),
                round(random.uniform(0, 50), 2),
                random.randint(0, 50),
                random.randint(0, 5000),
                random.randint(0, 3000),
                random.randint(0, 20),
                random.randint(0, 30),
                random.choice(["Y", "N"]),
                random.choice(["草稿", "已提交", "已审核"]),
                reporter,
                report_time,
                datetime.now()
            ))

        self._batch_insert("holter_records",
            ["holter_id", "patient_id", "visit_id", "record_date", "total_hours",
             "total_beats", "avg_hr", "min_hr", "max_hr", "min_hr_time",
             "max_hr_time", "pauses_count", "longest_pause_ms", "af_burden",
             "af_episodes", "ve_count", "sv_count", "vt_episodes", "svt_episodes",
             "st_deviation_flag", "report_status", "reporter_id", "report_time",
             "create_time"],
            rows)
        print(f"  [ECG] holter_records: {len(rows)} rows")

    def generate_holter_events(self, count: int = 15000):
        """生成Holter事件记录"""
        rows = []
        event_types = ["室早", "房早", "室速", "房颤", "ST改变", "停搏", "起搏"]

        for i in range(count):
            event_time = random_datetime("2023-01-01", "2024-12-31")
            rows.append((
                f"HE{str(i+1).zfill(6)}",
                f"HO{random.randint(1, 3000)}",
                event_time,
                random.choice(event_types),
                random.randint(1, 600),
                random.randint(40, 180),
                random.randint(50, 200),
                random.randint(45, 190),
                maybe_null(random.choice(["心悸", "胸闷", "头晕", "无症状", "乏力"]), 0.30),
                maybe_null(random.choice(["静息", "步行", "睡眠", "运动", "进食"]), 0.35),
                datetime.now()
            ))

        self._batch_insert("holter_events",
            ["event_id", "holter_id", "event_time", "event_type", "duration_seconds",
             "min_hr", "max_hr", "avg_hr", "symptom", "activity", "create_time"],
            rows)
        print(f"  [ECG] holter_events: {len(rows)} rows")

    def generate_stress_test_records(self, count: int = 2000):
        """生成运动平板记录"""
        rows = []
        protocols = ["Bruce", "Modified Bruce", "Balke", "Naughton"]
        test_results = ["阳性", "阴性", "可疑", "未完成"]
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("ecg_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            test_duration = random.randint(180, 1200)
            reporter = random.choice(doctor_ids) if doctor_ids else None
            report_time = random_datetime("2023-01-01", "2024-12-31")

            rows.append((
                f"ST{str(i+1).zfill(5)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                random.choice(protocols),
                round(random.uniform(2.0, 10.0), 1),
                round(random.uniform(0, 22), 1),
                random.randint(100, 190),
                random.randint(120, 170),
                f"{random.randint(100, 200)}/{random.randint(60, 110)}",
                test_duration,
                round(random.uniform(3.0, 15.0), 1),
                random.choice(test_results),
                maybe_null(random.choice(["达到目标心率", "疲劳", "胸痛", "ST段压低", "心律失常", "血压异常"]), 0.30),
                maybe_null(round(random.uniform(-0.3, 0.3), 2), 0.25),
                maybe_null(random.choice(["室早", "房早", "室上速", "无"]), 0.30),
                maybe_null(random.choice(["无", "轻度", "中度", "重度"]), 0.40),
                reporter,
                report_time,
                datetime.now()
            ))

        self._batch_insert("stress_test_records",
            ["test_id", "patient_id", "visit_id", "protocol", "max_speed", "max_grade",
             "max_hr", "target_hr", "max_bp", "test_duration", "max_mets",
             "test_result", "termination_reason", "st_deviation_max", "arrhythmia",
             "chest_pain", "reporter_id", "report_time", "create_time"],
            rows)
        print(f"  [ECG] stress_test_records: {len(rows)} rows")
