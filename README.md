# meddata-gen: 医院信息系统模拟数据生成器

用于医疗数据治理/ETL系统测试的模拟医院源系统数据库，模拟国内三甲医院真实数据场景，包含真实的质量问题。

## 快速开始

```bash
pip install -e .

# 一键创建数据库 + 生成数据 + 验证
meddata-gen run-all

# 或分步执行
meddata-gen init
meddata-gen generate
meddata-gen verify
```

## 项目说明

本工具在本地 PostgreSQL 中创建 7 个独立的医院源系统数据库，模拟 HIS/EMR/LIS/RIS/ECG/ICU/病案等系统的数据结构及数据交互关系。数据包含可控的空置率、关联断裂、逻辑矛盾等缺陷，用于验证 ETL 流程的数据采集、映射、清洗、质控和发布能力。

## 环境要求

- Python 3.8+
- PostgreSQL 14+ (本地运行，端口 5432)

```bash
pip install -e .
```

## 数据库连接配置

修改 `meddata_gen/config.py` 中的 `DB_CONFIG`：

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "wbg",
    "password": "",
    "database": "postgres",
}
```

## CLI 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `meddata-gen init` | 创建数据库 + 初始化表结构 | `meddata-gen init --module his,emr` |
| `meddata-gen generate` | 生成模拟数据 | `meddata-gen generate --scale small --seed 42` |
| `meddata-gen run-all` | 一键 init + generate + verify | `meddata-gen run-all --scale 0.5 --enable-rules` |
| `meddata-gen verify` | 验证数据量、关联率、缺失率 | `meddata-gen verify` |
| `meddata-gen assess` | 生成数据质量评估报告 (Markdown) | `meddata-gen assess -o reports/q.md` |
| `meddata-gen reset` | 删除全部模拟数据库（高危） | `meddata-gen reset --yes` |
| `meddata-gen docs` | 生成 markdown 数据字典 | `meddata-gen docs -o reports/dd.md` |

### 规模档位

| 档位 | 乘数 | 用途 |
|------|------|------|
| `tiny` | 0.01 | 冒烟测试 |
| `small` | 0.10 | 快速调试 |
| `medium` | 0.50 | 功能验证 |
| `full` | 1.00 | 完整生成 |

也支持直接传入数字：`--scale 0.25`

### 模块列表

- `his` — 医院信息系统
- `emr` — 电子病历系统
- `bingan` — 病案系统
- `lis` — 检验信息系统
- `ris` — 影像信息系统
- `ecg` — 心电信息系统
- `icu` — ICU 监护系统

非 HIS 模块会自动复用 HIS 生成的 patients/staff/departments 等核心数据，确保跨库关联率真实。

## 双模式数据生成

### Legacy 模式（默认）

按表独立填充，每个 Mixin 生成自己的表数据。适合快速生成大量测试数据。

```bash
meddata-gen generate --mode legacy --scale small
```

### Event 模式（事件驱动患者旅程）

模拟真实的患者就诊流程，一次就诊产生跨系统的、有时间因果链的数据。

```bash
# 事件驱动 + PostgreSQL 输出
meddata-gen generate --mode event --scale small

# 事件驱动 + CSV 输出（无需数据库）
meddata-gen generate --mode event --scale tiny --output-format csv --output-dir output/csv

# 事件驱动 + FHIR R4 Bundle 输出
meddata-gen generate --mode event --scale tiny --output-format fhir --output-dir output/fhir
```

### 临床规则引擎（`--enable-rules`）

启用规则引擎后，事件模式的数据生成将遵循临床逻辑约束，显著降低"男性看妇科"、"成年人去儿科"等不合理场景：

```bash
# 启用规则引擎
meddata-gen generate --mode event --scale small --enable-rules

# 配合 run-all 使用
meddata-gen run-all --mode event --scale small --enable-rules
```

**规则引擎核心能力：**

| 规则 | 默认值 | 说明 |
|------|--------|------|
| 患者-疾病画像绑定率 | 90% | 患者主病符合年龄/性别约束；10% 为异常数据 |
| 基础病就诊率 | 80% | 每次就诊使用基础病；20% 为新发疾病 |
| 科室匹配准确率 | 95% | 按疾病画像挂对应科室；5% 模拟挂错号 |
| 门诊就诊率 | 92% | 8% 未就诊（70% 退号 + 30% 爽约） |
| 住院入院率 | 95% | 5% 取消入院（60% 主动取消 + 40% 爽约） |

**85+ 疾病画像覆盖：** 心血管、呼吸、消化、内分泌、神经、肾脏、风湿免疫、血液、普外、骨科、心胸、泌尿、神外、妇科、产科、儿科、肿瘤、眼科/耳鼻喉/口腔、急诊、皮肤、精神等 21 个科室类别。

**全局配置：** 在 `config.py` 的 `BUSINESS_RULES` 中调整参数。

**事件驱动特性：**
- 疾病画像驱动：诊断决定检验异常模式、用药、手术概率、ICU 概率、住院天数
- 临床规则引擎（可选）：患者画像与疾病绑定、就诊率与退号率、混合绑定模型
- 时间因果链：申请时间 < 采集时间 < 结果时间 < 出院时间
- 跨系统一致性：同一次就诊的 patient_id / visit_id 在所有子系统中保持一致

## 多格式输出

| 格式 | 说明 | CLI 选项 |
|------|------|----------|
| PostgreSQL | 写入 7 个独立数据库（默认） | `--output-format postgres` |
| CSV | 输出到 `output/{system}/{table}.csv` | `--output-format csv` |
| FHIR R4 | 每患者一个 Bundle JSON | `--output-format fhir` |

## 质量评估报告

生成 Markdown 格式的数据质量评估报告，包含 5 个维度：

1. **统计保真度** — 年龄分布、科室住院量、检验项分布
2. **时间一致性** — 因果逆序事件数量（结果时间 < 申请时间等）
3. **跨系统关联率** — 各系统 `patient_id` 在 HIS 中的命中率
4. **临床一致性** — 疾病组 vs 对照组的检验值差异（如肺炎患者 WBC 显著升高）
5. **缺陷场景命中率** — 预定义场景实际触发的记录数与比例

```bash
meddata-gen assess -o reports/quality_report.md
cat reports/quality_report.md
```

## 数据库概览

| 数据库 | 系统 | 核心表 | 数据量 (full) |
|--------|------|--------|--------------|
| `his_db` | 医院信息系统 | 患者、住院/门诊记录、医嘱、收费明细、挂号、转科、结算、预交金、药品/科室/人员/床位字典 | 80万+ 条 |
| `emr_db` | 电子病历系统 | 病历文档、病程记录、入院/出院/死亡记录、手术记录、会诊、护理记录、输血记录、知情同意书、护理评估 | 35万+ 条 |
| `bingan_db` | 病案系统 | 病案首页、诊断明细、手术明细、肿瘤登记、病案借阅、质控缺陷、产科记录 | 5万+ 条 |
| `lis_db` | 检验信息系统 | 检验申请、标本、临检/生化/血液/免疫/分子结果、微生物、药敏、报告主表、危急值、室内质控 | 65万+ 条 |
| `ris_db` | 影像信息系统 | 检查申请、普放/CT/MRI/超声/核医学报告、介入报告、影像序列、胶片打印、设备字典 | 10万+ 条 |
| `ecg_db` | 心电信息系统 | 心电检查、波形数据、分析结果、Holter记录/事件、运动平板记录 | 5万+ 条 |
| `icu_monitoring_db` | ICU监护系统 | 入科记录、监护数据、呼吸机设置、出入量、血气分析、CRRT、镇静镇痛、气管插管、报警记录 | 60万+ 条 |

## 数据规模（full 档位）

| 指标 | 数量 |
|------|------|
| 患者数 | 5,000 |
| 时间范围 | 2023-01-01 ~ 2024-12-31（2年）|
| 住院人次 | 8,000 |
| 门诊人次 | 20,000 |
| 挂号记录 | 30,000 |
| 医嘱 | 120,000 |
| 收费明细 | 300,000 |
| 检验申请 | 60,000 |
| 影像检查 | 25,000 |
| 心电检查 | 15,000 |
| Holter 记录 | 3,000 |
| 运动平板 | 2,000 |
| ICU 入科 | 2,000 |
| 手术记录 | 4,000 |
| 肿瘤登记 | 300 |
| 总记录数 | ~260万+ 条 |

## 模拟的数据质量问题

### 1. 字段空置率（0% ~ 20%）
- 各系统按配置有不同的基础空置率
- 按字段重要性分级（critical/normal/optional）
- 示例：`his_db.patients` 中 phone 9.5%、address 14.6%、id_card 12.6% 为空

### 2. 跨系统关联率（70% ~ 100%）
- 各系统通过 `patient_id` / `visit_id` 与 HIS 关联
- 模拟部分系统数据未对接或历史数据缺失

| 系统 | 关联率 |
|------|--------|
| EMR | ~85% |
| 病案 | ~95% |
| LIS | ~90% |
| RIS | ~85% |
| ECG | ~80% |
| ICU | ~90% |

### 3. 场景化缺陷注入（事件模式）

与均匀随机缺陷不同，场景化缺陷模拟的是有明确业务根因的数据问题。在 `config.py` 中启用：

```python
from meddata_gen.quality.scenarios import PREDEFINED_SCENARIOS
QUALITY_SCENARIOS = PREDEFINED_SCENARIOS
```

预定义场景：

| 场景 | 目标系统/表 | 缺陷类型 | 时间范围 |
|------|------------|---------|---------|
| LIS 系统升级 outage | `lis_db.microbiology` | culture_result 95% 为空 | 2023-06-01 ~ 2023-06-15 |
| RIS-HIS 接口切换映射错误 | `ris_db.exam_orders` | patient_id 5% 映射错误 | 2024-01-01 ~ 2024-01-31 |
| ICU 监护仪时钟漂移 | `icu_monitoring_db.monitoring_data` | monitor_time 15% 时间错乱 | 2023-08-01 ~ 2023-08-15 |
| EMR 模板复制粘贴重复 | `emr_db.progress_notes` | content 3% 批量重复 | 全时段 |
| HIS 收费接口延迟 | `his_db.fee_items` | fee_time 8% 时间倒挂 | 2023-03-01 ~ 2023-03-10 |

### 4. 逻辑矛盾（~1.5%）
- 出院时间早于入院时间
- 负值金额/数量
- 极端异常值

### 5. 格式不一致（~2%）
- 日期格式混用（`2023/01/01`、`01/01/2023`、`2023年1月1日`）
- 编码大小写混用

### 6. 编码不统一
- ICD-10 为主，混入少量 ICD-9 历史编码
- 同一科室在不同系统使用不同编码

## 自定义配置

编辑 `meddata_gen/config.py` 调整数据规模和质量：

```python
# 数据规模
SYSTEM_SCALE = {
    "his_db": {"patients": 5000, "inpatients": 8000, ...},
    ...
}

# 数据质量
QUALITY = {
    "null_rate_range": (0.0, 0.20),      # 空置率范围
    "link_rate_range": (0.70, 1.00),     # 关联率范围
    "logic_error_rate": 0.015,            # 逻辑矛盾比例
    "format_inconsistency_rate": 0.02,    # 格式不一致比例
}

# 场景化缺陷（默认禁用）
QUALITY_SCENARIOS = []  # 设为 PREDEFINED_SCENARIOS 启用

# 随机种子（可复现生成）
RANDOM_SEED = 42
```

## Python API

### Legacy 模式

```python
from meddata_gen import DataGenerator
from meddata_gen.config import DB_CONFIG

gen = DataGenerator(DB_CONFIG, seed=42).connect("his_db")
gen.generate_patients(5000)
gen.close()
```

### Event 模式

```python
from meddata_gen.generators.event_driven import EventDrivenGenerator
from meddata_gen.config import DB_CONFIG

gen = EventDrivenGenerator(DB_CONFIG, seed=42)
gen.generate_departments()
gen.generate_staff(200)
gen.generate_drugs(500)
gen.generate_patients(5000)
gen.generate_beds()
gen.generate_journeys(inpatient_count=8000, outpatient_count=20000)
```

### 质量评估

```python
from meddata_gen.quality.assessor import QualityAssessor
from meddata_gen.config import DB_CONFIG

assessor = QualityAssessor(DB_CONFIG)
report = assessor.run()
print(report)
```

## 重新生成

如需清空并重跑：

```bash
meddata-gen reset --yes
meddata-gen run-all
```

## 文件结构

```
meddata_gen/
├── meddata_gen/
│   ├── __init__.py              # DataGenerator / EventDrivenGenerator 入口
│   ├── cli.py                   # meddata-gen CLI（7 个子命令）
│   ├── config.py                # 数据库连接、数据规模、质量配置
│   ├── seed_data.py             # 种子数据字典
│   ├── schema/                  # 7 个子系统的 DDL SQL
│   ├── core/
│   │   ├── base.py              # BaseGenerator（连接、缺陷注入工具）
│   │   ├── orchestrator.py      # 多模块编排器（Legacy/Event 双模式）
│   │   ├── events.py            # 事件模型（MedicalEvent / EventContext）
│   │   ├── journey_builder.py   # 患者旅程构建器
│   │   ├── materializer.py      # 事件物化层（事件 → 行数据 → 输出）
│   │   ├── handlers/            # 各系统事件处理器
│   │   │   ├── _common.py       # Handler 公共工具
│   │   │   ├── his_handlers.py
│   │   │   ├── lis_handlers.py
│   │   │   ├── ris_handlers.py
│   │   │   ├── emr_handlers.py
│   │   │   ├── bingan_handlers.py
│   │   │   ├── icu_handlers.py
│   │   │   └── ecg_handlers.py
│   ├── generators/
│   │   ├── his.py               # HIS 生成器 Mixin（12 个方法）
│   │   ├── emr.py               # EMR 生成器 Mixin（12 个方法）
│   │   ├── bingan.py            # 病案生成器 Mixin（7 个方法）
│   │   ├── lis.py               # LIS 生成器 Mixin（12 个方法）
│   │   ├── ris.py               # RIS 生成器 Mixin（10 个方法）
│   │   ├── ecg.py               # ECG 生成器 Mixin（6 个方法）
│   │   ├── icu.py               # ICU 生成器 Mixin（9 个方法）
│   │   └── event_driven.py      # EventDrivenGenerator
│   ├── clinical/
│   │   ├── disease_profiles.py  # ~85 种疾病画像定义
│   │   ├── patient_health.py    # 患者健康档案（疾病绑定）
│   │   └── lab_generator.py     # 疾病感知检验值生成器
│   ├── core/
│   │   ├── base.py              # BaseGenerator（连接、缺陷注入工具）
│   │   ├── orchestrator.py      # 多模块编排器（Legacy/Event 双模式）
│   │   ├── rule_engine.py       # 临床规则引擎
│   │   ├── events.py            # 事件模型（MedicalEvent / EventContext）
│   │   ├── journey_builder.py   # 患者旅程构建器
│   │   ├── materializer.py      # 事件物化层（事件 → 行数据 → 输出）
│   │   └── handlers/            # 各系统事件处理器
│   ├── quality/
│   │   ├── scenarios.py         # 场景化缺陷定义
│   │   ├── defect_engine.py     # 缺陷注入引擎
│   │   ├── assessor.py          # 质量评估器
│   │   └── metrics.py           # 质量指标数据结构
│   ├── output/
│   │   ├── base.py              # OutputWriter 抽象基类
│   │   ├── postgres.py          # PostgreSQL 写入器
│   │   ├── csv.py               # CSV 写入器
│   │   └── fhir.py              # FHIR R4 Bundle 写入器
│   └── tools/
│       └── data_dict.py         # 数据字典生成工具
├── docs/
│   └── CLI.md                   # CLI 详细文档
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 验证示例

```sql
-- 连接各数据库查看表行数
\c his_db
\dt
SELECT COUNT(*) FROM patients;

-- 检查缺失率
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE phone IS NULL) as null_phone,
    COUNT(*) FILTER (WHERE address IS NULL) as null_address
FROM patients;

-- 检查跨库关联率（在 postgres 库执行）
SELECT
    (SELECT COUNT(*) FROM emr_db.public.emr_documents
     WHERE patient_id IN (SELECT patient_id FROM his_db.public.patients)) * 1.0 /
    (SELECT COUNT(*) FROM emr_db.public.emr_documents);

-- 事件模式：验证时间因果（检验结果时间 >= 申请时间）
SELECT COUNT(*) FROM lis_db.public.routine_results r
JOIN lis_db.public.lab_orders o ON o.order_id = r.order_id
WHERE r.result_time < o.order_time;

-- 事件模式：验证肺炎患者的 WBC 均值
SELECT AVG(result_num) FROM lis_db.public.routine_results
WHERE item_name = '白细胞计数'
  AND patient_id IN (
      SELECT patient_id FROM his_db.public.inpatient_visits
      WHERE admission_diagnosis LIKE '%肺炎%'
  );

-- 规则引擎：验证妇科患者性别（应为 ~95% 女性）
SELECT p.gender, COUNT(*)
FROM his_db.public.patients p
JOIN his_db.public.outpatient_visits v ON p.patient_id = v.patient_id
WHERE v.dept_id = 'DEPT019'
GROUP BY p.gender;

-- 规则引擎：验证就诊率（挂号中应有 ~8% 未就诊）
SELECT status, COUNT(*)
FROM his_db.public.registrations
GROUP BY status;

-- 规则引擎：验证跨系统一致性（关联率应为 100%）
SELECT COUNT(*) FILTER (WHERE o.patient_id NOT IN (
    SELECT patient_id FROM his_db.public.patients
)) as unlinked
FROM lis_db.public.lab_orders o;
```
