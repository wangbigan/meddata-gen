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
| `meddata-gen run-all` | 一键 init + generate + verify | `meddata-gen run-all --scale 0.5` |
| `meddata-gen verify` | 验证数据量、关联率、缺失率 | `meddata-gen verify` |
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

## 数据库概览

| 数据库 | 系统 | 核心表 | 数据量 (full) |
|--------|------|--------|--------------|
| `his_db` | 医院信息系统 | 患者、住院记录、门诊记录、医嘱、收费明细、药品字典、科室字典、人员字典、床位信息 | 50万+ 条 |
| `emr_db` | 电子病历系统 | 病历文档、病程记录、入院记录、出院记录、手术记录、护理记录 | 27万+ 条 |
| `bingan_db` | 病案系统 | 病案首页、诊断明细、手术明细、肿瘤登记 | 3.8万+ 条 |
| `lis_db` | 检验信息系统 | 检验申请、标本、临检结果、生化结果、血液结果、微生物、药敏试验 | 56万+ 条 |
| `ris_db` | 影像信息系统 | 影像设备、检查申请、普放报告、CT报告、MRI报告、超声报告 | 5.3万+ 条 |
| `ecg_db` | 心电信息系统 | 心电检查、波形数据、分析结果 | 4.5万 条 |
| `icu_monitoring_db` | ICU监护系统 | 入科记录、监护数据、报警记录、血气分析 | 56.7万+ 条 |

## 数据规模

- **患者数**: 5,000 人
- **时间范围**: 2023-01-01 至 2024-12-31（2年）
- **住院人次**: 8,000
- **门诊人次**: 20,000
- **检验申请**: 60,000
- **影像检查**: 25,000
- **心电检查**: 15,000
- **ICU入科**: 2,000

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

### 3. 逻辑矛盾（~1.5%）
- 出院时间早于入院时间
- 负值金额/数量
- 极端异常值

### 4. 格式不一致（~2%）
- 日期格式混用（`2023/01/01`、`01/01/2023`、`2023年1月1日`）
- 编码大小写混用

### 5. 编码不统一
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

# 随机种子（可复现生成）
RANDOM_SEED = 42
```

## Python API

```python
from meddata_gen import DataGenerator
from meddata_gen.config import DB_CONFIG

gen = DataGenerator(DB_CONFIG, seed=42).connect("his_db")
gen.generate_patients(5000)
gen.close()
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
│   ├── __init__.py          # DataGenerator 组合入口
│   ├── cli.py               # meddata-gen CLI
│   ├── config.py            # 数据库连接、数据规模、质量配置
│   ├── seed_data.py         # 种子数据字典
│   ├── schema/              # 7 个子系统的 DDL SQL
│   ├── core/
│   │   ├── base.py          # BaseGenerator（连接、缺陷注入工具）
│   │   └── orchestrator.py  # 多模块编排器
│   ├── generators/
│   │   ├── his.py           # HIS 生成器 Mixin
│   │   ├── emr.py           # EMR 生成器 Mixin
│   │   ├── bingan.py        # 病案生成器 Mixin
│   │   ├── lis.py           # LIS 生成器 Mixin
│   │   ├── ris.py           # RIS 生成器 Mixin
│   │   ├── ecg.py           # ECG 生成器 Mixin
│   │   └── icu.py           # ICU 生成器 Mixin
│   └── tools/
│       └── data_dict.py     # 数据字典生成工具
├── run_all.py               # 旧入口兼容外壳（调用 meddata_gen）
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
```
