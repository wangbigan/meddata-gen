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
                datetime.now(), None
            ))

        self._batch_insert("lab_orders",
            ["order_id", "patient_id", "visit_id", "visit_type", "order_no",
             "order_time", "order_dept_id", "order_doctor_id", "order_doctor_name",
             "priority", "diagnosis", "clinical_note", "specimen_type",
             "specimen_requirements", "order_status", "report_time",
             "reporter_id", "verifier_id", "instrument_code", "create_time", "update_time"],
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
                datetime.now()
            ))

        self._batch_insert(table,
            ["result_id", "order_id", "specimen_id", "patient_id", "visit_id",
             "item_code", "item_name", "item_loinc", "result_value", "result_num",
             "unit", "reference_range", "ref_low", "ref_high", "abnormal_flag",
             "test_method", "instrument_code", "test_time", "report_time", "create_time"],
            rows)
        print(f"  [LIS] {table}: {len(rows)} rows")

    def generate_routine_results(self, count: int = 200000):
        """生成临检结果"""
        self._generate_lab_results("routine_results", count, LAB_ITEMS["routine"], "RT")

    def generate_biochem_results(self, count: int = 150000):
        """生出生化结果"""
        self._generate_lab_results("biochem_results", count, LAB_ITEMS["biochem"], "BC")

    def generate_blood_results(self, count: int = 80000):
        """生成血液结果"""
        self._generate_lab_results("blood_results", count, LAB_ITEMS["blood"], "BL")

    def generate_microbiology(self, count: int = 12000):
        """生成微生物结果"""
        rows = []

        for i in range(count):
            if self._should_link("lis_db") and self.patients:
                patient = random.choice(self.patients)
                patient_id = patient[0]
            else:
                patient_id = f"P{random.randint(1, 999999)}"

            organism = random.choice(MICRO_ORGANISMS)
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
                maybe_null("革兰阴性杆菌", 0.15),
                maybe_null("培养出细菌", 0.10),
                organism[0], organism[1],
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

            antibiotic = random.choice(ANTIBIOTICS)
            test_time = random_datetime("2023-01-01", "2024-12-31")

            rows.append((
                f"AS{str(i+1).zfill(6)}",
                f"MB{random.randint(1, 12000)}",
                f"LO{random.randint(1, 60000)}",
                patient_id,
                random.choice([o[1] for o in MICRO_ORGANISMS]),
                antibiotic[0], antibiotic[1],
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
