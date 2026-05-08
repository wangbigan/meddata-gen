-- ============================================================
-- EMR 数据库表结构 (电子病历系统)
-- 参考: 嘉和/卫宁/海泰 主流EMR数据结构
-- ============================================================

-- 病历文档主表
CREATE TABLE IF NOT EXISTS emr_documents (
    document_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),               -- 住院visit_id 或 门诊visit_id
    visit_type VARCHAR(10),             -- 住院/门诊/急诊
    document_type VARCHAR(30) NOT NULL, -- 入院记录/首次病程/日常病程/出院记录/死亡记录/手术记录/会诊记录
    document_title VARCHAR(200),
    document_content TEXT,
    dept_id VARCHAR(20),
    author_id VARCHAR(20),              -- 书写医生
    author_name VARCHAR(50),
    write_time TIMESTAMP,
    sign_time TIMESTAMP,                -- 签名时间
    sign_status CHAR(1),                -- 0=未签 1=已签
    modify_count INTEGER DEFAULT 0,     -- 修改次数
    modifier_id VARCHAR(20),
    modify_time TIMESTAMP,
    quality_status VARCHAR(10),         -- 甲/乙/丙/未评
    print_count INTEGER DEFAULT 0,
    status VARCHAR(10),                 -- 草稿/完成/归档
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE emr_documents IS '病历文档主表：电子病历系统中所有结构化/半结构化文档的统一索引';
COMMENT ON COLUMN emr_documents.document_id IS '病历文档主键ID';
COMMENT ON COLUMN emr_documents.patient_id IS '患者ID（关联 his_db.patients.patient_id）';
COMMENT ON COLUMN emr_documents.visit_id IS '关联就诊ID（住院 visit_id 或 门诊 visit_id）';
COMMENT ON COLUMN emr_documents.visit_type IS '就诊类型：住院/门诊/急诊';
COMMENT ON COLUMN emr_documents.document_type IS '文档类型：入院记录/首次病程/日常病程/出院记录/死亡记录/手术记录/会诊记录 等';
COMMENT ON COLUMN emr_documents.document_title IS '文档标题';
COMMENT ON COLUMN emr_documents.document_content IS '文档内容（富文本/纯文本/XML）';
COMMENT ON COLUMN emr_documents.dept_id IS '所属科室ID';
COMMENT ON COLUMN emr_documents.author_id IS '书写医生ID';
COMMENT ON COLUMN emr_documents.author_name IS '书写医生姓名（冗余字段）';
COMMENT ON COLUMN emr_documents.write_time IS '书写时间';
COMMENT ON COLUMN emr_documents.sign_time IS '电子签名时间';
COMMENT ON COLUMN emr_documents.sign_status IS '签名状态：0=未签 / 1=已签';
COMMENT ON COLUMN emr_documents.modify_count IS '累计修改次数';
COMMENT ON COLUMN emr_documents.modifier_id IS '最后修改人ID';
COMMENT ON COLUMN emr_documents.modify_time IS '最后修改时间';
COMMENT ON COLUMN emr_documents.quality_status IS '病历质控等级：甲/乙/丙/未评';
COMMENT ON COLUMN emr_documents.print_count IS '打印次数';
COMMENT ON COLUMN emr_documents.status IS '文档状态：草稿/完成/归档';
COMMENT ON COLUMN emr_documents.create_time IS '记录创建时间';
COMMENT ON COLUMN emr_documents.update_time IS '记录更新时间';

-- 病程记录
CREATE TABLE IF NOT EXISTS progress_notes (
    note_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    note_date DATE NOT NULL,
    note_time TIMESTAMP,
    note_type VARCHAR(20),              -- 日常病程/上级查房/交接班/抢救记录/阶段小结
    content TEXT,
    author_id VARCHAR(20),
    author_name VARCHAR(50),
    sign_time TIMESTAMP,
    record_time TIMESTAMP,              -- 记录时间
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE progress_notes IS '病程记录：住院期间医生对患者病情进展的连续性记录';
COMMENT ON COLUMN progress_notes.note_id IS '病程记录主键ID';
COMMENT ON COLUMN progress_notes.patient_id IS '患者ID';
COMMENT ON COLUMN progress_notes.visit_id IS '住院就诊ID';
COMMENT ON COLUMN progress_notes.note_date IS '病程记录日期';
COMMENT ON COLUMN progress_notes.note_time IS '病程记录精确时间';
COMMENT ON COLUMN progress_notes.note_type IS '病程类型：日常病程/上级查房/交接班/抢救记录/阶段小结';
COMMENT ON COLUMN progress_notes.content IS '病程内容文本';
COMMENT ON COLUMN progress_notes.author_id IS '书写医生ID';
COMMENT ON COLUMN progress_notes.author_name IS '书写医生姓名（冗余）';
COMMENT ON COLUMN progress_notes.sign_time IS '电子签名时间';
COMMENT ON COLUMN progress_notes.record_time IS '记录提交时间';
COMMENT ON COLUMN progress_notes.create_time IS '记录创建时间';

-- 入院记录
CREATE TABLE IF NOT EXISTS admission_records (
    record_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    admission_time TIMESTAMP,
    chief_complaint TEXT,               -- 主诉
    present_illness TEXT,               -- 现病史
    past_history TEXT,                  -- 既往史
    personal_history TEXT,              -- 个人史
    family_history TEXT,                -- 家族史
    allergy_history TEXT,               -- 过敏史
    physical_exam TEXT,                 -- 体格检查
    vital_signs TEXT,                   -- 生命体征
    auxiliary_exam TEXT,                -- 辅助检查
    preliminary_diagnosis TEXT,         -- 初步诊断
    diagnosis_icd TEXT,
    treatment_plan TEXT,                -- 诊疗计划
    doctor_id VARCHAR(20),
    doctor_name VARCHAR(50),
    write_time TIMESTAMP,
    sign_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE admission_records IS '入院记录：患者入院时由医生书写的完整病史采集与初步评估文档';
COMMENT ON COLUMN admission_records.record_id IS '入院记录主键ID';
COMMENT ON COLUMN admission_records.patient_id IS '患者ID';
COMMENT ON COLUMN admission_records.visit_id IS '住院就诊ID';
COMMENT ON COLUMN admission_records.admission_time IS '入院时间';
COMMENT ON COLUMN admission_records.chief_complaint IS '主诉（患者最主要的症状）';
COMMENT ON COLUMN admission_records.present_illness IS '现病史';
COMMENT ON COLUMN admission_records.past_history IS '既往史';
COMMENT ON COLUMN admission_records.personal_history IS '个人史';
COMMENT ON COLUMN admission_records.family_history IS '家族史';
COMMENT ON COLUMN admission_records.allergy_history IS '过敏史（药物/食物等）';
COMMENT ON COLUMN admission_records.physical_exam IS '体格检查';
COMMENT ON COLUMN admission_records.vital_signs IS '生命体征（T/P/R/BP）';
COMMENT ON COLUMN admission_records.auxiliary_exam IS '辅助检查（既往化验/影像结果）';
COMMENT ON COLUMN admission_records.preliminary_diagnosis IS '初步诊断（文本）';
COMMENT ON COLUMN admission_records.diagnosis_icd IS '初步诊断ICD-10编码（多个用分隔符）';
COMMENT ON COLUMN admission_records.treatment_plan IS '诊疗计划';
COMMENT ON COLUMN admission_records.doctor_id IS '书写医生ID';
COMMENT ON COLUMN admission_records.doctor_name IS '书写医生姓名（冗余）';
COMMENT ON COLUMN admission_records.write_time IS '书写时间';
COMMENT ON COLUMN admission_records.sign_time IS '签名时间';
COMMENT ON COLUMN admission_records.create_time IS '记录创建时间';

-- 出院记录
CREATE TABLE IF NOT EXISTS discharge_records (
    record_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    admission_time TIMESTAMP,
    discharge_time TIMESTAMP,
    hospital_days INTEGER,
    admission_diagnosis TEXT,
    discharge_diagnosis TEXT,
    diagnosis_icd TEXT,
    treatment_summary TEXT,             -- 诊治经过
    discharge_status VARCHAR(20),       -- 出院情况
    discharge_advice TEXT,              -- 出院医嘱
    follow_up_plan TEXT,                -- 随访计划
    doctor_id VARCHAR(20),
    doctor_name VARCHAR(50),
    write_time TIMESTAMP,
    sign_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE discharge_records IS '出院记录：患者出院时由医生书写的本次住院诊疗总结';
COMMENT ON COLUMN discharge_records.record_id IS '出院记录主键ID';
COMMENT ON COLUMN discharge_records.patient_id IS '患者ID';
COMMENT ON COLUMN discharge_records.visit_id IS '住院就诊ID';
COMMENT ON COLUMN discharge_records.admission_time IS '入院时间（冗余）';
COMMENT ON COLUMN discharge_records.discharge_time IS '出院时间';
COMMENT ON COLUMN discharge_records.hospital_days IS '住院天数';
COMMENT ON COLUMN discharge_records.admission_diagnosis IS '入院诊断';
COMMENT ON COLUMN discharge_records.discharge_diagnosis IS '出院诊断';
COMMENT ON COLUMN discharge_records.diagnosis_icd IS '出院诊断ICD-10编码';
COMMENT ON COLUMN discharge_records.treatment_summary IS '诊治经过总结';
COMMENT ON COLUMN discharge_records.discharge_status IS '出院情况：治愈/好转/未愈/死亡/其他';
COMMENT ON COLUMN discharge_records.discharge_advice IS '出院医嘱';
COMMENT ON COLUMN discharge_records.follow_up_plan IS '随访计划';
COMMENT ON COLUMN discharge_records.doctor_id IS '书写医生ID';
COMMENT ON COLUMN discharge_records.doctor_name IS '书写医生姓名（冗余）';
COMMENT ON COLUMN discharge_records.write_time IS '书写时间';
COMMENT ON COLUMN discharge_records.sign_time IS '签名时间';
COMMENT ON COLUMN discharge_records.create_time IS '记录创建时间';

-- 手术记录
CREATE TABLE IF NOT EXISTS surgery_records (
    record_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    surgery_id VARCHAR(20),
    surgery_name VARCHAR(200) NOT NULL,
    surgery_code VARCHAR(20),           -- ICD-9-CM3 编码
    surgery_level VARCHAR(10),          -- I级/II级/III级/IV级
    pre_op_diagnosis TEXT,
    post_op_diagnosis TEXT,
    surgeon_id VARCHAR(20),
    surgeon_name VARCHAR(50),
    assistant1_id VARCHAR(20),
    assistant2_id VARCHAR(20),
    anesthesiologist_id VARCHAR(20),
    anesthesia_type VARCHAR(30),        -- 全麻/硬膜外/腰麻/局麻
    surgery_start_time TIMESTAMP,
    surgery_end_time TIMESTAMP,
    surgery_duration INTEGER,           -- 分钟
    incision_type VARCHAR(20),          -- I类/II类/III类/IV类
    operative_procedure TEXT,           -- 手术经过
    intraoperative_findings TEXT,       -- 术中发现
    blood_loss DECIMAL(8,1),            -- 失血量 ml
    blood_transfusion DECIMAL(8,1),     -- 输血量 ml
    specimen TEXT,                      -- 标本
    post_op_advice TEXT,
    status VARCHAR(10),                 -- 已排/术中/已完成/取消
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE surgery_records IS '手术记录：每次手术的完整记录（手术名称、术者、麻醉、过程、发现等）';
COMMENT ON COLUMN surgery_records.record_id IS '手术记录主键ID';
COMMENT ON COLUMN surgery_records.patient_id IS '患者ID';
COMMENT ON COLUMN surgery_records.visit_id IS '住院就诊ID';
COMMENT ON COLUMN surgery_records.surgery_id IS '手术业务ID（与排手术系统关联）';
COMMENT ON COLUMN surgery_records.surgery_name IS '手术名称';
COMMENT ON COLUMN surgery_records.surgery_code IS '手术 ICD-9-CM3 编码';
COMMENT ON COLUMN surgery_records.surgery_level IS '手术等级：I级/II级/III级/IV级（按风险递增）';
COMMENT ON COLUMN surgery_records.pre_op_diagnosis IS '术前诊断';
COMMENT ON COLUMN surgery_records.post_op_diagnosis IS '术后诊断';
COMMENT ON COLUMN surgery_records.surgeon_id IS '主刀医生ID';
COMMENT ON COLUMN surgery_records.surgeon_name IS '主刀医生姓名（冗余）';
COMMENT ON COLUMN surgery_records.assistant1_id IS '一助医生ID';
COMMENT ON COLUMN surgery_records.assistant2_id IS '二助医生ID';
COMMENT ON COLUMN surgery_records.anesthesiologist_id IS '麻醉医生ID';
COMMENT ON COLUMN surgery_records.anesthesia_type IS '麻醉方式：全麻/硬膜外/腰麻/局麻 等';
COMMENT ON COLUMN surgery_records.surgery_start_time IS '手术开始时间';
COMMENT ON COLUMN surgery_records.surgery_end_time IS '手术结束时间';
COMMENT ON COLUMN surgery_records.surgery_duration IS '手术持续时间（分钟）';
COMMENT ON COLUMN surgery_records.incision_type IS '切口类别：I类(无菌)/II类(清洁污染)/III类(污染)/IV类(感染)';
COMMENT ON COLUMN surgery_records.operative_procedure IS '手术经过（详细步骤）';
COMMENT ON COLUMN surgery_records.intraoperative_findings IS '术中发现';
COMMENT ON COLUMN surgery_records.blood_loss IS '术中失血量（ml）';
COMMENT ON COLUMN surgery_records.blood_transfusion IS '术中输血量（ml）';
COMMENT ON COLUMN surgery_records.specimen IS '送检标本';
COMMENT ON COLUMN surgery_records.post_op_advice IS '术后医嘱';
COMMENT ON COLUMN surgery_records.status IS '手术状态：已排/术中/已完成/取消';
COMMENT ON COLUMN surgery_records.create_time IS '记录创建时间';

-- 护理记录
CREATE TABLE IF NOT EXISTS nursing_records (
    record_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    record_time TIMESTAMP NOT NULL,
    shift VARCHAR(10),                  -- 白班/夜班
    nurse_id VARCHAR(20),
    nurse_name VARCHAR(50),
    temperature DECIMAL(4,1),
    pulse INTEGER,
    respiration INTEGER,
    blood_pressure VARCHAR(15),         -- 120/80
    spo2 DECIMAL(5,2),
    consciousness VARCHAR(20),          -- 清醒/嗜睡/昏迷/模糊
    intake_fluid DECIMAL(8,1),          -- 入量
    output_fluid DECIMAL(8,1),          -- 出量
    urine DECIMAL(8,1),
    stool_count INTEGER,
    special_care TEXT,                  -- 特殊护理
    skin_condition TEXT,                -- 皮肤情况
    drainage TEXT,                      -- 引流管情况
    medication TEXT,                    -- 用药记录
    observation TEXT,                   -- 病情观察
    nursing_measures TEXT,              -- 护理措施
    signature_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE nursing_records IS '护理记录：护士对住院患者生命体征、病情观察与护理措施的连续记录';
COMMENT ON COLUMN nursing_records.record_id IS '护理记录主键ID';
COMMENT ON COLUMN nursing_records.patient_id IS '患者ID';
COMMENT ON COLUMN nursing_records.visit_id IS '住院就诊ID';
COMMENT ON COLUMN nursing_records.record_time IS '记录时间';
COMMENT ON COLUMN nursing_records.shift IS '班次：白班/夜班';
COMMENT ON COLUMN nursing_records.nurse_id IS '护士ID';
COMMENT ON COLUMN nursing_records.nurse_name IS '护士姓名（冗余）';
COMMENT ON COLUMN nursing_records.temperature IS '体温（℃）';
COMMENT ON COLUMN nursing_records.pulse IS '脉搏（次/分）';
COMMENT ON COLUMN nursing_records.respiration IS '呼吸频率（次/分）';
COMMENT ON COLUMN nursing_records.blood_pressure IS '血压（如 120/80 mmHg）';
COMMENT ON COLUMN nursing_records.spo2 IS '血氧饱和度（%）';
COMMENT ON COLUMN nursing_records.consciousness IS '意识状态：清醒/嗜睡/昏迷/模糊';
COMMENT ON COLUMN nursing_records.intake_fluid IS '入量（ml）：饮水/输液等总入量';
COMMENT ON COLUMN nursing_records.output_fluid IS '出量（ml）：尿量+引流量等总出量';
COMMENT ON COLUMN nursing_records.urine IS '尿量（ml）';
COMMENT ON COLUMN nursing_records.stool_count IS '大便次数';
COMMENT ON COLUMN nursing_records.special_care IS '特殊护理记录';
COMMENT ON COLUMN nursing_records.skin_condition IS '皮肤情况（压疮、伤口等）';
COMMENT ON COLUMN nursing_records.drainage IS '引流管情况（部位、量、性质）';
COMMENT ON COLUMN nursing_records.medication IS '用药记录';
COMMENT ON COLUMN nursing_records.observation IS '病情观察';
COMMENT ON COLUMN nursing_records.nursing_measures IS '护理措施';
COMMENT ON COLUMN nursing_records.signature_time IS '签名时间';
COMMENT ON COLUMN nursing_records.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_emr_patient_id ON emr_documents(patient_id);
CREATE INDEX IF NOT EXISTS idx_emr_visit_id ON emr_documents(visit_id);
CREATE INDEX IF NOT EXISTS idx_progress_visit_id ON progress_notes(visit_id);
CREATE INDEX IF NOT EXISTS idx_admission_visit_id ON admission_records(visit_id);
CREATE INDEX IF NOT EXISTS idx_discharge_visit_id ON discharge_records(visit_id);
CREATE INDEX IF NOT EXISTS idx_surgery_visit_id ON surgery_records(visit_id);
CREATE INDEX IF NOT EXISTS idx_nursing_visit_id ON nursing_records(visit_id);
CREATE INDEX IF NOT EXISTS idx_nursing_record_time ON nursing_records(record_time);

-- ----- 批次1: 新增表 -----

-- 死亡记录
CREATE TABLE IF NOT EXISTS death_records (
    record_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    death_time TIMESTAMP NOT NULL,
    death_cause TEXT,                   -- 直接死因
    death_diagnosis TEXT,               -- 死亡诊断
    death_icd VARCHAR(20),
    autopsy_flag CHAR(1),               -- 是否尸检 Y/N
    autopsy_result TEXT,
    notify_family_time TIMESTAMP,
    doctor_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE death_records IS '死亡记录：患者死亡时的死亡文书（嘉和/海泰 EMR 均有独立死亡记录模块）';
COMMENT ON COLUMN death_records.record_id IS '死亡记录主键ID';
COMMENT ON COLUMN death_records.patient_id IS '患者ID';
COMMENT ON COLUMN death_records.visit_id IS '住院就诊ID';
COMMENT ON COLUMN death_records.death_time IS '死亡时间';
COMMENT ON COLUMN death_records.death_cause IS '直接死因';
COMMENT ON COLUMN death_records.death_diagnosis IS '死亡诊断';
COMMENT ON COLUMN death_records.death_icd IS '死亡诊断ICD编码';
COMMENT ON COLUMN death_records.autopsy_flag IS '是否尸检：Y=是 / N=否';
COMMENT ON COLUMN death_records.autopsy_result IS '尸检结果';
COMMENT ON COLUMN death_records.notify_family_time IS '通知家属时间';
COMMENT ON COLUMN death_records.doctor_id IS '经治医生ID';
COMMENT ON COLUMN death_records.create_time IS '记录创建时间';

-- 会诊记录
CREATE TABLE IF NOT EXISTS consultation_records (
    consultation_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    consultation_type VARCHAR(20),      -- 院内会诊/院外会诊/急诊会诊/MDT
    request_dept_id VARCHAR(20),
    request_doctor_id VARCHAR(20),
    requested_dept_id VARCHAR(20) NOT NULL,
    requested_doctor_id VARCHAR(20),
    request_time TIMESTAMP,
    consultation_time TIMESTAMP,
    consultation_opinion TEXT,
    urgency VARCHAR(10),                -- 普通/紧急
    status VARCHAR(20),                 -- 待会诊/已完成/已取消
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE consultation_records IS '会诊记录：院内/院外会诊的完整记录（EMR 核心文书之一）';
COMMENT ON COLUMN consultation_records.consultation_id IS '会诊主键ID';
COMMENT ON COLUMN consultation_records.patient_id IS '患者ID';
COMMENT ON COLUMN consultation_records.visit_id IS '就诊ID';
COMMENT ON COLUMN consultation_records.consultation_type IS '会诊类型：院内会诊/院外会诊/急诊会诊/MDT多学科会诊';
COMMENT ON COLUMN consultation_records.request_dept_id IS '申请科室ID';
COMMENT ON COLUMN consultation_records.request_doctor_id IS '申请医生ID';
COMMENT ON COLUMN consultation_records.requested_dept_id IS '受邀科室ID';
COMMENT ON COLUMN consultation_records.requested_doctor_id IS '受邀医生ID';
COMMENT ON COLUMN consultation_records.request_time IS '申请时间';
COMMENT ON COLUMN consultation_records.consultation_time IS '会诊完成时间';
COMMENT ON COLUMN consultation_records.consultation_opinion IS '会诊意见';
COMMENT ON COLUMN consultation_records.urgency IS '紧急程度：普通/紧急';
COMMENT ON COLUMN consultation_records.status IS '会诊状态：待会诊/已完成/已取消';
COMMENT ON COLUMN consultation_records.create_time IS '记录创建时间';

-- EMR 结构化诊断明细
CREATE TABLE IF NOT EXISTS emr_diagnoses (
    diagnosis_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    diagnosis_type VARCHAR(20),         -- 入院/出院/术前/术后/日常/门急诊
    seq_no INTEGER DEFAULT 1,
    diagnosis_name TEXT,
    diagnosis_icd VARCHAR(20),
    diagnosis_time TIMESTAMP,
    doctor_id VARCHAR(20),
    is_principal CHAR(1),               -- 是否主诊断 Y/N
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE emr_diagnoses IS 'EMR 诊断明细：EMR 系统内的结构化诊断记录（与病案诊断不同，这是临床过程诊断）';
COMMENT ON COLUMN emr_diagnoses.diagnosis_id IS '诊断主键ID';
COMMENT ON COLUMN emr_diagnoses.patient_id IS '患者ID';
COMMENT ON COLUMN emr_diagnoses.visit_id IS '就诊ID';
COMMENT ON COLUMN emr_diagnoses.diagnosis_type IS '诊断类型：入院诊断/出院诊断/术前诊断/术后诊断/日常诊断/门急诊诊断';
COMMENT ON COLUMN emr_diagnoses.seq_no IS '诊断顺序号';
COMMENT ON COLUMN emr_diagnoses.diagnosis_name IS '诊断名称';
COMMENT ON COLUMN emr_diagnoses.diagnosis_icd IS '诊断ICD-10编码';
COMMENT ON COLUMN emr_diagnoses.diagnosis_time IS '诊断时间';
COMMENT ON COLUMN emr_diagnoses.doctor_id IS '诊断医生ID';
COMMENT ON COLUMN emr_diagnoses.is_principal IS '是否主诊断：Y=是 / N=否';
COMMENT ON COLUMN emr_diagnoses.create_time IS '记录创建时间';

-- ----- 批次1: 现有表补充字段 -----

ALTER TABLE emr_documents ADD COLUMN IF NOT EXISTS page_no INTEGER;
ALTER TABLE emr_documents ADD COLUMN IF NOT EXISTS print_status VARCHAR(20);
ALTER TABLE emr_documents ADD COLUMN IF NOT EXISTS archive_status VARCHAR(20);
ALTER TABLE emr_documents ADD COLUMN IF NOT EXISTS archive_time TIMESTAMP;
ALTER TABLE emr_documents ADD COLUMN IF NOT EXISTS archiver_id VARCHAR(20);
ALTER TABLE emr_documents ADD COLUMN IF NOT EXISTS template_id VARCHAR(20);

ALTER TABLE nursing_records ADD COLUMN IF NOT EXISTS pupil_size_left VARCHAR(10);
ALTER TABLE nursing_records ADD COLUMN IF NOT EXISTS pupil_size_right VARCHAR(10);
ALTER TABLE nursing_records ADD COLUMN IF NOT EXISTS light_reflex VARCHAR(20);
ALTER TABLE nursing_records ADD COLUMN IF NOT EXISTS pain_score INTEGER;
ALTER TABLE nursing_records ADD COLUMN IF NOT EXISTS fall_score INTEGER;
ALTER TABLE nursing_records ADD COLUMN IF NOT EXISTS braden_score INTEGER;
ALTER TABLE nursing_records ADD COLUMN IF NOT EXISTS catheter_care TEXT;
ALTER TABLE nursing_records ADD COLUMN IF NOT EXISTS wound_care TEXT;

ALTER TABLE admission_records ADD COLUMN IF NOT EXISTS menstrual_history TEXT;
ALTER TABLE admission_records ADD COLUMN IF NOT EXISTS obstetric_history TEXT;
ALTER TABLE admission_records ADD COLUMN IF NOT EXISTS psychological_status VARCHAR(50);
ALTER TABLE admission_records ADD COLUMN IF NOT EXISTS nutrition_status VARCHAR(50);
ALTER TABLE admission_records ADD COLUMN IF NOT EXISTS fall_risk VARCHAR(20);

-- 新增表索引
CREATE INDEX IF NOT EXISTS idx_death_visit_id ON death_records(visit_id);
CREATE INDEX IF NOT EXISTS idx_consultation_visit_id ON consultation_records(visit_id);
CREATE INDEX IF NOT EXISTS idx_emr_diag_visit_id ON emr_diagnoses(visit_id);

-- ----- 批次2: 新增表 -----

-- 输血记录
CREATE TABLE IF NOT EXISTS transfusion_records (
    transfusion_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    blood_type VARCHAR(10),
    blood_product VARCHAR(50),          -- 红细胞/血浆/血小板/冷沉淀
    volume_ml INTEGER,
    blood_bag_no VARCHAR(30),           -- 血袋号
    transfusion_start_time TIMESTAMP,
    transfusion_end_time TIMESTAMP,
    transfusion_reaction CHAR(1),       -- 有无不良反应 Y/N
    reaction_desc TEXT,
    pre_temp DECIMAL(4,1),              -- 输血前体温
    post_temp DECIMAL(4,1),             -- 输血后体温
    pre_bp VARCHAR(15),
    post_bp VARCHAR(15),
    pre_hr INTEGER,
    post_hr INTEGER,
    nurse_id VARCHAR(20),
    doctor_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE transfusion_records IS '输血记录：独立输血文书，含输血前评估和输血后评价';
COMMENT ON COLUMN transfusion_records.transfusion_id IS '输血记录主键ID';
COMMENT ON COLUMN transfusion_records.patient_id IS '患者ID';
COMMENT ON COLUMN transfusion_records.visit_id IS '就诊ID';
COMMENT ON COLUMN transfusion_records.blood_type IS '血型';
COMMENT ON COLUMN transfusion_records.blood_product IS '血液成分：红细胞/血浆/血小板/冷沉淀/全血';
COMMENT ON COLUMN transfusion_records.volume_ml IS '输血量（ml）';
COMMENT ON COLUMN transfusion_records.blood_bag_no IS '血袋号';
COMMENT ON COLUMN transfusion_records.transfusion_start_time IS '输血开始时间';
COMMENT ON COLUMN transfusion_records.transfusion_end_time IS '输血结束时间';
COMMENT ON COLUMN transfusion_records.transfusion_reaction IS '有无输血反应：Y=有 / N=无';
COMMENT ON COLUMN transfusion_records.reaction_desc IS '输血反应描述';
COMMENT ON COLUMN transfusion_records.pre_temp IS '输血前体温（℃）';
COMMENT ON COLUMN transfusion_records.post_temp IS '输血后体温（℃）';
COMMENT ON COLUMN transfusion_records.pre_bp IS '输血前血压';
COMMENT ON COLUMN transfusion_records.post_bp IS '输血后血压';
COMMENT ON COLUMN transfusion_records.pre_hr IS '输血前心率';
COMMENT ON COLUMN transfusion_records.post_hr IS '输血后心率';
COMMENT ON COLUMN transfusion_records.nurse_id IS '执行护士ID';
COMMENT ON COLUMN transfusion_records.doctor_id IS '主管医生ID';
COMMENT ON COLUMN transfusion_records.create_time IS '记录创建时间';

-- 知情同意书
CREATE TABLE IF NOT EXISTS informed_consents (
    consent_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    consent_type VARCHAR(50),           -- 手术同意/麻醉同意/输血同意/病危通知/特殊检查/侵入性操作
    consent_content TEXT,
    signer_name VARCHAR(50),            -- 签字人姓名
    signer_relation VARCHAR(20),        -- 本人/配偶/子女/父母/其他
    signer_phone VARCHAR(20),
    sign_time TIMESTAMP,
    doctor_id VARCHAR(20),              -- 告知医生
    witness_name VARCHAR(50),           -- 见证人
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE informed_consents IS '知情同意书：手术同意书、输血同意书、病危通知书等法律文书记录';
COMMENT ON COLUMN informed_consents.consent_id IS '同意书主键ID';
COMMENT ON COLUMN informed_consents.patient_id IS '患者ID';
COMMENT ON COLUMN informed_consents.visit_id IS '就诊ID';
COMMENT ON COLUMN informed_consents.consent_type IS '同意书类型：手术同意/麻醉同意/输血同意/病危通知/特殊检查/侵入性操作';
COMMENT ON COLUMN informed_consents.consent_content IS '同意书内容摘要';
COMMENT ON COLUMN informed_consents.signer_name IS '签字人姓名';
COMMENT ON COLUMN informed_consents.signer_relation IS '与患者关系：本人/配偶/子女/父母/其他';
COMMENT ON COLUMN informed_consents.signer_phone IS '签字人联系电话';
COMMENT ON COLUMN informed_consents.sign_time IS '签字时间';
COMMENT ON COLUMN informed_consents.doctor_id IS '告知医生ID';
COMMENT ON COLUMN informed_consents.witness_name IS '见证人姓名';
COMMENT ON COLUMN informed_consents.create_time IS '记录创建时间';

-- 护理评估单
CREATE TABLE IF NOT EXISTS nursing_assessments (
    assessment_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    assessment_type VARCHAR(30),        -- 入院/跌倒/压疮/VTE/疼痛/营养
    assessment_time TIMESTAMP,
    total_score INTEGER,
    risk_level VARCHAR(20),             -- 低/中/高/极高
    risk_factors TEXT,
    preventive_measures TEXT,
    nurse_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE nursing_assessments IS '护理评估单：入院评估、跌倒风险评估、压疮风险评估、VTE评估、疼痛评估等';
COMMENT ON COLUMN nursing_assessments.assessment_id IS '评估主键ID';
COMMENT ON COLUMN nursing_assessments.patient_id IS '患者ID';
COMMENT ON COLUMN nursing_assessments.visit_id IS '就诊ID';
COMMENT ON COLUMN nursing_assessments.assessment_type IS '评估类型：入院评估/跌倒风险评估/压疮风险评估/VTE风险评估/疼痛评估/营养评估';
COMMENT ON COLUMN nursing_assessments.assessment_time IS '评估时间';
COMMENT ON COLUMN nursing_assessments.total_score IS '评估总分';
COMMENT ON COLUMN nursing_assessments.risk_level IS '风险等级：低/中/高/极高';
COMMENT ON COLUMN nursing_assessments.risk_factors IS '风险因素';
COMMENT ON COLUMN nursing_assessments.preventive_measures IS '预防措施';
COMMENT ON COLUMN nursing_assessments.nurse_id IS '评估护士ID';
COMMENT ON COLUMN nursing_assessments.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_transfusion_visit_id ON transfusion_records(visit_id);
CREATE INDEX IF NOT EXISTS idx_consent_visit_id ON informed_consents(visit_id);
CREATE INDEX IF NOT EXISTS idx_nursing_assess_visit_id ON nursing_assessments(visit_id);
