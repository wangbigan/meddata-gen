# meddata-gen: 医院信息系统模拟数据生成器

用于医疗数据治理/ETL系统测试的模拟医院源系统数据库，模拟国内三甲医院真实数据场景，包含真实的质量问题。

## 这个项目是做什么的？

简单来说，这个工具能帮你**批量造一家虚拟三甲医院的全部业务数据**。

医院信息系统不是一个大数据库，而是很多独立的子系统：挂号收费用 HIS、医生写病历用 EMR、抽血化验用 LIS、拍 CT 用 RIS、重症监护用 ICU……每个系统都有自己的数据库。真实的医疗数据治理/ETL项目，最大的痛点就是**数据分散在不同系统、格式不统一、还有各种各样的质量问题**。

这个工具做的就是：在你的电脑上一次性创建 7 个独立的数据库，每个库对应一个真实的医院子系统，然后往里面灌入**看起来像真数据、但其实是假的**模拟数据。这些数据不是随机乱填的——它们遵循真实的业务逻辑，同时故意埋入一些常见的质量问题（比如某些字段为空、跨系统关联不上、时间顺序颠倒等），用来测试你的 ETL 流程能不能正确识别和清洗。

### 核心生成逻辑

你可以把它理解成两种"造数据"的思路：

**第一种：传统模式（Legacy）—— 按表填数据**

想象一个新手在Excel里一张表一张表地填：先把患者信息表填完，再填住院记录表，再填医嘱表……每张表独立生成，最后靠随机概率让某些字段关联起来。这种模式简单粗暴，适合快速生成大量测试数据，但缺陷是**不同表之间的数据缺乏内在逻辑**——比如一个患者昨天刚出院，今天的门诊记录却还在给他开住院医嘱。

**第二种：事件模式（Event）—— 模拟真实就诊流程**

这个模式更像是在"演一场戏"：先造一批虚拟患者，每个人分配一个基础疾病（比如高血压、糖尿病、骨折等）。然后模拟他们去医院的完整旅程——挂号、看病、做检查、开药、住院、手术、出院、结算。同一次就诊产生的所有数据（挂号记录、检验申请、CT报告、病历、收费明细等）自动分发到各个子系统的数据库中，**patient_id 和 visit_id 天然一致**。

事件模式还自带一个**临床规则引擎**（可选开启）：
- 患者画像绑定：50 岁男性不会被分配到"正常分娩"，但 10% 的异常数据会故意打破这个规则
- 科室匹配：高血压挂心内科，骨折去骨科，但 5% 会模拟挂错号
- 就诊率模拟：不是每个挂号都会变成真实就诊，约 8% 的门诊会退号或爽约
- 混合绑定：80% 的就诊看基础病，20% 看新发疾病

两种模式生成的数据，都可以**故意弄脏**：某些字段随机置空、跨系统关联断裂、时间顺序颠倒、日期格式混用、逻辑矛盾等。这些缺陷不是随机撒盐，而是按照真实场景中常见的数据质量问题模式来设计的。

## 快速开始

```bash
pip install -e ".[dev]"

# 一键创建数据库 + 加载内置字典 + 生成数据 + 验证
meddata-gen init
meddata-gen dict-import --use-builtin
meddata-gen generate --scale small
meddata-gen verify

# 或一键执行全部(自动加载内置字典需手动先执行 dict-import)
meddata-gen run-all --scale small
```

> **注意**: `init` 初始化后会提示先导入字典表。可通过 `dict-import --use-builtin` 快速加载内置示例字典,或先用 `dict-template` 导出 Excel 模板自行填写后再导入。

## 环境要求

- Python 3.8+
- 任意可访问的 PostgreSQL 14+ 实例（本地、Docker、云数据库均可）

### 方式一：Docker 快速启动（可选）

如果你没有现成的 PostgreSQL，可用项目自带的 Docker Compose 一键启动：

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 启动 PostgreSQL（自动创建 7 个数据库）
docker compose up -d

# 3. 安装 meddata-gen
pip install -e ".[dev]"
```

停止数据库：
```bash
docker compose down
# 保留数据卷：下次 up 数据还在
# 彻底删除数据：docker compose down -v
```

> 如果 5432 端口已被占用，修改 `.env` 中的 `MEDDATA_DB_PORT=5433`，并在 `docker compose up -d` 前执行 `export MEDDATA_DB_PORT=5433`。

### 方式二：连接已有 PostgreSQL

如果你已有 PostgreSQL（本地、局域网或云数据库），只需配置连接参数即可：

```bash
pip install -e ".[dev]"
```

## 数据库连接配置

连接参数优先从**环境变量**读取，其次回退到 `meddata_gen/config.py` 中的默认值。

### 通过环境变量配置（推荐）

```bash
cp .env.example .env
# 编辑 .env 填入实际的数据库地址、端口、账号密码
```

环境变量名：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MEDDATA_DB_HOST` | `127.0.0.1` | 数据库主机（IP 或域名） |
| `MEDDATA_DB_PORT` | `5432` | 端口 |
| `MEDDATA_DB_USER` | `wbg` | 用户名 |
| `MEDDATA_DB_PASSWORD` | `""` | 密码 |
| `MEDDATA_DB_NAME` | `postgres` | 管理数据库名 |

示例（连接远程数据库）：
```bash
export MEDDATA_DB_HOST=192.168.1.100
export MEDDATA_DB_PORT=5432
export MEDDATA_DB_USER=meddata
export MEDDATA_DB_PASSWORD=secret
export MEDDATA_DB_NAME=postgres
```

### 远程数据库注意事项

- 账号需具备 `CREATEDB` 权限（`init` 命令会自动创建 7 个子数据库）
- 确保网络可达（防火墙/安全组放行对应端口）
- 如果使用云数据库（RDS、Cloud SQL 等），建议手动创建 7 个数据库，然后仅使用 `generate` 命令生成数据，跳过 `init`

## CLI 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `meddata-gen init` | 创建数据库 + 初始化表结构 | `meddata-gen init --module his,emr` |
| `meddata-gen dict-template` | 导出字典填写模板 (Excel) | `meddata-gen dict-template -o dict.xlsx` |
| `meddata-gen dict-import` | 导入字典数据或加载内置示例 | `meddata-gen dict-import -f dict.xlsx` / `--use-builtin` |
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

## 字典数据管理

项目包含 8 张字典表，分布在 HIS/LIS/RIS 三个数据库中，用于为主业务表提供可校验的主数据（ICD-10 诊断、手术编码、检验项目、检查项目等）。`init` 完成后字典表为空，必须先导入数据才能进行真实的模拟数据生成。

### 方案 A: 使用内置示例字典（推荐快速体验）

```bash
meddata-gen dict-import --use-builtin
```

一键写入全部 8 张字典表，数据来源于项目 `seed_data.py` 中的常量（ICD-10 诊断 ~120 条、检验项目 ~70 条、微生物 ~30 条、抗生素 ~42 条、影像检查 ~60 条，以及硬编码的手术/医嘱/收费项目）。

### 方案 B: 自定义字典（推荐生产环境）

```bash
# 1. 导出 Excel 模板
meddata-gen dict-template -o dict_template.xlsx

# 2. 用 Excel 打开模板，按 sheet 填写或修改
#    - 必填列标红带 *，下拉列可选值已预置
#    - 可只填写需要的 sheet，未填写的导入时自动跳过

# 3. 导入（dry-run 先校验）
meddata-gen dict-import -f dict_template.xlsx --dry-run
meddata-gen dict-import -f dict_template.xlsx

# 4. 仅导入 LIS 子系统
meddata-gen dict-import -f dict_template.xlsx --system lis

# 5. 生成导入报告
meddata-gen dict-import -f dict_template.xlsx --report reports/dict_import.md
```

### 导入模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `upsert` (默认) | 主键冲突时更新，无冲突时插入 | 日常增量更新 |
| `replace` | 先 TRUNCATE 再全量插入 | 需要完全重置字典 |
| `append` | 仅插入，主键冲突时报错 | 严格追加新数据 |

### 字典表清单

| 字典表 | 数据库 | 说明 |
|--------|--------|------|
| `diagnosis_dict` | his_db | ICD-10 诊断编码 |
| `surgery_dict` | his_db | ICD-9-CM3 手术编码 |
| `order_items_dict` | his_db | 医嘱项目主数据 |
| `charge_items_dict` | his_db | 收费项目主数据 |
| `lab_items_dict` | lis_db | 检验项目（含 LOINC） |
| `organism_dict` | lis_db | 微生物菌株 |
| `antibiotic_dict` | lis_db | 抗生素 |
| `exam_items_dict` | ris_db | RIS 检查项目 |

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
