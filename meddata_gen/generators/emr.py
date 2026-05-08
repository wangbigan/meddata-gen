"""EMR 模块生成器：病历文档/病程/入院/出院/手术/护理记录。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from meddata_gen import config
from meddata_gen.seed_data import (
    ICD10_DIAGNOSES,
    generate_name,
    random_datetime,
    maybe_null,
)


class EMRMixin:
    """EMR（电子病历）数据生成。"""

    def generate_emr_documents(self, count: int = 30000):
        """生成EMR病历文档"""
        rows = []
        emr_doc_types = [
            "入院记录", "首次病程记录", "日常病程记录", "出院记录", "死亡记录",
            "手术记录", "会诊记录", "抢救记录", "转科记录", "交接班记录"
        ]
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            # 关联率控制
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                # 孤儿记录
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            doc_type = random.choice(emr_doc_types)
            write_time = random_datetime("2023-01-01", "2024-12-31")
            author = random.choice(doctor_ids) if doctor_ids else None

            rows.append((
                f"EMR{str(i+1).zfill(7)}", patient_id, visit_id,
                random.choice(["住院", "门诊", "急诊"]),
                doc_type,
                f"{doc_type}-{i+1}",
                maybe_null(f"这是{doc_type}的内容...", 0.05),
                random.choice([d["id"] for d in self.departments]),
                author,
                maybe_null(generate_name() if not author else None, 0.10),
                write_time,
                maybe_null(write_time + timedelta(hours=random.randint(1, 48)), 0.30),
                random.choice(["0", "1"]),
                random.randint(0, 5),
                maybe_null(author, 0.40),
                maybe_null(write_time + timedelta(days=random.randint(1, 3)), 0.50),
                random.choice(["甲", "乙", "丙", None]),
                random.randint(0, 5),
                random.choice(["草稿", "完成", "归档"]),
                maybe_null(random.randint(1, 50), 0.10),
                random.choice(["未打印", "已打印", "部分打印"]),
                random.choice(["未归档", "待归档", "已归档"]),
                maybe_null(write_time + timedelta(days=random.randint(1, 7)), 0.40),
                maybe_null(random.choice(doctor_ids) if doctor_ids else None, 0.40),
                maybe_null(f"TPL{random.randint(100, 999)}", 0.20),
                datetime.now(), None
            ))

        self._batch_insert("emr_documents",
            ["document_id", "patient_id", "visit_id", "visit_type", "document_type",
             "document_title", "document_content", "dept_id", "author_id", "author_name",
             "write_time", "sign_time", "sign_status", "modify_count", "modifier_id",
             "modify_time", "quality_status", "print_count", "status", "page_no",
             "print_status", "archive_status", "archive_time", "archiver_id", "template_id",
             "create_time", "update_time"],
            rows)
        print(f"  [EMR] emr_documents: {len(rows)} rows")

    def generate_progress_notes(self, count: int = 80000):
        """生成病程记录"""
        rows = []
        note_types = ["日常病程", "上级查房", "交接班", "抢救记录", "阶段小结"]
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            note_time = random_datetime("2023-01-01", "2024-12-31")
            author = random.choice(doctor_ids) if doctor_ids else None

            rows.append((
                f"PN{str(i+1).zfill(7)}", patient_id, visit_id,
                note_time.date(),
                note_time,
                random.choice(note_types),
                maybe_null("患者今日病情...", 0.10),
                author,
                maybe_null(generate_name(), 0.15),
                maybe_null(note_time + timedelta(hours=random.randint(1, 12)), 0.35),
                note_time,
                datetime.now()
            ))

        self._batch_insert("progress_notes",
            ["note_id", "patient_id", "visit_id", "note_date", "note_time", "note_type",
             "content", "author_id", "author_name", "sign_time", "record_time", "create_time"],
            rows)
        print(f"  [EMR] progress_notes: {len(rows)} rows")

    def generate_admission_records(self, count: int = 8000):
        """生成入院记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
                admission_time = visit[4]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"
                admission_time = random_datetime("2023-01-01", "2024-12-31")

            diagnosis = random.choice(ICD10_DIAGNOSES)
            doctor = random.choice(doctor_ids) if doctor_ids else None
            write_time = admission_time + timedelta(hours=random.randint(1, 6))

            rows.append((
                f"AR{str(i+1).zfill(7)}", patient_id, visit_id,
                admission_time,
                maybe_null("发热伴咳嗽1周", 0.12),
                maybe_null("患者1周前无明显诱因出现发热...", 0.15),
                maybe_null("否认高血压、糖尿病病史", 0.20),
                maybe_null("无吸烟饮酒史", 0.30),
                maybe_null("否认家族遗传病史", 0.35),
                maybe_null("否认药物及食物过敏史", 0.25),
                maybe_null("T 37.5C P 80次/分 R 20次/分 BP 120/80mmHg", 0.10),
                maybe_null("神志清楚，精神可", 0.15),
                maybe_null("血常规示WBC 10.5x10^9/L", 0.20),
                maybe_null(diagnosis[1], 0.08),
                maybe_null(diagnosis[0], 0.25),
                maybe_null("抗感染对症支持治疗", 0.15),
                doctor,
                maybe_null(generate_name(), 0.15),
                write_time,
                maybe_null(write_time + timedelta(hours=random.randint(1, 24)), 0.30),
                maybe_null("月经史正常", 0.50),
                maybe_null("孕0产0", 0.50),
                maybe_null(random.choice(["正常", "焦虑", "抑郁", "否认异常"]), 0.30),
                maybe_null(random.choice(["良好", "一般", "营养不良", "肥胖"]), 0.30),
                maybe_null(random.choice(["低危", "中危", "高危"]), 0.30),
                datetime.now()
            ))

        self._batch_insert("admission_records",
            ["record_id", "patient_id", "visit_id", "admission_time", "chief_complaint",
             "present_illness", "past_history", "personal_history", "family_history",
             "allergy_history", "physical_exam", "vital_signs", "auxiliary_exam",
             "preliminary_diagnosis", "diagnosis_icd", "treatment_plan", "doctor_id",
             "doctor_name", "write_time", "sign_time", "menstrual_history", "obstetric_history",
             "psychological_status", "nutrition_status", "fall_risk", "create_time"],
            rows)
        print(f"  [EMR] admission_records: {len(rows)} rows")

    def generate_discharge_records(self, count: int = 7800):
        """生成出院记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
                admission_time = visit[4]
                discharge_time = visit[12]
                hospital_days = visit[17]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"
                admission_time = random_datetime("2023-01-01", "2024-06-30")
                hospital_days = random.randint(3, 30)
                discharge_time = admission_time + timedelta(days=hospital_days)

            diagnosis = random.choice(ICD10_DIAGNOSES)
            doctor = random.choice(doctor_ids) if doctor_ids else None

            # 逻辑错误：少数出院时间早于入院时间
            if random.random() < config.QUALITY["logic_error_rate"]:
                discharge_time = admission_time - timedelta(days=random.randint(1, 5))

            rows.append((
                f"DR{str(i+1).zfill(7)}", patient_id, visit_id,
                admission_time,
                discharge_time,
                hospital_days if hospital_days is not None else random.randint(1, 30),
                maybe_null("发热待查", 0.15),
                maybe_null(diagnosis[1], 0.10),
                maybe_null(diagnosis[0], 0.25),
                maybe_null("入院后完善相关检查...", 0.15),
                maybe_null("治愈", 0.12),
                maybe_null("出院带药，定期复查", 0.18),
                maybe_null("1周后门诊复查", 0.30),
                doctor,
                maybe_null(generate_name(), 0.15),
                discharge_time - timedelta(hours=random.randint(1, 6)) if discharge_time else random_datetime("2023-01-01", "2024-12-31"),
                maybe_null(discharge_time, 0.30) if discharge_time else None,
                datetime.now()
            ))

        self._batch_insert("discharge_records",
            ["record_id", "patient_id", "visit_id", "admission_time", "discharge_time",
             "hospital_days", "admission_diagnosis", "discharge_diagnosis", "diagnosis_icd",
             "treatment_summary", "discharge_status", "discharge_advice", "follow_up_plan",
             "doctor_id", "doctor_name", "write_time", "sign_time", "create_time"],
            rows)
        print(f"  [EMR] discharge_records: {len(rows)} rows")

    def generate_death_records(self, count: int = 500):
        """生成死亡记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            death_time = random_datetime("2023-01-01", "2024-12-31")
            diagnosis = random.choice(ICD10_DIAGNOSES)
            doctor = random.choice(doctor_ids) if doctor_ids else None

            rows.append((
                f"DE{str(i+1).zfill(7)}", patient_id, visit_id,
                death_time,
                maybe_null(diagnosis[1], 0.10),
                maybe_null(diagnosis[1], 0.15),
                maybe_null(diagnosis[0], 0.20),
                random.choice(["Y", "N"]),
                maybe_null("尸检结果待补充", 0.60),
                maybe_null(death_time + timedelta(hours=random.randint(1, 12)), 0.30),
                doctor,
                datetime.now()
            ))

        self._batch_insert("death_records",
            ["record_id", "patient_id", "visit_id", "death_time", "death_cause",
             "death_diagnosis", "death_icd", "autopsy_flag", "autopsy_result",
             "notify_family_time", "doctor_id", "create_time"],
            rows)
        print(f"  [EMR] death_records: {len(rows)} rows")

    def generate_consultation_records(self, count: int = 3000):
        """生成会诊记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        dept_ids = [d["id"] for d in self.departments]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            request_time = random_datetime("2023-01-01", "2024-12-31")
            request_dept = random.choice(dept_ids) if dept_ids else None
            request_doctor = random.choice(doctor_ids) if doctor_ids else None
            requested_dept = random.choice(dept_ids) if dept_ids else None
            requested_doctor = random.choice(doctor_ids) if doctor_ids else None

            rows.append((
                f"CR{str(i+1).zfill(7)}", patient_id, visit_id,
                random.choice(["普通会诊", "急会诊", "多学科会诊", "远程会诊"]),
                request_dept,
                request_doctor,
                requested_dept,
                requested_doctor,
                request_time,
                maybe_null(request_time + timedelta(hours=random.randint(1, 48)), 0.25),
                maybe_null("会诊意见待补充", 0.20),
                random.choice(["普通", "紧急"]),
                random.choice(["申请中", "已安排", "已完成", "已取消"]),
                datetime.now()
            ))

        self._batch_insert("consultation_records",
            ["consultation_id", "patient_id", "visit_id", "consultation_type",
             "request_dept_id", "request_doctor_id", "requested_dept_id", "requested_doctor_id",
             "request_time", "consultation_time", "consultation_opinion", "urgency",
             "status", "create_time"],
            rows)
        print(f"  [EMR] consultation_records: {len(rows)} rows")

    def generate_emr_diagnoses(self, count: int = 50000):
        """生成EMR诊断明细"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            diagnosis = random.choice(ICD10_DIAGNOSES)
            diagnosis_time = random_datetime("2023-01-01", "2024-12-31")
            doctor = random.choice(doctor_ids) if doctor_ids else None

            rows.append((
                f"ED{str(i+1).zfill(7)}", patient_id, visit_id,
                random.choice(["入院诊断", "出院诊断", "术前诊断", "术后诊断", "病理诊断"]),
                random.randint(1, 10),
                diagnosis[1],
                maybe_null(diagnosis[0], 0.15),
                diagnosis_time,
                doctor,
                random.choice(["Y", "N"]),
                datetime.now()
            ))

        self._batch_insert("emr_diagnoses",
            ["diagnosis_id", "patient_id", "visit_id", "diagnosis_type", "seq_no",
             "diagnosis_name", "diagnosis_icd", "diagnosis_time", "doctor_id",
             "is_principal", "create_time"],
            rows)
        print(f"  [EMR] emr_diagnoses: {len(rows)} rows")

    def generate_surgery_records(self, count: int = 4000):
        """生成手术记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
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
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            surgery = random.choice(surgery_names)
            start_time = random_datetime("2023-01-01", "2024-12-31")
            duration = random.randint(30, 360)
            end_time = start_time + timedelta(minutes=duration)
            surgeon = random.choice(doctor_ids) if doctor_ids else None

            rows.append((
                f"SR{str(i+1).zfill(7)}", patient_id, visit_id,
                f"SG{str(i+1).zfill(6)}",
                surgery[0], surgery[1],
                random.choice(["I级", "II级", "III级", "IV级"]),
                maybe_null("术前诊断", 0.15),
                maybe_null("术后诊断", 0.15),
                surgeon,
                maybe_null(generate_name(), 0.15),
                maybe_null(random.choice(doctor_ids) if doctor_ids else None, 0.25),
                maybe_null(random.choice(doctor_ids) if doctor_ids else None, 0.40),
                maybe_null(random.choice(doctor_ids) if doctor_ids else None, 0.30),
                random.choice(["全麻", "硬膜外", "腰麻", "局麻", "颈丛"]),
                start_time, end_time, duration,
                random.choice(["I类", "II类", "III类", "IV类"]),
                maybe_null("手术经过顺利...", 0.12),
                maybe_null("术中所见...", 0.20),
                round(random.uniform(50, 2000), 1),
                round(random.uniform(0, 1000), 1),
                maybe_null("送病理", 0.30),
                maybe_null("注意休息，伤口换药", 0.25),
                random.choice(["已完成", "已完成", "已完成", "取消"]),
                datetime.now()
            ))

        self._batch_insert("surgery_records",
            ["record_id", "patient_id", "visit_id", "surgery_id", "surgery_name", "surgery_code",
             "surgery_level", "pre_op_diagnosis", "post_op_diagnosis", "surgeon_id", "surgeon_name",
             "assistant1_id", "assistant2_id", "anesthesiologist_id", "anesthesia_type",
             "surgery_start_time", "surgery_end_time", "surgery_duration", "incision_type",
             "operative_procedure", "intraoperative_findings", "blood_loss", "blood_transfusion",
             "specimen", "post_op_advice", "status", "create_time"],
            rows)
        print(f"  [EMR] surgery_records: {len(rows)} rows")

    def generate_nursing_records(self, count: int = 150000):
        """生成护理记录"""
        rows = []
        nurse_ids = [s[0] for s in self.staff if s[10] == "护士"]
        consciousness_list = ["清醒", "嗜睡", "昏迷", "模糊", "谵妄"]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            record_time = random_datetime("2023-01-01", "2024-12-31")
            nurse = random.choice(nurse_ids) if nurse_ids else None

            rows.append((
                f"NR{str(i+1).zfill(8)}", patient_id, visit_id,
                record_time,
                random.choice(["白班", "夜班"]),
                nurse,
                maybe_null(generate_name(), 0.15),
                maybe_null(round(random.uniform(36.0, 39.5), 1), 0.05),
                maybe_null(random.randint(60, 120), 0.05),
                maybe_null(random.randint(12, 30), 0.08),
                maybe_null(f"{random.randint(90, 160)}/{random.randint(60, 100)}", 0.06),
                maybe_null(round(random.uniform(90, 100), 1), 0.08),
                random.choice(consciousness_list),
                maybe_null(round(random.uniform(500, 3000), 1), 0.15),
                maybe_null(round(random.uniform(500, 3000), 1), 0.15),
                maybe_null(round(random.uniform(200, 2500), 1), 0.18),
                maybe_null(random.randint(0, 3), 0.30),
                maybe_null("无特殊", 0.25),
                maybe_null("完整", 0.20),
                maybe_null("无", 0.30),
                maybe_null("遵医嘱用药", 0.25),
                maybe_null("病情平稳", 0.20),
                maybe_null("继续观察", 0.25),
                maybe_null(round(random.uniform(2.0, 5.0), 1), 0.20),
                maybe_null(round(random.uniform(2.0, 5.0), 1), 0.20),
                maybe_null(random.choice(["灵敏", "迟钝", "消失"]), 0.25),
                maybe_null(random.randint(0, 10), 0.30),
                maybe_null(random.randint(0, 10), 0.30),
                maybe_null(random.randint(6, 23), 0.30),
                maybe_null(random.choice(["留置导尿护理", "膀胱冲洗", "更换尿袋"]), 0.40),
                maybe_null(random.choice(["换药", "引流管护理", "压疮护理"]), 0.40),
                record_time + timedelta(minutes=random.randint(1, 30)),
                datetime.now()
            ))

        self._batch_insert("nursing_records",
            ["record_id", "patient_id", "visit_id", "record_time", "shift", "nurse_id",
             "nurse_name", "temperature", "pulse", "respiration", "blood_pressure", "spo2",
             "consciousness", "intake_fluid", "output_fluid", "urine", "stool_count",
             "special_care", "skin_condition", "drainage", "medication", "observation",
             "nursing_measures", "pupil_size_left", "pupil_size_right", "light_reflex",
             "pain_score", "fall_score", "braden_score", "catheter_care", "wound_care",
             "signature_time", "create_time"],
            rows)
        print(f"  [EMR] nursing_records: {len(rows)} rows")

    def generate_transfusion_records(self, count: int = 2000):
        """生成输血记录"""
        rows = []
        blood_products = ["红细胞", "血浆", "血小板", "冷沉淀"]
        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            start_time = random_datetime("2023-01-01", "2024-12-31")
            duration = random.randint(60, 300)
            end_time = start_time + timedelta(minutes=duration)
            reaction = random.choice(["Y", "N", "N", "N", "N"])

            rows.append((
                f"TF{str(i+1).zfill(7)}", patient_id, visit_id,
                random.choice(["A", "B", "AB", "O", "RH-"]),
                random.choice(blood_products),
                random.randint(100, 600),
                f"BG{random.randint(100000, 999999)}",
                start_time, end_time,
                reaction,
                maybe_null("发热，寒战", 0.30) if reaction == "Y" else None,
                round(random.uniform(36.0, 37.5), 1),
                round(random.uniform(36.5, 39.0), 1) if reaction == "Y" else round(random.uniform(36.0, 37.5), 1),
                maybe_null(f"{random.randint(100, 140)}/{random.randint(60, 90)}", 0.10),
                maybe_null(f"{random.randint(100, 140)}/{random.randint(60, 90)}", 0.10),
                datetime.now()
            ))

        self._batch_insert("transfusion_records",
            ["transfusion_id", "patient_id", "visit_id", "blood_type", "blood_product",
             "volume_ml", "blood_bag_no", "transfusion_start_time", "transfusion_end_time",
             "transfusion_reaction", "reaction_desc", "pre_temp", "post_temp", "pre_bp", "post_bp", "create_time"],
            rows)
        print(f"  [EMR] transfusion_records: {len(rows)} rows")

    def generate_informed_consents(self, count: int = 5000):
        """生成知情同意书"""
        rows = []
        consent_types = ["手术同意", "麻醉同意", "输血同意", "病危通知", "特殊检查", "侵入性操作"]
        relations = ["本人", "配偶", "子女", "父母", "其他"]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            sign_time = random_datetime("2023-01-01", "2024-12-31")

            rows.append((
                f"IC{str(i+1).zfill(7)}", patient_id, visit_id,
                random.choice(consent_types),
                maybe_null("已详细告知患者/家属相关风险及替代方案", 0.15),
                maybe_null(generate_name(), 0.10),
                random.choice(relations),
                maybe_null(generate_phone(), 0.15),
                sign_time,
                maybe_null(f"ST{random.randint(1, 200)}", 0.20),
                maybe_null(generate_name(), 0.25),
                datetime.now()
            ))

        self._batch_insert("informed_consents",
            ["consent_id", "patient_id", "visit_id", "consent_type", "consent_content",
             "signer_name", "signer_relation", "signer_phone", "sign_time", "doctor_id",
             "witness_name", "create_time"],
            rows)
        print(f"  [EMR] informed_consents: {len(rows)} rows")

    def generate_nursing_assessments(self, count: int = 10000):
        """生成护理评估单"""
        rows = []
        assessment_types = ["入院", "跌倒", "压疮", "VTE", "疼痛", "营养"]
        risk_levels = ["低", "中", "高", "极高"]
        nurse_ids = [s[0] for s in self.staff if s[10] == "护士"]

        for i in range(count):
            if self._should_link("emr_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"

            assess_type = random.choice(assessment_types)
            total_score = random.randint(0, 25)
            risk_level = random.choice(risk_levels)

            rows.append((
                f"NA{str(i+1).zfill(7)}", patient_id, visit_id,
                assess_type,
                random_datetime("2023-01-01", "2024-12-31"),
                total_score,
                risk_level,
                maybe_null(f"评分{total_score}分，{risk_level}风险", 0.20),
                maybe_null("加强观察，落实预防措施", 0.20),
                random.choice(nurse_ids) if nurse_ids else None,
                datetime.now()
            ))

        self._batch_insert("nursing_assessments",
            ["assessment_id", "patient_id", "visit_id", "assessment_type", "assessment_time",
             "total_score", "risk_level", "risk_factors", "preventive_measures", "nurse_id", "create_time"],
            rows)
        print(f"  [EMR] nursing_assessments: {len(rows)} rows")
