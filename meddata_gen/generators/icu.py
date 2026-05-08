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
                random.choice(["Y", "N"]),
                random.choice(["Y", "N"]),
                maybe_null(random.choice(["去甲肾上腺素", "多巴胺", "多巴酚丁胺", "肾上腺素", "米力农", "硝酸甘油"]), 0.40),
                random.choice(["肠内营养", "肠外营养", "肠内+肠外", "禁食"]),
                datetime.now()
            ))

        self._batch_insert("icu_admissions",
            ["icu_admission_id", "patient_id", "visit_id", "hospital_visit_id", "bed_id",
             "bed_no", "admission_time", "admission_source", "admission_type",
             "primary_diagnosis", "secondary_diagnosis", "apacheii_score", "sofa_score",
             "gcs_score", "admission_weight", "height", "bmi", "expected_los",
             "discharge_time", "discharge_status", "discharge_destination",
             "actual_los", "death_flag", "mechanical_ventilation_flag",
             "renal_replacement_flag", "vasoactive_drugs", "nutrition_route", "create_time"],
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
                maybe_null(round(random.uniform(8, 20), 1), 0.35),
                maybe_null(round(random.uniform(270, 320), 1), 0.40),
                maybe_null(round(random.uniform(80, 500), 1), 0.30),
                datetime.now()
            ))

        self._batch_insert("blood_gas",
            ["gas_id", "patient_id", "icu_admission_id", "visit_id", "specimen_type",
             "collect_time", "ph", "pco2", "po2", "hco3", "be", "sao2", "lac",
             "glucose", "potassium", "sodium", "chloride", "calcium", "hemoglobin",
             "hct", "fio2", "temp", "vent_mode", "operator_id", "operator_name",
             "verify_flag", "ag", "osm", "pao2_fio2_ratio", "create_time"],
            rows)
        print(f"  [ICU] blood_gas: {len(rows)} rows")

    def generate_ventilator_settings(self, count: int = 8000):
        """生成呼吸机参数设置记录"""
        rows = []
        vent_modes = ["SIMV", "PSV", "PRVC", "AC", "CPAP", "ECMO", "Spontaneous"]

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            setting_time = random_datetime("2023-01-01", "2024-12-31")
            rows.append((
                f"VS{str(i+1).zfill(6)}",
                f"IA{random.randint(1, 2000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                setting_time,
                random.choice(vent_modes),
                random.randint(300, 800),
                random.randint(8, 35),
                round(random.uniform(0.3, 1.0), 2),
                random.randint(0, 15),
                random.randint(5, 25),
                random.choice(["1:1", "1:1.5", "1:2", "1:2.5", "1:3"]),
                round(random.uniform(-2.0, -0.5), 1),
                random.randint(15, 35),
                random.randint(20, 45),
                maybe_null(f"ST{random.randint(1, 200)}", 0.25),
                datetime.now()
            ))

        self._batch_insert("ventilator_settings",
            ["setting_id", "icu_admission_id", "patient_id", "visit_id", "setting_time",
             "vent_mode", "tv_set", "rr_set", "fio2_set", "peep_set",
             "pressure_support", "ie_ratio", "trigger_sensitivity",
             "plateau_pressure", "pip", "operator_id", "create_time"],
            rows)
        print(f"  [ICU] ventilator_settings: {len(rows)} rows")

    def generate_fluid_balance(self, count: int = 15000):
        """生成出入量明细"""
        rows = []

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            record_date = random_datetime("2023-01-01", "2024-12-31").date()
            intake_oral = round(random.uniform(0, 1500), 1)
            intake_iv = round(random.uniform(500, 4000), 1)
            intake_other = round(random.uniform(0, 500), 1)
            output_urine = round(random.uniform(200, 3000), 1)
            output_drainage = round(random.uniform(0, 800), 1)
            output_other = round(random.uniform(0, 500), 1)
            balance_total = round(
                (intake_oral + intake_iv + intake_other)
                - (output_urine + output_drainage + output_other), 1
            )
            nurse_ids = [s[0] for s in self.staff if s[10] == "护士"]

            rows.append((
                f"FB{str(i+1).zfill(6)}",
                f"IA{random.randint(1, 2000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                record_date,
                maybe_null(intake_oral, 0.20),
                maybe_null(intake_iv, 0.15),
                maybe_null(intake_other, 0.40),
                maybe_null(output_urine, 0.15),
                maybe_null(output_drainage, 0.35),
                maybe_null(output_other, 0.45),
                balance_total,
                maybe_null(random.choice(nurse_ids), 0.25) if nurse_ids else None,
                datetime.now()
            ))

        self._batch_insert("fluid_balance",
            ["balance_id", "icu_admission_id", "patient_id", "visit_id", "record_date",
             "intake_oral", "intake_iv", "intake_other",
             "output_urine", "output_drainage", "output_other",
             "balance_total", "nurse_id", "create_time"],
            rows)
        print(f"  [ICU] fluid_balance: {len(rows)} rows")

    def generate_crrt_records(self, count: int = 600):
        """生成CRRT记录"""
        rows = []
        treatment_modes = ["CVVH", "CVVHD", "CVVHDF", "SCUF"]
        anticoagulants = ["枸橼酸钠", "肝素", "低分子肝素", "无抗凝"]
        filter_models = ["Prismaflex M100", "Prismaflex M150", "Aquamax HF 16",
                         "HF 1400", "FX 60", "FX 80"]

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            start_time = random_datetime("2023-01-01", "2024-12-31")
            duration_hours = random.choices(range(4, 73), weights=[5]*10 + [10]*20 + [5]*30 + [2]*10)[0]
            end_time = start_time + timedelta(hours=duration_hours)
            anticoagulant = random.choice(anticoagulants)

            rows.append((
                f"CR{str(i+1).zfill(5)}",
                f"IA{random.randint(1, 2000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                start_time,
                end_time,
                random.choice(treatment_modes),
                round(random.uniform(100, 250), 1),
                round(random.uniform(500, 2000), 1),
                round(random.uniform(0, 2000), 1),
                anticoagulant,
                maybe_null(f"{random.randint(1, 50)}ml/h", 0.30) if anticoagulant != "无抗凝" else None,
                round(random.uniform(500, 5000), 1),
                round(random.uniform(0, 20000), 1),
                random.choice(filter_models),
                random.randint(4, 72),
                maybe_null(random.choice(["治疗完成", "滤器凝血", "患者转出", "病情好转", "死亡"]), 0.25),
                maybe_null(f"ST{random.randint(1, 200)}", 0.25),
                datetime.now()
            ))

        self._batch_insert("crrt_records",
            ["crrt_id", "icu_admission_id", "patient_id", "visit_id", "start_time",
             "end_time", "treatment_mode", "blood_flow", "dialysate_flow",
             "replacement_flow", "anticoagulant", "anticoagulant_dose",
             "uf_volume", "replacement_volume", "filter_model", "filter_life_hours",
             "termination_reason", "operator_id", "create_time"],
            rows)
        print(f"  [ICU] crrt_records: {len(rows)} rows")

    def generate_sedation_records(self, count: int = 25000):
        """生成镇静镇痛记录"""
        rows = []
        sedative_drugs = ["丙泊酚", "咪达唑仑", "右美托咪定", "劳拉西泮", "地西泮"]
        analgesic_drugs = ["芬太尼", "瑞芬太尼", "舒芬太尼", "吗啡", "地佐辛"]
        muscle_relaxants = ["顺阿曲库铵", "罗库溴铵", "维库溴铵", "泮库溴铵", None]

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            record_time = random_datetime("2023-01-01", "2024-12-31")
            nurse_ids = [s[0] for s in self.staff if s[10] == "护士"]

            rows.append((
                f"SR{str(i+1).zfill(6)}",
                f"IA{random.randint(1, 2000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                record_time,
                random.randint(-5, 4),
                random.randint(0, 8),
                random.randint(1, 6),
                maybe_null(random.choice(sedative_drugs), 0.20),
                maybe_null(f"{random.randint(10, 200)}mg/h", 0.25),
                maybe_null(random.choice(analgesic_drugs), 0.20),
                maybe_null(f"{random.randint(1, 50)}ug/h", 0.25),
                maybe_null(random.choice(muscle_relaxants), 0.60),
                maybe_null(random.choice(nurse_ids), 0.25) if nurse_ids else None,
                datetime.now()
            ))

        self._batch_insert("sedation_records",
            ["record_id", "icu_admission_id", "patient_id", "visit_id", "record_time",
             "rass_score", "cpot_score", "ramsay_score", "sedative_drug",
             "sedative_dose", "analgesic_drug", "analgesic_dose",
             "muscle_relaxant", "nurse_id", "create_time"],
            rows)
        print(f"  [ICU] sedation_records: {len(rows)} rows")

    def generate_intubation_records(self, count: int = 1200):
        """生成气管插管/拔管记录"""
        rows = []
        tube_types = ["气管插管", "气管切开", "喉罩"]
        extubation_outcomes = ["成功", "再插管", "拔管失败"]

        for i in range(count):
            if self._should_link("icu_monitoring_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            intubation_time = random_datetime("2023-01-01", "2024-12-31")
            los_hours = random.choices(range(1, 336), weights=[10]*24 + [5]*72 + [2]*240)[0]
            extubation_time = intubation_time + timedelta(hours=los_hours)
            doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

            rows.append((
                f"IT{str(i+1).zfill(5)}",
                f"IA{random.randint(1, 2000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                random.choice(tube_types),
                intubation_time,
                maybe_null(extubation_time, 0.20),
                maybe_null(f"{random.choice([6.0, 6.5, 7.0, 7.5, 8.0])}", 0.15),
                maybe_null(round(random.uniform(20.0, 25.0), 1), 0.15),
                maybe_null(random.choice(["呼吸衰竭", "全麻手术", "气道保护", "心肺复苏"]), 0.20),
                maybe_null(random.choice(["病情好转", "自主呼吸恢复", "转出ICU", "死亡"]), 0.30),
                maybe_null(random.choice(extubation_outcomes), 0.30),
                maybe_null(random.choice(doctor_ids), 0.25) if doctor_ids else None,
                datetime.now()
            ))

        self._batch_insert("intubation_records",
            ["record_id", "icu_admission_id", "patient_id", "visit_id", "tube_type",
             "intubation_time", "extubation_time", "tube_size", "depth_cm",
             "intubation_reason", "extubation_reason", "extubation_outcome",
             "doctor_id", "create_time"],
            rows)
        print(f"  [ICU] intubation_records: {len(rows)} rows")
