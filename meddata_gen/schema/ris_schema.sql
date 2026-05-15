-- ============================================================
-- RIS 数据库表结构 (影像信息系统)
-- 参考: GE/飞利浦/联影/东软 主流PACS/RIS数据结构
-- ============================================================

-- 影像设备字典
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(20) PRIMARY KEY,
    device_code VARCHAR(20) NOT NULL,
    device_name VARCHAR(100),
    modality VARCHAR(20) NOT NULL,      -- CT/MRI/XR/US/DR/MG/RF/DSA/PET/ECT
    manufacturer VARCHAR(100),
    model VARCHAR(50),
    location VARCHAR(100),
    room_no VARCHAR(20),
    dept_id VARCHAR(20),
    install_date DATE,
    status VARCHAR(10),                 -- 正常/维修/停用
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE devices IS '影像设备字典：医院在用的影像检查设备清单（CT、MRI、X光、超声等）';
COMMENT ON COLUMN devices.device_id IS '设备主键ID';
COMMENT ON COLUMN devices.device_code IS '设备编码（业务唯一码）';
COMMENT ON COLUMN devices.device_name IS '设备名称';
COMMENT ON COLUMN devices.modality IS '影像模态：CT/MRI/XR(普放)/US(超声)/DR(数字X光)/MG(乳腺)/RF(透视)/DSA(血管造影)/PET/ECT';
COMMENT ON COLUMN devices.manufacturer IS '生产厂商（GE/飞利浦/联影/西门子 等）';
COMMENT ON COLUMN devices.model IS '设备型号';
COMMENT ON COLUMN devices.location IS '设备物理位置';
COMMENT ON COLUMN devices.room_no IS '设备所在机房号';
COMMENT ON COLUMN devices.dept_id IS '所属科室ID';
COMMENT ON COLUMN devices.install_date IS '安装日期';
COMMENT ON COLUMN devices.status IS '设备状态：正常/维修/停用';
COMMENT ON COLUMN devices.create_time IS '记录创建时间';

-- 检查申请主表
CREATE TABLE IF NOT EXISTS exam_orders (
    order_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    visit_type VARCHAR(10),             -- 住院/门诊/急诊
    order_no VARCHAR(30),
    order_time TIMESTAMP,
    order_dept_id VARCHAR(20),
    order_doctor_id VARCHAR(20),
    order_doctor_name VARCHAR(50),
    exam_type VARCHAR(20),              -- 普放/CT/MRI/超声/核医学/介入
    exam_item_code VARCHAR(20),
    exam_item_name VARCHAR(200),
    exam_part VARCHAR(100),             -- 检查部位
    exam_method VARCHAR(100),           -- 检查方法
    clinical_diagnosis TEXT,
    purpose TEXT,                       -- 检查目的
    priority VARCHAR(10),               -- 普通/紧急
    pregnancy_status CHAR(1),           -- 是否妊娠
    allergy_history TEXT,               -- 造影剂过敏史
    contrast_agent VARCHAR(50),         -- 计划使用造影剂
    order_status VARCHAR(10),           -- 已申请/已预约/已检查/已报告/已审核/已取消
    device_id VARCHAR(20),
    appointment_time TIMESTAMP,
    exam_time TIMESTAMP,
    fee DECIMAL(10,2),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP
);

COMMENT ON TABLE exam_orders IS '影像检查申请主表：医生开具的影像检查单（一单一项检查）';
COMMENT ON COLUMN exam_orders.order_id IS '检查申请主键ID';
COMMENT ON COLUMN exam_orders.patient_id IS '患者ID';
COMMENT ON COLUMN exam_orders.visit_id IS '关联就诊ID';
COMMENT ON COLUMN exam_orders.visit_type IS '就诊类型：住院/门诊/急诊';
COMMENT ON COLUMN exam_orders.order_no IS '申请单号';
COMMENT ON COLUMN exam_orders.order_time IS '开单时间';
COMMENT ON COLUMN exam_orders.order_dept_id IS '开单科室ID';
COMMENT ON COLUMN exam_orders.order_doctor_id IS '开单医生ID';
COMMENT ON COLUMN exam_orders.order_doctor_name IS '开单医生姓名（冗余）';
COMMENT ON COLUMN exam_orders.exam_type IS '检查大类：普放/CT/MRI/超声/核医学/介入';
COMMENT ON COLUMN exam_orders.exam_item_code IS '检查项目编码';
COMMENT ON COLUMN exam_orders.exam_item_name IS '检查项目名称';
COMMENT ON COLUMN exam_orders.exam_part IS '检查部位（头/胸/腹/盆腔等）';
COMMENT ON COLUMN exam_orders.exam_method IS '检查方法（平扫/增强/MRA/MRV 等）';
COMMENT ON COLUMN exam_orders.clinical_diagnosis IS '临床诊断（送检诊断）';
COMMENT ON COLUMN exam_orders.purpose IS '检查目的';
COMMENT ON COLUMN exam_orders.priority IS '优先级：普通/紧急';
COMMENT ON COLUMN exam_orders.pregnancy_status IS '是否妊娠：Y=是 / N=否';
COMMENT ON COLUMN exam_orders.allergy_history IS '造影剂过敏史';
COMMENT ON COLUMN exam_orders.contrast_agent IS '计划使用的造影剂';
COMMENT ON COLUMN exam_orders.order_status IS '申请状态：已申请/已预约/已检查/已报告/已审核/已取消';
COMMENT ON COLUMN exam_orders.device_id IS '执行设备ID（关联 devices.device_id）';
COMMENT ON COLUMN exam_orders.appointment_time IS '预约检查时间';
COMMENT ON COLUMN exam_orders.exam_time IS '实际检查时间';
COMMENT ON COLUMN exam_orders.fee IS '检查费用';
COMMENT ON COLUMN exam_orders.create_time IS '记录创建时间';
COMMENT ON COLUMN exam_orders.update_time IS '记录更新时间';

-- 普放(XR/DR/MG)报告
CREATE TABLE IF NOT EXISTS xray_reports (
    report_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    exam_no VARCHAR(30),                -- 检查号
    device_id VARCHAR(20),
    exam_part VARCHAR(100),
    exam_method VARCHAR(100),
    film_count INTEGER,                 -- 摄片张数
    image_count INTEGER,                -- 图像数量
    technique TEXT,                     -- 检查技术
    findings TEXT,                      -- 影像表现
    impression TEXT,                    -- 影像诊断/印象
    report_status VARCHAR(10),          -- 草稿/已提交/已审核
    reporter_id VARCHAR(20),
    reporter_name VARCHAR(50),
    report_time TIMESTAMP,
    auditor_id VARCHAR(20),
    auditor_name VARCHAR(50),
    audit_time TIMESTAMP,
    critical_value CHAR(1),             -- 是否危急值
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE xray_reports IS '普放报告：包括 XR/DR/MG（数字X光、乳腺X光等）的影像诊断报告';
COMMENT ON COLUMN xray_reports.report_id IS '报告主键ID';
COMMENT ON COLUMN xray_reports.order_id IS '关联检查申请ID';
COMMENT ON COLUMN xray_reports.patient_id IS '患者ID';
COMMENT ON COLUMN xray_reports.visit_id IS '就诊ID';
COMMENT ON COLUMN xray_reports.exam_no IS '检查号（PACS系统中的检查唯一号）';
COMMENT ON COLUMN xray_reports.device_id IS '执行设备ID';
COMMENT ON COLUMN xray_reports.exam_part IS '检查部位';
COMMENT ON COLUMN xray_reports.exam_method IS '检查方法';
COMMENT ON COLUMN xray_reports.film_count IS '摄片张数';
COMMENT ON COLUMN xray_reports.image_count IS '图像数量';
COMMENT ON COLUMN xray_reports.technique IS '检查技术参数';
COMMENT ON COLUMN xray_reports.findings IS '影像表现（描述部分）';
COMMENT ON COLUMN xray_reports.impression IS '影像诊断/印象（结论部分）';
COMMENT ON COLUMN xray_reports.report_status IS '报告状态：草稿/已提交/已审核';
COMMENT ON COLUMN xray_reports.reporter_id IS '报告医生ID';
COMMENT ON COLUMN xray_reports.reporter_name IS '报告医生姓名（冗余）';
COMMENT ON COLUMN xray_reports.report_time IS '报告时间';
COMMENT ON COLUMN xray_reports.auditor_id IS '审核医生ID';
COMMENT ON COLUMN xray_reports.auditor_name IS '审核医生姓名（冗余）';
COMMENT ON COLUMN xray_reports.audit_time IS '审核时间';
COMMENT ON COLUMN xray_reports.critical_value IS '是否危急值：Y/N';
COMMENT ON COLUMN xray_reports.create_time IS '记录创建时间';

-- CT报告
CREATE TABLE IF NOT EXISTS ct_reports (
    report_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    exam_no VARCHAR(30),
    device_id VARCHAR(20),
    exam_part VARCHAR(100),
    contrast_agent VARCHAR(50),         -- 使用造影剂
    contrast_dose VARCHAR(30),          -- 造影剂剂量
    slice_thickness VARCHAR(20),        -- 层厚
    kv VARCHAR(10),                     -- 管电压
    ma VARCHAR(10),                     -- 管电流
    findings TEXT,
    impression TEXT,
    report_status VARCHAR(10),
    reporter_id VARCHAR(20),
    reporter_name VARCHAR(50),
    report_time TIMESTAMP,
    auditor_id VARCHAR(20),
    auditor_name VARCHAR(50),
    audit_time TIMESTAMP,
    critical_value CHAR(1),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ct_reports IS 'CT影像报告：CT扫描后由放射科医生书写的影像诊断报告';
COMMENT ON COLUMN ct_reports.report_id IS '报告主键ID';
COMMENT ON COLUMN ct_reports.order_id IS '关联检查申请ID';
COMMENT ON COLUMN ct_reports.patient_id IS '患者ID';
COMMENT ON COLUMN ct_reports.visit_id IS '就诊ID';
COMMENT ON COLUMN ct_reports.exam_no IS '检查号';
COMMENT ON COLUMN ct_reports.device_id IS '执行设备ID';
COMMENT ON COLUMN ct_reports.exam_part IS '检查部位';
COMMENT ON COLUMN ct_reports.contrast_agent IS '使用造影剂名称';
COMMENT ON COLUMN ct_reports.contrast_dose IS '造影剂剂量';
COMMENT ON COLUMN ct_reports.slice_thickness IS '扫描层厚';
COMMENT ON COLUMN ct_reports.kv IS '管电压（kV）';
COMMENT ON COLUMN ct_reports.ma IS '管电流（mA）';
COMMENT ON COLUMN ct_reports.findings IS '影像表现';
COMMENT ON COLUMN ct_reports.impression IS '影像诊断/印象';
COMMENT ON COLUMN ct_reports.report_status IS '报告状态：草稿/已提交/已审核';
COMMENT ON COLUMN ct_reports.reporter_id IS '报告医生ID';
COMMENT ON COLUMN ct_reports.reporter_name IS '报告医生姓名（冗余）';
COMMENT ON COLUMN ct_reports.report_time IS '报告时间';
COMMENT ON COLUMN ct_reports.auditor_id IS '审核医生ID';
COMMENT ON COLUMN ct_reports.auditor_name IS '审核医生姓名（冗余）';
COMMENT ON COLUMN ct_reports.audit_time IS '审核时间';
COMMENT ON COLUMN ct_reports.critical_value IS '是否危急值：Y/N';
COMMENT ON COLUMN ct_reports.create_time IS '记录创建时间';

-- MRI报告
CREATE TABLE IF NOT EXISTS mri_reports (
    report_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    exam_no VARCHAR(30),
    device_id VARCHAR(20),
    exam_part VARCHAR(100),
    sequence TEXT,                      -- 扫描序列
    contrast_agent VARCHAR(50),
    findings TEXT,
    impression TEXT,
    report_status VARCHAR(10),
    reporter_id VARCHAR(20),
    reporter_name VARCHAR(50),
    report_time TIMESTAMP,
    auditor_id VARCHAR(20),
    auditor_name VARCHAR(50),
    audit_time TIMESTAMP,
    critical_value CHAR(1),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE mri_reports IS 'MRI 影像报告：磁共振扫描后的影像诊断报告';
COMMENT ON COLUMN mri_reports.report_id IS '报告主键ID';
COMMENT ON COLUMN mri_reports.order_id IS '关联检查申请ID';
COMMENT ON COLUMN mri_reports.patient_id IS '患者ID';
COMMENT ON COLUMN mri_reports.visit_id IS '就诊ID';
COMMENT ON COLUMN mri_reports.exam_no IS '检查号';
COMMENT ON COLUMN mri_reports.device_id IS '执行设备ID';
COMMENT ON COLUMN mri_reports.exam_part IS '检查部位';
COMMENT ON COLUMN mri_reports.sequence IS '扫描序列（T1WI/T2WI/FLAIR/DWI 等）';
COMMENT ON COLUMN mri_reports.contrast_agent IS '使用造影剂';
COMMENT ON COLUMN mri_reports.findings IS '影像表现';
COMMENT ON COLUMN mri_reports.impression IS '影像诊断/印象';
COMMENT ON COLUMN mri_reports.report_status IS '报告状态：草稿/已提交/已审核';
COMMENT ON COLUMN mri_reports.reporter_id IS '报告医生ID';
COMMENT ON COLUMN mri_reports.reporter_name IS '报告医生姓名（冗余）';
COMMENT ON COLUMN mri_reports.report_time IS '报告时间';
COMMENT ON COLUMN mri_reports.auditor_id IS '审核医生ID';
COMMENT ON COLUMN mri_reports.auditor_name IS '审核医生姓名（冗余）';
COMMENT ON COLUMN mri_reports.audit_time IS '审核时间';
COMMENT ON COLUMN mri_reports.critical_value IS '是否危急值：Y/N';
COMMENT ON COLUMN mri_reports.create_time IS '记录创建时间';

-- 超声报告
CREATE TABLE IF NOT EXISTS ultrasound_reports (
    report_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    exam_no VARCHAR(30),
    device_id VARCHAR(20),
    exam_part VARCHAR(100),             -- 检查部位: 腹部/心脏/甲状腺/乳腺/妇科...
    exam_type VARCHAR(30),              -- B超/彩超/三维/造影
    probe_frequency VARCHAR(20),        -- 探头频率
    ultrasound_findings TEXT,           -- 超声所见
    ultrasound_diagnosis TEXT,          -- 超声提示
    measurements TEXT,                  -- 测量数据
    images_count INTEGER,               -- 留存图像数
    video_flag CHAR(1),                 -- 是否有视频
    report_status VARCHAR(10),
    reporter_id VARCHAR(20),
    reporter_name VARCHAR(50),
    report_time TIMESTAMP,
    auditor_id VARCHAR(20),
    auditor_name VARCHAR(50),
    audit_time TIMESTAMP,
    critical_value CHAR(1),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ultrasound_reports IS '超声报告：B超、彩超、三维超声、造影超声等检查报告';
COMMENT ON COLUMN ultrasound_reports.report_id IS '报告主键ID';
COMMENT ON COLUMN ultrasound_reports.order_id IS '关联检查申请ID';
COMMENT ON COLUMN ultrasound_reports.patient_id IS '患者ID';
COMMENT ON COLUMN ultrasound_reports.visit_id IS '就诊ID';
COMMENT ON COLUMN ultrasound_reports.exam_no IS '检查号';
COMMENT ON COLUMN ultrasound_reports.device_id IS '执行设备ID';
COMMENT ON COLUMN ultrasound_reports.exam_part IS '检查部位：腹部/心脏/甲状腺/乳腺/妇科 等';
COMMENT ON COLUMN ultrasound_reports.exam_type IS '检查类型：B超/彩超/三维/造影';
COMMENT ON COLUMN ultrasound_reports.probe_frequency IS '探头频率（MHz）';
COMMENT ON COLUMN ultrasound_reports.ultrasound_findings IS '超声所见（描述）';
COMMENT ON COLUMN ultrasound_reports.ultrasound_diagnosis IS '超声提示（结论）';
COMMENT ON COLUMN ultrasound_reports.measurements IS '关键测量数据（如左室舒张末径等）';
COMMENT ON COLUMN ultrasound_reports.images_count IS '留存图像数';
COMMENT ON COLUMN ultrasound_reports.video_flag IS '是否有动态视频：Y/N';
COMMENT ON COLUMN ultrasound_reports.report_status IS '报告状态：草稿/已提交/已审核';
COMMENT ON COLUMN ultrasound_reports.reporter_id IS '报告医生ID';
COMMENT ON COLUMN ultrasound_reports.reporter_name IS '报告医生姓名（冗余）';
COMMENT ON COLUMN ultrasound_reports.report_time IS '报告时间';
COMMENT ON COLUMN ultrasound_reports.auditor_id IS '审核医生ID';
COMMENT ON COLUMN ultrasound_reports.auditor_name IS '审核医生姓名（冗余）';
COMMENT ON COLUMN ultrasound_reports.audit_time IS '审核时间';
COMMENT ON COLUMN ultrasound_reports.critical_value IS '是否危急值：Y/N';
COMMENT ON COLUMN ultrasound_reports.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_examorder_patient_id ON exam_orders(patient_id);
CREATE INDEX IF NOT EXISTS idx_examorder_visit_id ON exam_orders(visit_id);
CREATE INDEX IF NOT EXISTS idx_xray_order_id ON xray_reports(order_id);
CREATE INDEX IF NOT EXISTS idx_ct_order_id ON ct_reports(order_id);
CREATE INDEX IF NOT EXISTS idx_mri_order_id ON mri_reports(order_id);
CREATE INDEX IF NOT EXISTS idx_us_order_id ON ultrasound_reports(order_id);

-- ----- 批次1: 新增表 -----

-- 检查图像/序列信息
CREATE TABLE IF NOT EXISTS exam_images (
    image_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    series_uid VARCHAR(64),
    study_uid VARCHAR(64),
    modality VARCHAR(20),
    image_count INTEGER,
    storage_path TEXT,
    file_size_mb DECIMAL(8,2),
    upload_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE exam_images IS '检查图像/序列信息：DICOM 序列级信息（GE/联影 PACS 核心表）';
COMMENT ON COLUMN exam_images.image_id IS '图像记录主键ID';
COMMENT ON COLUMN exam_images.order_id IS '关联检查申请ID';
COMMENT ON COLUMN exam_images.patient_id IS '患者ID';
COMMENT ON COLUMN exam_images.visit_id IS '就诊ID';
COMMENT ON COLUMN exam_images.series_uid IS 'DICOM Series Instance UID';
COMMENT ON COLUMN exam_images.study_uid IS 'DICOM Study Instance UID';
COMMENT ON COLUMN exam_images.modality IS '影像模态';
COMMENT ON COLUMN exam_images.image_count IS '序列内图像数量';
COMMENT ON COLUMN exam_images.storage_path IS '存储路径';
COMMENT ON COLUMN exam_images.file_size_mb IS '文件大小（MB）';
COMMENT ON COLUMN exam_images.upload_time IS '上传时间';
COMMENT ON COLUMN exam_images.create_time IS '记录创建时间';

-- ----- 批次1: 现有表补充字段 -----

ALTER TABLE exam_orders ADD COLUMN IF NOT EXISTS technician_id VARCHAR(20);
ALTER TABLE exam_orders ADD COLUMN IF NOT EXISTS technician_name VARCHAR(50);
ALTER TABLE exam_orders ADD COLUMN IF NOT EXISTS exam_duration_minutes INTEGER;
ALTER TABLE exam_orders ADD COLUMN IF NOT EXISTS contrast_reaction TEXT;
ALTER TABLE exam_orders ADD COLUMN IF NOT EXISTS radiation_dose_msv DECIMAL(8,4);

ALTER TABLE xray_reports ADD COLUMN IF NOT EXISTS ai_findings TEXT;
ALTER TABLE xray_reports ADD COLUMN IF NOT EXISTS template_id VARCHAR(20);
ALTER TABLE xray_reports ADD COLUMN IF NOT EXISTS comparison_study_uid VARCHAR(64);
ALTER TABLE xray_reports ADD COLUMN IF NOT EXISTS key_image_count INTEGER;
ALTER TABLE xray_reports ADD COLUMN IF NOT EXISTS report_complexity VARCHAR(20);

ALTER TABLE ct_reports ADD COLUMN IF NOT EXISTS ai_findings TEXT;
ALTER TABLE ct_reports ADD COLUMN IF NOT EXISTS template_id VARCHAR(20);
ALTER TABLE ct_reports ADD COLUMN IF NOT EXISTS comparison_study_uid VARCHAR(64);
ALTER TABLE ct_reports ADD COLUMN IF NOT EXISTS key_image_count INTEGER;
ALTER TABLE ct_reports ADD COLUMN IF NOT EXISTS report_complexity VARCHAR(20);

ALTER TABLE mri_reports ADD COLUMN IF NOT EXISTS ai_findings TEXT;
ALTER TABLE mri_reports ADD COLUMN IF NOT EXISTS template_id VARCHAR(20);
ALTER TABLE mri_reports ADD COLUMN IF NOT EXISTS comparison_study_uid VARCHAR(64);
ALTER TABLE mri_reports ADD COLUMN IF NOT EXISTS key_image_count INTEGER;
ALTER TABLE mri_reports ADD COLUMN IF NOT EXISTS report_complexity VARCHAR(20);

ALTER TABLE ultrasound_reports ADD COLUMN IF NOT EXISTS ai_findings TEXT;
ALTER TABLE ultrasound_reports ADD COLUMN IF NOT EXISTS template_id VARCHAR(20);
ALTER TABLE ultrasound_reports ADD COLUMN IF NOT EXISTS comparison_study_uid VARCHAR(64);
ALTER TABLE ultrasound_reports ADD COLUMN IF NOT EXISTS key_image_count INTEGER;
ALTER TABLE ultrasound_reports ADD COLUMN IF NOT EXISTS report_complexity VARCHAR(20);

-- 新增表索引
CREATE INDEX IF NOT EXISTS idx_examimage_order_id ON exam_images(order_id);
CREATE INDEX IF NOT EXISTS idx_examimage_study_uid ON exam_images(study_uid);

-- ----- 批次2: 新增表 -----

-- 胶片打印记录
CREATE TABLE IF NOT EXISTS film_prints (
    print_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    print_time TIMESTAMP,
    film_size VARCHAR(20),              -- 14×17/10×12/8×10/14×14
    sheet_count INTEGER,                -- 张数
    printer_id VARCHAR(20),
    operator_id VARCHAR(20),
    cost DECIMAL(8,2),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE film_prints IS '胶片打印记录：放射科胶片打印流水';
COMMENT ON COLUMN film_prints.print_id IS '打印主键ID';
COMMENT ON COLUMN film_prints.order_id IS '关联检查申请ID';
COMMENT ON COLUMN film_prints.patient_id IS '患者ID';
COMMENT ON COLUMN film_prints.print_time IS '打印时间';
COMMENT ON COLUMN film_prints.film_size IS '胶片尺寸：14×17/10×12/8×10/14×14';
COMMENT ON COLUMN film_prints.sheet_count IS '打印张数';
COMMENT ON COLUMN film_prints.printer_id IS '打印机ID';
COMMENT ON COLUMN film_prints.operator_id IS '操作人ID';
COMMENT ON COLUMN film_prints.cost IS '费用';
COMMENT ON COLUMN film_prints.create_time IS '记录创建时间';

-- 介入/DSA 报告
CREATE TABLE IF NOT EXISTS intervention_reports (
    report_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    procedure_name VARCHAR(200),
    access_route VARCHAR(50),           -- 股动脉/桡动脉/颈静脉等
    contrast_agent VARCHAR(50),
    contrast_volume_ml INTEGER,
    procedure_start_time TIMESTAMP,
    procedure_end_time TIMESTAMP,
    findings TEXT,
    impression TEXT,
    complications TEXT,                 -- 并发症
    report_status VARCHAR(20),
    reporter_id VARCHAR(20),
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE intervention_reports IS '介入/DSA 报告：数字减影血管造影及介入治疗独立报告';
COMMENT ON COLUMN intervention_reports.report_id IS '报告主键ID';
COMMENT ON COLUMN intervention_reports.order_id IS '关联检查申请ID';
COMMENT ON COLUMN intervention_reports.patient_id IS '患者ID';
COMMENT ON COLUMN intervention_reports.visit_id IS '就诊ID';
COMMENT ON COLUMN intervention_reports.procedure_name IS '介入手术/操作名称';
COMMENT ON COLUMN intervention_reports.access_route IS '入路：股动脉/桡动脉/颈静脉/股静脉等';
COMMENT ON COLUMN intervention_reports.contrast_agent IS '使用造影剂';
COMMENT ON COLUMN intervention_reports.contrast_volume_ml IS '造影剂用量（ml）';
COMMENT ON COLUMN intervention_reports.procedure_start_time IS '操作开始时间';
COMMENT ON COLUMN intervention_reports.procedure_end_time IS '操作结束时间';
COMMENT ON COLUMN intervention_reports.findings IS '操作所见';
COMMENT ON COLUMN intervention_reports.impression IS '诊断印象';
COMMENT ON COLUMN intervention_reports.complications IS '并发症';
COMMENT ON COLUMN intervention_reports.report_status IS '报告状态';
COMMENT ON COLUMN intervention_reports.reporter_id IS '报告医生ID';
COMMENT ON COLUMN intervention_reports.report_time IS '报告时间';
COMMENT ON COLUMN intervention_reports.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_film_order_id ON film_prints(order_id);
CREATE INDEX IF NOT EXISTS idx_intervention_order_id ON intervention_reports(order_id);

-- ----- 批次3: 新增表 -----

-- 核医学报告
CREATE TABLE IF NOT EXISTS nuclear_medicine_reports (
    report_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    patient_id VARCHAR(20) NOT NULL,
    visit_id VARCHAR(20),
    exam_type VARCHAR(20),              -- PET/ECT/SPECT
    exam_part VARCHAR(100),
    radiopharmaceutical VARCHAR(100),   -- 放射性药物
    injected_dose_mbq DECIMAL(8,2),     -- 注射剂量 MBq
    injected_time TIMESTAMP,
    uptake_rate VARCHAR(50),            -- 摄取率
    imaging_time TIMESTAMP,
    findings TEXT,
    impression TEXT,
    suv_max DECIMAL(6,2),               -- PET最大SUV值
    comparison_result VARCHAR(50),
    report_status VARCHAR(20),
    reporter_id VARCHAR(20),
    report_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE nuclear_medicine_reports IS '核医学报告：PET/ECT/SPECT 独立报告';
COMMENT ON COLUMN nuclear_medicine_reports.report_id IS '报告主键ID';
COMMENT ON COLUMN nuclear_medicine_reports.order_id IS '关联检查申请ID';
COMMENT ON COLUMN nuclear_medicine_reports.patient_id IS '患者ID';
COMMENT ON COLUMN nuclear_medicine_reports.visit_id IS '就诊ID';
COMMENT ON COLUMN nuclear_medicine_reports.exam_type IS '检查类型：PET/ECT/SPECT';
COMMENT ON COLUMN nuclear_medicine_reports.exam_part IS '检查部位';
COMMENT ON COLUMN nuclear_medicine_reports.radiopharmaceutical IS '放射性药物';
COMMENT ON COLUMN nuclear_medicine_reports.injected_dose_mbq IS '注射剂量（MBq）';
COMMENT ON COLUMN nuclear_medicine_reports.injected_time IS '注射时间';
COMMENT ON COLUMN nuclear_medicine_reports.uptake_rate IS '摄取率';
COMMENT ON COLUMN nuclear_medicine_reports.imaging_time IS '显像时间';
COMMENT ON COLUMN nuclear_medicine_reports.findings IS '影像所见';
COMMENT ON COLUMN nuclear_medicine_reports.impression IS '诊断意见';
COMMENT ON COLUMN nuclear_medicine_reports.suv_max IS '最大SUV值（PET）';
COMMENT ON COLUMN nuclear_medicine_reports.comparison_result IS '与既往对比';
COMMENT ON COLUMN nuclear_medicine_reports.report_status IS '报告状态';
COMMENT ON COLUMN nuclear_medicine_reports.reporter_id IS '报告医生ID';
COMMENT ON COLUMN nuclear_medicine_reports.report_time IS '报告时间';
COMMENT ON COLUMN nuclear_medicine_reports.create_time IS '记录创建时间';

CREATE INDEX IF NOT EXISTS idx_nuclear_order_id ON nuclear_medicine_reports(order_id);

-- ============================================================
-- 字典表 (Dictionary Tables)
-- 通过 meddata-gen dict-template / dict-import 命令由用户填写后导入
-- ============================================================

-- 检查项目字典
CREATE TABLE IF NOT EXISTS exam_items_dict (
    exam_item_code    VARCHAR(20) PRIMARY KEY,
    exam_item_name    VARCHAR(200) NOT NULL,
    exam_type         VARCHAR(20) NOT NULL,
    body_part         VARCHAR(50),
    contrast_required BOOLEAN DEFAULT FALSE,
    standard_price    NUMERIC(10,2),
    duration_min      INT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE exam_items_dict IS '检查项目字典:RIS 检查项目主数据';
COMMENT ON COLUMN exam_items_dict.exam_item_code IS '检查项目编码,主键';
COMMENT ON COLUMN exam_items_dict.exam_item_name IS '项目名称';
COMMENT ON COLUMN exam_items_dict.exam_type IS '检查类型:xray/ct/mri/us/nm/intervention';
COMMENT ON COLUMN exam_items_dict.body_part IS '检查部位';
COMMENT ON COLUMN exam_items_dict.contrast_required IS '是否需要造影剂';
COMMENT ON COLUMN exam_items_dict.standard_price IS '标准价格(元)';
COMMENT ON COLUMN exam_items_dict.duration_min IS '标准时长(分钟)';
COMMENT ON COLUMN exam_items_dict.created_at IS '导入时间';
