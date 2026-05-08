-- ============================================================
-- LIS 数据库表结构 (检验信息系统)
-- 参考: 迈瑞/贝克曼/罗氏/安图 主流LIS数据结构
-- ============================================================

-- 检验申请主表
CREATE TABLE IF NOT EXISTS lab_orders (
    order_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),               -- 住院/门诊visit_id
    visit_type VARCHAR(10),             -- 住院/门诊/急诊/体检
    order_no VARCHAR(30),               -- 申请单号
    order_time TIMESTAMP,
    order_dept_id VARCHAR(20),
    order_doctor_id VARCHAR(20),
    order_doctor_name VARCHAR(50),
    priority VARCHAR(10),               -- 普通/紧急/抢救
    diagnosis TEXT,
    clinical_note TEXT,                 -- 临床备注
    specimen_type VARCHAR(50),          -- 标本类型: 血清/血浆/全血/尿液/粪便...
    specimen_requirements TEXT,         -- 标本要求
    order_status VARCHAR(10),           -- 已申请/已采样/已签收/检验中/已完成/已取消
    report_time TIMESTAMP,
    reporter_id VARCHAR(20),
    verifier_id VARCHAR(20),
    instrument_code VARCHAR(20),        -- 检验仪器编码
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE lab_orders IS '检验申请主表：医生开具的检验项目申请单（一单可对应多个检验项目）';
COMMENT ON COLUMN lab_orders.order_id IS '检验申请主键ID';
COMMENT ON COLUMN lab_orders.patient_id IS '患者ID（关联 his_db.patients.patient_id）';
COMMENT ON COLUMN lab_orders.visit_id IS '关联就诊ID（住院或门诊）';
COMMENT ON COLUMN lab_orders.visit_type IS '就诊类型：住院/门诊/急诊/体检';
COMMENT ON COLUMN lab_orders.order_no IS '申请单号（业务编号）';
COMMENT ON COLUMN lab_orders.order_time IS '开单时间';
COMMENT ON COLUMN lab_orders.order_dept_id IS '开单科室ID';
COMMENT ON COLUMN lab_orders.order_doctor_id IS '开单医生ID';
COMMENT ON COLUMN lab_orders.order_doctor_name IS '开单医生姓名（冗余）';
COMMENT ON COLUMN lab_orders.priority IS '申请优先级：普通/紧急/抢救';
COMMENT ON COLUMN lab_orders.diagnosis IS '临床诊断（送检诊断）';
COMMENT ON COLUMN lab_orders.clinical_note IS '临床备注';
COMMENT ON COLUMN lab_orders.specimen_type IS '标本类型：血清/血浆/全血/尿液/粪便/痰/脑脊液 等';
COMMENT ON COLUMN lab_orders.specimen_requirements IS '标本采集要求（空腹、容器等）';
COMMENT ON COLUMN lab_orders.order_status IS '申请状态：已申请/已采样/已签收/检验中/已完成/已取消';
COMMENT ON COLUMN lab_orders.report_time IS '报告时间';
COMMENT ON COLUMN lab_orders.reporter_id IS '报告人ID';
COMMENT ON COLUMN lab_orders.verifier_id IS '审核人ID';
COMMENT ON COLUMN lab_orders.instrument_code IS '检验仪器编码';
COMMENT ON COLUMN lab_orders.create_time IS '记录创建时间';
COMMENT ON COLUMN lab_orders.update_time IS '记录更新时间';

-- 标本信息
CREATE TABLE IF NOT EXISTS specimens (
    specimen_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    barcode VARCHAR(30),                -- 标本条码
    specimen_type VARCHAR(50),
    specimen_sub_type VARCHAR(50),      -- 子类型
    collect_time TIMESTAMP,             -- 采集时间
    collector_id VARCHAR(20),
    collect_location VARCHAR(100),      -- 采集地点
    receive_time TIMESTAMP,             -- 接收时间
    receiver_id VARCHAR(20),
    receive_status VARCHAR(20),         -- 合格/不合格/溶血/脂血/凝块
    reject_reason VARCHAR(100),         -- 拒收原因
    volume VARCHAR(20),                 -- 标本量
    container VARCHAR(50),              -- 容器类型
    transport_temp VARCHAR(20),         -- 运输温度
    bed_no VARCHAR(10),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE specimens IS '标本信息：检验申请对应的实物标本采集与签收记录';
COMMENT ON COLUMN specimens.specimen_id IS '标本主键ID';
COMMENT ON COLUMN specimens.order_id IS '关联检验申请ID（关联 lab_orders.order_id）';
COMMENT ON COLUMN specimens.patient_id IS '患者ID';
COMMENT ON COLUMN specimens.visit_id IS '就诊ID';
COMMENT ON COLUMN specimens.barcode IS '标本条码（唯一标识，扫码识别）';
COMMENT ON COLUMN specimens.specimen_type IS '标本类型';
COMMENT ON COLUMN specimens.specimen_sub_type IS '标本子类型（如静脉血/动脉血）';
COMMENT ON COLUMN specimens.collect_time IS '标本采集时间';
COMMENT ON COLUMN specimens.collector_id IS '采集人ID';
COMMENT ON COLUMN specimens.collect_location IS '采集地点（病区/门诊/采血室）';
COMMENT ON COLUMN specimens.receive_time IS '检验科签收时间';
COMMENT ON COLUMN specimens.receiver_id IS '签收人ID';
COMMENT ON COLUMN specimens.receive_status IS '签收状态：合格/不合格/溶血/脂血/凝块';
COMMENT ON COLUMN specimens.reject_reason IS '拒收原因（不合格时填写）';
COMMENT ON COLUMN specimens.volume IS '标本量';
COMMENT ON COLUMN specimens.container IS '采集容器类型';
COMMENT ON COLUMN specimens.transport_temp IS '运输温度（常温/冷藏）';
COMMENT ON COLUMN specimens.bed_no IS '采集时床位号';
COMMENT ON COLUMN specimens.create_time IS '记录创建时间';

-- 临检结果 (Routine)
CREATE TABLE IF NOT EXISTS routine_results (
    result_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    specimen_id VARCHAR(20),
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    item_code VARCHAR(20) NOT NULL,     -- 检验项目编码
    item_name VARCHAR(100),             -- 检验项目名称
    item_loinc VARCHAR(20),             -- LOINC编码
    result_value VARCHAR(100),          -- 结果值(文本)
    result_num DECIMAL(12,4),           -- 结果值(数值)
    unit VARCHAR(20),                   -- 单位
    reference_range VARCHAR(50),        -- 参考范围
    ref_low DECIMAL(12,4),              -- 参考低值
    ref_high DECIMAL(12,4),             -- 参考高值
    abnormal_flag VARCHAR(10),          -- H/L/异常/阳性/阴性
    test_method VARCHAR(50),            -- 检验方法
    instrument_code VARCHAR(20),
    test_time TIMESTAMP,                -- 检验时间
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE routine_results IS '临检结果：常规检验结果（血常规、尿常规、便常规等）';
COMMENT ON COLUMN routine_results.result_id IS '结果主键ID';
COMMENT ON COLUMN routine_results.order_id IS '关联检验申请ID';
COMMENT ON COLUMN routine_results.specimen_id IS '关联标本ID';
COMMENT ON COLUMN routine_results.patient_id IS '患者ID';
COMMENT ON COLUMN routine_results.visit_id IS '就诊ID';
COMMENT ON COLUMN routine_results.item_code IS '检验项目编码';
COMMENT ON COLUMN routine_results.item_name IS '检验项目名称（如WBC白细胞计数）';
COMMENT ON COLUMN routine_results.item_loinc IS 'LOINC标准编码';
COMMENT ON COLUMN routine_results.result_value IS '结果值（文本，可承载非数值如"阳性"/"阴性"）';
COMMENT ON COLUMN routine_results.result_num IS '结果数值（数值型项目专用）';
COMMENT ON COLUMN routine_results.unit IS '结果单位（10^9/L、g/L、mmol/L 等）';
COMMENT ON COLUMN routine_results.reference_range IS '参考范围文本（如 "3.5~9.5"）';
COMMENT ON COLUMN routine_results.ref_low IS '参考下限';
COMMENT ON COLUMN routine_results.ref_high IS '参考上限';
COMMENT ON COLUMN routine_results.abnormal_flag IS '异常标志：H=高 / L=低 / 异常 / 阳性 / 阴性';
COMMENT ON COLUMN routine_results.test_method IS '检验方法';
COMMENT ON COLUMN routine_results.instrument_code IS '检验仪器编码';
COMMENT ON COLUMN routine_results.test_time IS '上机检测时间';
COMMENT ON COLUMN routine_results.report_time IS '报告时间';
COMMENT ON COLUMN routine_results.create_time IS '记录创建时间';

-- 生化结果 (Biochemistry)
CREATE TABLE IF NOT EXISTS biochem_results (
    result_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    specimen_id VARCHAR(20),
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    item_code VARCHAR(20) NOT NULL,
    item_name VARCHAR(100),
    item_loinc VARCHAR(20),
    result_value VARCHAR(100),
    result_num DECIMAL(12,4),
    unit VARCHAR(20),
    reference_range VARCHAR(50),
    ref_low DECIMAL(12,4),
    ref_high DECIMAL(12,4),
    abnormal_flag VARCHAR(10),
    test_method VARCHAR(50),
    instrument_code VARCHAR(20),
    test_time TIMESTAMP,
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE biochem_results IS '生化检验结果：肝功、肾功、电解质、心肌酶谱等生化项目';
COMMENT ON COLUMN biochem_results.result_id IS '结果主键ID';
COMMENT ON COLUMN biochem_results.order_id IS '关联检验申请ID';
COMMENT ON COLUMN biochem_results.specimen_id IS '关联标本ID';
COMMENT ON COLUMN biochem_results.patient_id IS '患者ID';
COMMENT ON COLUMN biochem_results.visit_id IS '就诊ID';
COMMENT ON COLUMN biochem_results.item_code IS '检验项目编码';
COMMENT ON COLUMN biochem_results.item_name IS '检验项目名称（如ALT丙氨酸氨基转移酶）';
COMMENT ON COLUMN biochem_results.item_loinc IS 'LOINC标准编码';
COMMENT ON COLUMN biochem_results.result_value IS '结果值（文本）';
COMMENT ON COLUMN biochem_results.result_num IS '结果数值';
COMMENT ON COLUMN biochem_results.unit IS '结果单位（U/L、mmol/L 等）';
COMMENT ON COLUMN biochem_results.reference_range IS '参考范围文本';
COMMENT ON COLUMN biochem_results.ref_low IS '参考下限';
COMMENT ON COLUMN biochem_results.ref_high IS '参考上限';
COMMENT ON COLUMN biochem_results.abnormal_flag IS '异常标志：H/L/异常';
COMMENT ON COLUMN biochem_results.test_method IS '检验方法';
COMMENT ON COLUMN biochem_results.instrument_code IS '检验仪器编码';
COMMENT ON COLUMN biochem_results.test_time IS '上机检测时间';
COMMENT ON COLUMN biochem_results.report_time IS '报告时间';
COMMENT ON COLUMN biochem_results.create_time IS '记录创建时间';

-- 血液结果 (Hematology)
CREATE TABLE IF NOT EXISTS blood_results (
    result_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    specimen_id VARCHAR(20),
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    item_code VARCHAR(20) NOT NULL,
    item_name VARCHAR(100),
    item_loinc VARCHAR(20),
    result_value VARCHAR(100),
    result_num DECIMAL(12,4),
    unit VARCHAR(20),
    reference_range VARCHAR(50),
    ref_low DECIMAL(12,4),
    ref_high DECIMAL(12,4),
    abnormal_flag VARCHAR(10),
    test_method VARCHAR(50),
    instrument_code VARCHAR(20),
    test_time TIMESTAMP,
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE blood_results IS '血液学检验结果：凝血功能、血型、血气补充等血液专项检验';
COMMENT ON COLUMN blood_results.result_id IS '结果主键ID';
COMMENT ON COLUMN blood_results.order_id IS '关联检验申请ID';
COMMENT ON COLUMN blood_results.specimen_id IS '关联标本ID';
COMMENT ON COLUMN blood_results.patient_id IS '患者ID';
COMMENT ON COLUMN blood_results.visit_id IS '就诊ID';
COMMENT ON COLUMN blood_results.item_code IS '检验项目编码';
COMMENT ON COLUMN blood_results.item_name IS '检验项目名称（如PT凝血酶原时间）';
COMMENT ON COLUMN blood_results.item_loinc IS 'LOINC标准编码';
COMMENT ON COLUMN blood_results.result_value IS '结果值（文本）';
COMMENT ON COLUMN blood_results.result_num IS '结果数值';
COMMENT ON COLUMN blood_results.unit IS '结果单位';
COMMENT ON COLUMN blood_results.reference_range IS '参考范围文本';
COMMENT ON COLUMN blood_results.ref_low IS '参考下限';
COMMENT ON COLUMN blood_results.ref_high IS '参考上限';
COMMENT ON COLUMN blood_results.abnormal_flag IS '异常标志：H/L/异常';
COMMENT ON COLUMN blood_results.test_method IS '检验方法';
COMMENT ON COLUMN blood_results.instrument_code IS '检验仪器编码';
COMMENT ON COLUMN blood_results.test_time IS '上机检测时间';
COMMENT ON COLUMN blood_results.report_time IS '报告时间';
COMMENT ON COLUMN blood_results.create_time IS '记录创建时间';

-- 微生物结果
CREATE TABLE IF NOT EXISTS microbiology (
    micro_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    specimen_id VARCHAR(20),
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    test_seq INTEGER,                   -- 检验序号
    culture_no VARCHAR(30),             -- 培养编号
    specimen_type VARCHAR(50),
    collect_site VARCHAR(100),          -- 采集部位
    gram_stain VARCHAR(200),            -- 革兰染色结果
    culture_result TEXT,                -- 培养结果
    organism_code VARCHAR(20),          -- 菌种编码
    organism_name VARCHAR(200),         -- 菌种名称
    colony_count VARCHAR(50),           -- 菌落计数
    incubation_days INTEGER,            -- 培养天数
    isolate_no INTEGER,                 -- 分离株编号
    technician_id VARCHAR(20),
    test_time TIMESTAMP,
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE microbiology IS '微生物结果：细菌/真菌培养鉴定结果（与药敏试验关联）';
COMMENT ON COLUMN microbiology.micro_id IS '微生物结果主键ID';
COMMENT ON COLUMN microbiology.order_id IS '关联检验申请ID';
COMMENT ON COLUMN microbiology.specimen_id IS '关联标本ID';
COMMENT ON COLUMN microbiology.patient_id IS '患者ID';
COMMENT ON COLUMN microbiology.visit_id IS '就诊ID';
COMMENT ON COLUMN microbiology.test_seq IS '检验序号（同一标本多次检验时使用）';
COMMENT ON COLUMN microbiology.culture_no IS '培养编号';
COMMENT ON COLUMN microbiology.specimen_type IS '标本类型';
COMMENT ON COLUMN microbiology.collect_site IS '采集部位（伤口/痰/尿/血等）';
COMMENT ON COLUMN microbiology.gram_stain IS '革兰染色结果';
COMMENT ON COLUMN microbiology.culture_result IS '培养结果描述';
COMMENT ON COLUMN microbiology.organism_code IS '菌种编码';
COMMENT ON COLUMN microbiology.organism_name IS '菌种名称（如金黄色葡萄球菌）';
COMMENT ON COLUMN microbiology.colony_count IS '菌落计数（如 10^5 CFU/ml）';
COMMENT ON COLUMN microbiology.incubation_days IS '培养天数';
COMMENT ON COLUMN microbiology.isolate_no IS '分离株编号（一份标本可分离出多株）';
COMMENT ON COLUMN microbiology.technician_id IS '操作技师ID';
COMMENT ON COLUMN microbiology.test_time IS '检测时间';
COMMENT ON COLUMN microbiology.report_time IS '报告时间';
COMMENT ON COLUMN microbiology.create_time IS '记录创建时间';

-- 药敏试验
CREATE TABLE IF NOT EXISTS antibiotic_sensitivity (
    sensitivity_id VARCHAR(20) PRIMARY KEY,
    micro_id VARCHAR(20) NOT NULL,
    order_id VARCHAR(20),
    patient_id VARCHAR(20) NOT NULL,
    organism_name VARCHAR(200),
    antibiotic_code VARCHAR(20),        -- 抗生素编码
    antibiotic_name VARCHAR(100),       -- 抗生素名称
    mic VARCHAR(20),                    -- 最小抑菌浓度
    kb_zone INTEGER,                    -- 抑菌圈直径 mm
    result VARCHAR(10),                 -- S/I/R (敏感/中介/耐药)
    method VARCHAR(20),                 -- 药敏方法
    standard VARCHAR(20),               -- 判定标准 CLSI/EUCAST
    instrument_code VARCHAR(20),
    test_time TIMESTAMP,
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE antibiotic_sensitivity IS '药敏试验：针对微生物培养出的菌株做的抗生素敏感性测定';
COMMENT ON COLUMN antibiotic_sensitivity.sensitivity_id IS '药敏结果主键ID';
COMMENT ON COLUMN antibiotic_sensitivity.micro_id IS '关联微生物结果ID（关联 microbiology.micro_id）';
COMMENT ON COLUMN antibiotic_sensitivity.order_id IS '关联检验申请ID';
COMMENT ON COLUMN antibiotic_sensitivity.patient_id IS '患者ID';
COMMENT ON COLUMN antibiotic_sensitivity.organism_name IS '受试菌种名称（冗余）';
COMMENT ON COLUMN antibiotic_sensitivity.antibiotic_code IS '抗生素编码';
COMMENT ON COLUMN antibiotic_sensitivity.antibiotic_name IS '抗生素名称';
COMMENT ON COLUMN antibiotic_sensitivity.mic IS '最小抑菌浓度（MIC，单位 μg/ml）';
COMMENT ON COLUMN antibiotic_sensitivity.kb_zone IS 'KB纸片法抑菌圈直径（mm）';
COMMENT ON COLUMN antibiotic_sensitivity.result IS '判读结果：S=敏感 / I=中介 / R=耐药';
COMMENT ON COLUMN antibiotic_sensitivity.method IS '药敏方法：MIC法 / KB纸片法 等';
COMMENT ON COLUMN antibiotic_sensitivity.standard IS '判定标准：CLSI / EUCAST';
COMMENT ON COLUMN antibiotic_sensitivity.instrument_code IS '使用仪器编码';
COMMENT ON COLUMN antibiotic_sensitivity.test_time IS '测试时间';
COMMENT ON COLUMN antibiotic_sensitivity.report_time IS '报告时间';
COMMENT ON COLUMN antibiotic_sensitivity.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_laborder_patient_id ON lab_orders(patient_id);
CREATE INDEX IF NOT EXISTS idx_laborder_visit_id ON lab_orders(visit_id);
CREATE INDEX IF NOT EXISTS idx_specimen_order_id ON specimens(order_id);
CREATE INDEX IF NOT EXISTS idx_routine_patient_id ON routine_results(patient_id);
CREATE INDEX IF NOT EXISTS idx_biochem_patient_id ON biochem_results(patient_id);
CREATE INDEX IF NOT EXISTS idx_blood_patient_id ON blood_results(patient_id);
CREATE INDEX IF NOT EXISTS idx_micro_patient_id ON microbiology(patient_id);
CREATE INDEX IF NOT EXISTS idx_anti_micro_id ON antibiotic_sensitivity(micro_id);

-- ----- 批次1: 新增表 -----

-- 检验报告主表
CREATE TABLE IF NOT EXISTS lab_report_master (
    report_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    report_no VARCHAR(30),
    report_time TIMESTAMP,
    verify_time TIMESTAMP,
    reporter_id VARCHAR(20),
    verifier_id VARCHAR(20),
    report_status VARCHAR(20),          -- 草稿/已提交/已审核
    critical_value_flag CHAR(1),        -- 是否危急值 Y/N
    critical_value_handled CHAR(1),     -- 危急值是否已处理 Y/N
    specimen_type VARCHAR(50),
    specimen_status VARCHAR(20),        -- 合格/溶血/脂血/凝块
    instrument_code VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);
COMMENT ON TABLE lab_report_master IS '检验报告主表：统一报告头表（迈瑞/罗氏 LIS 均有），汇总各分类结果';
COMMENT ON COLUMN lab_report_master.report_id IS '报告主键ID';
COMMENT ON COLUMN lab_report_master.order_id IS '关联检验申请ID';
COMMENT ON COLUMN lab_report_master.patient_id IS '患者ID';
COMMENT ON COLUMN lab_report_master.visit_id IS '就诊ID';
COMMENT ON COLUMN lab_report_master.report_no IS '报告编号';
COMMENT ON COLUMN lab_report_master.report_time IS '报告时间';
COMMENT ON COLUMN lab_report_master.verify_time IS '审核时间';
COMMENT ON COLUMN lab_report_master.reporter_id IS '报告人ID';
COMMENT ON COLUMN lab_report_master.verifier_id IS '审核人ID';
COMMENT ON COLUMN lab_report_master.report_status IS '报告状态：草稿/已提交/已审核/已发布';
COMMENT ON COLUMN lab_report_master.critical_value_flag IS '是否危急值：Y=是 / N=否';
COMMENT ON COLUMN lab_report_master.critical_value_handled IS '危急值是否已处理闭环：Y=是 / N=否';
COMMENT ON COLUMN lab_report_master.specimen_type IS '标本类型';
COMMENT ON COLUMN lab_report_master.specimen_status IS '标本质量状态：合格/溶血/脂血/凝块';
COMMENT ON COLUMN lab_report_master.instrument_code IS '检验仪器编码';
COMMENT ON COLUMN lab_report_master.create_time IS '记录创建时间';
COMMENT ON COLUMN lab_report_master.update_time IS '记录更新时间';

-- 危急值处理记录
CREATE TABLE IF NOT EXISTS critical_values (
    cv_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    report_id VARCHAR(20),
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    item_name VARCHAR(100),
    result_value VARCHAR(100),
    reference_range VARCHAR(50),
    cv_time TIMESTAMP NOT NULL,
    notified_doctor_id VARCHAR(20),
    notification_time TIMESTAMP,
    confirmation_time TIMESTAMP,
    handler_id VARCHAR(20),
    handle_action TEXT,
    status VARCHAR(20),                 -- 已通知/已确认/已处理
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE critical_values IS '危急值处理记录：危急值闭环管理（JCI/三甲评审重点，检验科质控核心）';
COMMENT ON COLUMN critical_values.cv_id IS '危急值主键ID';
COMMENT ON COLUMN critical_values.order_id IS '关联检验申请ID';
COMMENT ON COLUMN critical_values.report_id IS '关联报告ID';
COMMENT ON COLUMN critical_values.patient_id IS '患者ID';
COMMENT ON COLUMN critical_values.visit_id IS '就诊ID';
COMMENT ON COLUMN critical_values.item_name IS '危急值项目名称';
COMMENT ON COLUMN critical_values.result_value IS '危急值结果';
COMMENT ON COLUMN critical_values.reference_range IS '参考范围';
COMMENT ON COLUMN critical_values.cv_time IS '危急值检出时间';
COMMENT ON COLUMN critical_values.notified_doctor_id IS '被通知医生ID';
COMMENT ON COLUMN critical_values.notification_time IS '通知时间';
COMMENT ON COLUMN critical_values.confirmation_time IS '确认时间';
COMMENT ON COLUMN critical_values.handler_id IS '处理人ID';
COMMENT ON COLUMN critical_values.handle_action IS '处理措施';
COMMENT ON COLUMN critical_values.status IS '处理状态：已通知/已确认/已处理/已关闭';
COMMENT ON COLUMN critical_values.create_time IS '记录创建时间';

-- ----- 批次1: 现有表补充字段 -----

ALTER TABLE lab_orders ADD COLUMN IF NOT EXISTS barcode VARCHAR(30);
ALTER TABLE lab_orders ADD COLUMN IF NOT EXISTS collect_time TIMESTAMP;
ALTER TABLE lab_orders ADD COLUMN IF NOT EXISTS collect_user_id VARCHAR(20);
ALTER TABLE lab_orders ADD COLUMN IF NOT EXISTS receive_time TIMESTAMP;
ALTER TABLE lab_orders ADD COLUMN IF NOT EXISTS receive_user_id VARCHAR(20);
ALTER TABLE lab_orders ADD COLUMN IF NOT EXISTS specimen_quality VARCHAR(20);

ALTER TABLE routine_results ADD COLUMN IF NOT EXISTS dilution_factor INTEGER DEFAULT 1;
ALTER TABLE routine_results ADD COLUMN IF NOT EXISTS delta_check_flag CHAR(1);
ALTER TABLE routine_results ADD COLUMN IF NOT EXISTS instrument_channel VARCHAR(20);
ALTER TABLE routine_results ADD COLUMN IF NOT EXISTS reagent_lot_no VARCHAR(30);

ALTER TABLE biochem_results ADD COLUMN IF NOT EXISTS dilution_factor INTEGER DEFAULT 1;
ALTER TABLE biochem_results ADD COLUMN IF NOT EXISTS delta_check_flag CHAR(1);
ALTER TABLE biochem_results ADD COLUMN IF NOT EXISTS instrument_channel VARCHAR(20);
ALTER TABLE biochem_results ADD COLUMN IF NOT EXISTS reagent_lot_no VARCHAR(30);

ALTER TABLE blood_results ADD COLUMN IF NOT EXISTS dilution_factor INTEGER DEFAULT 1;
ALTER TABLE blood_results ADD COLUMN IF NOT EXISTS delta_check_flag CHAR(1);
ALTER TABLE blood_results ADD COLUMN IF NOT EXISTS instrument_channel VARCHAR(20);
ALTER TABLE blood_results ADD COLUMN IF NOT EXISTS reagent_lot_no VARCHAR(30);

-- 新增表索引
CREATE INDEX IF NOT EXISTS idx_labreport_order_id ON lab_report_master(order_id);
CREATE INDEX IF NOT EXISTS idx_labreport_patient_id ON lab_report_master(patient_id);
CREATE INDEX IF NOT EXISTS idx_cv_patient_id ON critical_values(patient_id);
CREATE INDEX IF NOT EXISTS idx_cv_order_id ON critical_values(order_id);

-- ----- 批次2: 新增表 -----

-- 免疫/发光结果
CREATE TABLE IF NOT EXISTS immunoassay_results (
    result_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    item_code VARCHAR(20) NOT NULL,
    item_name VARCHAR(100),
    result_value VARCHAR(100),
    result_num DECIMAL(12,4),
    unit VARCHAR(20),
    reference_range VARCHAR(50),
    abnormal_flag VARCHAR(10),
    method VARCHAR(50),                 -- 化学发光/电化学发光/ELISA/放射免疫
    instrument_code VARCHAR(20),
    test_time TIMESTAMP,
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE immunoassay_results IS '免疫/发光结果：肿瘤标志物、激素、心肌标志物等免疫学检验（罗氏 cobas 常见）';
COMMENT ON COLUMN immunoassay_results.result_id IS '结果主键ID';
COMMENT ON COLUMN immunoassay_results.order_id IS '关联检验申请ID';
COMMENT ON COLUMN immunoassay_results.patient_id IS '患者ID';
COMMENT ON COLUMN immunoassay_results.visit_id IS '就诊ID';
COMMENT ON COLUMN immunoassay_results.item_code IS '检验项目编码';
COMMENT ON COLUMN immunoassay_results.item_name IS '检验项目名称';
COMMENT ON COLUMN immunoassay_results.result_value IS '结果值（文本）';
COMMENT ON COLUMN immunoassay_results.result_num IS '结果数值';
COMMENT ON COLUMN immunoassay_results.unit IS '单位';
COMMENT ON COLUMN immunoassay_results.reference_range IS '参考范围';
COMMENT ON COLUMN immunoassay_results.abnormal_flag IS '异常标志：H/L/异常/阳性/阴性';
COMMENT ON COLUMN immunoassay_results.method IS '检测方法：化学发光/电化学发光/ELISA/放射免疫';
COMMENT ON COLUMN immunoassay_results.instrument_code IS '仪器编码';
COMMENT ON COLUMN immunoassay_results.test_time IS '检测时间';
COMMENT ON COLUMN immunoassay_results.report_time IS '报告时间';
COMMENT ON COLUMN immunoassay_results.create_time IS '记录创建时间';

-- 分子诊断结果
CREATE TABLE IF NOT EXISTS molecular_results (
    result_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    item_code VARCHAR(20) NOT NULL,
    item_name VARCHAR(100),
    result_value VARCHAR(100),
    qualitative_result VARCHAR(20),     -- 阴性/阳性/可疑
    ct_value DECIMAL(5,2),              -- CT值（PCR用）
    gene_target VARCHAR(100),           -- 靶基因
    mutation_info TEXT,                 -- 突变信息
    method VARCHAR(50),                 -- PCR/测序/FISH/芯片
    specimen_type VARCHAR(50),
    collect_time TIMESTAMP,
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE molecular_results IS '分子诊断结果：PCR、基因测序、FISH等分子检验（安图/达安 LIS 支持）';
COMMENT ON COLUMN molecular_results.result_id IS '结果主键ID';
COMMENT ON COLUMN molecular_results.order_id IS '关联检验申请ID';
COMMENT ON COLUMN molecular_results.patient_id IS '患者ID';
COMMENT ON COLUMN molecular_results.visit_id IS '就诊ID';
COMMENT ON COLUMN molecular_results.item_code IS '检验项目编码';
COMMENT ON COLUMN molecular_results.item_name IS '检验项目名称';
COMMENT ON COLUMN molecular_results.result_value IS '结果值';
COMMENT ON COLUMN molecular_results.qualitative_result IS '定性结果：阴性/阳性/可疑';
COMMENT ON COLUMN molecular_results.ct_value IS 'CT值（PCR检测用）';
COMMENT ON COLUMN molecular_results.gene_target IS '检测靶基因';
COMMENT ON COLUMN molecular_results.mutation_info IS '突变信息描述';
COMMENT ON COLUMN molecular_results.method IS '检测方法：PCR/测序/FISH/芯片';
COMMENT ON COLUMN molecular_results.specimen_type IS '标本类型';
COMMENT ON COLUMN molecular_results.collect_time IS '采集时间';
COMMENT ON COLUMN molecular_results.report_time IS '报告时间';
COMMENT ON COLUMN molecular_results.create_time IS '记录创建时间';

-- 室内质控
CREATE TABLE IF NOT EXISTS qc_internal (
    qc_id VARCHAR(20) PRIMARY KEY,
    item_code VARCHAR(20) NOT NULL,
    item_name VARCHAR(100),
    lot_no VARCHAR(30),                 -- 质控品批号
    level VARCHAR(10),                  -- 质控品水平：L1/L2/L3
    target_value DECIMAL(12,4),
    sd DECIMAL(12,4),
    cv DECIMAL(6,2),                    -- 变异系数%
    measured_value DECIMAL(12,4),
    run_date DATE,
    instrument_code VARCHAR(20),
    status VARCHAR(20),                 -- 在控/警告/失控
    operator_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE qc_internal IS '室内质控：检验科每日室内质控数据记录';
COMMENT ON COLUMN qc_internal.qc_id IS '质控主键ID';
COMMENT ON COLUMN qc_internal.item_code IS '检验项目编码';
COMMENT ON COLUMN qc_internal.item_name IS '检验项目名称';
COMMENT ON COLUMN qc_internal.lot_no IS '质控品批号';
COMMENT ON COLUMN qc_internal.level IS '质控品水平：L1/L2/L3';
COMMENT ON COLUMN qc_internal.target_value IS '靶值';
COMMENT ON COLUMN qc_internal.sd IS '标准差';
COMMENT ON COLUMN qc_internal.cv IS '变异系数（%）';
COMMENT ON COLUMN qc_internal.measured_value IS '实测值';
COMMENT ON COLUMN qc_internal.run_date IS '运行日期';
COMMENT ON COLUMN qc_internal.instrument_code IS '仪器编码';
COMMENT ON COLUMN qc_internal.status IS '质控状态：在控/警告/失控';
COMMENT ON COLUMN qc_internal.operator_id IS '操作人ID';
COMMENT ON COLUMN qc_internal.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_immuno_patient_id ON immunoassay_results(patient_id);
CREATE INDEX IF NOT EXISTS idx_molecular_patient_id ON molecular_results(patient_id);
CREATE INDEX IF NOT EXISTS idx_qc_run_date ON qc_internal(run_date);
