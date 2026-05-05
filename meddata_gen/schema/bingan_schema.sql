-- ============================================================
-- 病案数据库表结构
-- 参考: 今创/曼荼罗 主流病案系统数据结构
-- ============================================================

-- 病案首页
CREATE TABLE IF NOT EXISTS medical_records (
    record_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    medical_record_no VARCHAR(20) NOT NULL,
    admission_time TIMESTAMP,
    discharge_time TIMESTAMP,
    hospital_days INTEGER,
    admission_dept VARCHAR(100),
    discharge_dept VARCHAR(100),
    transfer_dept TEXT,                 -- 转科情况
    dept_count INTEGER DEFAULT 1,       -- 转科次数
    admission_type VARCHAR(20),         -- 急诊/门诊/其他医疗机构转入
    discharge_type VARCHAR(20),         -- 医嘱离院/医嘱转院/非医嘱离院/死亡/其他
    discharge_status VARCHAR(20),       -- 治愈/好转/未愈/死亡/其他
    -- 诊断信息
    principal_diagnosis TEXT,           -- 主要诊断
    principal_diagnosis_icd VARCHAR(20),
    principal_diagnosis_code VARCHAR(20),
    other_diagnoses TEXT,               -- 其他诊断
    external_cause TEXT,                -- 外部原因
    external_cause_icd VARCHAR(20),
    pathological_diagnosis TEXT,        -- 病理诊断
    pathological_code VARCHAR(20),
    -- 手术信息
    surgery_count INTEGER DEFAULT 0,
    -- 费用信息
    total_cost DECIMAL(12,2),
    self_pay DECIMAL(12,2),
    drug_cost DECIMAL(12,2),
    material_cost DECIMAL(12,2),
    exam_cost DECIMAL(12,2),
    lab_cost DECIMAL(12,2),
    surgery_cost DECIMAL(12,2),
    anesthesia_cost DECIMAL(12,2),
    nursing_cost DECIMAL(12,2),
    -- 患者信息补充
    age INTEGER,
    age_month INTEGER,                  -- 婴儿月龄
    weight DECIMAL(6,2),                -- 新生儿体重 g
    birth_weight DECIMAL(6,2),          -- 出生体重
    -- 其他
    drg_code VARCHAR(20),               -- DRG编码
    drg_name VARCHAR(200),
    mdc_code VARCHAR(10),               -- MDC编码
    quality_control VARCHAR(10),        -- 病历质控等级
    teaching_case CHAR(1),              -- 是否教学病例 Y/N
    research_case CHAR(1),              -- 是否科研病例 Y/N
    coding_doctor VARCHAR(50),          -- 编码员
    coding_time TIMESTAMP,
    archive_time TIMESTAMP,             -- 归档时间
    archive_status VARCHAR(10),         -- 未归档/已归档/借阅中
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE medical_records IS '病案首页：每次住院一份，是医保结算/DRG/质控的核心标准化文档';
COMMENT ON COLUMN medical_records.record_id IS '病案首页主键ID';
COMMENT ON COLUMN medical_records.patient_id IS '患者ID（关联 his_db.patients.patient_id）';
COMMENT ON COLUMN medical_records.visit_id IS '住院就诊ID（关联 his_db.inpatient_visits.visit_id）';
COMMENT ON COLUMN medical_records.medical_record_no IS '病历号';
COMMENT ON COLUMN medical_records.admission_time IS '入院时间';
COMMENT ON COLUMN medical_records.discharge_time IS '出院时间';
COMMENT ON COLUMN medical_records.hospital_days IS '住院天数';
COMMENT ON COLUMN medical_records.admission_dept IS '入院科室名称';
COMMENT ON COLUMN medical_records.discharge_dept IS '出院科室名称';
COMMENT ON COLUMN medical_records.transfer_dept IS '转科情况描述（多个科室名称的连接文本）';
COMMENT ON COLUMN medical_records.dept_count IS '转科次数（住院期间经过的科室总数）';
COMMENT ON COLUMN medical_records.admission_type IS '入院途径：急诊/门诊/其他医疗机构转入';
COMMENT ON COLUMN medical_records.discharge_type IS '离院方式：医嘱离院/医嘱转院/非医嘱离院/死亡/其他';
COMMENT ON COLUMN medical_records.discharge_status IS '出院情况：治愈/好转/未愈/死亡/其他';
COMMENT ON COLUMN medical_records.principal_diagnosis IS '主要诊断名称';
COMMENT ON COLUMN medical_records.principal_diagnosis_icd IS '主要诊断 ICD-10 编码';
COMMENT ON COLUMN medical_records.principal_diagnosis_code IS '主要诊断院内分类编码';
COMMENT ON COLUMN medical_records.other_diagnoses IS '其他诊断（合并症/并发症列表）';
COMMENT ON COLUMN medical_records.external_cause IS '损伤外部原因描述';
COMMENT ON COLUMN medical_records.external_cause_icd IS '损伤外部原因 ICD-10 编码';
COMMENT ON COLUMN medical_records.pathological_diagnosis IS '病理诊断';
COMMENT ON COLUMN medical_records.pathological_code IS '病理诊断编码';
COMMENT ON COLUMN medical_records.surgery_count IS '手术操作次数';
COMMENT ON COLUMN medical_records.total_cost IS '住院总费用（元）';
COMMENT ON COLUMN medical_records.self_pay IS '个人自付金额';
COMMENT ON COLUMN medical_records.drug_cost IS '药品总费用';
COMMENT ON COLUMN medical_records.material_cost IS '耗材总费用';
COMMENT ON COLUMN medical_records.exam_cost IS '检查总费用';
COMMENT ON COLUMN medical_records.lab_cost IS '检验总费用';
COMMENT ON COLUMN medical_records.surgery_cost IS '手术总费用';
COMMENT ON COLUMN medical_records.anesthesia_cost IS '麻醉总费用';
COMMENT ON COLUMN medical_records.nursing_cost IS '护理总费用';
COMMENT ON COLUMN medical_records.age IS '年龄（足岁）';
COMMENT ON COLUMN medical_records.age_month IS '婴儿月龄（不足1岁时填写）';
COMMENT ON COLUMN medical_records.weight IS '体重（kg / 新生儿用 g）';
COMMENT ON COLUMN medical_records.birth_weight IS '新生儿出生体重（g）';
COMMENT ON COLUMN medical_records.drg_code IS 'DRG分组编码';
COMMENT ON COLUMN medical_records.drg_name IS 'DRG分组名称';
COMMENT ON COLUMN medical_records.mdc_code IS 'MDC（主要诊断大类）编码';
COMMENT ON COLUMN medical_records.quality_control IS '病历质控等级：甲/乙/丙';
COMMENT ON COLUMN medical_records.teaching_case IS '是否教学病例：Y/N';
COMMENT ON COLUMN medical_records.research_case IS '是否科研病例：Y/N';
COMMENT ON COLUMN medical_records.coding_doctor IS '编码员姓名';
COMMENT ON COLUMN medical_records.coding_time IS '编码完成时间';
COMMENT ON COLUMN medical_records.archive_time IS '病案归档时间';
COMMENT ON COLUMN medical_records.archive_status IS '归档状态：未归档/已归档/借阅中';
COMMENT ON COLUMN medical_records.create_time IS '记录创建时间';
COMMENT ON COLUMN medical_records.update_time IS '记录更新时间';

-- 病案诊断明细
CREATE TABLE IF NOT EXISTS diagnoses (
    diagnosis_id VARCHAR(20) PRIMARY KEY,
    record_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    seq_no INTEGER NOT NULL,            -- 诊断顺序号
    diagnosis_type VARCHAR(20),         -- 主要诊断/其他诊断/并发症/院内感染
    diagnosis_name TEXT,
    diagnosis_icd VARCHAR(20),
    diagnosis_version VARCHAR(10),       -- ICD-9/ICD-10
    in_condition VARCHAR(10),           -- 入院病情: 有/临床未确定/情况不明/无
    discharge_status VARCHAR(20),       -- 出院情况
    doctor_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE diagnoses IS '病案诊断明细：一份病案可对应多条诊断（主要+其他+并发症+院内感染）';
COMMENT ON COLUMN diagnoses.diagnosis_id IS '诊断明细主键ID';
COMMENT ON COLUMN diagnoses.record_id IS '关联病案首页ID（关联 medical_records.record_id）';
COMMENT ON COLUMN diagnoses.patient_id IS '患者ID';
COMMENT ON COLUMN diagnoses.visit_id IS '住院就诊ID';
COMMENT ON COLUMN diagnoses.seq_no IS '诊断顺序号（1=主要诊断，依次递增）';
COMMENT ON COLUMN diagnoses.diagnosis_type IS '诊断类型：主要诊断/其他诊断/并发症/院内感染';
COMMENT ON COLUMN diagnoses.diagnosis_name IS '诊断名称';
COMMENT ON COLUMN diagnoses.diagnosis_icd IS '诊断 ICD 编码';
COMMENT ON COLUMN diagnoses.diagnosis_version IS '编码版本：ICD-9 / ICD-10';
COMMENT ON COLUMN diagnoses.in_condition IS '入院病情：有/临床未确定/情况不明/无';
COMMENT ON COLUMN diagnoses.discharge_status IS '该诊断的出院情况';
COMMENT ON COLUMN diagnoses.doctor_id IS '诊断医生ID';
COMMENT ON COLUMN diagnoses.create_time IS '记录创建时间';

-- 手术操作明细
CREATE TABLE IF NOT EXISTS surgeries (
    surgery_id VARCHAR(20) PRIMARY KEY,
    record_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    seq_no INTEGER NOT NULL,            -- 手术顺序号
    surgery_name VARCHAR(200),
    surgery_icd VARCHAR(20),            -- ICD-9-CM3 编码
    surgery_date DATE,
    surgery_level VARCHAR(10),          -- I级/II级/III级/IV级
    surgeon_name VARCHAR(50),
    assistant1_name VARCHAR(50),
    assistant2_name VARCHAR(50),
    anesthesia_type VARCHAR(30),
    anesthesia_doctor VARCHAR(50),
    incision_healing VARCHAR(10),       -- 甲/乙/丙
    anesthesia_level VARCHAR(10),       -- ASA分级
    is_emergency CHAR(1),               -- 是否急诊手术
    is_sterile CHAR(1),                 -- 是否无菌手术
    is_microscope CHAR(1),              -- 是否显微手术
    is_reoperation CHAR(1),             -- 是否二次手术
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE surgeries IS '手术操作明细（病案）：病案首页归口管理的手术操作记录';
COMMENT ON COLUMN surgeries.surgery_id IS '手术操作主键ID';
COMMENT ON COLUMN surgeries.record_id IS '关联病案首页ID';
COMMENT ON COLUMN surgeries.patient_id IS '患者ID';
COMMENT ON COLUMN surgeries.visit_id IS '住院就诊ID';
COMMENT ON COLUMN surgeries.seq_no IS '手术顺序号（同一次住院多次手术的顺序）';
COMMENT ON COLUMN surgeries.surgery_name IS '手术/操作名称';
COMMENT ON COLUMN surgeries.surgery_icd IS 'ICD-9-CM3 手术操作编码';
COMMENT ON COLUMN surgeries.surgery_date IS '手术日期';
COMMENT ON COLUMN surgeries.surgery_level IS '手术等级：I级(微小)/II级(中等)/III级(较大)/IV级(重大)';
COMMENT ON COLUMN surgeries.surgeon_name IS '主刀医生姓名';
COMMENT ON COLUMN surgeries.assistant1_name IS '一助姓名';
COMMENT ON COLUMN surgeries.assistant2_name IS '二助姓名';
COMMENT ON COLUMN surgeries.anesthesia_type IS '麻醉方式';
COMMENT ON COLUMN surgeries.anesthesia_doctor IS '麻醉医生姓名';
COMMENT ON COLUMN surgeries.incision_healing IS '切口愈合等级：甲(良好)/乙(欠佳)/丙(感染)';
COMMENT ON COLUMN surgeries.anesthesia_level IS '麻醉ASA分级：I~V级（评估患者麻醉风险）';
COMMENT ON COLUMN surgeries.is_emergency IS '是否急诊手术：Y/N';
COMMENT ON COLUMN surgeries.is_sterile IS '是否无菌手术：Y/N';
COMMENT ON COLUMN surgeries.is_microscope IS '是否显微手术：Y/N';
COMMENT ON COLUMN surgeries.is_reoperation IS '是否二次手术：Y/N';
COMMENT ON COLUMN surgeries.create_time IS '记录创建时间';

-- 肿瘤登记
CREATE TABLE IF NOT EXISTS tumor_registry (
    tumor_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    medical_record_no VARCHAR(20),
    report_no VARCHAR(20),              -- 报告编号
    tumor_site VARCHAR(100),            -- 肿瘤部位
    tumor_code VARCHAR(20),             -- ICD-O编码
    morphology VARCHAR(50),             -- 形态学编码
    behavior VARCHAR(20),               -- 行为学
    grade VARCHAR(20),                  -- 分化程度
    t_stage VARCHAR(10),                -- T分期
    n_stage VARCHAR(10),                -- N分期
    m_stage VARCHAR(10),                -- M分期
    tnm_stage VARCHAR(20),              -- TNM总分期
    clinical_stage VARCHAR(20),         -- 临床分期
    pathological_stage VARCHAR(20),     -- 病理分期
    diagnosis_basis VARCHAR(50),        -- 诊断依据
    first_diagnosis_date DATE,          -- 首次诊断日期
    report_date DATE,                   -- 报告日期
    reporter VARCHAR(50),
    hospital_code VARCHAR(20),          -- 上报医院编码
    follow_up_status VARCHAR(20),       -- 随访状态
    survival_status VARCHAR(20),        -- 生存状态
    survival_months INTEGER,            -- 生存月数
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tumor_registry IS '肿瘤登记：恶性肿瘤患者登记上报数据，对接肿瘤登记报告系统';
COMMENT ON COLUMN tumor_registry.tumor_id IS '肿瘤登记主键ID';
COMMENT ON COLUMN tumor_registry.patient_id IS '患者ID';
COMMENT ON COLUMN tumor_registry.visit_id IS '住院/门诊就诊ID';
COMMENT ON COLUMN tumor_registry.medical_record_no IS '病历号';
COMMENT ON COLUMN tumor_registry.report_no IS '肿瘤报告编号';
COMMENT ON COLUMN tumor_registry.tumor_site IS '肿瘤原发部位（如肺、肝、乳腺等）';
COMMENT ON COLUMN tumor_registry.tumor_code IS '肿瘤 ICD-O 编码';
COMMENT ON COLUMN tumor_registry.morphology IS '形态学编码';
COMMENT ON COLUMN tumor_registry.behavior IS '行为学：良性/原位/恶性 等';
COMMENT ON COLUMN tumor_registry.grade IS '分化程度：高/中/低分化';
COMMENT ON COLUMN tumor_registry.t_stage IS 'T分期（原发肿瘤大小/侵犯范围）';
COMMENT ON COLUMN tumor_registry.n_stage IS 'N分期（区域淋巴结情况）';
COMMENT ON COLUMN tumor_registry.m_stage IS 'M分期（远处转移情况）';
COMMENT ON COLUMN tumor_registry.tnm_stage IS 'TNM 总分期（如 IIIA）';
COMMENT ON COLUMN tumor_registry.clinical_stage IS '临床分期';
COMMENT ON COLUMN tumor_registry.pathological_stage IS '病理分期';
COMMENT ON COLUMN tumor_registry.diagnosis_basis IS '诊断依据：临床/影像/病理 等';
COMMENT ON COLUMN tumor_registry.first_diagnosis_date IS '首次诊断日期';
COMMENT ON COLUMN tumor_registry.report_date IS '上报日期';
COMMENT ON COLUMN tumor_registry.reporter IS '报告医生姓名';
COMMENT ON COLUMN tumor_registry.hospital_code IS '上报医院编码';
COMMENT ON COLUMN tumor_registry.follow_up_status IS '随访状态：失访/随访中/已结束';
COMMENT ON COLUMN tumor_registry.survival_status IS '生存状态：存活/死亡/失访';
COMMENT ON COLUMN tumor_registry.survival_months IS '生存时间（月）';
COMMENT ON COLUMN tumor_registry.create_time IS '记录创建时间';

CREATE INDEX idx_mr_patient_id ON medical_records(patient_id);
CREATE INDEX idx_mr_visit_id ON medical_records(visit_id);
CREATE INDEX idx_mr_record_no ON medical_records(medical_record_no);
CREATE INDEX idx_diagnosis_record_id ON diagnoses(record_id);
CREATE INDEX idx_diagnosis_icd ON diagnoses(diagnosis_icd);
CREATE INDEX idx_surgery_record_id ON surgeries(record_id);
CREATE INDEX idx_tumor_patient_id ON tumor_registry(patient_id);
