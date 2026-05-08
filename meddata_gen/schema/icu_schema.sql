-- ============================================================
-- ICU 监护数据库表结构
-- 参考: 飞利浦/迈瑞/GE/理邦 主流监护系统数据结构
-- ============================================================

-- ICU入科记录
CREATE TABLE IF NOT EXISTS icu_admissions (
    icu_admission_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20) NOT NULL,
    hospital_visit_id VARCHAR(20),      -- 关联住院记录
    bed_id VARCHAR(20),
    bed_no VARCHAR(10),
    admission_time TIMESTAMP NOT NULL,
    admission_source VARCHAR(50),       -- 急诊/手术室/病房/外院转入
    admission_type VARCHAR(20),         -- 计划入ICU/抢救入ICU/术后入ICU
    primary_diagnosis TEXT,
    secondary_diagnosis TEXT,
    apacheii_score INTEGER,             -- APACHE II评分
    sofa_score INTEGER,                 -- SOFA评分
    gcs_score INTEGER,                  -- GCS评分
    admission_weight DECIMAL(6,2),      -- 入科体重 kg
    height DECIMAL(5,1),                -- 身高 cm
    bmi DECIMAL(5,2),
    expected_los DECIMAL(4,1),          -- 预计住院天数
    discharge_time TIMESTAMP,
    discharge_status VARCHAR(20),       -- 转病房/死亡/自动出院/转院
    discharge_destination VARCHAR(50),  -- 出院去向
    actual_los DECIMAL(5,1),            -- 实际住院天数
    death_flag CHAR(1),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE icu_admissions IS 'ICU入科记录：每次进入ICU的入科评估与转出信息';
COMMENT ON COLUMN icu_admissions.icu_admission_id IS 'ICU入科主键ID（一次ICU住院全过程）';
COMMENT ON COLUMN icu_admissions.patient_id IS '患者ID（关联 his_db.patients.patient_id）';
COMMENT ON COLUMN icu_admissions.visit_id IS '住院就诊ID';
COMMENT ON COLUMN icu_admissions.hospital_visit_id IS '关联住院记录ID（冗余字段，便于追溯）';
COMMENT ON COLUMN icu_admissions.bed_id IS 'ICU床位ID';
COMMENT ON COLUMN icu_admissions.bed_no IS 'ICU床位号';
COMMENT ON COLUMN icu_admissions.admission_time IS '入ICU时间';
COMMENT ON COLUMN icu_admissions.admission_source IS '入科来源：急诊/手术室/病房/外院转入';
COMMENT ON COLUMN icu_admissions.admission_type IS '入科类型：计划入ICU/抢救入ICU/术后入ICU';
COMMENT ON COLUMN icu_admissions.primary_diagnosis IS '主要诊断';
COMMENT ON COLUMN icu_admissions.secondary_diagnosis IS '次要诊断';
COMMENT ON COLUMN icu_admissions.apacheii_score IS 'APACHE II 评分（急性生理与慢性健康评分，分数越高病情越重）';
COMMENT ON COLUMN icu_admissions.sofa_score IS 'SOFA 评分（脓毒症相关器官功能衰竭评估）';
COMMENT ON COLUMN icu_admissions.gcs_score IS 'GCS 评分（格拉斯哥昏迷量表，3-15）';
COMMENT ON COLUMN icu_admissions.admission_weight IS '入科体重（kg）';
COMMENT ON COLUMN icu_admissions.height IS '身高（cm）';
COMMENT ON COLUMN icu_admissions.bmi IS 'BMI 体重指数';
COMMENT ON COLUMN icu_admissions.expected_los IS '预计住ICU天数';
COMMENT ON COLUMN icu_admissions.discharge_time IS '出ICU时间（NULL 表示在科）';
COMMENT ON COLUMN icu_admissions.discharge_status IS '转出状态：转病房/死亡/自动出院/转院';
COMMENT ON COLUMN icu_admissions.discharge_destination IS '出科去向（具体科室或医院）';
COMMENT ON COLUMN icu_admissions.actual_los IS '实际住ICU天数';
COMMENT ON COLUMN icu_admissions.death_flag IS '是否死亡：Y/N';
COMMENT ON COLUMN icu_admissions.create_time IS '记录创建时间';

-- 监护仪数据 (时序数据，5分钟间隔)
CREATE TABLE IF NOT EXISTS monitoring_data (
    data_id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    icu_admission_id VARCHAR(20),
    visit_id VARCHAR(20),
    bed_id VARCHAR(20),
    monitor_time TIMESTAMP NOT NULL,
    hr INTEGER,                         -- 心率 bpm
    sbp INTEGER,                        -- 收缩压 mmHg
    dbp INTEGER,                        -- 舒张压 mmHg
    map INTEGER,                        -- 平均动脉压 mmHg
    spo2 DECIMAL(5,2),                  -- 血氧饱和度 %
    rr INTEGER,                         -- 呼吸频率 次/分
    temp DECIMAL(4,1),                  -- 体温 °C
    cvp INTEGER,                        -- 中心静脉压 mmHg
    pap_systolic INTEGER,               -- 肺动脉收缩压
    pap_diastolic INTEGER,              -- 肺动脉舒张压
    co DECIMAL(4,2),                    -- 心输出量 L/min
    ci DECIMAL(4,2),                    -- 心指数
    sv DECIMAL(5,1),                    -- 每搏量
    svv DECIMAL(5,2),                   -- 每搏变异度 %
    pvp DECIMAL(5,2),                   -- 脉压变异度 %
    etco2 INTEGER,                      -- 呼气末CO2 mmHg
    fio2 DECIMAL(5,2),                  -- 吸入氧浓度 %
    peep INTEGER,                       -- PEEP cmH2O
    pip INTEGER,                        -- 峰压 cmH2O
    plateau_pressure INTEGER,           -- 平台压
    tv_set INTEGER,                     -- 设定潮气量 ml
    tv_actual INTEGER,                  -- 实际潮气量 ml
    mv DECIMAL(5,2),                    -- 分钟通气量 L/min
    ie_ratio VARCHAR(10),               -- 吸呼比
    icp INTEGER,                        -- 颅内压 mmHg
    cpp INTEGER,                        -- 脑灌注压 mmHg
    bis DECIMAL(4,1),                   -- 脑电双频指数
    urine_output DECIMAL(6,1),          -- 尿量 ml/h
    data_source VARCHAR(20),            -- 监护仪/呼吸机/血气/输液泵
    device_id VARCHAR(20),
    alarm_flag CHAR(1),                 -- 该时间点是否有报警
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE monitoring_data IS 'ICU监护仪时序数据（典型5分钟间隔）：心电监护、呼吸机、血流动力学等参数的快照';
COMMENT ON COLUMN monitoring_data.data_id IS '监护数据自增主键';
COMMENT ON COLUMN monitoring_data.patient_id IS '患者ID';
COMMENT ON COLUMN monitoring_data.icu_admission_id IS '关联ICU入科ID';
COMMENT ON COLUMN monitoring_data.visit_id IS '住院就诊ID';
COMMENT ON COLUMN monitoring_data.bed_id IS '床位ID';
COMMENT ON COLUMN monitoring_data.monitor_time IS '监护数据时间戳';
COMMENT ON COLUMN monitoring_data.hr IS '心率（bpm 次/分）';
COMMENT ON COLUMN monitoring_data.sbp IS '收缩压（mmHg）';
COMMENT ON COLUMN monitoring_data.dbp IS '舒张压（mmHg）';
COMMENT ON COLUMN monitoring_data.map IS '平均动脉压（mmHg）';
COMMENT ON COLUMN monitoring_data.spo2 IS '血氧饱和度（%）';
COMMENT ON COLUMN monitoring_data.rr IS '呼吸频率（次/分）';
COMMENT ON COLUMN monitoring_data.temp IS '体温（℃）';
COMMENT ON COLUMN monitoring_data.cvp IS '中心静脉压（mmHg）';
COMMENT ON COLUMN monitoring_data.pap_systolic IS '肺动脉收缩压（mmHg）';
COMMENT ON COLUMN monitoring_data.pap_diastolic IS '肺动脉舒张压（mmHg）';
COMMENT ON COLUMN monitoring_data.co IS '心输出量（L/min）';
COMMENT ON COLUMN monitoring_data.ci IS '心指数（L/min/m²）';
COMMENT ON COLUMN monitoring_data.sv IS '每搏量（ml）';
COMMENT ON COLUMN monitoring_data.svv IS '每搏变异度（%）';
COMMENT ON COLUMN monitoring_data.pvp IS '脉压变异度（%）';
COMMENT ON COLUMN monitoring_data.etco2 IS '呼气末二氧化碳分压（mmHg）';
COMMENT ON COLUMN monitoring_data.fio2 IS '吸入氧浓度（%）';
COMMENT ON COLUMN monitoring_data.peep IS '呼气末正压 PEEP（cmH2O）';
COMMENT ON COLUMN monitoring_data.pip IS '气道峰压（cmH2O）';
COMMENT ON COLUMN monitoring_data.plateau_pressure IS '平台压（cmH2O）';
COMMENT ON COLUMN monitoring_data.tv_set IS '设定潮气量（ml）';
COMMENT ON COLUMN monitoring_data.tv_actual IS '实际潮气量（ml）';
COMMENT ON COLUMN monitoring_data.mv IS '分钟通气量（L/min）';
COMMENT ON COLUMN monitoring_data.ie_ratio IS '吸呼比（如 1:2）';
COMMENT ON COLUMN monitoring_data.icp IS '颅内压（mmHg）';
COMMENT ON COLUMN monitoring_data.cpp IS '脑灌注压（mmHg）';
COMMENT ON COLUMN monitoring_data.bis IS '脑电双频指数（BIS，0-100）';
COMMENT ON COLUMN monitoring_data.urine_output IS '小时尿量（ml/h）';
COMMENT ON COLUMN monitoring_data.data_source IS '数据来源：监护仪/呼吸机/血气/输液泵';
COMMENT ON COLUMN monitoring_data.device_id IS '产生数据的设备ID';
COMMENT ON COLUMN monitoring_data.alarm_flag IS '该时间点是否有报警：Y/N';
COMMENT ON COLUMN monitoring_data.create_time IS '记录创建时间';

-- 报警记录
CREATE TABLE IF NOT EXISTS alarms (
    alarm_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    icu_admission_id VARCHAR(20),
    visit_id VARCHAR(20),
    bed_id VARCHAR(20),
    alarm_time TIMESTAMP NOT NULL,
    alarm_level VARCHAR(10),            -- 高/中/低/提示
    alarm_type VARCHAR(50),             -- 心率异常/血压异常/血氧异常/呼吸异常...
    parameter_name VARCHAR(50),         -- 报警参数名
    parameter_value VARCHAR(20),        -- 报警时参数值
    threshold_low VARCHAR(20),          -- 低限
    threshold_high VARCHAR(20),         -- 高限
    alarm_message TEXT,
    duration_seconds INTEGER,           -- 报警持续秒数
    handled_flag CHAR(1),               -- 是否已处理
    handler_id VARCHAR(20),
    handler_name VARCHAR(50),
    handle_time TIMESTAMP,
    handle_action TEXT,                 -- 处理措施
    status VARCHAR(10),                 -- 未处理/已处理/已确认
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE alarms IS 'ICU报警记录：监护设备触发的报警事件及医护处理情况';
COMMENT ON COLUMN alarms.alarm_id IS '报警主键ID';
COMMENT ON COLUMN alarms.patient_id IS '患者ID';
COMMENT ON COLUMN alarms.icu_admission_id IS '关联ICU入科ID';
COMMENT ON COLUMN alarms.visit_id IS '住院就诊ID';
COMMENT ON COLUMN alarms.bed_id IS '床位ID';
COMMENT ON COLUMN alarms.alarm_time IS '报警发生时间';
COMMENT ON COLUMN alarms.alarm_level IS '报警等级：高/中/低/提示';
COMMENT ON COLUMN alarms.alarm_type IS '报警类型：心率异常/血压异常/血氧异常/呼吸异常 等';
COMMENT ON COLUMN alarms.parameter_name IS '报警参数名（如 HR、SpO2）';
COMMENT ON COLUMN alarms.parameter_value IS '报警时参数值';
COMMENT ON COLUMN alarms.threshold_low IS '低报警阈值';
COMMENT ON COLUMN alarms.threshold_high IS '高报警阈值';
COMMENT ON COLUMN alarms.alarm_message IS '报警消息内容';
COMMENT ON COLUMN alarms.duration_seconds IS '报警持续秒数';
COMMENT ON COLUMN alarms.handled_flag IS '是否已处理：Y/N';
COMMENT ON COLUMN alarms.handler_id IS '处理人ID';
COMMENT ON COLUMN alarms.handler_name IS '处理人姓名';
COMMENT ON COLUMN alarms.handle_time IS '处理时间';
COMMENT ON COLUMN alarms.handle_action IS '处理措施描述';
COMMENT ON COLUMN alarms.status IS '报警状态：未处理/已处理/已确认';
COMMENT ON COLUMN alarms.create_time IS '记录创建时间';

-- 血气分析
CREATE TABLE IF NOT EXISTS blood_gas (
    gas_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    icu_admission_id VARCHAR(20),
    visit_id VARCHAR(20),
    specimen_type VARCHAR(20),          -- 动脉血/静脉血/混合静脉血
    collect_time TIMESTAMP,
    ph DECIMAL(4,2),
    pco2 DECIMAL(5,1),                  -- mmHg
    po2 DECIMAL(5,1),                   -- mmHg
    hco3 DECIMAL(5,1),                  -- mmol/L
    be DECIMAL(5,1),                    -- 碱剩余 mmol/L
    sao2 DECIMAL(5,2),                  -- %
    lac DECIMAL(5,2),                   -- 乳酸 mmol/L
    glucose DECIMAL(5,1),               -- 血糖 mmol/L
    potassium DECIMAL(4,1),             -- 钾 mmol/L
    sodium DECIMAL(5,1),                -- 钠 mmol/L
    chloride DECIMAL(5,1),              -- 氯 mmol/L
    calcium DECIMAL(4,2),               -- 钙 mmol/L
    hemoglobin DECIMAL(4,1),            -- 血红蛋白 g/dL
    hct DECIMAL(5,2),                   -- 红细胞压积 %
    fio2 DECIMAL(5,2),                  -- 吸氧浓度 %
    temp DECIMAL(4,1),                  -- 标本温度
    vent_mode VARCHAR(30),              -- 通气模式
    operator_id VARCHAR(20),
    operator_name VARCHAR(50),
    verify_flag CHAR(1),                -- 是否已审核
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE blood_gas IS '血气分析：ICU床旁血气分析结果（动脉/静脉血气）';
COMMENT ON COLUMN blood_gas.gas_id IS '血气主键ID';
COMMENT ON COLUMN blood_gas.patient_id IS '患者ID';
COMMENT ON COLUMN blood_gas.icu_admission_id IS '关联ICU入科ID';
COMMENT ON COLUMN blood_gas.visit_id IS '住院就诊ID';
COMMENT ON COLUMN blood_gas.specimen_type IS '标本类型：动脉血/静脉血/混合静脉血';
COMMENT ON COLUMN blood_gas.collect_time IS '采血时间';
COMMENT ON COLUMN blood_gas.ph IS 'pH 值（参考值 7.35~7.45）';
COMMENT ON COLUMN blood_gas.pco2 IS '二氧化碳分压 PaCO2（mmHg）';
COMMENT ON COLUMN blood_gas.po2 IS '氧分压 PaO2（mmHg）';
COMMENT ON COLUMN blood_gas.hco3 IS '碳酸氢根 HCO3-（mmol/L）';
COMMENT ON COLUMN blood_gas.be IS '碱剩余 BE（mmol/L）';
COMMENT ON COLUMN blood_gas.sao2 IS '动脉血氧饱和度 SaO2（%）';
COMMENT ON COLUMN blood_gas.lac IS '乳酸（mmol/L）';
COMMENT ON COLUMN blood_gas.glucose IS '血糖（mmol/L）';
COMMENT ON COLUMN blood_gas.potassium IS '钾离子（mmol/L）';
COMMENT ON COLUMN blood_gas.sodium IS '钠离子（mmol/L）';
COMMENT ON COLUMN blood_gas.chloride IS '氯离子（mmol/L）';
COMMENT ON COLUMN blood_gas.calcium IS '钙离子（mmol/L）';
COMMENT ON COLUMN blood_gas.hemoglobin IS '血红蛋白（g/dL）';
COMMENT ON COLUMN blood_gas.hct IS '红细胞压积 Hct（%）';
COMMENT ON COLUMN blood_gas.fio2 IS '采血时吸入氧浓度（%）';
COMMENT ON COLUMN blood_gas.temp IS '标本温度（℃）';
COMMENT ON COLUMN blood_gas.vent_mode IS '通气模式（如 SIMV / PSV / CPAP）';
COMMENT ON COLUMN blood_gas.operator_id IS '操作人ID';
COMMENT ON COLUMN blood_gas.operator_name IS '操作人姓名';
COMMENT ON COLUMN blood_gas.verify_flag IS '是否已审核：Y/N';
COMMENT ON COLUMN blood_gas.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_icuadm_patient_id ON icu_admissions(patient_id);
CREATE INDEX IF NOT EXISTS idx_icuadm_visit_id ON icu_admissions(visit_id);
CREATE INDEX IF NOT EXISTS idx_monitor_patient_id ON monitoring_data(patient_id);
CREATE INDEX IF NOT EXISTS idx_monitor_time ON monitoring_data(monitor_time);
CREATE INDEX IF NOT EXISTS idx_alarm_patient_id ON alarms(patient_id);
CREATE INDEX IF NOT EXISTS idx_alarm_time ON alarms(alarm_time);
CREATE INDEX IF NOT EXISTS idx_bloodgas_patient_id ON blood_gas(patient_id);
CREATE INDEX IF NOT EXISTS idx_bloodgas_collect_time ON blood_gas(collect_time);

-- ----- 批次1: 新增表 -----

-- 呼吸机参数设置
CREATE TABLE IF NOT EXISTS ventilator_settings (
    setting_id VARCHAR(20) PRIMARY KEY,
    icu_admission_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    setting_time TIMESTAMP NOT NULL,
    vent_mode VARCHAR(30),              -- SIMV/PSV/PRVC/AC/CPAP/ECMO
    tv_set INTEGER,                     -- 设定潮气量 ml
    rr_set INTEGER,                     -- 设定呼吸频率 次/分
    fio2_set DECIMAL(5,2),              -- 设定吸入氧浓度 %
    peep_set INTEGER,                   -- 设定PEEP cmH2O
    pressure_support INTEGER,           -- 压力支持 cmH2O
    ie_ratio VARCHAR(10),               -- 吸呼比
    trigger_sensitivity DECIMAL(4,1),   -- 触发灵敏度
    plateau_pressure INTEGER,
    pip INTEGER,
    operator_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ventilator_settings IS '呼吸机参数设置：呼吸机设置记录（飞利浦/迈瑞监护系统均有独立呼吸机参数表）';
COMMENT ON COLUMN ventilator_settings.setting_id IS '设置记录主键ID';
COMMENT ON COLUMN ventilator_settings.icu_admission_id IS '关联ICU入科ID';
COMMENT ON COLUMN ventilator_settings.patient_id IS '患者ID';
COMMENT ON COLUMN ventilator_settings.visit_id IS '就诊ID';
COMMENT ON COLUMN ventilator_settings.setting_time IS '设置时间';
COMMENT ON COLUMN ventilator_settings.vent_mode IS '通气模式：SIMV/PSV/PRVC/AC/CPAP/ECMO/Spontaneous';
COMMENT ON COLUMN ventilator_settings.tv_set IS '设定潮气量（ml）';
COMMENT ON COLUMN ventilator_settings.rr_set IS '设定呼吸频率（次/分）';
COMMENT ON COLUMN ventilator_settings.fio2_set IS '设定吸入氧浓度（%）';
COMMENT ON COLUMN ventilator_settings.peep_set IS '设定呼气末正压（cmH2O）';
COMMENT ON COLUMN ventilator_settings.pressure_support IS '压力支持（cmH2O）';
COMMENT ON COLUMN ventilator_settings.ie_ratio IS '吸呼比（如 1:2）';
COMMENT ON COLUMN ventilator_settings.trigger_sensitivity IS '触发灵敏度';
COMMENT ON COLUMN ventilator_settings.plateau_pressure IS '平台压（cmH2O）';
COMMENT ON COLUMN ventilator_settings.pip IS '峰压（cmH2O）';
COMMENT ON COLUMN ventilator_settings.operator_id IS '操作人ID';
COMMENT ON COLUMN ventilator_settings.create_time IS '记录创建时间';

-- 出入量明细
CREATE TABLE IF NOT EXISTS fluid_balance (
    balance_id VARCHAR(20) PRIMARY KEY,
    icu_admission_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    record_date DATE NOT NULL,
    intake_oral DECIMAL(8,1),           -- 口服入量 ml
    intake_iv DECIMAL(8,1),             -- 静脉入量 ml
    intake_other DECIMAL(8,1),          -- 其他入量 ml
    output_urine DECIMAL(8,1),          -- 尿量 ml
    output_drainage DECIMAL(8,1),       -- 引流量 ml
    output_other DECIMAL(8,1),          -- 其他出量 ml
    balance_total DECIMAL(8,1),         -- 出入量差值 ml
    nurse_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE fluid_balance IS '出入量明细：24小时出入量汇总（ICU 每日必做护理记录）';
COMMENT ON COLUMN fluid_balance.balance_id IS '出入量主键ID';
COMMENT ON COLUMN fluid_balance.icu_admission_id IS '关联ICU入科ID';
COMMENT ON COLUMN fluid_balance.patient_id IS '患者ID';
COMMENT ON COLUMN fluid_balance.visit_id IS '就诊ID';
COMMENT ON COLUMN fluid_balance.record_date IS '记录日期';
COMMENT ON COLUMN fluid_balance.intake_oral IS '口服入量（ml）';
COMMENT ON COLUMN fluid_balance.intake_iv IS '静脉入量（ml）';
COMMENT ON COLUMN fluid_balance.intake_other IS '其他入量（ml）';
COMMENT ON COLUMN fluid_balance.output_urine IS '尿量（ml）';
COMMENT ON COLUMN fluid_balance.output_drainage IS '引流量（ml）';
COMMENT ON COLUMN fluid_balance.output_other IS '其他出量（ml）';
COMMENT ON COLUMN fluid_balance.balance_total IS '出入量差值（ml，正=正平衡，负=负平衡）';
COMMENT ON COLUMN fluid_balance.nurse_id IS '记录护士ID';
COMMENT ON COLUMN fluid_balance.create_time IS '记录创建时间';

-- ----- 批次1: 现有表补充字段 -----

ALTER TABLE icu_admissions ADD COLUMN IF NOT EXISTS mechanical_ventilation_flag CHAR(1);
ALTER TABLE icu_admissions ADD COLUMN IF NOT EXISTS renal_replacement_flag CHAR(1);
ALTER TABLE icu_admissions ADD COLUMN IF NOT EXISTS vasoactive_drugs TEXT;
ALTER TABLE icu_admissions ADD COLUMN IF NOT EXISTS nutrition_route VARCHAR(20);

ALTER TABLE blood_gas ADD COLUMN IF NOT EXISTS ag DECIMAL(5,1);
ALTER TABLE blood_gas ADD COLUMN IF NOT EXISTS osm DECIMAL(6,1);
ALTER TABLE blood_gas ADD COLUMN IF NOT EXISTS pao2_fio2_ratio DECIMAL(6,1);

-- 新增表索引
CREATE INDEX IF NOT EXISTS idx_vent_icuadm_id ON ventilator_settings(icu_admission_id);
CREATE INDEX IF NOT EXISTS idx_fluid_icuadm_id ON fluid_balance(icu_admission_id);
CREATE INDEX IF NOT EXISTS idx_fluid_record_date ON fluid_balance(record_date);

-- ----- 批次2: 新增表 -----

-- CRRT 记录
CREATE TABLE IF NOT EXISTS crrt_records (
    crrt_id VARCHAR(20) PRIMARY KEY,
    icu_admission_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    treatment_mode VARCHAR(20),         -- CVVH/CVVHD/CVVHDF/SCUF
    blood_flow DECIMAL(5,1),            -- ml/min
    dialysate_flow DECIMAL(6,1),        -- ml/h
    replacement_flow DECIMAL(6,1),      -- ml/h
    anticoagulant VARCHAR(50),          -- 抗凝剂
    anticoagulant_dose VARCHAR(30),
    uf_volume DECIMAL(8,1),             -- 超滤量 ml
    replacement_volume DECIMAL(8,1),    -- 置换量 ml
    filter_model VARCHAR(50),
    filter_life_hours INTEGER,          -- 滤器使用时间
    termination_reason TEXT,
    operator_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE crrt_records IS 'CRRT 记录：连续性肾脏替代治疗记录（ICU 常规操作）';
COMMENT ON COLUMN crrt_records.crrt_id IS 'CRRT主键ID';
COMMENT ON COLUMN crrt_records.icu_admission_id IS '关联ICU入科ID';
COMMENT ON COLUMN crrt_records.patient_id IS '患者ID';
COMMENT ON COLUMN crrt_records.visit_id IS '就诊ID';
COMMENT ON COLUMN crrt_records.start_time IS '治疗开始时间';
COMMENT ON COLUMN crrt_records.end_time IS '治疗结束时间';
COMMENT ON COLUMN crrt_records.treatment_mode IS '治疗模式：CVVH/CVVHD/CVVHDF/SCUF';
COMMENT ON COLUMN crrt_records.blood_flow IS '血流速（ml/min）';
COMMENT ON COLUMN crrt_records.dialysate_flow IS '透析液流速（ml/h）';
COMMENT ON COLUMN crrt_records.replacement_flow IS '置换液流速（ml/h）';
COMMENT ON COLUMN crrt_records.anticoagulant IS '抗凝剂';
COMMENT ON COLUMN crrt_records.anticoagulant_dose IS '抗凝剂剂量';
COMMENT ON COLUMN crrt_records.uf_volume IS '超滤量（ml）';
COMMENT ON COLUMN crrt_records.replacement_volume IS '置换量（ml）';
COMMENT ON COLUMN crrt_records.filter_model IS '滤器型号';
COMMENT ON COLUMN crrt_records.filter_life_hours IS '滤器使用时间（小时）';
COMMENT ON COLUMN crrt_records.termination_reason IS '终止原因';
COMMENT ON COLUMN crrt_records.operator_id IS '操作人ID';
COMMENT ON COLUMN crrt_records.create_time IS '记录创建时间';

-- 镇静镇痛记录
CREATE TABLE IF NOT EXISTS sedation_records (
    record_id VARCHAR(20) PRIMARY KEY,
    icu_admission_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    record_time TIMESTAMP,
    rass_score INTEGER,                 -- Richmond躁动镇静评分 -5~+4
    cpot_score INTEGER,                 -- 危重症疼痛观察工具 0~8
    ramsay_score INTEGER,               -- Ramsay镇静评分 1~6
    sedative_drug VARCHAR(100),         -- 镇静药物
    sedative_dose VARCHAR(50),
    analgesic_drug VARCHAR(100),        -- 镇痛药物
    analgesic_dose VARCHAR(50),
    muscle_relaxant VARCHAR(100),       -- 肌松药
    nurse_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE sedation_records IS '镇静镇痛记录：RASS/CPOT/Ramsay 评分及用药（ICU 质控核心）';
COMMENT ON COLUMN sedation_records.record_id IS '记录主键ID';
COMMENT ON COLUMN sedation_records.icu_admission_id IS '关联ICU入科ID';
COMMENT ON COLUMN sedation_records.patient_id IS '患者ID';
COMMENT ON COLUMN sedation_records.visit_id IS '就诊ID';
COMMENT ON COLUMN sedation_records.record_time IS '记录时间';
COMMENT ON COLUMN sedation_records.rass_score IS 'RASS评分（Richmond躁动镇静评分）：-5~+4';
COMMENT ON COLUMN sedation_records.cpot_score IS 'CPOT评分（危重症疼痛观察工具）：0~8';
COMMENT ON COLUMN sedation_records.ramsay_score IS 'Ramsay镇静评分：1~6';
COMMENT ON COLUMN sedation_records.sedative_drug IS '镇静药物';
COMMENT ON COLUMN sedation_records.sedative_dose IS '镇静药物剂量';
COMMENT ON COLUMN sedation_records.analgesic_drug IS '镇痛药物';
COMMENT ON COLUMN sedation_records.analgesic_dose IS '镇痛药物剂量';
COMMENT ON COLUMN sedation_records.muscle_relaxant IS '肌松药物';
COMMENT ON COLUMN sedation_records.nurse_id IS '记录护士ID';
COMMENT ON COLUMN sedation_records.create_time IS '记录创建时间';

-- 气管插管/拔管记录
CREATE TABLE IF NOT EXISTS intubation_records (
    record_id VARCHAR(20) PRIMARY KEY,
    icu_admission_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    tube_type VARCHAR(20),              -- 气管插管/气管切开/喉罩
    intubation_time TIMESTAMP,
    extubation_time TIMESTAMP,
    tube_size VARCHAR(10),              -- 导管型号
    depth_cm DECIMAL(4,1),              -- 置入深度 cm
    intubation_reason TEXT,
    extubation_reason TEXT,
    extubation_outcome VARCHAR(20),     -- 成功/再插管/拔管失败
    doctor_id VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE intubation_records IS '气管插管/拔管记录：气道管理关键记录';
COMMENT ON COLUMN intubation_records.record_id IS '记录主键ID';
COMMENT ON COLUMN intubation_records.icu_admission_id IS '关联ICU入科ID';
COMMENT ON COLUMN intubation_records.patient_id IS '患者ID';
COMMENT ON COLUMN intubation_records.visit_id IS '就诊ID';
COMMENT ON COLUMN intubation_records.tube_type IS '导管类型：气管插管/气管切开/喉罩';
COMMENT ON COLUMN intubation_records.intubation_time IS '插管时间';
COMMENT ON COLUMN intubation_records.extubation_time IS '拔管时间';
COMMENT ON COLUMN intubation_records.tube_size IS '导管型号';
COMMENT ON COLUMN intubation_records.depth_cm IS '置入深度（cm）';
COMMENT ON COLUMN intubation_records.intubation_reason IS '插管原因';
COMMENT ON COLUMN intubation_records.extubation_reason IS '拔管原因';
COMMENT ON COLUMN intubation_records.extubation_outcome IS '拔管结局：成功/再插管/拔管失败';
COMMENT ON COLUMN intubation_records.doctor_id IS '操作医生ID';
COMMENT ON COLUMN intubation_records.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_crrt_icuadm_id ON crrt_records(icu_admission_id);
CREATE INDEX IF NOT EXISTS idx_sedation_icuadm_id ON sedation_records(icu_admission_id);
CREATE INDEX IF NOT EXISTS idx_intubation_icuadm_id ON intubation_records(icu_admission_id);
