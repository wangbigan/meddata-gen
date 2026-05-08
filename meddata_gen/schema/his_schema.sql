-- ============================================================
-- HIS 数据库表结构 (医院信息系统)
-- 参考: 东软/卫宁/东华 主流HIS数据结构
-- ============================================================

-- 科室字典
CREATE TABLE IF NOT EXISTS departments (
    dept_id VARCHAR(20) PRIMARY KEY,
    dept_code VARCHAR(20) NOT NULL,
    dept_name VARCHAR(100) NOT NULL,
    dept_type VARCHAR(20),              -- 临床科室/医技科室/行政科室
    parent_dept_id VARCHAR(20),
    ward_flag CHAR(1),                  -- 是否病区 Y/N
    outpatient_flag CHAR(1),            -- 是否门诊科室 Y/N
    inpatient_flag CHAR(1),             -- 是否住院科室 Y/N
    director_id VARCHAR(20),            -- 科主任
    location VARCHAR(200),
    phone VARCHAR(20),
    status CHAR(1) DEFAULT '1',         -- 0=停用 1=启用
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE departments IS '科室字典：医院组织架构基础数据，包含临床、医技、行政等所有科室信息';
COMMENT ON COLUMN departments.dept_id IS '科室主键ID（业务编码）';
COMMENT ON COLUMN departments.dept_code IS '科室编码（业务唯一码，可与上级或外部系统对接）';
COMMENT ON COLUMN departments.dept_name IS '科室名称（如内科、外科、检验科等）';
COMMENT ON COLUMN departments.dept_type IS '科室类型：临床科室/医技科室/行政科室';
COMMENT ON COLUMN departments.parent_dept_id IS '上级科室ID（自关联，构建科室层级树）';
COMMENT ON COLUMN departments.ward_flag IS '是否病区标志：Y=是病区 / N=否';
COMMENT ON COLUMN departments.outpatient_flag IS '是否门诊科室标志：Y=是 / N=否';
COMMENT ON COLUMN departments.inpatient_flag IS '是否住院科室标志：Y=是 / N=否';
COMMENT ON COLUMN departments.director_id IS '科主任人员ID（关联 staff.staff_id）';
COMMENT ON COLUMN departments.location IS '科室位置（楼栋/楼层/区域）';
COMMENT ON COLUMN departments.phone IS '科室联系电话';
COMMENT ON COLUMN departments.status IS '状态：0=停用 / 1=启用';
COMMENT ON COLUMN departments.create_time IS '记录创建时间';
COMMENT ON COLUMN departments.update_time IS '记录更新时间';

-- 人员字典 (医生/护士/技师)
CREATE TABLE IF NOT EXISTS staff (
    staff_id VARCHAR(20) PRIMARY KEY,
    staff_code VARCHAR(20) NOT NULL,
    staff_name VARCHAR(50) NOT NULL,
    gender CHAR(1),
    birthday DATE,
    id_card VARCHAR(18),
    phone VARCHAR(20),
    email VARCHAR(50),
    dept_id VARCHAR(20),
    title VARCHAR(30),                  -- 职称: 主任医师/副主任医师/主治医师/住院医师
    job_type VARCHAR(20),               -- 医生/护士/药师/技师/行政
    specialty VARCHAR(100),             -- 专长
    education VARCHAR(20),              -- 学历
    entry_date DATE,
    license_no VARCHAR(30),             -- 执业证书号
    status CHAR(1) DEFAULT '1',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE staff IS '人员字典：医院全体在册人员（医生、护士、药师、技师、行政等）';
COMMENT ON COLUMN staff.staff_id IS '人员主键ID（业务编码）';
COMMENT ON COLUMN staff.staff_code IS '员工工号（业务唯一码）';
COMMENT ON COLUMN staff.staff_name IS '员工姓名';
COMMENT ON COLUMN staff.gender IS '性别：M=男 / F=女 / U=未知';
COMMENT ON COLUMN staff.birthday IS '出生日期';
COMMENT ON COLUMN staff.id_card IS '身份证号（18位）';
COMMENT ON COLUMN staff.phone IS '联系电话';
COMMENT ON COLUMN staff.email IS '电子邮箱';
COMMENT ON COLUMN staff.dept_id IS '所属科室ID（关联 departments.dept_id）';
COMMENT ON COLUMN staff.title IS '职称：主任医师/副主任医师/主治医师/住院医师/主管护师/护师等';
COMMENT ON COLUMN staff.job_type IS '岗位类别：医生/护士/药师/技师/行政';
COMMENT ON COLUMN staff.specialty IS '专长方向（亚专业、擅长疾病等）';
COMMENT ON COLUMN staff.education IS '最高学历：博士/硕士/本科/大专/中专';
COMMENT ON COLUMN staff.entry_date IS '入职日期';
COMMENT ON COLUMN staff.license_no IS '执业证书号（医师执业证书/护士执业证书号）';
COMMENT ON COLUMN staff.status IS '在职状态：0=离职 / 1=在职';
COMMENT ON COLUMN staff.create_time IS '记录创建时间';
COMMENT ON COLUMN staff.update_time IS '记录更新时间';

-- 患者基本信息
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    medical_record_no VARCHAR(20) NOT NULL,
    patient_name VARCHAR(50) NOT NULL,
    gender CHAR(1) NOT NULL,            -- M/F/U
    birthday DATE,
    age INTEGER,                        -- 冗余字段
    id_card VARCHAR(18),
    health_card_no VARCHAR(30),         -- 医保卡号
    insurance_type VARCHAR(20),         -- 医保类型: 城镇职工/城乡居民/自费/商业保险
    insurance_no VARCHAR(30),
    nationality VARCHAR(20) DEFAULT '中国',
    ethnicity VARCHAR(20),              -- 民族
    blood_type VARCHAR(5),              -- A/B/AB/O/RH阴性
    marital_status VARCHAR(10),         -- 已婚/未婚/离异/丧偶
    occupation VARCHAR(30),
    phone VARCHAR(20),
    address VARCHAR(200),
    emergency_contact VARCHAR(50),
    emergency_phone VARCHAR(20),
    allergy_history TEXT,
    family_history TEXT,
    past_history TEXT,
    register_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP,
    status CHAR(1) DEFAULT '1'          -- 0=注销 1=正常
);

COMMENT ON TABLE patients IS '患者基本信息：医院核心主数据，是所有业务系统关联的根实体';
COMMENT ON COLUMN patients.patient_id IS '患者主键ID（系统内部唯一ID，跨系统关联键）';
COMMENT ON COLUMN patients.medical_record_no IS '病历号（医院档案号，唯一标识患者档案）';
COMMENT ON COLUMN patients.patient_name IS '患者姓名';
COMMENT ON COLUMN patients.gender IS '性别：M=男 / F=女 / U=未知';
COMMENT ON COLUMN patients.birthday IS '出生日期';
COMMENT ON COLUMN patients.age IS '年龄（冗余字段，需注意与 birthday 的一致性）';
COMMENT ON COLUMN patients.id_card IS '身份证号（18位）';
COMMENT ON COLUMN patients.health_card_no IS '医保卡号';
COMMENT ON COLUMN patients.insurance_type IS '医保类型：城镇职工/城乡居民/自费/商业保险';
COMMENT ON COLUMN patients.insurance_no IS '医保编号';
COMMENT ON COLUMN patients.nationality IS '国籍，默认 中国';
COMMENT ON COLUMN patients.ethnicity IS '民族（如汉族、回族等）';
COMMENT ON COLUMN patients.blood_type IS '血型：A/B/AB/O/RH阴性';
COMMENT ON COLUMN patients.marital_status IS '婚姻状况：已婚/未婚/离异/丧偶';
COMMENT ON COLUMN patients.occupation IS '职业';
COMMENT ON COLUMN patients.phone IS '联系电话';
COMMENT ON COLUMN patients.address IS '联系地址';
COMMENT ON COLUMN patients.emergency_contact IS '紧急联系人姓名';
COMMENT ON COLUMN patients.emergency_phone IS '紧急联系人电话';
COMMENT ON COLUMN patients.allergy_history IS '过敏史（药物过敏、食物过敏等）';
COMMENT ON COLUMN patients.family_history IS '家族史';
COMMENT ON COLUMN patients.past_history IS '既往史';
COMMENT ON COLUMN patients.register_time IS '建档时间';
COMMENT ON COLUMN patients.update_time IS '记录更新时间';
COMMENT ON COLUMN patients.status IS '档案状态：0=注销 / 1=正常';

-- 住院记录
CREATE TABLE IF NOT EXISTS inpatient_visits (
    visit_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    medical_record_no VARCHAR(20),
    admission_type VARCHAR(20),         -- 急诊/门诊/转院/其他
    admission_time TIMESTAMP NOT NULL,
    admission_dept_id VARCHAR(20),
    admission_ward_id VARCHAR(20),
    admission_bed_no VARCHAR(10),
    admission_diagnosis TEXT,
    attending_doctor_id VARCHAR(20),
    resident_doctor_id VARCHAR(20),
    chief_doctor_id VARCHAR(20),
    discharge_time TIMESTAMP,
    discharge_dept_id VARCHAR(20),
    discharge_ward_id VARCHAR(20),
    discharge_diagnosis TEXT,
    discharge_status VARCHAR(20),       -- 治愈/好转/未愈/死亡/其他
    days INTEGER,                       -- 住院天数
    total_cost DECIMAL(12,2),
    pre_payment DECIMAL(12,2),
    balance DECIMAL(12,2),
    insurance_pay DECIMAL(12,2),
    self_pay DECIMAL(12,2),
    status VARCHAR(10),                 -- 在院/出院/转科/死亡
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE inpatient_visits IS '住院记录：每条记录代表一次住院就诊（一次入院到出院的完整流程）';
COMMENT ON COLUMN inpatient_visits.visit_id IS '住院就诊主键ID（住院号，跨系统关联键）';
COMMENT ON COLUMN inpatient_visits.patient_id IS '患者ID（关联 patients.patient_id）';
COMMENT ON COLUMN inpatient_visits.medical_record_no IS '病历号（冗余，便于按病历查询）';
COMMENT ON COLUMN inpatient_visits.admission_type IS '入院途径：急诊/门诊/转院/其他';
COMMENT ON COLUMN inpatient_visits.admission_time IS '入院时间';
COMMENT ON COLUMN inpatient_visits.admission_dept_id IS '入院科室ID';
COMMENT ON COLUMN inpatient_visits.admission_ward_id IS '入院病区ID';
COMMENT ON COLUMN inpatient_visits.admission_bed_no IS '入院床位号';
COMMENT ON COLUMN inpatient_visits.admission_diagnosis IS '入院诊断（文本，可能含多个诊断）';
COMMENT ON COLUMN inpatient_visits.attending_doctor_id IS '主治医师ID';
COMMENT ON COLUMN inpatient_visits.resident_doctor_id IS '住院医师ID';
COMMENT ON COLUMN inpatient_visits.chief_doctor_id IS '主任医师ID';
COMMENT ON COLUMN inpatient_visits.discharge_time IS '出院时间（NULL 表示尚未出院）';
COMMENT ON COLUMN inpatient_visits.discharge_dept_id IS '出院科室ID';
COMMENT ON COLUMN inpatient_visits.discharge_ward_id IS '出院病区ID';
COMMENT ON COLUMN inpatient_visits.discharge_diagnosis IS '出院诊断';
COMMENT ON COLUMN inpatient_visits.discharge_status IS '出院情况：治愈/好转/未愈/死亡/其他';
COMMENT ON COLUMN inpatient_visits.days IS '住院天数';
COMMENT ON COLUMN inpatient_visits.total_cost IS '住院总费用';
COMMENT ON COLUMN inpatient_visits.pre_payment IS '预交金额';
COMMENT ON COLUMN inpatient_visits.balance IS '结算余额';
COMMENT ON COLUMN inpatient_visits.insurance_pay IS '医保支付金额';
COMMENT ON COLUMN inpatient_visits.self_pay IS '自费金额';
COMMENT ON COLUMN inpatient_visits.status IS '当前状态：在院/出院/转科/死亡';
COMMENT ON COLUMN inpatient_visits.create_time IS '记录创建时间';
COMMENT ON COLUMN inpatient_visits.update_time IS '记录更新时间';

-- 门诊记录
CREATE TABLE IF NOT EXISTS outpatient_visits (
    visit_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_date DATE NOT NULL,
    visit_time TIMESTAMP,
    dept_id VARCHAR(20),
    doctor_id VARCHAR(20),
    visit_type VARCHAR(20),             -- 普通/专家/急诊/复诊
    chief_complaint TEXT,
    present_illness TEXT,
    diagnosis TEXT,
    diagnosis_icd VARCHAR(20),
    treatment TEXT,
    fee_amount DECIMAL(10,2),
    status VARCHAR(10),                 -- 已挂号/就诊中/已结束/已取消
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE outpatient_visits IS '门诊记录：每条记录代表一次门诊或急诊就诊';
COMMENT ON COLUMN outpatient_visits.visit_id IS '门诊就诊主键ID（门诊号，跨系统关联键）';
COMMENT ON COLUMN outpatient_visits.patient_id IS '患者ID（关联 patients.patient_id）';
COMMENT ON COLUMN outpatient_visits.visit_date IS '就诊日期';
COMMENT ON COLUMN outpatient_visits.visit_time IS '就诊具体时间';
COMMENT ON COLUMN outpatient_visits.dept_id IS '就诊科室ID';
COMMENT ON COLUMN outpatient_visits.doctor_id IS '接诊医生ID';
COMMENT ON COLUMN outpatient_visits.visit_type IS '门诊类型：普通/专家/急诊/复诊';
COMMENT ON COLUMN outpatient_visits.chief_complaint IS '主诉';
COMMENT ON COLUMN outpatient_visits.present_illness IS '现病史';
COMMENT ON COLUMN outpatient_visits.diagnosis IS '诊断（文本描述）';
COMMENT ON COLUMN outpatient_visits.diagnosis_icd IS '诊断ICD-10编码';
COMMENT ON COLUMN outpatient_visits.treatment IS '处置/治疗内容';
COMMENT ON COLUMN outpatient_visits.fee_amount IS '本次就诊总费用';
COMMENT ON COLUMN outpatient_visits.status IS '就诊状态：已挂号/就诊中/已结束/已取消';
COMMENT ON COLUMN outpatient_visits.create_time IS '记录创建时间';

-- 医嘱主表
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(20) PRIMARY KEY,
    visit_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    order_type VARCHAR(10) NOT NULL,    -- 长期/临时/备用
    order_category VARCHAR(20),         -- 药品/检验/检查/手术/护理/膳食
    start_time TIMESTAMP NOT NULL,
    stop_time TIMESTAMP,
    doctor_id VARCHAR(20),
    nurse_id VARCHAR(20),
    dept_id VARCHAR(20),
    priority VARCHAR(10),               -- 普通/紧急/抢救
    order_status VARCHAR(10),           -- 新开/审核/执行/停止/作废
    verify_time TIMESTAMP,
    verify_nurse_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE orders IS '医嘱主表：医生开具的所有医嘱（药品、检验、检查、手术、护理等）的主信息';
COMMENT ON COLUMN orders.order_id IS '医嘱主键ID';
COMMENT ON COLUMN orders.visit_id IS '关联就诊ID（住院 visit_id 或门诊 visit_id）';
COMMENT ON COLUMN orders.patient_id IS '患者ID';
COMMENT ON COLUMN orders.order_type IS '医嘱类型：长期/临时/备用';
COMMENT ON COLUMN orders.order_category IS '医嘱分类：药品/检验/检查/手术/护理/膳食';
COMMENT ON COLUMN orders.start_time IS '医嘱开始执行时间';
COMMENT ON COLUMN orders.stop_time IS '医嘱停止时间（NULL 表示尚未停止）';
COMMENT ON COLUMN orders.doctor_id IS '开嘱医生ID';
COMMENT ON COLUMN orders.nurse_id IS '执行护士ID';
COMMENT ON COLUMN orders.dept_id IS '开嘱科室ID';
COMMENT ON COLUMN orders.priority IS '优先级：普通/紧急/抢救';
COMMENT ON COLUMN orders.order_status IS '医嘱状态：新开/审核/执行/停止/作废';
COMMENT ON COLUMN orders.verify_time IS '护士核对时间';
COMMENT ON COLUMN orders.verify_nurse_id IS '核对护士ID';
COMMENT ON COLUMN orders.create_time IS '记录创建时间';
COMMENT ON COLUMN orders.update_time IS '记录更新时间';

-- 医嘱明细
CREATE TABLE IF NOT EXISTS order_details (
    detail_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    item_code VARCHAR(20),              -- 项目编码
    item_name VARCHAR(200) NOT NULL,    -- 项目名称
    item_type VARCHAR(20),              -- 药品/耗材/服务
    dosage VARCHAR(50),                 -- 剂量
    dosage_unit VARCHAR(20),            -- 剂量单位
    frequency VARCHAR(30),              -- 频次: Qd/Bid/Tid/Qid
    route VARCHAR(30),                  -- 给药途径: 口服/静脉/肌肉/皮下
    duration INTEGER,                   -- 疗程天数
    total_quantity DECIMAL(10,2),
    unit VARCHAR(20),
    unit_price DECIMAL(10,4),
    total_amount DECIMAL(12,2),
    specification VARCHAR(100),         -- 规格
    manufacturer VARCHAR(100),          -- 生产厂家
    group_no VARCHAR(20),               -- 成组号
    remark TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE order_details IS '医嘱明细：医嘱具体执行项（每条医嘱可对应一条或多条明细，含药品/耗材/服务）';
COMMENT ON COLUMN order_details.detail_id IS '明细主键ID';
COMMENT ON COLUMN order_details.order_id IS '所属医嘱ID（关联 orders.order_id）';
COMMENT ON COLUMN order_details.item_code IS '项目编码（药品编码/收费项编码）';
COMMENT ON COLUMN order_details.item_name IS '项目名称';
COMMENT ON COLUMN order_details.item_type IS '项目类型：药品/耗材/服务';
COMMENT ON COLUMN order_details.dosage IS '剂量数值（如 0.5、500）';
COMMENT ON COLUMN order_details.dosage_unit IS '剂量单位（mg/g/ml/IU 等）';
COMMENT ON COLUMN order_details.frequency IS '频次：Qd（每日一次）/ Bid（每日两次）/ Tid（每日三次）/ Qid（每日四次）';
COMMENT ON COLUMN order_details.route IS '给药途径：口服/静脉/肌肉/皮下/外用 等';
COMMENT ON COLUMN order_details.duration IS '疗程天数';
COMMENT ON COLUMN order_details.total_quantity IS '总数量';
COMMENT ON COLUMN order_details.unit IS '计费单位（盒/瓶/支 等）';
COMMENT ON COLUMN order_details.unit_price IS '单价';
COMMENT ON COLUMN order_details.total_amount IS '总金额（unit_price × total_quantity）';
COMMENT ON COLUMN order_details.specification IS '规格（如 0.5g×24片/盒）';
COMMENT ON COLUMN order_details.manufacturer IS '生产厂家';
COMMENT ON COLUMN order_details.group_no IS '成组号（同一组医嘱共享，如皮试+注射的组合）';
COMMENT ON COLUMN order_details.remark IS '备注';
COMMENT ON COLUMN order_details.create_time IS '记录创建时间';

-- 收费明细
CREATE TABLE IF NOT EXISTS fee_items (
    fee_id VARCHAR(20) PRIMARY KEY,
    visit_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    fee_type VARCHAR(20),               -- 药品费/检查费/检验费/治疗费/手术费/床位费/护理费/材料费
    item_code VARCHAR(20),
    item_name VARCHAR(200),
    specification VARCHAR(100),
    unit VARCHAR(20),
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,4),
    total_amount DECIMAL(12,2),
    dept_id VARCHAR(20),
    doctor_id VARCHAR(20),
    fee_time TIMESTAMP,
    pay_status VARCHAR(10),             -- 未收费/已收费/已退费/记账
    invoice_no VARCHAR(30),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE fee_items IS '收费明细：每次就诊产生的全部收费项目（按项目+次数粒度）';
COMMENT ON COLUMN fee_items.fee_id IS '收费明细主键ID';
COMMENT ON COLUMN fee_items.visit_id IS '关联就诊ID（住院或门诊）';
COMMENT ON COLUMN fee_items.patient_id IS '患者ID';
COMMENT ON COLUMN fee_items.fee_type IS '费用类型：药品费/检查费/检验费/治疗费/手术费/床位费/护理费/材料费';
COMMENT ON COLUMN fee_items.item_code IS '收费项目编码';
COMMENT ON COLUMN fee_items.item_name IS '收费项目名称';
COMMENT ON COLUMN fee_items.specification IS '规格';
COMMENT ON COLUMN fee_items.unit IS '计价单位';
COMMENT ON COLUMN fee_items.quantity IS '数量';
COMMENT ON COLUMN fee_items.unit_price IS '单价';
COMMENT ON COLUMN fee_items.total_amount IS '小计金额';
COMMENT ON COLUMN fee_items.dept_id IS '执行科室ID';
COMMENT ON COLUMN fee_items.doctor_id IS '开单医生ID';
COMMENT ON COLUMN fee_items.fee_time IS '记费时间';
COMMENT ON COLUMN fee_items.pay_status IS '收费状态：未收费/已收费/已退费/记账';
COMMENT ON COLUMN fee_items.invoice_no IS '发票号';
COMMENT ON COLUMN fee_items.create_time IS '记录创建时间';

-- 药品字典
CREATE TABLE IF NOT EXISTS drugs (
    drug_id VARCHAR(20) PRIMARY KEY,
    drug_code VARCHAR(20) NOT NULL,
    drug_name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),          -- 通用名
    english_name VARCHAR(200),
    dosage_form VARCHAR(50),            -- 剂型: 片剂/胶囊/注射剂/口服液
    specification VARCHAR(100),         -- 规格
    unit VARCHAR(20),
    manufacturer VARCHAR(100),
    approval_no VARCHAR(50),            -- 批准文号
    drug_type VARCHAR(20),              -- 西药/中成药/中草药
    category VARCHAR(50),               -- 抗菌药物/心血管/消化系统/神经系统...
    atc_code VARCHAR(10),               -- ATC编码
    storage_condition VARCHAR(20),      -- 常温/冷藏/冷冻
    status CHAR(1) DEFAULT '1',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE drugs IS '药品字典：医院在用的全部药品基础信息';
COMMENT ON COLUMN drugs.drug_id IS '药品主键ID';
COMMENT ON COLUMN drugs.drug_code IS '药品编码（业务唯一码）';
COMMENT ON COLUMN drugs.drug_name IS '药品商品名';
COMMENT ON COLUMN drugs.generic_name IS '药品通用名';
COMMENT ON COLUMN drugs.english_name IS '英文名';
COMMENT ON COLUMN drugs.dosage_form IS '剂型：片剂/胶囊/注射剂/口服液/颗粒/栓剂 等';
COMMENT ON COLUMN drugs.specification IS '规格（如 0.5g×24片/盒）';
COMMENT ON COLUMN drugs.unit IS '最小计价单位';
COMMENT ON COLUMN drugs.manufacturer IS '生产厂家';
COMMENT ON COLUMN drugs.approval_no IS '批准文号（国药准字...）';
COMMENT ON COLUMN drugs.drug_type IS '药品大类：西药/中成药/中草药';
COMMENT ON COLUMN drugs.category IS '功能分类：抗菌药物/心血管/消化系统/神经系统 等';
COMMENT ON COLUMN drugs.atc_code IS 'WHO ATC编码（解剖学治疗学化学分类）';
COMMENT ON COLUMN drugs.storage_condition IS '储存条件：常温/冷藏/冷冻';
COMMENT ON COLUMN drugs.status IS '状态：0=停用 / 1=启用';
COMMENT ON COLUMN drugs.create_time IS '记录创建时间';

-- 床位信息
CREATE TABLE IF NOT EXISTS beds (
    bed_id VARCHAR(20) PRIMARY KEY,
    ward_id VARCHAR(20),
    room_no VARCHAR(20),
    bed_no VARCHAR(10) NOT NULL,
    bed_type VARCHAR(20),               -- 普通床/监护床/抢救床/隔离床
    dept_id VARCHAR(20),
    status VARCHAR(10),                 -- 空闲/占用/维修/停用
    patient_id VARCHAR(20),
    visit_id VARCHAR(20),
    price DECIMAL(8,2),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE beds IS '床位信息：病区物理床位的实时占用与配置情况';
COMMENT ON COLUMN beds.bed_id IS '床位主键ID';
COMMENT ON COLUMN beds.ward_id IS '所属病区ID';
COMMENT ON COLUMN beds.room_no IS '房间号';
COMMENT ON COLUMN beds.bed_no IS '床位号（如 12-3）';
COMMENT ON COLUMN beds.bed_type IS '床位类型：普通床/监护床/抢救床/隔离床';
COMMENT ON COLUMN beds.dept_id IS '所属科室ID';
COMMENT ON COLUMN beds.status IS '床位状态：空闲/占用/维修/停用';
COMMENT ON COLUMN beds.patient_id IS '当前占床患者ID（占用时填写）';
COMMENT ON COLUMN beds.visit_id IS '当前占床就诊ID';
COMMENT ON COLUMN beds.price IS '床位日单价';
COMMENT ON COLUMN beds.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(patient_name);
CREATE INDEX IF NOT EXISTS idx_inpatient_patient_id ON inpatient_visits(patient_id);
CREATE INDEX IF NOT EXISTS idx_inpatient_admission_time ON inpatient_visits(admission_time);
CREATE INDEX IF NOT EXISTS idx_outpatient_patient_id ON outpatient_visits(patient_id);
CREATE INDEX IF NOT EXISTS idx_outpatient_visit_date ON outpatient_visits(visit_date);
CREATE INDEX IF NOT EXISTS idx_orders_visit_id ON orders(visit_id);
CREATE INDEX IF NOT EXISTS idx_fee_visit_id ON fee_items(visit_id);
CREATE INDEX IF NOT EXISTS idx_staff_dept_id ON staff(dept_id);

-- ----- 批次1: 新增表 -----

-- 挂号记录
CREATE TABLE IF NOT EXISTS registrations (
    reg_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    reg_time TIMESTAMP NOT NULL,
    reg_type VARCHAR(20),               -- 现场/预约/急诊/转诊
    reg_dept_id VARCHAR(20),
    reg_doctor_id VARCHAR(20),
    fee_type VARCHAR(20),               -- 普通/专家/特需/急诊
    sequence_no INTEGER,                -- 就诊序号
    status VARCHAR(20),                 -- 候诊/就诊/过号/退号/爽约
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE registrations IS '挂号记录：门诊/急诊就诊的挂号登记信息（东软/卫宁 HIS 均有独立挂号主表）';
COMMENT ON COLUMN registrations.reg_id IS '挂号主键ID';
COMMENT ON COLUMN registrations.patient_id IS '患者ID（关联 patients.patient_id）';
COMMENT ON COLUMN registrations.visit_id IS '关联就诊ID（门诊 visit_id）';
COMMENT ON COLUMN registrations.reg_time IS '挂号时间';
COMMENT ON COLUMN registrations.reg_type IS '挂号类型：现场挂号/预约挂号/急诊挂号/转诊挂号';
COMMENT ON COLUMN registrations.reg_dept_id IS '挂号科室ID';
COMMENT ON COLUMN registrations.reg_doctor_id IS '挂号医生ID';
COMMENT ON COLUMN registrations.fee_type IS '挂号费类型：普通/专家/特需/急诊';
COMMENT ON COLUMN registrations.sequence_no IS '当日就诊序号';
COMMENT ON COLUMN registrations.status IS '挂号状态：候诊/就诊中/已就诊/过号/退号/爽约';
COMMENT ON COLUMN registrations.create_time IS '记录创建时间';

-- 转科记录
CREATE TABLE IF NOT EXISTS transfer_records (
    transfer_id VARCHAR(20) PRIMARY KEY,
    visit_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    from_dept_id VARCHAR(20),
    to_dept_id VARCHAR(20) NOT NULL,
    transfer_time TIMESTAMP NOT NULL,
    transfer_reason TEXT,
    bed_no VARCHAR(10),
    doctor_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE transfer_records IS '转科记录：住院期间患者转科信息（东软 HIS 独立转科模块）';
COMMENT ON COLUMN transfer_records.transfer_id IS '转科记录主键ID';
COMMENT ON COLUMN transfer_records.visit_id IS '住院就诊ID（关联 inpatient_visits.visit_id）';
COMMENT ON COLUMN transfer_records.patient_id IS '患者ID';
COMMENT ON COLUMN transfer_records.from_dept_id IS '转出科室ID';
COMMENT ON COLUMN transfer_records.to_dept_id IS '转入科室ID';
COMMENT ON COLUMN transfer_records.transfer_time IS '转科时间';
COMMENT ON COLUMN transfer_records.transfer_reason IS '转科原因';
COMMENT ON COLUMN transfer_records.bed_no IS '转入后床位号';
COMMENT ON COLUMN transfer_records.doctor_id IS '经治医生ID';
COMMENT ON COLUMN transfer_records.create_time IS '记录创建时间';

-- 结算主表
CREATE TABLE IF NOT EXISTS settlements (
    settlement_id VARCHAR(20) PRIMARY KEY,
    visit_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    settlement_type VARCHAR(20),        -- 出院结算/中途结算/门诊结算/急诊结算
    settlement_time TIMESTAMP,
    total_amount DECIMAL(12,2),
    insurance_pay DECIMAL(12,2),
    self_pay DECIMAL(12,2),
    invoice_no VARCHAR(30),
    settlement_status VARCHAR(20),      -- 已结算/已作废/已冲正
    cashier_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE settlements IS '结算主表：住院/门诊费用结算头表（医保结算/自费结算的汇总信息）';
COMMENT ON COLUMN settlements.settlement_id IS '结算主键ID';
COMMENT ON COLUMN settlements.visit_id IS '关联就诊ID';
COMMENT ON COLUMN settlements.patient_id IS '患者ID';
COMMENT ON COLUMN settlements.settlement_type IS '结算类型：出院结算/中途结算/门诊结算/急诊结算';
COMMENT ON COLUMN settlements.settlement_time IS '结算时间';
COMMENT ON COLUMN settlements.total_amount IS '结算总金额';
COMMENT ON COLUMN settlements.insurance_pay IS '医保支付金额';
COMMENT ON COLUMN settlements.self_pay IS '个人自付金额';
COMMENT ON COLUMN settlements.invoice_no IS '发票号';
COMMENT ON COLUMN settlements.settlement_status IS '结算状态：已结算/已作废/已冲正';
COMMENT ON COLUMN settlements.cashier_id IS '收费员ID';
COMMENT ON COLUMN settlements.create_time IS '记录创建时间';

-- 预交金记录
CREATE TABLE IF NOT EXISTS prepayments (
    prepay_id VARCHAR(20) PRIMARY KEY,
    visit_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    prepay_time TIMESTAMP NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    pay_method VARCHAR(20),             -- 现金/银行卡/微信/支付宝/医保卡
    receipt_no VARCHAR(30),
    balance DECIMAL(12,2),
    operator_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE prepayments IS '预交金记录：住院患者预交金的缴存/使用/退还流水（卫宁 HIS 预交金管理子模块）';
COMMENT ON COLUMN prepayments.prepay_id IS '预交金记录主键ID';
COMMENT ON COLUMN prepayments.visit_id IS '住院就诊ID';
COMMENT ON COLUMN prepayments.patient_id IS '患者ID';
COMMENT ON COLUMN prepayments.prepay_time IS '缴存时间';
COMMENT ON COLUMN prepayments.amount IS '缴存金额（负数表示退费）';
COMMENT ON COLUMN prepayments.pay_method IS '支付方式：现金/银行卡/微信/支付宝/医保卡';
COMMENT ON COLUMN prepayments.receipt_no IS '收据号';
COMMENT ON COLUMN prepayments.balance IS '缴存后余额';
COMMENT ON COLUMN prepayments.operator_id IS '收费操作员ID';
COMMENT ON COLUMN prepayments.create_time IS '记录创建时间';

-- ----- 批次1: 现有表补充字段 -----

ALTER TABLE patients ADD COLUMN IF NOT EXISTS contact_relation VARCHAR(20);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS height DECIMAL(5,1);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS weight DECIMAL(6,2);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS card_no VARCHAR(30);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS register_user_id VARCHAR(20);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS first_visit_date DATE;

ALTER TABLE inpatient_visits ADD COLUMN IF NOT EXISTS admission_weight DECIMAL(6,2);
ALTER TABLE inpatient_visits ADD COLUMN IF NOT EXISTS admission_height DECIMAL(5,1);
ALTER TABLE inpatient_visits ADD COLUMN IF NOT EXISTS allergy_drugs TEXT;
ALTER TABLE inpatient_visits ADD COLUMN IF NOT EXISTS companion_name VARCHAR(50);
ALTER TABLE inpatient_visits ADD COLUMN IF NOT EXISTS companion_phone VARCHAR(20);
ALTER TABLE inpatient_visits ADD COLUMN IF NOT EXISTS surgery_flag CHAR(1);
ALTER TABLE inpatient_visits ADD COLUMN IF NOT EXISTS rescue_count INTEGER DEFAULT 0;
ALTER TABLE inpatient_visits ADD COLUMN IF NOT EXISTS critical_flag CHAR(1);

ALTER TABLE staff ADD COLUMN IF NOT EXISTS practice_scope VARCHAR(200);
ALTER TABLE staff ADD COLUMN IF NOT EXISTS practice_location VARCHAR(200);
ALTER TABLE staff ADD COLUMN IF NOT EXISTS signature_image TEXT;
ALTER TABLE staff ADD COLUMN IF NOT EXISTS role_code VARCHAR(20);

-- 新增表索引
CREATE INDEX IF NOT EXISTS idx_reg_patient_id ON registrations(patient_id);
CREATE INDEX IF NOT EXISTS idx_transfer_visit_id ON transfer_records(visit_id);
CREATE INDEX IF NOT EXISTS idx_settlement_visit_id ON settlements(visit_id);
CREATE INDEX IF NOT EXISTS idx_prepay_visit_id ON prepayments(visit_id);

-- ----- 批次2: 新增表 -----

-- 发药记录
CREATE TABLE IF NOT EXISTS drug_dispenses (
    dispense_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    dispense_time TIMESTAMP,
    pharmacy_id VARCHAR(20),            -- 药房ID
    pharmacist_id VARCHAR(20),
    status VARCHAR(20),                 -- 待配药/已配药/已发药/已退药
    return_reason TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE drug_dispenses IS '发药记录：医嘱执行闭环的关键环节，连接医嘱-药房-患者';
COMMENT ON COLUMN drug_dispenses.dispense_id IS '发药主键ID';
COMMENT ON COLUMN drug_dispenses.order_id IS '关联医嘱ID';
COMMENT ON COLUMN drug_dispenses.patient_id IS '患者ID';
COMMENT ON COLUMN drug_dispenses.visit_id IS '就诊ID';
COMMENT ON COLUMN drug_dispenses.dispense_time IS '发药时间';
COMMENT ON COLUMN drug_dispenses.pharmacy_id IS '药房ID';
COMMENT ON COLUMN drug_dispenses.pharmacist_id IS '发药药师ID';
COMMENT ON COLUMN drug_dispenses.status IS '发药状态：待配药/已配药/已发药/已退药';
COMMENT ON COLUMN drug_dispenses.return_reason IS '退药原因';
COMMENT ON COLUMN drug_dispenses.create_time IS '记录创建时间';

-- 手术排程
CREATE TABLE IF NOT EXISTS operation_schedules (
    schedule_id VARCHAR(20) PRIMARY KEY,
    visit_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    surgery_name VARCHAR(200),
    surgery_code VARCHAR(20),           -- ICD-9-CM3
    surgery_room VARCHAR(20),
    schedule_date DATE,
    schedule_start_time TIMESTAMP,
    schedule_end_time TIMESTAMP,
    surgeon_id VARCHAR(20),
    anesthesia_doctor_id VARCHAR(20),
    scrub_nurse_id VARCHAR(20),
    circulating_nurse_id VARCHAR(20),
    status VARCHAR(20),                 -- 已申请/已排程/已完成/已取消
    cancel_reason TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE operation_schedules IS '手术排程：HIS 手术申请与排程管理（与 EMR 手术记录不同，这是管理视角）';
COMMENT ON COLUMN operation_schedules.schedule_id IS '排程主键ID';
COMMENT ON COLUMN operation_schedules.visit_id IS '住院就诊ID';
COMMENT ON COLUMN operation_schedules.patient_id IS '患者ID';
COMMENT ON COLUMN operation_schedules.surgery_name IS '手术名称';
COMMENT ON COLUMN operation_schedules.surgery_code IS '手术ICD-9-CM3编码';
COMMENT ON COLUMN operation_schedules.surgery_room IS '手术间';
COMMENT ON COLUMN operation_schedules.schedule_date IS '排程日期';
COMMENT ON COLUMN operation_schedules.schedule_start_time IS '预计开始时间';
COMMENT ON COLUMN operation_schedules.schedule_end_time IS '预计结束时间';
COMMENT ON COLUMN operation_schedules.surgeon_id IS '主刀医生ID';
COMMENT ON COLUMN operation_schedules.anesthesia_doctor_id IS '麻醉医生ID';
COMMENT ON COLUMN operation_schedules.scrub_nurse_id IS '器械护士ID';
COMMENT ON COLUMN operation_schedules.circulating_nurse_id IS '巡回护士ID';
COMMENT ON COLUMN operation_schedules.status IS '排程状态：已申请/已排程/已完成/已取消';
COMMENT ON COLUMN operation_schedules.cancel_reason IS '取消原因';
COMMENT ON COLUMN operation_schedules.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_dispense_order_id ON drug_dispenses(order_id);
CREATE INDEX IF NOT EXISTS idx_schedule_visit_id ON operation_schedules(visit_id);
