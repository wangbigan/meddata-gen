"""HIS 模块生成器：科室/人员/药品/患者/住院/门诊/医嘱/收费/床位。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from meddata_gen.seed_data import (
    DEPARTMENTS,
    DOCTOR_TITLES,
    NURSE_TITLES,
    TECH_TITLES,
    PHARMACIST_TITLES,
    ADMIN_TITLES,
    DRUG_CATEGORIES,
    DRUG_NAMES,
    INSURANCE_TYPES,
    ETHNICITIES,
    ICD10_DIAGNOSES,
    generate_name,
    generate_id_card,
    generate_phone,
    generate_address,
    random_datetime,
    maybe_null,
    random_date_between,
)


class HISMixin:
    """HIS（医院信息系统）数据生成。"""

    def generate_departments(self):
        """生成科室字典"""
        rows = []
        for d in DEPARTMENTS:
            rows.append((
                d["id"], d["code"], d["name"], d["type"],
                None, d["ward"], d["outpatient"], d["inpatient"],
                None, None, None, "1",
                datetime.now(), None
            ))
        self._batch_insert("departments",
            ["dept_id", "dept_code", "dept_name", "dept_type", "parent_dept_id",
             "ward_flag", "outpatient_flag", "inpatient_flag", "director_id",
             "location", "phone", "status", "create_time", "update_time"],
            rows)
        self.departments = DEPARTMENTS
        print(f"  [HIS] departments: {len(rows)} rows")

    def generate_staff(self, count: int = 200):
        """生成人员字典"""
        rows = []
        dept_ids = [d["id"] for d in self.departments if d.get("ward") == "Y" or d.get("outpatient") == "Y"]
        clinical_depts = [d["id"] for d in self.departments if d.get("ward") == "Y"]

        job_type_weights = [("医生", 0.45), ("护士", 0.35), ("技师", 0.08), ("药师", 0.07), ("行政", 0.05)]

        for i in range(count):
            staff_id = f"ST{str(i+1).zfill(5)}"
            job_type = random.choices([j[0] for j in job_type_weights], weights=[j[1] for j in job_type_weights])[0]

            if job_type == "医生":
                title = random.choice(DOCTOR_TITLES)
                dept = random.choice(clinical_depts)
            elif job_type == "护士":
                title = random.choice(NURSE_TITLES)
                dept = random.choice(clinical_depts)
            elif job_type == "技师":
                title = random.choice(TECH_TITLES)
                dept = random.choice(dept_ids)
            elif job_type == "药师":
                title = random.choice(PHARMACIST_TITLES)
                dept = random.choice([d["id"] for d in self.departments if "药" in d["name"]] or dept_ids)
            else:
                title = random.choice(ADMIN_TITLES)
                dept = random.choice([d["id"] for d in self.departments if d["type"] == "行政科室"] or dept_ids)

            gender = random.choice(["M", "F"])
            birthday = random_date_between(
                datetime(1960, 1, 1),
                datetime(2000, 1, 1)
            )

            rows.append((
                staff_id, f"E{str(i+1).zfill(4)}", generate_name(),
                gender, birthday,
                generate_id_card(birthday, gender) if random.random() > 0.1 else None,
                maybe_null(generate_phone(), 0.15),
                maybe_null(f"staff{i+1}@hospital.cn", 0.3),
                dept, title, job_type,
                None, None,
                random_date_between(datetime(2005, 1, 1), datetime(2024, 1, 1)),
                f"Y{random.randint(100000, 999999)}",
                maybe_null(random.choice(["内科", "外科", "妇产科", "儿科", "全科"]), 0.40) if job_type == "医生" else None,
                maybe_null(random.choice(["本院", "分院A", "分院B"]), 0.50),
                maybe_null(f"SIG{random.randint(1000, 9999)}", 0.60),
                maybe_null(random.choice(["ROLE001", "ROLE002", "ROLE003", "ROLE004"]), 0.30),
                "1", datetime.now(), None
            ))

        self._batch_insert("staff",
            ["staff_id", "staff_code", "staff_name", "gender", "birthday", "id_card",
             "phone", "email", "dept_id", "title", "job_type", "specialty", "education",
             "entry_date", "license_no", "practice_scope", "practice_location",
             "signature_image", "role_code", "status", "create_time", "update_time"],
            rows)
        self.staff = rows
        print(f"  [HIS] staff: {len(rows)} rows")

    def generate_drugs(self, count: int = 500):
        """生成药品字典"""
        rows = []
        all_drugs = []
        for cat, subcats in DRUG_CATEGORIES:
            drugs_in_cat = DRUG_NAMES.get(cat, [])
            for name, spec, unit in drugs_in_cat:
                all_drugs.append((cat, cat, name, spec, unit))

        random.shuffle(all_drugs)
        selected = all_drugs[:min(count, len(all_drugs))]

        for i, (cat, subcat, name, spec, unit) in enumerate(selected):
            drug_id = f"DR{str(i+1).zfill(5)}"
            rows.append((
                drug_id,
                f"D{str(i+1).zfill(5)}",
                name,
                name.split("片")[0].split("胶囊")[0].split("注射液")[0] if "片" in name or "胶囊" in name or "注射液" in name else name,
                None,
                random.choice(["片剂", "胶囊", "注射剂", "口服液", "颗粒", "散剂"]),
                spec,
                unit,
                random.choice(["华北制药", "哈药集团", "石药集团", "恒瑞医药", "齐鲁制药", "扬子江药业", "白云山", "云南白药", "同仁堂", "三九药业"]),
                f"国药准字H{random.randint(10000000, 99999999)}",
                "西药" if cat != "中成药" else "中成药",
                cat,
                None,
                "常温",
                "1",
                datetime.now()
            ))

        self._batch_insert("drugs",
            ["drug_id", "drug_code", "drug_name", "generic_name", "english_name", "dosage_form",
             "specification", "unit", "manufacturer", "approval_no", "drug_type", "category",
             "atc_code", "storage_condition", "status", "create_time"],
            rows)
        self.drugs = rows
        print(f"  [HIS] drugs: {len(rows)} rows")

    def generate_patients(self, count: int = 5000):
        """生成患者基本信息"""
        rows = []
        for i in range(count):
            patient_id = f"P{str(i+1).zfill(6)}"
            gender = random.choices(["M", "F", "U"], weights=[0.48, 0.51, 0.01])[0]

            # 年龄分布: 偏向中老年
            age_years = random.choices(
                range(0, 101),
                weights=[5]*5 + [8]*10 + [10]*15 + [12]*20 + [15]*20 + [12]*15 + [8]*10 + [5]*6
            )[0]
            birthday = (datetime(2024, 1, 1) - timedelta(days=age_years*365 + random.randint(0, 364))).date()

            rows.append((
                patient_id,
                f"MR{random.randint(100000, 999999)}",
                generate_name(),
                gender,
                birthday,
                age_years if not self._should_null("his_db", "normal") else None,
                maybe_null(generate_id_card(birthday, gender), 0.12) if gender != "U" else None,
                maybe_null(f"HC{random.randint(100000000, 999999999)}", 0.15),
                maybe_null(random.choice(INSURANCE_TYPES), 0.08),
                maybe_null(f"IN{random.randint(100000000, 999999999)}", 0.20),
                maybe_null("中国", 0.05),
                maybe_null(random.choice(ETHNICITIES), 0.10),
                maybe_null(random.choice(["A", "B", "AB", "O", "RH-"]), 0.15),
                maybe_null(random.choice(["已婚", "未婚", "离异", "丧偶"]), 0.12),
                maybe_null(random.choice(["工人", "农民", "职员", "教师", "退休", "个体", "学生", "无业"]), 0.18),
                maybe_null(generate_phone(), 0.10),
                maybe_null(generate_address(), 0.15),
                maybe_null(generate_name(), 0.25),
                maybe_null(generate_phone(), 0.30),
                maybe_null("无", 0.35),
                maybe_null("无特殊", 0.40),
                maybe_null("无特殊", 0.40),
                maybe_null(random.choice(["父亲", "母亲", "配偶", "子女", "兄弟", "姐妹"]), 0.30),
                maybe_null(round(random.uniform(150.0, 190.0), 1), 0.25),
                maybe_null(round(random.uniform(45.0, 100.0), 2), 0.25),
                maybe_null(f"C{random.randint(100000000, 999999999)}", 0.20),
                maybe_null(f"ST{random.randint(1, 200)}", 0.15),
                maybe_null(random_date_between(datetime(2010, 1, 1), datetime(2024, 1, 1)), 0.20),
                datetime.now(), None, "1"
            ))

        self._batch_insert("patients",
            ["patient_id", "medical_record_no", "patient_name", "gender", "birthday", "age",
             "id_card", "health_card_no", "insurance_type", "insurance_no", "nationality",
             "ethnicity", "blood_type", "marital_status", "occupation", "phone", "address",
             "emergency_contact", "emergency_phone", "allergy_history", "family_history",
             "past_history", "contact_relation", "height", "weight", "card_no",
             "register_user_id", "first_visit_date", "register_time", "update_time", "status"],
            rows)
        self.patients = rows
        print(f"  [HIS] patients: {len(rows)} rows")

    def generate_inpatient_visits(self, count: int = 8000):
        """生成住院记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        clinical_depts = [d["id"] for d in self.departments if d.get("ward") == "Y"]

        for i in range(count):
            patient = random.choice(self.patients)
            patient_id = patient[0]
            admission_time = random_datetime("2023-01-01", "2024-12-30")
            # 住院天数 1-30天，少数更长
            los = random.choices(
                range(1, 61),
                weights=[15]*3 + [20]*7 + [15]*10 + [10]*15 + [5]*20 + [3]*5
            )[0]
            discharge_time = admission_time + timedelta(days=los)

            admission_dept = random.choice(clinical_depts)
            attending = random.choice(doctor_ids) if doctor_ids else None

            status = random.choices(
                ["在院", "出院", "转科", "死亡"],
                weights=[2, 85, 8, 5]
            )[0]

            if status == "在院":
                discharge_time = None
            elif status == "死亡":
                discharge_status = "死亡"
            elif status == "转科":
                discharge_status = random.choice(["治愈", "好转", "转科"])
            else:
                discharge_status = random.choices(["治愈", "好转", "未愈", "其他"], weights=[30, 50, 15, 5])[0]

            total_cost = round(random.uniform(2000, 150000), 2)
            insurance_pay = round(total_cost * random.uniform(0.4, 0.8), 2)

            rows.append((
                f"IV{str(i+1).zfill(7)}", patient_id,
                patient[1] if not self._should_null("his_db") else None,
                maybe_null(random.choice(["急诊", "门诊", "转院", "其他"]), 0.08),
                admission_time,
                admission_dept,
                admission_dept,
                maybe_null(f"{random.randint(1, 30)}床", 0.05),
                maybe_null("待完善", 0.15),
                attending,
                maybe_null(attending, 0.20),
                maybe_null(attending, 0.30),
                discharge_time if status != "在院" else None,
                maybe_null(admission_dept, 0.10) if status != "在院" else None,
                maybe_null(admission_dept, 0.15) if status != "在院" else None,
                maybe_null("出院诊断待完善", 0.20) if status != "在院" else None,
                discharge_status if status != "在院" else None,
                los if status != "在院" else (datetime.now() - admission_time).days,
                total_cost,
                round(total_cost * 0.3, 2),
                round(total_cost * 0.1, 2),
                insurance_pay,
                round(total_cost - insurance_pay, 2),
                status,
                maybe_null(round(random.uniform(45.0, 100.0), 2), 0.30),
                maybe_null(round(random.uniform(150.0, 190.0), 1), 0.30),
                maybe_null("青霉素;头孢", 0.50),
                maybe_null(generate_name(), 0.40),
                maybe_null(generate_phone(), 0.45),
                random.choice(["Y", "N"]),
                random.randint(0, 5) if random.random() > 0.9 else 0,
                random.choice(["Y", "N"]),
                datetime.now(), None
            ))

        self._batch_insert("inpatient_visits",
            ["visit_id", "patient_id", "medical_record_no", "admission_type", "admission_time",
             "admission_dept_id", "admission_ward_id", "admission_bed_no", "admission_diagnosis",
             "attending_doctor_id", "resident_doctor_id", "chief_doctor_id", "discharge_time",
             "discharge_dept_id", "discharge_ward_id", "discharge_diagnosis", "discharge_status",
             "days", "total_cost", "pre_payment", "balance", "insurance_pay", "self_pay",
             "status", "admission_weight", "admission_height", "allergy_drugs",
             "companion_name", "companion_phone", "surgery_flag", "rescue_count",
             "critical_flag", "create_time", "update_time"],
            rows)
        self.inpatients = rows
        print(f"  [HIS] inpatient_visits: {len(rows)} rows")

    def generate_outpatient_visits(self, count: int = 20000):
        """生成门诊记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        outpatient_depts = [d["id"] for d in self.departments if d.get("outpatient") == "Y"]

        for i in range(count):
            patient = random.choice(self.patients)
            patient_id = patient[0]
            visit_date = random_date_between(datetime(2023, 1, 1), datetime(2024, 12, 31))
            visit_time = datetime.combine(visit_date, datetime.min.time()) + timedelta(
                hours=random.randint(7, 21), minutes=random.randint(0, 59)
            )

            dept = random.choice(outpatient_depts)
            doctor = random.choice(doctor_ids) if doctor_ids else None

            diagnosis = random.choice(ICD10_DIAGNOSES)
            fee = round(random.uniform(20, 2000), 2)

            rows.append((
                f"OV{str(i+1).zfill(7)}", patient_id,
                visit_date,
                visit_time,
                dept, doctor,
                random.choice(["普通", "专家", "急诊", "复诊"]),
                maybe_null("发热伴咳嗽3天", 0.15),
                maybe_null("患者3天前受凉后出现发热...", 0.20),
                maybe_null(diagnosis[1], 0.10),
                maybe_null(diagnosis[0], 0.25),
                maybe_null("对症处理，随诊", 0.18),
                fee,
                random.choice(["已结束", "已结束", "已结束", "已取消"]),
                datetime.now()
            ))

        self._batch_insert("outpatient_visits",
            ["visit_id", "patient_id", "visit_date", "visit_time", "dept_id", "doctor_id",
             "visit_type", "chief_complaint", "present_illness", "diagnosis", "diagnosis_icd",
             "treatment", "fee_amount", "status", "create_time"],
            rows)
        self.outpatients = rows
        print(f"  [HIS] outpatient_visits: {len(rows)} rows")

    def generate_orders(self, count: int = 120000):
        """生成医嘱"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        nurse_ids = [s[0] for s in self.staff if s[10] == "护士"]

        all_visits = self.inpatients + self.outpatients
        for i in range(count):
            visit = random.choice(all_visits)
            visit_id = visit[0]
            patient_id = visit[1]

            start_time = random_datetime("2023-01-01", "2024-12-31")
            order_type = random.choice(["长期", "临时", "备用"])
            category = random.choice(["药品", "检验", "检查", "手术", "护理", "膳食"])
            stop_time = start_time + timedelta(days=random.randint(1, 14)) if order_type == "长期" else None

            rows.append((
                f"OR{str(i+1).zfill(8)}", visit_id, patient_id,
                order_type, category,
                start_time,
                stop_time if not self._should_null("his_db") else None,
                random.choice(doctor_ids) if doctor_ids else None,
                random.choice(nurse_ids) if nurse_ids and random.random() > 0.3 else None,
                random.choice([d["id"] for d in self.departments]),
                random.choice(["普通", "紧急", "抢救"]) if category != "膳食" else "普通",
                random.choice(["新开", "审核", "执行", "停止", "作废"]),
                maybe_null(start_time + timedelta(minutes=random.randint(5, 60)), 0.25),
                random.choice(nurse_ids) if nurse_ids else None,
                datetime.now(), None
            ))

        self._batch_insert("orders",
            ["order_id", "visit_id", "patient_id", "order_type", "order_category",
             "start_time", "stop_time", "doctor_id", "nurse_id", "dept_id",
             "priority", "order_status", "verify_time", "verify_nurse_id", "create_time", "update_time"],
            rows)
        print(f"  [HIS] orders: {len(rows)} rows")

    def generate_fee_items(self, count: int = 300000):
        """生成收费明细"""
        rows = []
        fee_types = ["药品费", "检查费", "检验费", "治疗费", "手术费", "床位费", "护理费", "材料费", "诊查费", "其他"]

        for i in range(count):
            visit = random.choice(self.inpatients + self.outpatients)
            visit_id = visit[0]
            patient_id = visit[1]
            fee_type = random.choice(fee_types)

            qty = random.randint(1, 20) if fee_type in ["药品费", "材料费"] else 1
            unit_price = round(random.uniform(1, 5000), 4)

            rows.append((
                f"FE{str(i+1).zfill(8)}", visit_id, patient_id,
                fee_type,
                f"ITEM{random.randint(1000, 99999)}",
                f"{fee_type}项目{random.randint(1, 999)}",
                maybe_null("常规", 0.30),
                maybe_null("次", 0.20) if fee_type != "药品费" else "盒",
                qty,
                unit_price,
                round(qty * unit_price, 2),
                random.choice([d["id"] for d in self.departments]),
                random.choice([s[0] for s in self.staff]),
                random_datetime("2023-01-01", "2024-12-31"),
                random.choice(["已收费", "已收费", "已收费", "已退费", "记账"]),
                maybe_null(f"INV{random.randint(1000000, 9999999)}", 0.15),
                datetime.now()
            ))

        self._batch_insert("fee_items",
            ["fee_id", "visit_id", "patient_id", "fee_type", "item_code", "item_name",
             "specification", "unit", "quantity", "unit_price", "total_amount",
             "dept_id", "doctor_id", "fee_time", "pay_status", "invoice_no", "create_time"],
            rows)
        print(f"  [HIS] fee_items: {len(rows)} rows")

    def generate_beds(self):
        """生成床位信息"""
        rows = []
        clinical_depts = [d for d in self.departments if d.get("ward") == "Y"]
        bed_types = ["普通床", "监护床", "抢救床", "隔离床"]
        for dept in clinical_depts:
            num_beds = random.randint(20, 80)
            for i in range(1, num_beds + 1):
                room_no = f"{random.randint(1, 20)}"
                rows.append((
                    f"BD{dept['id']}{str(i).zfill(3)}",
                    f"WD{dept['id']}",
                    room_no,
                    f"{room_no}-{i}",
                    random.choice(bed_types),
                    dept["id"],
                    random.choice(["空闲", "占用", "维修", "停用"]),
                    None,
                    None,
                    round(random.uniform(30.0, 500.0), 2),
                    datetime.now()
                ))
        self._batch_insert("beds",
            ["bed_id", "ward_id", "room_no", "bed_no", "bed_type", "dept_id",
             "status", "patient_id", "visit_id", "price", "create_time"],
            rows)
        print(f"  [HIS] beds: {len(rows)} rows")

    def generate_registrations(self, count: int = 30000):
        """生成挂号记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        outpatient_depts = [d["id"] for d in self.departments if d.get("outpatient") == "Y"]

        for i in range(count):
            patient = random.choice(self.patients)
            patient_id = patient[0]
            reg_time = random_datetime("2023-01-01", "2024-12-31")

            rows.append((
                f"RG{str(i+1).zfill(7)}",
                patient_id,
                f"OV{random.randint(1, 20000)}" if random.random() > 0.3 else None,
                reg_time,
                random.choice(["现场", "预约", "急诊", "转诊"]),
                random.choice(outpatient_depts) if outpatient_depts else None,
                random.choice(doctor_ids) if doctor_ids else None,
                random.choice(["普通", "专家", "特需", "急诊"]),
                random.randint(1, 200),
                random.choice(["候诊", "就诊中", "已就诊", "过号", "退号", "爽约"]),
                datetime.now()
            ))

        self._batch_insert("registrations",
            ["reg_id", "patient_id", "visit_id", "reg_time", "reg_type",
             "reg_dept_id", "reg_doctor_id", "fee_type", "sequence_no",
             "status", "create_time"],
            rows)
        print(f"  [HIS] registrations: {len(rows)} rows")

    def generate_transfer_records(self, count: int = 2000):
        """生成转科记录"""
        rows = []
        doctor_ids = [s[0] for s in self.staff if s[10] == "医生"]
        clinical_depts = [d["id"] for d in self.departments if d.get("ward") == "Y"]

        for i in range(count):
            visit = random.choice(self.inpatients)
            visit_id = visit[0]
            patient_id = visit[1]
            transfer_time = random_datetime("2023-01-01", "2024-12-31")

            from_dept = random.choice(clinical_depts) if clinical_depts else None
            to_dept = random.choice(clinical_depts) if clinical_depts else None

            rows.append((
                f"TR{str(i+1).zfill(7)}",
                visit_id,
                patient_id,
                from_dept,
                to_dept,
                transfer_time,
                maybe_null(random.choice(["病情需要", "专科治疗", "手术需要", "床位调整", "患者要求"]), 0.20),
                maybe_null(f"{random.randint(1, 30)}床", 0.10),
                random.choice(doctor_ids) if doctor_ids else None,
                datetime.now()
            ))

        self._batch_insert("transfer_records",
            ["transfer_id", "visit_id", "patient_id", "from_dept_id", "to_dept_id",
             "transfer_time", "transfer_reason", "bed_no", "doctor_id", "create_time"],
            rows)
        print(f"  [HIS] transfer_records: {len(rows)} rows")

    def generate_settlements(self, count: int = 15000):
        """生成结算主表"""
        rows = []
        staff_ids = [s[0] for s in self.staff]

        for i in range(count):
            visit = random.choice(self.inpatients + self.outpatients)
            visit_id = visit[0]
            patient_id = visit[1]
            settlement_time = random_datetime("2023-01-01", "2024-12-31")

            total_amount = round(random.uniform(50, 150000), 2)
            insurance_pay = round(total_amount * random.uniform(0.3, 0.8), 2)

            rows.append((
                f"ST{str(i+1).zfill(7)}",
                visit_id,
                patient_id,
                random.choice(["出院结算", "中途结算", "门诊结算", "急诊结算"]),
                settlement_time,
                total_amount,
                insurance_pay,
                round(total_amount - insurance_pay, 2),
                f"INV{random.randint(1000000, 9999999)}",
                random.choice(["已结算", "已结算", "已结算", "已作废", "已冲正"]),
                random.choice(staff_ids) if staff_ids else None,
                datetime.now()
            ))

        self._batch_insert("settlements",
            ["settlement_id", "visit_id", "patient_id", "settlement_type",
             "settlement_time", "total_amount", "insurance_pay", "self_pay",
             "invoice_no", "settlement_status", "cashier_id", "create_time"],
            rows)
        print(f"  [HIS] settlements: {len(rows)} rows")

    def generate_prepayments(self, count: int = 50000):
        """生成预交金记录"""
        rows = []
        staff_ids = [s[0] for s in self.staff]

        for i in range(count):
            visit = random.choice(self.inpatients)
            visit_id = visit[0]
            patient_id = visit[1]
            prepay_time = random_datetime("2023-01-01", "2024-12-31")
            amount = round(random.uniform(1000, 50000), 2)

            rows.append((
                f"PP{str(i+1).zfill(7)}",
                visit_id,
                patient_id,
                prepay_time,
                amount,
                random.choice(["现金", "银行卡", "微信", "支付宝", "医保卡"]),
                f"RC{random.randint(1000000, 9999999)}",
                round(amount + random.uniform(-5000, 20000), 2),
                random.choice(staff_ids) if staff_ids else None,
                datetime.now()
            ))

        self._batch_insert("prepayments",
            ["prepay_id", "visit_id", "patient_id", "prepay_time", "amount",
             "pay_method", "receipt_no", "balance", "operator_id", "create_time"],
            rows)
        print(f"  [HIS] prepayments: {len(rows)} rows")
