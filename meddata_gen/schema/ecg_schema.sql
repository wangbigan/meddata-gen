-- ============================================================
-- ECG 数据库表结构 (心电信息系统)
-- 参考: 纳龙/邦健/GE/飞利浦 主流心电系统数据结构
-- ============================================================

-- 心电检查记录
CREATE TABLE IF NOT EXISTS ecg_exams (
    exam_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    visit_type VARCHAR(10),             -- 住院/门诊/急诊/体检
    exam_no VARCHAR(30),                -- 检查编号
    order_id VARCHAR(20),               -- 关联医嘱/申请单
    exam_type VARCHAR(30),              -- 常规12导联/18导联/动态心电图/运动平板/心电监护
    device_id VARCHAR(20),              -- 设备编码
    device_model VARCHAR(50),           -- 设备型号
    exam_location VARCHAR(100),         -- 检查地点: 心电图室/病房/急诊/ICU
    exam_time TIMESTAMP NOT NULL,
    request_doctor VARCHAR(50),         -- 申请医生
    request_dept VARCHAR(100),          -- 申请科室
    operator_id VARCHAR(20),            -- 操作技师
    operator_name VARCHAR(50),
    patient_state VARCHAR(50),          -- 患者状态: 静息/运动后/吸氧中/疼痛发作
    heart_rate INTEGER,                 -- 心率 bpm
    sampling_rate INTEGER,              -- 采样率 Hz
    filter_low DECIMAL(5,1),            -- 低频滤波 Hz
    filter_high DECIMAL(5,1),           -- 高频滤波 Hz
    lead_system VARCHAR(20),            -- 导联体系: 标准12导联/18导联/Mason-Likar
    duration INTEGER,                   -- 采集时长 秒
    status VARCHAR(10),                 -- 已采集/分析中/已完成/已审核
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE ecg_exams IS '心电检查记录：每条对应一次心电图采集，描述采集设备、参数与状态';
COMMENT ON COLUMN ecg_exams.exam_id IS '心电检查主键ID';
COMMENT ON COLUMN ecg_exams.patient_id IS '患者ID';
COMMENT ON COLUMN ecg_exams.visit_id IS '关联就诊ID';
COMMENT ON COLUMN ecg_exams.visit_type IS '就诊类型：住院/门诊/急诊/体检';
COMMENT ON COLUMN ecg_exams.exam_no IS '检查编号（业务编号）';
COMMENT ON COLUMN ecg_exams.order_id IS '关联医嘱/申请单ID';
COMMENT ON COLUMN ecg_exams.exam_type IS '心电检查类型：常规12导联/18导联/动态心电图(Holter)/运动平板/心电监护';
COMMENT ON COLUMN ecg_exams.device_id IS '设备编码';
COMMENT ON COLUMN ecg_exams.device_model IS '设备型号';
COMMENT ON COLUMN ecg_exams.exam_location IS '检查地点：心电图室/病房/急诊/ICU';
COMMENT ON COLUMN ecg_exams.exam_time IS '检查时间';
COMMENT ON COLUMN ecg_exams.request_doctor IS '申请医生姓名';
COMMENT ON COLUMN ecg_exams.request_dept IS '申请科室名称';
COMMENT ON COLUMN ecg_exams.operator_id IS '操作技师ID';
COMMENT ON COLUMN ecg_exams.operator_name IS '操作技师姓名';
COMMENT ON COLUMN ecg_exams.patient_state IS '患者状态：静息/运动后/吸氧中/疼痛发作';
COMMENT ON COLUMN ecg_exams.heart_rate IS '采集时心率（bpm 次/分）';
COMMENT ON COLUMN ecg_exams.sampling_rate IS '采样率（Hz）';
COMMENT ON COLUMN ecg_exams.filter_low IS '低频滤波（Hz）';
COMMENT ON COLUMN ecg_exams.filter_high IS '高频滤波（Hz）';
COMMENT ON COLUMN ecg_exams.lead_system IS '导联体系：标准12导联/18导联/Mason-Likar';
COMMENT ON COLUMN ecg_exams.duration IS '采集时长（秒）';
COMMENT ON COLUMN ecg_exams.status IS '检查状态：已采集/分析中/已完成/已审核';
COMMENT ON COLUMN ecg_exams.create_time IS '记录创建时间';
COMMENT ON COLUMN ecg_exams.update_time IS '记录更新时间';

-- 心电波形数据 (简化存储关键参数，非原始波形)
CREATE TABLE IF NOT EXISTS ecg_waveforms (
    waveform_id VARCHAR(20) PRIMARY KEY,
    exam_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    lead_name VARCHAR(10) NOT NULL,     -- I/II/III/aVR/aVL/aVF/V1-V6
    baseline DECIMAL(8,2),              -- 基线 mV
    amplitude_min DECIMAL(8,2),         -- 最小振幅
    amplitude_max DECIMAL(8,2),         -- 最大振幅
    p_wave_amplitude DECIMAL(6,2),
    p_wave_duration DECIMAL(6,1),       -- ms
    qrs_amplitude DECIMAL(6,2),
    qrs_duration DECIMAL(6,1),          -- ms
    t_wave_amplitude DECIMAL(6,2),
    t_wave_duration DECIMAL(6,1),       -- ms
    st_segment DECIMAL(6,2),            -- ST段偏移 mV
    pr_interval DECIMAL(6,1),           -- ms
    qt_interval DECIMAL(6,1),           -- ms
    qtc_interval DECIMAL(6,1),          -- 校正QT ms
    quality_score INTEGER,              -- 信号质量评分 0-100
    artifact_flag CHAR(1),              -- 是否有伪差
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ecg_waveforms IS '心电波形数据：每个导联一条记录，存储波形特征参数（非原始采样信号）';
COMMENT ON COLUMN ecg_waveforms.waveform_id IS '波形数据主键ID';
COMMENT ON COLUMN ecg_waveforms.exam_id IS '关联心电检查ID（关联 ecg_exams.exam_id）';
COMMENT ON COLUMN ecg_waveforms.patient_id IS '患者ID';
COMMENT ON COLUMN ecg_waveforms.lead_name IS '导联名称：I/II/III/aVR/aVL/aVF/V1-V6';
COMMENT ON COLUMN ecg_waveforms.baseline IS '基线（mV）';
COMMENT ON COLUMN ecg_waveforms.amplitude_min IS '最小振幅（mV）';
COMMENT ON COLUMN ecg_waveforms.amplitude_max IS '最大振幅（mV）';
COMMENT ON COLUMN ecg_waveforms.p_wave_amplitude IS 'P波振幅（mV）';
COMMENT ON COLUMN ecg_waveforms.p_wave_duration IS 'P波时限（ms）';
COMMENT ON COLUMN ecg_waveforms.qrs_amplitude IS 'QRS波振幅（mV）';
COMMENT ON COLUMN ecg_waveforms.qrs_duration IS 'QRS波时限（ms）';
COMMENT ON COLUMN ecg_waveforms.t_wave_amplitude IS 'T波振幅（mV）';
COMMENT ON COLUMN ecg_waveforms.t_wave_duration IS 'T波时限（ms）';
COMMENT ON COLUMN ecg_waveforms.st_segment IS 'ST段偏移（mV，正=抬高 / 负=压低）';
COMMENT ON COLUMN ecg_waveforms.pr_interval IS 'PR间期（ms）';
COMMENT ON COLUMN ecg_waveforms.qt_interval IS 'QT间期（ms）';
COMMENT ON COLUMN ecg_waveforms.qtc_interval IS '校正QT间期（QTc，ms）';
COMMENT ON COLUMN ecg_waveforms.quality_score IS '信号质量评分（0-100，越高越好）';
COMMENT ON COLUMN ecg_waveforms.artifact_flag IS '是否有伪差：Y/N';
COMMENT ON COLUMN ecg_waveforms.create_time IS '记录创建时间';

-- 心电分析结果
CREATE TABLE IF NOT EXISTS ecg_analyses (
    analysis_id VARCHAR(20) PRIMARY KEY,
    exam_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    rhythm VARCHAR(50),                 -- 主导心律: 窦性心律/房颤/房扑/室上速/室速...
    heart_rate INTEGER,
    p_axis INTEGER,                     -- P电轴
    qrs_axis INTEGER,                   -- QRS电轴
    t_axis INTEGER,                     -- T电轴
    pr_interval DECIMAL(6,1),
    qrs_duration DECIMAL(6,1),
    qt_interval DECIMAL(6,1),
    qtc_interval DECIMAL(6,1),
    diagnosis TEXT,                     -- 诊断结论
    diagnosis_codes TEXT,               -- 诊断编码 (ICD或内部编码)
    abnormalities TEXT,                 -- 异常发现列表
    severity VARCHAR(10),               -- 正常/异常/危急
    interpretation TEXT,                -- 解释说明
    comparison_result VARCHAR(50),      -- 与既往对比: 无明显变化/改善/加重/新出现
    comparison_exam_id VARCHAR(20),     -- 对比检查ID
    ai_score DECIMAL(4,2),              -- AI辅助诊断置信度
    reporter_id VARCHAR(20),
    reporter_name VARCHAR(50),
    report_time TIMESTAMP,
    auditor_id VARCHAR(20),
    auditor_name VARCHAR(50),
    audit_time TIMESTAMP,
    report_status VARCHAR(10),          -- 草稿/已提交/已审核
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ecg_analyses IS '心电分析结果：每次心电检查的诊断结论与关键全局参数';
COMMENT ON COLUMN ecg_analyses.analysis_id IS '分析结果主键ID';
COMMENT ON COLUMN ecg_analyses.exam_id IS '关联心电检查ID';
COMMENT ON COLUMN ecg_analyses.patient_id IS '患者ID';
COMMENT ON COLUMN ecg_analyses.rhythm IS '主导心律：窦性心律/房颤/房扑/室上速/室速 等';
COMMENT ON COLUMN ecg_analyses.heart_rate IS '心率（bpm）';
COMMENT ON COLUMN ecg_analyses.p_axis IS 'P电轴（度）';
COMMENT ON COLUMN ecg_analyses.qrs_axis IS 'QRS电轴（度）';
COMMENT ON COLUMN ecg_analyses.t_axis IS 'T电轴（度）';
COMMENT ON COLUMN ecg_analyses.pr_interval IS 'PR间期（ms）';
COMMENT ON COLUMN ecg_analyses.qrs_duration IS 'QRS时限（ms）';
COMMENT ON COLUMN ecg_analyses.qt_interval IS 'QT间期（ms）';
COMMENT ON COLUMN ecg_analyses.qtc_interval IS '校正QT间期（QTc，ms）';
COMMENT ON COLUMN ecg_analyses.diagnosis IS '诊断结论（文本描述）';
COMMENT ON COLUMN ecg_analyses.diagnosis_codes IS '诊断编码（ICD或内部编码，多个用分隔符）';
COMMENT ON COLUMN ecg_analyses.abnormalities IS '异常发现列表';
COMMENT ON COLUMN ecg_analyses.severity IS '严重程度：正常/异常/危急';
COMMENT ON COLUMN ecg_analyses.interpretation IS '解释说明（医师诊断意见）';
COMMENT ON COLUMN ecg_analyses.comparison_result IS '与既往对比：无明显变化/改善/加重/新出现';
COMMENT ON COLUMN ecg_analyses.comparison_exam_id IS '对比的既往检查ID';
COMMENT ON COLUMN ecg_analyses.ai_score IS 'AI辅助诊断置信度（0~1）';
COMMENT ON COLUMN ecg_analyses.reporter_id IS '报告医生ID';
COMMENT ON COLUMN ecg_analyses.reporter_name IS '报告医生姓名（冗余）';
COMMENT ON COLUMN ecg_analyses.report_time IS '报告时间';
COMMENT ON COLUMN ecg_analyses.auditor_id IS '审核医生ID';
COMMENT ON COLUMN ecg_analyses.auditor_name IS '审核医生姓名（冗余）';
COMMENT ON COLUMN ecg_analyses.audit_time IS '审核时间';
COMMENT ON COLUMN ecg_analyses.report_status IS '报告状态：草稿/已提交/已审核';
COMMENT ON COLUMN ecg_analyses.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_ecgexam_patient_id ON ecg_exams(patient_id);
CREATE INDEX IF NOT EXISTS idx_ecgexam_exam_time ON ecg_exams(exam_time);
CREATE INDEX IF NOT EXISTS idx_waveform_exam_id ON ecg_waveforms(exam_id);
CREATE INDEX IF NOT EXISTS idx_analysis_exam_id ON ecg_analyses(exam_id);

-- ----- 批次3: 新增表 -----

-- 动态心电图(Holter)记录
CREATE TABLE IF NOT EXISTS holter_records (
    holter_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    record_date DATE NOT NULL,
    total_hours INTEGER,                -- 记录总时长
    total_beats BIGINT,                 -- 总心搏数
    avg_hr INTEGER,                     -- 平均心率
    min_hr INTEGER,
    max_hr INTEGER,
    min_hr_time TIMESTAMP,
    max_hr_time TIMESTAMP,
    pauses_count INTEGER,               -- 停搏次数
    longest_pause_ms INTEGER,           -- 最长停搏 ms
    af_burden DECIMAL(5,2),             -- 房颤负荷 %
    af_episodes INTEGER,                -- 房颤阵数
    ve_count INTEGER,                   -- 室早次数
    sv_count INTEGER,                   -- 室上早次数
    vt_episodes INTEGER,                -- 室速阵数
    svt_episodes INTEGER,               -- 室上速阵数
    st_deviation_flag CHAR(1),          -- ST段改变 Y/N
    report_status VARCHAR(20),
    reporter_id VARCHAR(20),
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE holter_records IS '动态心电图(Holter)记录：24小时心电监测汇总（纳龙/邦健 Holter 系统）';
COMMENT ON COLUMN holter_records.holter_id IS 'Holter主键ID';
COMMENT ON COLUMN holter_records.patient_id IS '患者ID';
COMMENT ON COLUMN holter_records.visit_id IS '就诊ID';
COMMENT ON COLUMN holter_records.record_date IS '记录日期';
COMMENT ON COLUMN holter_records.total_hours IS '有效记录时长（小时）';
COMMENT ON COLUMN holter_records.total_beats IS '总心搏数';
COMMENT ON COLUMN holter_records.avg_hr IS '平均心率（bpm）';
COMMENT ON COLUMN holter_records.min_hr IS '最慢心率（bpm）';
COMMENT ON COLUMN holter_records.max_hr IS '最快心率（bpm）';
COMMENT ON COLUMN holter_records.min_hr_time IS '最慢心率发生时间';
COMMENT ON COLUMN holter_records.max_hr_time IS '最快心率发生时间';
COMMENT ON COLUMN holter_records.pauses_count IS '停搏次数（>2s）';
COMMENT ON COLUMN holter_records.longest_pause_ms IS '最长停搏（ms）';
COMMENT ON COLUMN holter_records.af_burden IS '房颤负荷（%）';
COMMENT ON COLUMN holter_records.af_episodes IS '房颤阵数';
COMMENT ON COLUMN holter_records.ve_count IS '室性早搏次数';
COMMENT ON COLUMN holter_records.sv_count IS '室上性早搏次数';
COMMENT ON COLUMN holter_records.vt_episodes IS '室速阵数';
COMMENT ON COLUMN holter_records.svt_episodes IS '室上速阵数';
COMMENT ON COLUMN holter_records.st_deviation_flag IS '是否有ST段改变：Y/N';
COMMENT ON COLUMN holter_records.report_status IS '报告状态';
COMMENT ON COLUMN holter_records.reporter_id IS '报告医生ID';
COMMENT ON COLUMN holter_records.report_time IS '报告时间';
COMMENT ON COLUMN holter_records.create_time IS '记录创建时间';

-- Holter 事件记录
CREATE TABLE IF NOT EXISTS holter_events (
    event_id VARCHAR(20) PRIMARY KEY,
    holter_id VARCHAR(20) NOT NULL,
    event_time TIMESTAMP,
    event_type VARCHAR(50),             -- 室早/房早/室速/房颤/ST改变/停搏/起搏
    duration_seconds INTEGER,
    min_hr INTEGER,
    max_hr INTEGER,
    avg_hr INTEGER,
    symptom TEXT,                       -- 患者症状
    activity TEXT,                      -- 当时活动
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE holter_events IS 'Holter 事件记录：24小时监测期间标记的心律失常事件';
COMMENT ON COLUMN holter_events.event_id IS '事件主键ID';
COMMENT ON COLUMN holter_events.holter_id IS '关联Holter记录ID';
COMMENT ON COLUMN holter_events.event_time IS '事件发生时间';
COMMENT ON COLUMN holter_events.event_type IS '事件类型：室早/房早/室速/房颤/ST改变/停搏/起搏';
COMMENT ON COLUMN holter_events.duration_seconds IS '持续时间（秒）';
COMMENT ON COLUMN holter_events.min_hr IS '事件期间最慢心率';
COMMENT ON COLUMN holter_events.max_hr IS '事件期间最快心率';
COMMENT ON COLUMN holter_events.avg_hr IS '事件期间平均心率';
COMMENT ON COLUMN holter_events.symptom IS '患者症状描述';
COMMENT ON COLUMN holter_events.activity IS '当时活动状态';
COMMENT ON COLUMN holter_events.create_time IS '记录创建时间';

-- 运动平板记录
CREATE TABLE IF NOT EXISTS stress_test_records (
    test_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    protocol VARCHAR(30),               -- Bruce/Modified Bruce/Balke/Naughton
    max_speed DECIMAL(4,1),             -- km/h
    max_grade DECIMAL(4,1),             -- %
    max_hr INTEGER,
    target_hr INTEGER,                  -- 目标心率
    max_bp VARCHAR(15),
    test_duration INTEGER,              -- 测试时长 秒
    max_mets DECIMAL(4,1),              -- 最大代谢当量
    test_result VARCHAR(20),            -- 阳性/阴性/可疑/未完成
    termination_reason TEXT,
    st_deviation_max DECIMAL(5,2),      -- 最大ST段偏移 mV
    arrhythmia TEXT,                    -- 诱发心律失常
    chest_pain VARCHAR(20),             -- 胸痛分级
    reporter_id VARCHAR(20),
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE stress_test_records IS '运动平板记录：运动负荷心电图独立检查类型';
COMMENT ON COLUMN stress_test_records.test_id IS '运动平板主键ID';
COMMENT ON COLUMN stress_test_records.patient_id IS '患者ID';
COMMENT ON COLUMN stress_test_records.visit_id IS '就诊ID';
COMMENT ON COLUMN stress_test_records.protocol IS '运动方案：Bruce/Modified Bruce/Balke/Naughton';
COMMENT ON COLUMN stress_test_records.max_speed IS '最大速度（km/h）';
COMMENT ON COLUMN stress_test_records.max_grade IS '最大坡度（%）';
COMMENT ON COLUMN stress_test_records.max_hr IS '最大心率（bpm）';
COMMENT ON COLUMN stress_test_records.target_hr IS '目标心率（bpm）';
COMMENT ON COLUMN stress_test_records.max_bp IS '最高血压';
COMMENT ON COLUMN stress_test_records.test_duration IS '测试时长（秒）';
COMMENT ON COLUMN stress_test_records.max_mets IS '最大代谢当量（METs）';
COMMENT ON COLUMN stress_test_records.test_result IS '测试结果：阳性/阴性/可疑/未完成';
COMMENT ON COLUMN stress_test_records.termination_reason IS '终止原因';
COMMENT ON COLUMN stress_test_records.st_deviation_max IS '最大ST段偏移（mV）';
COMMENT ON COLUMN stress_test_records.arrhythmia IS '诱发心律失常';
COMMENT ON COLUMN stress_test_records.chest_pain IS '胸痛分级';
COMMENT ON COLUMN stress_test_records.reporter_id IS '报告医生ID';
COMMENT ON COLUMN stress_test_records.report_time IS '报告时间';
COMMENT ON COLUMN stress_test_records.create_time IS '记录创建时间';

-- 现有表补充字段
ALTER TABLE ecg_exams ADD COLUMN IF NOT EXISTS lead_off_info VARCHAR(100);
ALTER TABLE ecg_exams ADD COLUMN IF NOT EXISTS baseline_drift VARCHAR(20);
ALTER TABLE ecg_exams ADD COLUMN IF NOT EXISTS exercise_stage VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_holter_patient_id ON holter_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_holter_event_holter_id ON holter_events(holter_id);
CREATE INDEX IF NOT EXISTS idx_stress_patient_id ON stress_test_records(patient_id);
