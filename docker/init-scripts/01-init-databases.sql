-- 自动创建 meddata-gen 所需的 7 个子系统数据库
-- 此脚本由 PostgreSQL docker-entrypoint-initdb.d 机制在首次启动时执行

CREATE DATABASE his_db ENCODING 'UTF8';
CREATE DATABASE emr_db ENCODING 'UTF8';
CREATE DATABASE bingan_db ENCODING 'UTF8';
CREATE DATABASE lis_db ENCODING 'UTF8';
CREATE DATABASE ris_db ENCODING 'UTF8';
CREATE DATABASE ecg_db ENCODING 'UTF8';
CREATE DATABASE icu_monitoring_db ENCODING 'UTF8';

COMMENT ON DATABASE his_db IS 'HIS 医院信息系统：患者主索引、住院/门诊就诊、医嘱、收费、药品、科室、人员等核心业务数据';
COMMENT ON DATABASE emr_db IS 'EMR 电子病历系统：病历文档、病程记录、入院/出院记录、手术记录、护理记录等病历类数据';
COMMENT ON DATABASE bingan_db IS '病案系统：病案首页、诊断明细、手术明细、肿瘤登记，对接医保结算/DRG/质控';
COMMENT ON DATABASE lis_db IS 'LIS 检验信息系统：申请单/标本/临检/生化/血液/微生物/药敏等检验结果';
COMMENT ON DATABASE ris_db IS 'RIS 影像信息系统：检查申请、普放/CT/MRI/超声等影像报告及设备信息';
COMMENT ON DATABASE ecg_db IS 'ECG 心电信息系统：心电检查、波形参数、分析结果';
COMMENT ON DATABASE icu_monitoring_db IS 'ICU 监护系统：入科记录、监护仪时序数据、报警事件、血气分析';
