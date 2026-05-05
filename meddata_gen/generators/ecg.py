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
                datetime.now(), None
            ))

        self._batch_insert("ecg_exams",
            ["exam_id", "patient_id", "visit_id", "visit_type", "exam_no", "order_id",
             "exam_type", "device_id", "device_model", "exam_location", "exam_time",
             "request_doctor", "request_dept", "operator_id", "operator_name",
             "patient_state", "heart_rate", "sampling_rate", "filter_low", "filter_high",
             "lead_system", "duration", "status", "create_time", "update_time"],
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
