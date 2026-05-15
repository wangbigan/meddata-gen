"""LIS 模块生成器：检验申请/标本/临检/生化/血液/微生物/药敏。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from meddata_gen.seed_data import (
    LAB_ITEMS,
    MICRO_ORGANISMS,
    ANTIBIOTICS,
    ICD10_DIAGNOSES,
    generate_name,
    random_datetime,
    maybe_null,
)


class LISMixin:
    """LIS（检验信息系统）数据生成。"""

    def _get_lab_items(self, category: str):
        """从 _dict_cache 获取指定类别的检验项目，回退到 LAB_ITEMS。"""
        cache = getattr(self, "_dict_cache", {})
        rows = cache.get("lab_items_dict", [])
        items = []
        for row in rows:
            if len(row) >= 7 and row[2] == category:
                items.append((row[0], row[1], row[4], row[5], row[6]))
        return items if items else LAB_ITEMS.get(category, [])

    def generate_lab_orders(self, count: int = 60000):
        """生成检验申请"""
        rows = []
        specimen_types = ["血清", "血浆", "全血", "尿液", "粪便", "脑脊液", "胸腹水", "痰液", "分泌物", "组织"]
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]

        for i in range(count):
            if self._should_link("lis_db") and self.inpatients:
                visit = random.choice(self.inpatients)
                patient_id = visit[1]
                visit_id = visit[0]
                visit_type = random.choice(["住院", "门诊", "急诊"])
            else:
                patient_id = f"P{random.randint(1, 999999)}"
                visit_id = f"IV{random.randint(1, 9999999)}"
                visit_type = random.choice(["住院", "门诊", "急诊", "体检"])

            order_time = random_datetime("2023-01-01", "2024-12-31")
            reporter = random.choice(doctor_ids) if doctor_ids else None

            collect_time = maybe_null(order_time + timedelta(minutes=random.randint(5, 60)), 0.20)
            receive_time = maybe_null(order_time + timedelta(minutes=random.randint(30, 180)), 0.30) if collect_time else None

            rows.append((
                f"LO{str(i+1).zfill(7)}", patient_id, visit_id, visit_type,
                f"LAB{random.randint(1000000, 9999999)}",
                order_time,
                random.choice([d["id"] for d in self.departments]),
                reporter,
                maybe_null(generate_name(), 0.15),
                random.choice(["普通", "紧急", "抢救"]),
                maybe_null(random.choice(ICD10_DIAGNOSES)[1], 0.20),
                maybe_null("请查血常规、生化全套", 0.30),
                random.choice(specimen_types),
                maybe_null("空腹采血", 0.40),
                random.choice(["已申请", "已采样", "已签收", "检验中", "已完成", "已取消"]),
                maybe_null(order_time + timedelta(hours=random.randint(1, 48)), 0.25),
                reporter,
                maybe_null(reporter, 0.35),
                maybe_null(f"INST{random.randint(1, 50)}", 0.20),
                maybe_null(f"BAR{random.randint(100000000, 999999999)}", 0.15),
                collect_time,
                maybe_null(f"ST{random.randint(1, 200)}", 0.25) if collect_time else None,
                receive_time,
                maybe_null(f"ST{random.randint(1, 200)}", 0.30) if receive_time else None,
                maybe_null(random.choice(["合格", "溶血", "脂血", "凝块"]), 0.20),
                datetime.now(), None
            ))

        self._batch_insert("lab_orders",
            ["order_id", "patient_id", "visit_id", "visit_type", "order_no",
             "order_time", "order_dept_id", "order_doctor_id", "order_doctor_name",
             "priority", "diagnosis", "clinical_note", "specimen_type",
             "specimen_requirements", "order_status", "report_time",
             "reporter_id", "verifier_id", "instrument_code", "barcode",
             "collect_time", "collect_user_id", "receive_time", "receive_user_id",
             "specimen_quality", "create_time", "update_time"],
            rows)
        print(f"  [LIS] lab_orders: {len(rows)} rows")

    def generate_specimens(self, count: int = 58000):
        """生成标本信息"""
        rows = []

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            collect_time = random_datetime("2023-01-01", "2024-12-31")
            receive_time = collect_time + timedelta(minutes=random.randint(5, 120))

            rows.append((
                f"SP{str(i+1).zfill(7)}",
                f"LO{random.randint(1, 60000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                f"BAR{random.randint(100000000, 999999999)}",
                random.choice(["血清", "血浆", "全血", "尿液", "粪便", "脑脊液", "胸腹水", "痰液"]),
                maybe_null(random.choice(["促凝管", "EDTA管", "肝素管", "枸橼酸钠管", "无菌管"]), 0.15),
                collect_time,
                maybe_null(f"ST{random.randint(1, 200)}", 0.20),
                random.choice(["病房", "门诊", "急诊", "ICU"]),
                receive_time,
                maybe_null(f"ST{random.randint(1, 200)}", 0.25),
                random.choice(["合格", "合格", "合格", "不合格", "溶血", "脂血", "凝块"]),
                maybe_null("标本量不足", 0.70),
                maybe_null(f"{random.randint(1, 10)}ml", 0.15),
                maybe_null(random.choice(["真空采血管", "尿管", "便盒", "无菌杯"]), 0.20),
                maybe_null("常温", 0.30),
                maybe_null(f"{random.randint(1, 50)}床", 0.40),
                datetime.now()
            ))

        self._batch_insert("specimens",
            ["specimen_id", "order_id", "patient_id", "visit_id", "barcode",
             "specimen_type", "specimen_sub_type", "collect_time", "collector_id",
             "collect_location", "receive_time", "receiver_id", "receive_status",
             "reject_reason", "volume", "container", "transport_temp", "bed_no", "create_time"],
            rows)
        print(f"  [LIS] specimens: {len(rows)} rows")

    def _generate_lab_results(self, table: str, count: int, items: list, result_type: str):
        """通用检验结果生成"""
        rows = []

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            item = random.choice(items)
            test_time = random_datetime("2023-01-01", "2024-12-31")

            # 生成结果值
            try:
                ref_low = float(item[3]) if item[3] else None
                ref_high = float(item[4]) if item[4] else None
            except:
                ref_low, ref_high = None, None

            if ref_low is not None and ref_high is not None:
                # 90%在正常范围内，10%异常
                if random.random() < 0.9:
                    val = random.uniform(ref_low, ref_high)
                else:
                    # 异常值
                    if random.random() < 0.5:
                        val = ref_low * random.uniform(0.3, 0.95)
                    else:
                        val = ref_high * random.uniform(1.05, 3.0)
                flag = "N" if ref_low <= val <= ref_high else ("H" if val > ref_high else "L")
            else:
                val = random.uniform(0, 100)
                flag = "N"

            rows.append((
                f"LR{result_type}{str(i+1).zfill(8)}",
                f"LO{random.randint(1, 60000)}",
                f"SP{random.randint(1, 58000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                item[0], item[1],
                maybe_null(item[0], 0.30),
                f"{val:.2f}",
                round(val, 4),
                item[2],
                f"{item[3]}-{item[4]}" if item[3] and item[4] else None,
                ref_low, ref_high,
                flag,
                maybe_null(random.choice(["比色法", "酶法", "免疫比浊", "电极法", "流式细胞"]), 0.25),
                maybe_null(f"INST{random.randint(1, 50)}", 0.20),
                test_time,
                maybe_null(test_time + timedelta(hours=random.randint(1, 24)), 0.15),
                random.randint(1, 20) if random.random() > 0.9 else 1,
                random.choice(["Y", "N"]),
                maybe_null(f"CH{random.randint(1, 20)}", 0.40),
                maybe_null(f"LOT{random.randint(1000, 9999)}", 0.35),
                datetime.now()
            ))

        self._batch_insert(table,
            ["result_id", "order_id", "specimen_id", "patient_id", "visit_id",
             "item_code", "item_name", "item_loinc", "result_value", "result_num",
             "unit", "reference_range", "ref_low", "ref_high", "abnormal_flag",
             "test_method", "instrument_code", "test_time", "report_time",
             "dilution_factor", "delta_check_flag", "instrument_channel",
             "reagent_lot_no", "create_time"],
            rows)
        print(f"  [LIS] {table}: {len(rows)} rows")

    def generate_routine_results(self, count: int = 200000):
        """生成临检结果"""
        self._generate_lab_results("routine_results", count, self._get_lab_items("routine"), "RT")

    def generate_biochem_results(self, count: int = 150000):
        """生出生化结果"""
        self._generate_lab_results("biochem_results", count, self._get_lab_items("biochem"), "BC")

    def generate_blood_results(self, count: int = 80000):
        """生成血液结果"""
        self._generate_lab_results("blood_results", count, self._get_lab_items("blood"), "BL")

    def generate_microbiology(self, count: int = 12000):
        """生成微生物结果"""
        rows = []

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            org = self._sample_dict("organism_dict")
            if org is None:
                org = random.choice(MICRO_ORGANISMS) + (None, None)
            test_time = random_datetime("2023-01-01", "2024-12-31")

            rows.append((
                f"MB{str(i+1).zfill(6)}",
                f"LO{random.randint(1, 60000)}",
                f"SP{random.randint(1, 58000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                random.randint(1, 10),
                f"CUL{random.randint(10000, 99999)}",
                random.choice(["痰", "血", "尿", "粪便", "脓液", "脑脊液", "胸腹水", "分泌物"]),
                maybe_null("肺部", 0.30),
                maybe_null(org[3] if len(org) > 3 and org[3] else "革兰阴性杆菌", 0.15),
                maybe_null("培养出细菌", 0.10),
                org[0], org[1],
                maybe_null(f"{random.randint(10, 10000)} CFU/ml", 0.40),
                random.randint(1, 7),
                random.randint(1, 5),
                maybe_null(f"ST{random.randint(1, 200)}", 0.25),
                test_time,
                maybe_null(test_time + timedelta(days=random.randint(1, 7)), 0.20),
                datetime.now()
            ))

        self._batch_insert("microbiology",
            ["micro_id", "order_id", "specimen_id", "patient_id", "visit_id",
             "test_seq", "culture_no", "specimen_type", "collect_site", "gram_stain",
             "culture_result", "organism_code", "organism_name", "colony_count",
             "incubation_days", "isolate_no", "technician_id", "test_time",
             "report_time", "create_time"],
            rows)
        print(f"  [LIS] microbiology: {len(rows)} rows")

    def generate_antibiotic_sensitivity(self, count: int = 8000):
        """生成药敏试验"""
        rows = []

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            ab = self._sample_dict("antibiotic_dict")
            if ab is None:
                ab = random.choice(ANTIBIOTICS) + (None,)
            org_name = self._sample_dict("organism_dict")
            if org_name is None:
                org_name = random.choice(MICRO_ORGANISMS)
            test_time = random_datetime("2023-01-01", "2024-12-31")

            rows.append((
                f"AS{str(i+1).zfill(6)}",
                f"MB{random.randint(1, 12000)}",
                f"LO{random.randint(1, 60000)}",
                patient_id,
                org_name[1] if org_name else "大肠埃希菌",
                ab[0], ab[1],
                maybe_null(f"{random.uniform(0.01, 64):.2f}", 0.20),
                maybe_null(random.randint(6, 40), 0.25),
                random.choice(["S", "I", "R", "S", "S", "I", "R"]),
                random.choice(["纸片扩散法", "微量肉汤稀释", "E-test"]),
                random.choice(["CLSI", "EUCAST"]),
                maybe_null(f"INST{random.randint(1, 50)}", 0.30),
                test_time,
                maybe_null(test_time + timedelta(days=random.randint(1, 3)), 0.25),
                datetime.now()
            ))

        self._batch_insert("antibiotic_sensitivity",
            ["sensitivity_id", "micro_id", "order_id", "patient_id", "organism_name",
             "antibiotic_code", "antibiotic_name", "mic", "kb_zone", "result",
             "method", "standard", "instrument_code", "test_time", "report_time", "create_time"],
            rows)
        print(f"  [LIS] antibiotic_sensitivity: {len(rows)} rows")

    def generate_lab_report_master(self, count: int = 60000):
        """生成检验报告主表"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        specimen_types = ["血清", "血浆", "全血", "尿液", "粪便", "脑脊液", "胸腹水", "痰液", "分泌物", "组织"]

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            report_time = random_datetime("2023-01-01", "2024-12-31")
            reporter = random.choice(doctor_ids) if doctor_ids else None
            is_critical = random.choice(["Y", "N"])

            rows.append((
                f"RM{str(i+1).zfill(7)}",
                f"LO{random.randint(1, 60000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                f"RPT{random.randint(1000000, 9999999)}",
                report_time,
                maybe_null(report_time + timedelta(minutes=random.randint(10, 120)), 0.30),
                reporter,
                maybe_null(reporter, 0.35),
                random.choice(["草稿", "已提交", "已审核", "已发布"]),
                is_critical,
                "Y" if is_critical == "Y" and random.random() > 0.3 else "N",
                random.choice(specimen_types),
                random.choice(["合格", "合格", "合格", "溶血", "脂血", "凝块"]),
                maybe_null(f"INST{random.randint(1, 50)}", 0.20),
                datetime.now(), None
            ))

        self._batch_insert("lab_report_master",
            ["report_id", "order_id", "patient_id", "visit_id", "report_no",
             "report_time", "verify_time", "reporter_id", "verifier_id",
             "report_status", "critical_value_flag", "critical_value_handled",
             "specimen_type", "specimen_status", "instrument_code",
             "create_time", "update_time"],
            rows)
        print(f"  [LIS] lab_report_master: {len(rows)} rows")

    def generate_critical_values(self, count: int = 3000):
        """生成危急值处理记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        cv_items = ["钾", "钠", "血糖", "血气pH", "血气PO2", "血气PCO2", "血红蛋白", "血小板", "白细胞", "钙"]

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            cv_time = random_datetime("2023-01-01", "2024-12-31")
            notified_doctor = random.choice(doctor_ids) if doctor_ids else None
            notification_time = maybe_null(cv_time + timedelta(minutes=random.randint(1, 30)), 0.15)
            confirmation_time = maybe_null(notification_time + timedelta(minutes=random.randint(5, 60)), 0.25) if notification_time else None
            handler = random.choice(doctor_ids) if doctor_ids and confirmation_time else None

            rows.append((
                f"CV{str(i+1).zfill(6)}",
                f"LO{random.randint(1, 60000)}",
                f"RM{random.randint(1, 60000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                random.choice(cv_items),
                f"{random.uniform(0.5, 15.0):.2f}",
                maybe_null(f"{random.uniform(3.5, 5.5):.1f}-{random.uniform(3.5, 5.5):.1f}", 0.20),
                cv_time,
                notified_doctor,
                notification_time,
                confirmation_time,
                handler,
                maybe_null(random.choice(["立即处理", "复查确认", "调整用药", "转入ICU"]), 0.20),
                random.choice(["已通知", "已确认", "已处理", "已关闭"]),
                datetime.now()
            ))

        self._batch_insert("critical_values",
            ["cv_id", "order_id", "report_id", "patient_id", "visit_id",
             "item_name", "result_value", "reference_range", "cv_time",
             "notified_doctor_id", "notification_time", "confirmation_time",
             "handler_id", "handle_action", "status", "create_time"],
            rows)
        print(f"  [LIS] critical_values: {len(rows)} rows")

    def generate_immunoassay_results(self, count: int = 50000):
        """生成免疫组化/肿瘤标志物结果"""
        rows = []
        immuno_items = [
            ("AFP", "甲胎蛋白", "ng/ml", "0", "7"),
            ("CEA", "癌胚抗原", "ng/ml", "0", "5"),
            ("CA125", "糖类抗原125", "U/ml", "0", "35"),
            ("CA199", "糖类抗原19-9", "U/ml", "0", "37"),
            ("CA153", "糖类抗原15-3", "U/ml", "0", "25"),
            ("CA724", "糖类抗原72-4", "U/ml", "0", "6.9"),
            ("PSA", "前列腺特异抗原", "ng/ml", "0", "4"),
            ("NSE", "神经元特异性烯醇化酶", "ng/ml", "0", "16.3"),
            ("CYFRA211", "细胞角蛋白19片段", "ng/ml", "0", "3.3"),
            ("SCC", "鳞状细胞癌抗原", "ng/ml", "0", "1.5"),
        ]

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            item = random.choice(immuno_items)
            test_time = random_datetime("2023-01-01", "2024-12-31")

            try:
                ref_low = float(item[3]) if item[3] else None
                ref_high = float(item[4]) if item[4] else None
            except:
                ref_low, ref_high = None, None

            if ref_low is not None and ref_high is not None:
                if random.random() < 0.85:
                    val = random.uniform(ref_low, ref_high)
                else:
                    val = ref_high * random.uniform(1.05, 5.0)
                flag = "N" if val <= ref_high else "H"
            else:
                val = random.uniform(0, 100)
                flag = "N"

            rows.append((
                f"IM{str(i+1).zfill(7)}",
                f"LO{random.randint(1, 60000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                item[0], item[1],
                f"{val:.2f}",
                round(val, 4),
                item[2],
                f"{item[3]}-{item[4]}" if item[3] and item[4] else None,
                flag,
                random.choice(["化学发光", "电化学发光", "ELISA"]),
                maybe_null(f"INST{random.randint(1, 50)}", 0.20),
                test_time,
                maybe_null(test_time + timedelta(hours=random.randint(1, 24)), 0.15),
                datetime.now()
            ))

        self._batch_insert("immunoassay_results",
            ["result_id", "order_id", "patient_id", "visit_id", "item_code", "item_name",
             "result_value", "result_num", "unit", "reference_range", "abnormal_flag",
             "method", "instrument_code", "test_time", "report_time", "create_time"],
            rows)
        print(f"  [LIS] immunoassay_results: {len(rows)} rows")

    def generate_molecular_results(self, count: int = 10000):
        """生成分子诊断/基因检测/PCR结果"""
        rows = []
        molecular_items = [
            ("HPV-DNA", "HPV基因检测", "PCR"),
            ("HBV-DNA", "乙肝DNA定量", "PCR"),
            ("HCV-RNA", "丙肝RNA定量", "PCR"),
            ("COVID-19", "新型冠状病毒核酸", "PCR"),
            ("EGFR", "EGFR基因突变", "测序"),
            ("ALK", "ALK基因融合", "FISH"),
            ("BRAF", "BRAF基因突变", "测序"),
            ("KRAS", "KRAS基因突变", "测序"),
            ("BRCA1", "BRCA1基因突变", "测序"),
            ("BRCA2", "BRCA2基因突变", "测序"),
        ]

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            item = random.choice(molecular_items)
            test_time = random_datetime("2023-01-01", "2024-12-31")
            qualitative = random.choice(["阴性", "阴性", "阴性", "阳性", "可疑"])

            rows.append((
                f"ML{str(i+1).zfill(7)}",
                f"LO{random.randint(1, 60000)}",
                patient_id,
                f"IV{random.randint(1, 8000)}",
                item[0], item[1],
                f"{random.uniform(10, 10000000):.1f}" if qualitative == "阳性" else "未检出",
                qualitative,
                round(random.uniform(15.0, 40.0), 2) if qualitative == "阳性" else None,
                maybe_null(f"Exon{random.randint(1, 30)}", 0.30) if "基因" in item[1] else None,
                maybe_null(random.choice(["c.2573T>G", "c.1799T>A", "缺失"]), 0.40) if "基因" in item[1] else None,
                item[2],
                random.choice(["血清", "血浆", "全血", "组织", "痰液"]),
                maybe_null(test_time - timedelta(days=random.randint(1, 3)), 0.20),
                maybe_null(test_time + timedelta(hours=random.randint(1, 48)), 0.15),
                datetime.now()
            ))

        self._batch_insert("molecular_results",
            ["result_id", "order_id", "patient_id", "visit_id", "item_code", "item_name",
             "result_value", "qualitative_result", "ct_value", "gene_target", "mutation_info",
             "method", "specimen_type", "collect_time", "report_time", "create_time"],
            rows)
        print(f"  [LIS] molecular_results: {len(rows)} rows")

    def generate_qc_internal(self, count: int = 5000):
        """生成室内质控记录"""
        rows = []
        qc_items = [
            ("GLU", "葡萄糖"), ("UREA", "尿素"), ("CREA", "肌酐"),
            ("ALT", "谷丙转氨酶"), ("AST", "谷草转氨酶"), ("K", "钾"),
            ("Na", "钠"), ("Cl", "氯"), ("Ca", "钙"),
        ]

        for i in range(count):
            item = random.choice(qc_items)
            target = random.uniform(2.0, 10.0)
            sd = target * 0.02
            measured = random.gauss(target, sd)
            status = "在控"
            if abs(measured - target) > 3 * sd:
                status = "失控"
            elif abs(measured - target) > 2 * sd:
                status = "警告"

            rows.append((
                f"QC{str(i+1).zfill(6)}",
                item[0], item[1],
                f"LOT{random.randint(1000, 9999)}",
                random.choice(["L1", "L2", "L3"]),
                round(target, 4),
                round(sd, 4),
                round(abs(sd / target * 100), 2) if target != 0 else 0,
                round(measured, 4),
                random_date_between(datetime(2023, 1, 1), datetime(2024, 12, 31)),
                maybe_null(f"INST{random.randint(1, 50)}", 0.20),
                status,
                maybe_null(f"ST{random.randint(1, 200)}", 0.30),
                datetime.now()
            ))

        self._batch_insert("qc_internal",
            ["qc_id", "item_code", "item_name", "lot_no", "level", "target_value", "sd",
             "cv", "measured_value", "run_date", "instrument_code", "status", "operator_id", "create_time"],
            rows)
        print(f"  [LIS] qc_internal: {len(rows)} rows")
