"""RIS 模块生成器：影像设备/检查申请/普放/CT/MRI/超声报告。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from meddata_gen.seed_data import (
    RIS_EXAM_TYPES,
    ICD10_DIAGNOSES,
    generate_name,
    random_datetime,
    random_date_between,
    maybe_null,
)


class RISMixin:
    """RIS（放射信息系统）数据生成。"""

    def generate_devices(self, count: int = 30):
        """生成影像设备字典"""
        devices = [
            ("XR01", "DR", "Discovery XR656", "GE"),
            ("XR02", "DR", "DigitalDiagnost", "飞利浦"),
            ("CT01", "CT", "Revolution CT", "GE"),
            ("CT02", "CT", "SOMATOM Force", "西门子"),
            ("CT03", "CT", "uCT 960+", "联影"),
            ("CT04", "CT", "Aquilion ONE", "佳能"),
            ("MR01", "MRI", "SIGNA 7.0T", "GE"),
            ("MR02", "MRI", "MAGNETOM Vida", "西门子"),
            ("MR03", "MRI", "uMR 890", "联影"),
            ("US01", "US", "LOGIQ E20", "GE"),
            ("US02", "US", "EPIQ 7", "飞利浦"),
            ("US03", "US", "Resona R9", "迈瑞"),
            ("MG01", "MG", "Senographe Pristina", "GE"),
            ("RF01", "RF", "Uni-Vision", "东芝"),
            ("PET01", "PET", "Discovery MI", "GE"),
        ]

        rows = []
        for i, (code, modality, model, manufacturer) in enumerate(devices):
            rows.append((
                f"DV{str(i+1).zfill(3)}", code,
                f"{modality}-{model}",
                modality,
                manufacturer,
                model,
                random.choice([d["id"] for d in self.departments if "放射" in d["name"] or "超声" in d["name"]]),
                f"Room-{random.randint(101, 999)}",
                random_date_between(datetime(2015, 1, 1), datetime(2023, 1, 1)),
                random.choice(["正常", "正常", "维修", "停用"]),
                datetime.now()
            ))

        self._batch_insert("devices",
            ["device_id", "device_code", "device_name", "modality", "manufacturer",
             "model", "location", "room_no", "install_date", "status", "create_time"],
            rows)
        print(f"  [RIS] devices: {len(rows)} rows")

    def generate_exam_orders(self, count: int = 25000):
        """生成检查申请"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        exam_items = []
        for modality, items in RIS_EXAM_TYPES.items():
            for item in items:
                exam_items.append((modality, item))

        for i in range(count):
            if self._should_link("ris_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
                visit_type = random.choice(["住院", "门诊", "急诊"])
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"
                visit_type = random.choice(["住院", "门诊", "急诊", "体检"])

            exam = self._sample_dict("exam_items_dict")
            if exam is None:
                modality_item = random.choice(exam_items)
                exam = (
                    f"EX{random.randint(1000000, 9999999)}",
                    modality_item[1], modality_item[0], None, None, None, None,
                )
            order_time = random_datetime("2023-01-01", "2024-12-31")

            rows.append((
                f"EO{str(i+1).zfill(7)}", patient_id, visit_id, visit_type,
                f"EX{random.randint(1000000, 9999999)}",
                order_time,
                random.choice([d["id"] for d in self.departments]),
                random.choice(doctor_ids) if doctor_ids else None,
                maybe_null(generate_name(), 0.15),
                exam[2] if exam[2] else "xray",   # exam_type
                exam[0],                          # exam_item_code
                exam[1],                          # exam_item_name
                maybe_null(random.choice(["头部", "胸部", "腹部", "盆腔", "脊柱", "四肢", "心脏", "甲状腺", "乳腺"]), 0.10),
                maybe_null("平扫+增强", 0.35),
                maybe_null(random.choice(ICD10_DIAGNOSES)[1], 0.20),
                maybe_null("进一步明确诊断", 0.30),
                random.choice(["普通", "紧急"]),
                random.choice(["Y", "N"]),
                maybe_null("无", 0.40),
                maybe_null("碘海醇", 0.50),
                random.choice(["已申请", "已预约", "已检查", "已报告", "已审核", "已取消"]),
                maybe_null(f"DV{random.randint(1, 15)}", 0.25),
                maybe_null(order_time + timedelta(hours=random.randint(1, 48)), 0.30),
                maybe_null(order_time + timedelta(hours=random.randint(2, 72)), 0.35),
                round(random.uniform(50, 5000), 2),
                maybe_null(random.choice(doctor_ids) if doctor_ids else None, 0.30),
                maybe_null(generate_name(), 0.15),
                maybe_null(random.randint(5, 120), 0.25),
                maybe_null(random.choice(["无", "轻度", "中度", "重度"]), 0.50),
                maybe_null(round(random.uniform(0.1, 15.0), 2), 0.40),
                datetime.now(), None
            ))

        self._batch_insert("exam_orders",
            ["order_id", "patient_id", "visit_id", "visit_type", "order_no",
             "order_time", "order_dept_id", "order_doctor_id", "order_doctor_name",
             "exam_type", "exam_item_code", "exam_item_name", "exam_part", "exam_method",
             "clinical_diagnosis", "purpose", "priority", "pregnancy_status",
             "allergy_history", "contrast_agent", "order_status", "device_id",
             "appointment_time", "exam_time", "fee", "technician_id", "technician_name",
             "exam_duration_minutes", "contrast_reaction", "radiation_dose_msv",
             "create_time", "update_time"],
            rows)
        print(f"  [RIS] exam_orders: {len(rows)} rows")

    def _generate_ris_reports(self, table: str, count: int, report_type: str, report_fields: list, extra_fields: list = None):
        """通用影像报告生成"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        findings_templates = [
            "未见明显异常。",
            "所见区域组织结构清晰，未见明显占位性病变。",
            "可见片状高密度影，边界欠清。",
            "可见结节状密度增高影，直径约{}cm。",
            "可见条索状高密度影，考虑陈旧性改变。",
            "可见斑片状磨玻璃影，建议随访复查。",
            "可见胸腔积液征象。",
            "可见肿大淋巴结影。",
            "可见骨质破坏征象。",
        ]
        impression_templates = [
            "未见明显异常。",
            "考虑炎症，建议治疗后复查。",
            "考虑良性病变，建议随访。",
            "不除外恶性可能，建议进一步检查。",
            "考虑占位性病变，建议增强扫描。",
            "符合{}表现。",
            "建议穿刺活检明确诊断。",
        ]

        for i in range(count):
            if self._should_link("ris_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            report_time = random_datetime("2023-01-01", "2024-12-31")
            reporter = random.choice(doctor_ids) if doctor_ids else None
            finding = random.choice(findings_templates)
            if "{}" in finding:
                finding = finding.format(round(random.uniform(0.3, 5.0), 1))
            impression = random.choice(impression_templates)
            if "{}" in impression:
                impression = impression.format(random.choice(["肺炎", "肺结核", "肿瘤", "结节"]))

            base_row = [
                f"{report_type.upper()}{str(i+1).zfill(7)}",
                f"EO{random.randint(1, 25000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                f"EX{random.randint(1000000, 9999999)}",
                maybe_null(f"DV{random.randint(1, 15)}", 0.25),
                maybe_null(random.choice(["头部", "胸部", "腹部", "盆腔"]), 0.15),
            ]

            if extra_fields:
                base_row.extend(extra_fields(i))

            if report_type == "ultrasound":
                base_row.extend([
                    maybe_null(finding, 0.12),
                    maybe_null(impression, 0.10),
                    maybe_null("测量数据", 0.30),
                    maybe_null(random.randint(2, 8), 0.20),
                    random.choice(["Y", "N"]),
                ])
            else:
                base_row.extend([
                    maybe_null(finding, 0.12),
                    maybe_null(impression, 0.10),
                ])

            base_row.extend([
                maybe_null("AI辅助诊断结果", 0.60),
                maybe_null(f"TPL{random.randint(100, 999)}", 0.30),
                maybe_null(f"STU{random.randint(1000000, 9999999)}", 0.40),
                maybe_null(random.randint(1, 8), 0.25),
                maybe_null(random.choice(["简单", "一般", "复杂"]), 0.30),
                random.choice(["草稿", "已提交", "已审核"]),
                reporter,
                maybe_null(generate_name(), 0.15),
                report_time,
                maybe_null(reporter, 0.30),
                maybe_null(generate_name(), 0.35),
                maybe_null(report_time + timedelta(hours=random.randint(1, 24)), 0.30),
                random.choice(["Y", "N"]),
                datetime.now()
            ])

            rows.append(tuple(base_row))

        all_fields = ["report_id", "order_id", "patient_id", "visit_id", "exam_no", "device_id", "exam_part"]
        if report_type == "xray":
            all_fields.extend(["film_count", "image_count", "technique"])
        elif report_type == "ct":
            all_fields.extend(["contrast_agent", "contrast_dose", "slice_thickness", "kv", "ma"])
        elif report_type == "mri":
            all_fields.extend(["sequence", "contrast_agent"])
        elif report_type == "ultrasound":
            all_fields.extend(["exam_type", "probe_frequency", "ultrasound_findings", "ultrasound_diagnosis",
                              "measurements", "images_count", "video_flag"])
        if report_type != "ultrasound":
            all_fields.extend(["findings", "impression"])
        all_fields.extend(["ai_findings", "template_id", "comparison_study_uid", "key_image_count",
                           "report_complexity", "report_status", "reporter_id", "reporter_name",
                           "report_time", "auditor_id", "auditor_name", "audit_time", "critical_value", "create_time"])

        self._batch_insert(table, all_fields, rows)
        print(f"  [RIS] {table}: {len(rows)} rows")

    def generate_xray_reports(self, count: int = 10000):
        """生成普放报告"""
        self._generate_ris_reports("xray_reports", count, "xray",
            [], lambda i: [maybe_null(random.randint(1, 4), 0.15), maybe_null(random.randint(1, 8), 0.15), maybe_null("常规摄影", 0.20)])

    def generate_ct_reports(self, count: int = 8000):
        """生成CT报告"""
        self._generate_ris_reports("ct_reports", count, "ct",
            [], lambda i: [maybe_null("碘海醇", 0.40), maybe_null(f"{random.randint(50, 100)}ml", 0.45),
                          maybe_null(f"{random.choice([1, 2, 5, 10])}mm", 0.20), maybe_null("120", 0.25), maybe_null("200", 0.25)])

    def generate_mri_reports(self, count: int = 4000):
        """生成MRI报告"""
        self._generate_ris_reports("mri_reports", count, "mri",
            [], lambda i: [maybe_null("T1WI/T2WI/FLAIR/DWI", 0.20), maybe_null("莫迪司", 0.50)])

    def generate_ultrasound_reports(self, count: int = 6000):
        """生成超声报告"""
        self._generate_ris_reports("ultrasound_reports", count, "ultrasound",
            [], lambda i: [random.choice(["B超", "彩超", "三维", "造影"]), maybe_null("5-12MHz", 0.20)])

    def generate_exam_images(self, count: int = 50000):
        """生成检查图像"""
        rows = []
        modalities = ["DR", "CT", "MRI", "US", "MG", "RF", "PET"]

        for i in range(count):
            if self._should_link("ris_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            order_id = f"EO{random.randint(1, 25000)}"
            modality = random.choice(modalities)
            image_count = random.randint(1, 500)

            rows.append((
                f"IMG{str(i+1).zfill(8)}", order_id, patient_id,
                f"IV{random.randint(1, 8000)}",
                maybe_null(f"1.2.840.{random.randint(100000, 999999)}.{random.randint(1, 9999)}", 0.10),
                maybe_null(f"1.2.840.{random.randint(100000, 999999)}.{random.randint(1, 9999)}", 0.10),
                modality,
                image_count,
                maybe_null(f"/storage/{modality.lower()}/{random.randint(2023, 2024)}/{random.randint(1, 12):02d}/{order_id}", 0.15),
                round(random.uniform(0.5, 2000.0), 2),
                random_datetime("2023-01-01", "2024-12-31"),
                datetime.now()
            ))

        self._batch_insert("exam_images",
            ["image_id", "order_id", "patient_id", "visit_id", "series_uid", "study_uid",
             "modality", "image_count", "storage_path", "file_size_mb", "upload_time", "create_time"],
            rows)
        print(f"  [RIS] exam_images: {len(rows)} rows")

    def generate_film_prints(self, count: int = 15000):
        """生成胶片打印"""
        rows = []
        staff_ids = [s[0] for s in self.staff]

        for i in range(count):
            if self._should_link("ris_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            order_id = f"EO{random.randint(1, 25000)}"
            print_time = random_datetime("2023-01-01", "2024-12-31")
            operator = random.choice(staff_ids) if staff_ids else None

            rows.append((
                f"FP{str(i+1).zfill(7)}", order_id, patient_id,
                print_time,
                random.choice(["8x10", "10x12", "11x14", "14x17"]),
                random.randint(1, 10),
                maybe_null(f"PR{random.randint(1, 20):02d}", 0.20),
                operator,
                round(random.uniform(5.0, 200.0), 2),
                datetime.now()
            ))

        self._batch_insert("film_prints",
            ["print_id", "order_id", "patient_id", "print_time", "film_size",
             "sheet_count", "printer_id", "operator_id", "cost", "create_time"],
            rows)
        print(f"  [RIS] film_prints: {len(rows)} rows")

    def generate_intervention_reports(self, count: int = 2000):
        """生成介入报告"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        procedures = [
            "冠状动脉造影", "经皮冠状动脉介入治疗", "射频消融术",
            "起搏器植入术", "支架植入术", "栓塞术", "引流术",
            "穿刺活检", "椎体成形术", "血管成形术",
        ]

        for i in range(count):
            if self._should_link("ris_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            order_id = f"EO{random.randint(1, 25000)}"
            procedure = random.choice(procedures)
            start_time = random_datetime("2023-01-01", "2024-12-31")
            duration = random.randint(30, 240)
            end_time = start_time + timedelta(minutes=duration)
            reporter = random.choice(doctor_ids) if doctor_ids else None

            rows.append((
                f"IR{str(i+1).zfill(7)}", order_id, patient_id,
                f"IV{random.randint(1, 8000)}",
                procedure,
                random.choice(["股动脉", "桡动脉", "颈静脉", "股静脉", "经皮"]),
                maybe_null("碘海醇", 0.30),
                maybe_null(random.randint(50, 300), 0.30),
                start_time,
                end_time,
                maybe_null("手术过程顺利...", 0.15),
                maybe_null("术后情况良好", 0.15),
                maybe_null(random.choice(["无", "出血", "血肿", "造影剂过敏", "血管痉挛"]), 0.50),
                random.choice(["草稿", "已提交", "已审核"]),
                reporter,
                maybe_null(start_time + timedelta(hours=random.randint(1, 12)), 0.25),
                datetime.now()
            ))

        self._batch_insert("intervention_reports",
            ["report_id", "order_id", "patient_id", "visit_id", "procedure_name",
             "access_route", "contrast_agent", "contrast_volume_ml", "procedure_start_time",
             "procedure_end_time", "findings", "impression", "complications",
             "report_status", "reporter_id", "report_time", "create_time"],
            rows)
        print(f"  [RIS] intervention_reports: {len(rows)} rows")

    def generate_nuclear_medicine_reports(self, count: int = 3000):
        """生成核医学报告（PET/ECT/SPECT）"""
        rows = []
        exam_types = ["PET", "ECT", "SPECT"]
        radiopharmaceuticals = ["18F-FDG", "99mTc-MDP", "99mTc-MIBI", "131I", "68Ga-PSMA"]
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("ris_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            order_id = f"EO{random.randint(1, 25000)}"
            exam_type = random.choice(exam_types)
            injected_time = random_datetime("2023-01-01", "2024-12-31")
            imaging_time = injected_time + timedelta(minutes=random.randint(30, 120))
            reporter = random.choice(doctor_ids) if doctor_ids else None

            rows.append((
                f"NM{str(i+1).zfill(7)}", order_id, patient_id,
                f"IV{random.randint(1, 8000)}",
                exam_type,
                maybe_null(random.choice(["全身", "头部", "胸部", "腹部", "骨骼"]), 0.10),
                random.choice(radiopharmaceuticals),
                round(random.uniform(100, 400), 2),
                injected_time,
                maybe_null(f"{random.uniform(1, 10):.1f}%", 0.30),
                imaging_time,
                maybe_null("显像剂分布均匀...", 0.15),
                maybe_null("未见明显异常放射性浓聚灶", 0.15),
                round(random.uniform(1.0, 15.0), 2) if exam_type == "PET" else None,
                maybe_null(random.choice(["与既往对比无明显变化", "病灶缩小", "新发病灶"]), 0.30),
                random.choice(["草稿", "已提交", "已审核"]),
                reporter,
                maybe_null(imaging_time + timedelta(hours=random.randint(1, 12)), 0.25),
                datetime.now()
            ))

        self._batch_insert("nuclear_medicine_reports",
            ["report_id", "order_id", "patient_id", "visit_id", "exam_type", "exam_part",
             "radiopharmaceutical", "injected_dose_mbq", "injected_time", "uptake_rate",
             "imaging_time", "findings", "impression", "suv_max", "comparison_result",
             "report_status", "reporter_id", "report_time", "create_time"],
            rows)
        print(f"  [RIS] nuclear_medicine_reports: {len(rows)} rows")
