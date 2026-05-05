"""ICU 模块生成器：入科/监护/报警/血气。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from meddata_gen.seed_data import (
    ICD10_DIAGNOSES,
    ICU_ALARM_TYPES,
    generate_name,
    random_datetime,
    maybe_null,
)


class ICUMixin:
    """ICU（重症监护）数据生成。"""

    def generate_icu_admissions(self, count: int = 2000):
        """生成ICU入科记录"""
        rows = []
        icu_depts = [d for d in self.departments if "ICU" in d["name"] or "重症" in d["name"]]
        icu_dept_ids = [d["id"] for d in icu_depts] if icu_depts else [d["id"] for d in self.departments[:5]]

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
                hospital_visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"
                hospital_visit_id = f"IV{random.randint(1, 9999999)}"

            admission_time = random_datetime("2023-01-01", "2024-11-30")
            los = random.choices(range(1, 31), weights=[20]*5 + [15]*10 + [10]*10 + [5]*5)[0]
            discharge_time = admission_time + timedelta(days=los)
            death_flag = random.choice(["Y", "N", "N", "N", "N"])

            if death_flag == "Y":
                discharge_status = "死亡"
                discharge_destination = "太平间"
            else:
                discharge_status = random.choice(["转病房", "转院", "自动出院"])
                discharge_destination = random.choice(["普通病房", "专科病房", "康复医院"])

            rows.append((
                f"IA{str(i+1).zfill(5)}", patient_id, visit_id, hospital_visit_id,
                f"BD{random.randint(1, 5000)}",
                f"{random.randint(1, 50)}床",
                admission_time,
                random.choice(["急诊", "手术室", "病房", "外院转入"]),
                random.choice(["计划入ICU", "抢救入ICU", "术后入ICU"]),
                random.choice(ICD10_DIAGNOSES)[1],
                maybe_null(random.choice(ICD10_DIAGNOSES)[1], 0.30),
                random.randint(0, 40),
                random.randint(0, 20),
                random.randint(3, 15),
                round(random.uniform(40, 100), 2),
                round(random.uniform(150, 190), 1),
                round(random.uniform(15, 35), 2),
                round(los * random.uniform(0.8, 1.5), 1),
                discharge_time,
                discharge_status,
                discharge_destination,
                los,
                death_flag,
                datetime.now()
            ))

        self._batch_insert("icu_admissions",
            ["icu_admission_id", "patient_id", "visit_id", "hospital_visit_id", "bed_id",
             "bed_no", "admission_time", "admission_source", "admission_type",
             "primary_diagnosis", "secondary_diagnosis", "apacheii_score", "sofa_score",
             "gcs_score", "admission_weight", "height", "bmi", "expected_los",
             "discharge_time", "discharge_status", "discharge_destination",
             "actual_los", "death_flag", "create_time"],
            rows)
        print(f"  [ICU] icu_admissions: {len(rows)} rows")

    def generate_monitoring_data(self, count: int = 500000):
        """生成监护仪数据"""
        rows = []

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            monitor_time = random_datetime("2023-01-01", "2024-12-31")
            has_alarm = random.choice(["Y", "N", "N", "N", "N"])

            rows.append((
                patient_id,
                f"IA{random.randint(1, 2000)}",
                f"IV{random.randint(1, 8000)}",
                f"BD{random.randint(1, 5000)}",
                monitor_time,
                random.randint(50, 140) if random.random() > 0.05 else None,
                random.randint(90, 170) if random.random() > 0.05 else None,
                random.randint(50, 100) if random.random() > 0.05 else None,
                random.randint(60, 120) if random.random() > 0.06 else None,
                round(random.uniform(88, 100), 1) if random.random() > 0.05 else None,
                random.randint(10, 35) if random.random() > 0.06 else None,
                round(random.uniform(35.5, 39.5), 1) if random.random() > 0.07 else None,
                maybe_null(random.randint(5, 15), 0.30),
                maybe_null(random.randint(20, 40), 0.50),
                maybe_null(random.randint(8, 20), 0.50),
                maybe_null(round(random.uniform(4, 10), 2), 0.50),
                maybe_null(round(random.uniform(2, 5), 2), 0.55),
                maybe_null(round(random.uniform(50, 90), 1), 0.55),
                maybe_null(round(random.uniform(5, 15), 2), 0.60),
                maybe_null(round(random.uniform(8, 18), 2), 0.60),
                maybe_null(random.randint(30, 50), 0.65),
                maybe_null(round(random.uniform(30, 60), 2), 0.65),
                maybe_null(random.randint(30, 100), 0.70),
                maybe_null(round(random.uniform(21, 100), 2), 0.70),
                maybe_null(random.randint(5, 25), 0.70),
                random.randint(200, 800),
                random.randint(200, 800),
                round(random.uniform(5, 20), 2),
                "1:2",
                maybe_null(random.randint(5, 25), 0.80),
                maybe_null(random.randint(50, 90), 0.80),
                maybe_null(round(random.uniform(40, 60), 1), 0.85),
                maybe_null(round(random.uniform(0, 200), 1), 0.50),
                random.choice(["监护仪", "呼吸机", "血气", "输液泵"]),
                maybe_null(f"INST{random.randint(1, 20)}", 0.30),
                has_alarm,
                datetime.now()
            ))

        self._batch_insert("monitoring_data",
            ["patient_id", "icu_admission_id", "visit_id", "bed_id", "monitor_time",
             "hr", "sbp", "dbp", "map", "spo2", "rr", "temp", "cvp",
             "pap_systolic", "pap_diastolic", "co", "ci", "sv", "svv", "pvp",
             "etco2", "fio2", "peep", "pip", "plateau_pressure", "tv_set", "tv_actual",
             "mv", "ie_ratio", "icp", "cpp", "bis", "urine_output", "data_source",
             "device_id", "alarm_flag", "create_time"],
            rows)
        print(f"  [ICU] monitoring_data: {len(rows)} rows")

    def generate_alarms(self, count: int = 50000):
        """生成报警记录"""
        rows = []

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            alarm_time = random_datetime("2023-01-01", "2024-12-31")
            nurse_ids = [s[0] for s in self.staff if s[10] == "护士"]
            handler = random.choice(nurse_ids) if nurse_ids else None
            handled = random.choice(["Y", "N", "Y", "Y"])

            rows.append((
                f"AL{str(i+1).zfill(6)}", patient_id,
                f"IA{random.randint(1, 2000)}",
                f"IV{random.randint(1, 8000)}",
                f"BD{random.randint(1, 5000)}",
                alarm_time,
                random.choice(["高", "中", "低", "提示"]),
                random.choice(ICU_ALARM_TYPES),
                random.choice(["心率", "血压", "血氧", "呼吸", "体温"]),
                f"{random.randint(50, 200)}",
                maybe_null(f"{random.randint(50, 100)}", 0.30),
                maybe_null(f"{random.randint(100, 200)}", 0.30),
                random.choice(ICU_ALARM_TYPES),
                random.randint(10, 600),
                handled,
                handler,
                maybe_null(generate_name(), 0.25),
                alarm_time + timedelta(minutes=random.randint(1, 30)) if handled == "Y" else None,
                maybe_null("调整报警限", 0.40) if handled == "Y" else None,
                random.choice(["已处理", "已处理", "未处理"]),
                datetime.now()
            ))

        self._batch_insert("alarms",
            ["alarm_id", "patient_id", "icu_admission_id", "visit_id", "bed_id",
             "alarm_time", "alarm_level", "alarm_type", "parameter_name",
             "parameter_value", "threshold_low", "threshold_high", "alarm_message",
             "duration_seconds", "handled_flag", "handler_id", "handler_name",
             "handle_time", "handle_action", "status", "create_time"],
            rows)
        print(f"  [ICU] alarms: {len(rows)} rows")

    def generate_blood_gas(self, count: int = 15000):
        """生成血气分析"""
        rows = []

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            collect_time = random_datetime("2023-01-01", "2024-12-31")
            ph = round(random.uniform(7.20, 7.55), 2)
            pco2 = round(random.uniform(25, 70), 1)
            po2 = round(random.uniform(50, 350), 1)
            hco3 = round(random.uniform(15, 35), 1)

            rows.append((
                f"BG{str(i+1).zfill(6)}", patient_id,
                f"IA{random.randint(1, 2000)}",
                f"IV{random.randint(1, 8000)}",
                random.choice(["动脉血", "静脉血", "混合静脉血"]),
                collect_time,
                ph,
                pco2,
                po2,
                hco3,
                round(hco3 - 24 + 0.03 * (ph - 7.4) * 100, 1),
                round(po2 / (random.uniform(0.4, 1.0) * 7.6), 1),
                round(random.uniform(0.5, 8.0), 2),
                round(random.uniform(3.5, 15.0), 1),
                round(random.uniform(3.0, 6.0), 1),
                round(random.uniform(130, 155), 1),
                round(random.uniform(95, 115), 1),
                round(random.uniform(0.9, 1.3), 2),
                round(random.uniform(10, 18), 1),
                round(random.uniform(30, 55), 1),
                maybe_null(round(random.uniform(20, 100), 2), 0.30),
                round(random.uniform(35.5, 39.0), 1),
                random.choice(["SIMV", "AC", "PSV", "CPAP", "PRVC", "PCV", "VCV", "HFOV"]),
                maybe_null(f"ST{random.randint(1, 200)}", 0.25),
                maybe_null(generate_name(), 0.30),
                random.choice(["Y", "N"]),
                datetime.now()
            ))

        self._batch_insert("blood_gas",
            ["gas_id", "patient_id", "icu_admission_id", "visit_id", "specimen_type",
             "collect_time", "ph", "pco2", "po2", "hco3", "be", "sao2", "lac",
             "glucose", "potassium", "sodium", "chloride", "calcium", "hemoglobin",
             "hct", "fio2", "temp", "vent_mode", "operator_id", "operator_name",
             "verify_flag", "create_time"],
            rows)
        print(f"  [ICU] blood_gas: {len(rows)} rows")
