"""病案模块生成器：病案首页/诊断/手术/肿瘤登记。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from meddata_gen.seed_data import (
    ICD10_DIAGNOSES,
    generate_name,
    random_datetime,
    random_date_between,
    maybe_null,
)


class BinganMixin:
    """病案（住院首页/编码）数据生成。"""

    def generate_medical_records(self, count: int = 7800):
        """生成病案首页"""
        rows = []

        for i in range(count):
            if self._should_link("bingan_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
                medical_record_no = visit[2] if visit[2] else f"MR{random.randint(100000, 999999)}"
                admission_time = visit[4]
                discharge_time = visit[12]
                hospital_days = visit[17]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"
                medical_record_no = f"MR{random.randint(100000, 999999)}"
                admission_time = random_datetime("2023-01-01", "2024-06-30")
                hospital_days = random.randint(3, 30)
                discharge_time = admission_time + timedelta(days=hospital_days)

            diagnosis = random.choice(ICD10_DIAGNOSES)
            total_cost = round(random.uniform(3000, 200000), 2)

            rows.append((
                f"BA{str(i+1).zfill(7)}", patient_id, visit_id, medical_record_no,
                admission_time,
                discharge_time,
                hospital_days,
                random.choice([d["name"] for d in self.departments]),
                random.choice([d["name"] for d in self.departments]),
                maybe_null("无", 0.20),
                random.randint(1, 5),
                random.choice(["急诊", "门诊", "转院"]),
                random.choice(["医嘱离院", "医嘱转院", "非医嘱离院", "死亡", "其他"]),
                random.choice(["治愈", "好转", "未愈", "死亡", "其他"]),
                maybe_null(diagnosis[1], 0.08),
                maybe_null(diagnosis[0], 0.10),
                maybe_null(diagnosis[0], 0.15),
                maybe_null("其他诊断", 0.25),
                maybe_null("外伤", 0.40),
                maybe_null("病理诊断", 0.35),
                maybe_null("病理号", 0.45),
                random.randint(0, 5),
                total_cost,
                round(total_cost * random.uniform(0.2, 0.5), 2),
                round(total_cost * random.uniform(0.2, 0.4), 2),
                round(total_cost * random.uniform(0.05, 0.15), 2),
                round(total_cost * random.uniform(0.05, 0.12), 2),
                round(total_cost * random.uniform(0.03, 0.10), 2),
                round(total_cost * random.uniform(0.05, 0.20), 2),
                round(total_cost * random.uniform(0.02, 0.08), 2),
                round(total_cost * random.uniform(0.02, 0.06), 2),
                random.randint(18, 85),
                maybe_null(random.randint(1, 11), 0.95),
                maybe_null(round(random.uniform(2500, 4000), 2), 0.98),
                maybe_null(round(random.uniform(2500, 4000), 2), 0.98),
                maybe_null(f"DRG{random.randint(100, 999)}", 0.30),
                maybe_null(f"DRG名称{random.randint(1, 100)}", 0.35),
                maybe_null(f"MDC{random.randint(1, 26)}", 0.35),
                random.choice(["甲", "乙", "丙"]),
                random.choice(["Y", "N"]),
                random.choice(["Y", "N"]),
                generate_name(),
                datetime.now(),
                maybe_null(discharge_time + timedelta(days=random.randint(1, 7)), 0.20) if discharge_time else None,
                random.choice(["未归档", "已归档", "借阅中"]),
                datetime.now(), None,
                random.randint(1, 10),
                random.randint(0, 5),
                maybe_null(random.choice(["无", "发热", "皮疹", "寒战", "血红蛋白尿", "过敏性休克"]), 0.70),
                random.choice(["Y", "N"]),
                maybe_null(f"P{random.randint(100000, 999999)}", 0.40),
                maybe_null(round(random.uniform(0.5, 5.0), 4), 0.45),
                maybe_null(random.choice(["医保", "自费", "商保", "公费", "异地结算"]), 0.30),
            ))

        self._batch_insert("medical_records",
            ["record_id", "patient_id", "visit_id", "medical_record_no", "admission_time",
             "discharge_time", "hospital_days", "admission_dept", "discharge_dept",
             "transfer_dept", "dept_count", "admission_type", "discharge_type",
             "discharge_status", "principal_diagnosis", "principal_diagnosis_icd",
             "principal_diagnosis_code", "other_diagnoses", "external_cause",
             "pathological_diagnosis", "pathological_code", "surgery_count", "total_cost",
             "self_pay", "drug_cost", "material_cost", "exam_cost", "lab_cost",
             "surgery_cost", "anesthesia_cost", "nursing_cost", "age", "age_month",
             "weight", "birth_weight", "drg_code", "drg_name", "mdc_code",
             "quality_control", "teaching_case", "research_case", "coding_doctor",
             "coding_time", "archive_time", "archive_status", "create_time", "update_time",
             "admission_count", "transfusion_count", "transfusion_reaction",
             "autopsy_flag", "pathology_no", "drg_weight", "insurance_settlement_type"],
            rows)
        print(f"  [BINGAN] medical_records: {len(rows)} rows")

    def generate_bingan_diagnoses(self, count: int = 25000):
        """生成病案诊断明细"""
        rows = []
        diagnosis_types = ["主要诊断", "其他诊断", "并发症", "院内感染"]

        for i in range(count):
            if self._should_link("bingan_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            diagnosis = random.choice(ICD10_DIAGNOSES)
            # 混入少量ICD-9编码
            icd_version = random.choice(["ICD-10", "ICD-10", "ICD-10", "ICD-9"])

            rows.append((
                f"BD{str(i+1).zfill(7)}",
                f"BA{random.randint(1, 8000)}",
                patient_id, visit_id,
                random.randint(1, 10),
                random.choice(diagnosis_types),
                diagnosis[1],
                diagnosis[0],
                icd_version,
                random.choice(["有", "临床未确定", "情况不明", "无"]),
                random.choice(["治愈", "好转", "未愈", "死亡", "其他"]),
                random.choice([s[0] for s in self.staff if s[10] == "医生"]),
                datetime.now()
            ))

        self._batch_insert("diagnoses",
            ["diagnosis_id", "record_id", "patient_id", "visit_id", "seq_no",
             "diagnosis_type", "diagnosis_name", "diagnosis_icd", "diagnosis_version",
             "in_condition", "discharge_status", "doctor_id", "create_time"],
            rows)
        print(f"  [BINGAN] diagnoses: {len(rows)} rows")

    def generate_bingan_surgeries(self, count: int = 4500):
        """生成手术操作明细"""
        rows = []
        surgery_names = [
            ("阑尾切除术", "47.0"), ("胆囊切除术", "51.2"), ("胃大部切除术", "43.7"),
            ("肠切除术", "45.7"), ("脾切除术", "41.5"), ("肝部分切除术", "50.2"),
            ("甲状腺切除术", "06.4"), ("乳腺切除术", "85.4"), ("剖宫产术", "74.1"),
            ("子宫切除术", "68.4"), ("髋关节置换术", "81.5"), ("膝关节置换术", "81.5"),
            ("脊柱融合术", "81.0"), ("开颅术", "01.2"), ("冠状动脉搭桥术", "36.1"),
            ("心脏瓣膜置换术", "35.2"), ("肺叶切除术", "32.4"), ("肾切除术", "55.5"),
            ("前列腺切除术", "60.5"), ("骨折内固定术", "79.3"),
        ]

        for i in range(count):
            if self._should_link("bingan_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            surgery = random.choice(surgery_names)
            rows.append((
                f"BS{str(i+1).zfill(7)}",
                f"BA{random.randint(1, 8000)}",
                patient_id, visit_id,
                random.randint(1, 5),
                surgery[0], surgery[1],
                random_date_between(datetime(2023, 1, 1), datetime(2024, 12, 31)),
                random.choice(["I级", "II级", "III级", "IV级"]),
                maybe_null(generate_name(), 0.15),
                maybe_null(generate_name(), 0.30),
                maybe_null(generate_name(), 0.45),
                random.choice(["全麻", "硬膜外", "腰麻", "局麻"]),
                maybe_null(generate_name(), 0.25),
                random.choice(["甲", "乙", "丙"]),
                random.choice(["I", "II", "III", "IV", "V"]),
                random.choice(["Y", "N"]),
                random.choice(["Y", "N"]),
                random.choice(["Y", "N"]),
                random.choice(["Y", "N"]),
                datetime.now()
            ))

        self._batch_insert("surgeries",
            ["surgery_id", "record_id", "patient_id", "visit_id", "seq_no",
             "surgery_name", "surgery_icd", "surgery_date", "surgery_level",
             "surgeon_name", "assistant1_name", "assistant2_name", "anesthesia_type",
             "anesthesia_doctor", "incision_healing", "anesthesia_level",
             "is_emergency", "is_sterile", "is_microscope", "is_reoperation", "create_time"],
            rows)
        print(f"  [BINGAN] surgeries: {len(rows)} rows")

    def generate_tumor_registry(self, count: int = 300):
        """生成肿瘤登记"""
        rows = []
        tumor_sites = [
            "肺", "胃", "肝", "结肠", "直肠", "乳腺", "食管", "宫颈", "卵巢",
            "前列腺", "膀胱", "肾", "胰腺", "甲状腺", "脑", "鼻咽", "淋巴",
            "骨", "皮肤", "软组织",
        ]

        for i in range(count):
            if self._should_link("bingan_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            site = random.choice(tumor_sites)
            first_dx = random_date_between(datetime(2020, 1, 1), datetime(2024, 6, 30))

            rows.append((
                f"TR{str(i+1).zfill(5)}", patient_id,
                f"IV{random.randint(1, 8000)}",
                f"MR{random.randint(100000, 999999)}",
                f"TR{random.randint(10000, 99999)}",
                site,
                f"C{random.randint(15, 80)}",
                f"8{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}/3",
                random.choice(["良性", "恶性", "原位", "交界性"]),
                random.choice(["高分化", "中分化", "低分化", "未分化"]),
                random.choice(["T1", "T2", "T3", "T4", "Tx"]),
                random.choice(["N0", "N1", "N2", "N3", "Nx"]),
                random.choice(["M0", "M1", "Mx"]),
                maybe_null(f"{random.choice(['T1','T2','T3','T4'])}N{random.choice(['0','1','2','3'])}M{random.choice(['0','1'])}", 0.15),
                random.choice(["I期", "II期", "III期", "IV期"]),
                maybe_null(random.choice(["I期", "II期", "III期", "IV期"]), 0.25),
                random.choice(["病理", "临床", "细胞学", "影像学"]),
                first_dx,
                first_dx + timedelta(days=random.randint(1, 30)),
                generate_name(),
                f"HOSP{random.randint(100, 999)}",
                random.choice(["存活", "失访", "死亡", "未知"]),
                random.choice(["存活", "死亡", "未知"]),
                random.randint(0, 60),
                datetime.now()
            ))

        self._batch_insert("tumor_registry",
            ["tumor_id", "patient_id", "visit_id", "medical_record_no", "report_no",
             "tumor_site", "tumor_code", "morphology", "behavior", "grade",
             "t_stage", "n_stage", "m_stage", "tnm_stage", "clinical_stage",
             "pathological_stage", "diagnosis_basis", "first_diagnosis_date",
             "report_date", "reporter", "hospital_code", "follow_up_status",
             "survival_status", "survival_months", "create_time"],
            rows)
        print(f"  [BINGAN] tumor_registry: {len(rows)} rows")

    def generate_medical_record_borrows(self, count: int = 800):
        """生成病案借阅记录"""
        rows = []
        statuses = ["借阅中", "已归还", "已逾期", "已续借"]

        for i in range(count):
            if self._should_link("bingan_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            borrow_time = random_datetime("2023-01-01", "2024-12-31")
            expected_return_time = borrow_time + timedelta(days=random.randint(3, 30))
            status = random.choice(statuses)
            return_time = (
                borrow_time + timedelta(days=random.randint(1, 35))
                if status in ["已归还", "已逾期"] else None
            )

            rows.append((
                f"BR{str(i+1).zfill(5)}",
                f"BA{random.randint(1, 8000)}",
                patient_id,
                generate_name(),
                random.choice([d["name"] for d in self.departments]),
                maybe_null(f"138{random.randint(10000000, 99999999)}", 0.30),
                borrow_time,
                expected_return_time,
                return_time,
                maybe_null(random.choice(["科研", "教学", "质控", "医保审核", "司法", "随访"]), 0.25),
                status,
                datetime.now()
            ))

        self._batch_insert("medical_record_borrows",
            ["borrow_id", "record_id", "patient_id", "borrower_name", "borrower_dept",
             "borrower_phone", "borrow_time", "expected_return_time", "return_time",
             "borrow_purpose", "status", "create_time"],
            rows)
        print(f"  [BINGAN] medical_record_borrows: {len(rows)} rows")

    def generate_qc_defects(self, count: int = 5000):
        """生成病案质控缺陷记录"""
        rows = []
        defect_types = ["首页", "病程", "医嘱", "知情同意", "签名", "其他"]
        severities = ["甲", "乙", "丙", "单项否决"]
        defect_items = [
            "主诊断填写不完整", "出院情况未填写", "手术名称与编码不符",
            "病程记录不及时", "上级医师查房记录缺失", "知情同意书未签字",
            "首页基本信息缺项", "诊断依据不充分", "手术记录不完整",
            "麻醉记录单缺失", "护理记录不完整", "检验报告单未归档",
            "医嘱开立不规范", "会诊记录不及时", "交接班记录缺失",
        ]

        for i in range(count):
            if self._should_link("bingan_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            qc_time = random_datetime("2023-01-01", "2024-12-31")
            is_rectified = random.choice(["Y", "N", "Y", "Y"])
            rectify_time = (
                qc_time + timedelta(days=random.randint(1, 7))
                if is_rectified == "Y" else None
            )
            doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

            rows.append((
                f"QD{str(i+1).zfill(5)}",
                f"BA{random.randint(1, 8000)}",
                patient_id,
                random.choice(defect_types),
                random.choice(defect_items),
                random.choice(severities),
                maybe_null(random.choice(["描述不完整", "信息缺失", "逻辑错误", "格式不规范"]), 0.35),
                maybe_null(random.choice(doctor_ids), 0.25) if doctor_ids else None,
                qc_time,
                is_rectified,
                maybe_null(rectify_time, 0.30),
                datetime.now()
            ))

        self._batch_insert("qc_defects",
            ["defect_id", "record_id", "patient_id", "defect_type", "defect_item",
             "severity", "description", "qc_doctor_id", "qc_time",
             "is_rectified", "rectify_time", "create_time"],
            rows)
        print(f"  [BINGAN] qc_defects: {len(rows)} rows")

    def generate_obstetric_records(self, count: int = 600):
        """生成产科记录"""
        rows = []
        delivery_modes = ["顺产", "剖宫产", "产钳助产", "真空吸引"]
        amniotic_volumes = ["少", "中", "多"]
        amniotic_characters = ["清亮", "Ⅰ度污染", "Ⅱ度污染", "Ⅲ度污染", "血性"]
        neonatal_statuses = ["活产", "死胎", "死产"]

        for i in range(count):
            if self._should_link("bingan_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            gravida = random.randint(1, 5)
            para = random.randint(0, min(gravida, 3))
            abortions = max(0, gravida - para - random.randint(0, 1))
            gestational_weeks = round(random.uniform(37.0, 42.0), 1)
            gestational_days = int((gestational_weeks % 1) * 7)
            delivery_date = random_datetime("2023-01-01", "2024-12-31")
            first_stage = round(random.uniform(4.0, 16.0), 1)
            second_stage = round(random.uniform(0.5, 3.0), 1)
            third_stage = random.randint(5, 30)
            labor_duration = round(first_stage + second_stage + third_stage / 60, 1)
            apgar1 = random.randint(7, 10)
            apgar5 = random.randint(8, 10)
            apgar10 = random.randint(8, 10) if random.random() > 0.3 else None

            rows.append((
                f"OB{str(i+1).zfill(5)}",
                visit_id,
                patient_id,
                gravida,
                para,
                abortions,
                gestational_weeks,
                gestational_days,
                random.choice(delivery_modes),
                delivery_date,
                labor_duration,
                first_stage,
                second_stage,
                third_stage,
                random.choice(["Y", "N"]),
                maybe_null(random.choice(["0", "I", "II", "III"]), 0.50),
                apgar1,
                apgar5,
                apgar10,
                random.randint(2500, 4000),
                round(random.uniform(48.0, 52.0), 1),
                random.choice(["M", "F"]),
                random.choice(neonatal_statuses),
                random.randint(400, 700),
                random.choice(amniotic_volumes),
                random.choice(amniotic_characters),
                random.randint(100, 800),
                datetime.now()
            ))

        self._batch_insert("obstetric_records",
            ["record_id", "visit_id", "patient_id", "gravida", "para", "abortions",
             "gestational_weeks", "gestational_days", "delivery_mode", "delivery_date",
             "labor_duration_hours", "first_stage_hours", "second_stage_hours",
             "third_stage_minutes", "episiotomy_flag", "perineal_tear_degree",
             "apgar_score_1min", "apgar_score_5min", "apgar_score_10min",
             "birth_weight_g", "birth_length_cm", "neonatal_gender",
             "neonatal_status", "placental_weight_g", "amniotic_fluid_volume",
             "amniotic_fluid_character", "postpartum_bleeding_ml", "create_time"],
            rows)
        print(f"  [BINGAN] obstetric_records: {len(rows)} rows")
