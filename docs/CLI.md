# meddata-gen CLI 详细文档

本文档详细介绍 `meddata-gen` 命令行工具的每个子命令、参数及其实现逻辑。

---

## 目录

- [命令总览](#命令总览)
- [init — 数据库初始化](#init--数据库初始化)
- [generate — 数据生成](#generate--数据生成)
- [run-all — 一键执行](#run-all--一键执行)
- [verify — 数据验证](#verify--数据验证)
- [assess — 质量评估报告](#assess--质量评估报告)
- [reset — 删除数据库](#reset--删除数据库)
- [docs — 数据字典](#docs--数据字典)
- [公共工具函数](#公共工具函数)
- [典型工作流](#典型工作流)

---

## 命令总览

```
meddata-gen [全局选项] <子命令> [子命令选项]
```

| 子命令 | 功能 | 核心文件 |
|--------|------|----------|
| `init` | 创建数据库 + 执行 DDL | `cli.py:cmd_init` |
| `generate` | 生成模拟数据 | `cli.py:cmd_generate` |
| `run-all` | init + generate + verify 串联 | `cli.py:cmd_run_all` |
| `verify` | 统计表行数 + 跨库关联率 | `cli.py:cmd_verify` |
| `assess` | 生成 Markdown 质量报告 | `cli.py:cmd_assess` |
| `reset` | 删除全部 7 个数据库 | `cli.py:cmd_reset` |
| `docs` | 生成 Markdown 数据字典 | `cli.py:cmd_docs` |

全局选项：
- `--version` — 显示版本号
- `--help` — 显示帮助信息

---

## init — 数据库初始化

### 用法

```bash
meddata-gen init [选项]
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-m, --module` | 可重复 | `all` | 目标模块，支持逗号分隔多次传入 |
| `--dry-run` | flag | False | 只打印计划，不实际执行 |

### 模块可选值

`his`, `emr`, `bingan`, `lis`, `ris`, `ecg`, `icu`, `all`

```bash
# 初始化全部模块
meddata-gen init

# 只初始化 HIS 和 LIS
meddata-gen init -m his -m lis
meddata-gen init -m his,lis

# 只打印计划
meddata-gen init --dry-run
```

### 实现逻辑

**源码位置**: `meddata_gen/cli.py:cmd_init`

```
1. _parse_modules(modules)
   - 解析 --module 参数，去重保序
   - 支持 'all' 展开为全部 7 个模块

2. _check_connection(config.DB_CONFIG)
   - 尝试连接 PostgreSQL，失败则退出

3. orchestrator.create_databases(config.DB_CONFIG, dbs=target_dbs)
   - 遍历目标数据库，执行 CREATE DATABASE IF NOT EXISTS
   - 同时写入 COMMENT ON DATABASE

4. orchestrator.init_schema(config.DB_CONFIG, db_name)
   - 对每个数据库，通过 importlib.resources 读取 schema/*.sql
   - 使用 DataGenerator.connect(db_name) 执行 DDL
   - 所有 schema 使用 CREATE TABLE IF NOT EXISTS，支持重复执行
```

**依赖**: 需要本地 PostgreSQL 服务已启动，且 DB_CONFIG 中的用户有创建数据库权限。

---

## generate — 数据生成

### 用法

```bash
meddata-gen generate [选项]
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-m, --module` | 可重复 | `all` | 目标模块（legacy 模式有效） |
| `-s, --scale` | string | `full` | 规模档位或浮点数 |
| `--seed` | int | None | 随机种子，覆盖配置 |
| `--dry-run` | flag | False | 只打印计划 |
| `--mode` | choice | `legacy` | `legacy` / `event` |
| `--output-format` | choice | `postgres` | `postgres` / `csv` / `fhir`（event 模式有效） |
| `--output-dir` | string | None | CSV/FHIR 输出目录 |
| `--enable-rules` | flag | False | 启用临床规则引擎（仅 event 模式有效） |

### 规模档位

| 档位 | 乘数 | 用途 |
|------|------|------|
| `tiny` | 0.01 | 冒烟测试，约 50 患者 |
| `small` | 0.10 | 快速调试，约 500 患者 |
| `medium` | 0.50 | 功能验证，约 2500 患者 |
| `full` | 1.00 | 完整生成，5000 患者 |

也支持直接传入数字：`--scale 0.25`

### 用法示例

```bash
# Legacy 模式，全部模块，full 规模
meddata-gen generate

# Legacy 模式，指定模块和规模
meddata-gen generate -m his,emr -s small --seed 42

# Event 模式，PostgreSQL 输出
meddata-gen generate --mode event -s small --seed 42

# Event 模式，CSV 输出（无需数据库连接）
meddata-gen generate --mode event -s tiny --output-format csv --output-dir output/csv

# Event 模式，FHIR R4 Bundle 输出
meddata-gen generate --mode event -s tiny --output-format fhir --output-dir output/fhir

# Event 模式 + 规则引擎（推荐）
meddata-gen generate --mode event -s small --seed 42 --enable-rules
```

### 实现逻辑

**源码位置**: `meddata_gen/cli.py:cmd_generate`

```
1. _resolve_scale(scale_arg)
   - 如果是档位名（tiny/small/medium/full），返回对应乘数
   - 否则尝试解析为浮点数

2. 分支判断 mode:

   mode == "event":
     - 调用 orchestrator.run_event_driven()
     - 如果指定 --enable-rules:
         - 创建 ClinicalRuleEngine 实例
         - 患者生成时绑定 DiseaseProfile（90% 匹配年龄/性别）
         - 就诊时按疾病画像选择科室（95% 准确率）
         - 应用就诊率过滤（8% 门诊未就诊，5% 住院取消）
     - 内部创建 EventDrivenGenerator
     - Phase 1: 生成基础字典（departments/staff/drugs/patients/beds）
     - Phase 2: 为每个患者构建就诊旅程（JourneyBuilder）
     - 事件通过 Materializer 物化为行数据
     - 根据 output-format 选择 writer:
         postgres -> PostgresWriter（批量 INSERT）
         csv      -> CSVWriter（文件系统输出）
         fhir     -> FHIRBundleWriter（JSON Bundle）

   mode == "legacy":
     - 调用 orchestrator.Orchestrator.run(modules)
     - 按 MODULE_PIPELINES 定义的顺序执行
     - HIS 始终第一个执行，其他模块通过 _share_state() 复用 HIS 状态
     - 每个模块独立连接到各自的数据库
```

### Legacy vs Event 模式对比

| 维度 | Legacy | Event |
|------|--------|-------|
| 数据生成方式 | 按表独立填充 | 按患者就诊旅程生成 |
| 时间一致性 | 较弱（随机时间戳） | 强（申请→采集→结果→出院因果链） |
| 跨系统关联 | 通过 _should_link 概率关联 | 同一 visit_id 天然一致 |
| 疾病画像 | 不适用 | 驱动检验异常、用药、手术概率 |
| 临床规则引擎 | 不适用 | `--enable-rules` 可选开启 |
| 患者-疾病绑定 | 随机分配 | 90% 匹配年龄/性别，10% 异常 |
| 就诊率模拟 | 不适用 | 8% 门诊未就诊，5% 住院取消 |
| 场景缺陷 | 均匀撒盐 | 按业务根因集中注入 |
| 输出格式 | 仅 PostgreSQL | PostgreSQL / CSV / FHIR |
| 适用场景 | 快速生成大量数据 | 模拟真实业务流程 |

---

## run-all — 一键执行

### 用法

```bash
meddata-gen run-all [选项]
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-s, --scale` | string | `full` | 规模档位 |
| `--seed` | int | None | 随机种子 |
| `--skip-init` | flag | False | 跳过 init（数据库已存在） |
| `--skip-verify` | flag | False | 跳过 verify |
| `--mode` | choice | `legacy` | 生成模式 |
| `--output-format` | choice | `postgres` | 事件模式输出格式 |
| `--output-dir` | string | None | CSV/FHIR 输出目录 |
| `--enable-rules` | flag | False | 启用临床规则引擎（仅 event 模式有效） |

### 用法示例

```bash
# 完整流程
meddata-gen run-all

# 跳过 init，使用 event 模式
meddata-gen run-all --skip-init --mode event -s small

# CSV 输出
meddata-gen run-all --mode event --output-format csv --output-dir ./data

# 启用规则引擎（推荐用于事件模式）
meddata-gen run-all --mode event -s small --enable-rules
```

### 实现逻辑

**源码位置**: `meddata_gen/cli.py:cmd_run_all`

```
1. 如果未指定 --skip-init:
   - ctx.invoke(cmd_init, modules=(), dry_run=False)

2. ctx.invoke(cmd_generate, ...)
   - 将所有参数透传给 generate
   - 包含 `--enable-rules` 时，事件模式会创建 ClinicalRuleEngine

3. 如果未指定 --skip-verify:
   - ctx.invoke(cmd_verify)
```

`run-all` 是 `init` + `generate` + `verify` 的串联，通过 Click 的 `ctx.invoke()` 实现命令复用，避免代码重复。

---

## verify — 数据验证

### 用法

```bash
meddata-gen verify
```

无参数。

### 输出内容

1. **各表行数统计** — 遍历 7 个数据库的 public schema，统计每张表的行数
2. **跨库关联率** — 计算各系统 `patient_id` 在 `his_db.patients` 中的命中率

### 实现逻辑

**源码位置**: `meddata_gen/cli.py:cmd_verify`

```
1. 连接 his_db，读取全部 patient_id 到内存集合

2. 对每个非 HIS 数据库的核心表:
   - 连接目标数据库
   - SELECT patient_id FROM {table}
   - 计算命中 his_patients 集合的比例
   - 输出: emr_db.emr_documents: 85.23% (8523/10000)

3. 输出示例:
   === 各表行数 ===
     [his_db]
       patients: 5,000 rows
       inpatient_visits: 8,000 rows
       ...

   === 跨库关联率（patient_id -> his_db.patients） ===
     emr_db.emr_documents: 85.23% (8523/10000)
     lis_db.lab_orders: 90.15% (9015/10000)
     ...
```

---

## assess — 质量评估报告

### 用法

```bash
meddata-gen assess [选项]
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-o, --output` | string | `reports/quality_report.md` | 输出文件路径 |

### 用法示例

```bash
meddata-gen assess
meddata-gen assess -o reports/q.md
```

### 实现逻辑

**源码位置**: `meddata_gen/cli.py:cmd_assess` → `meddata_gen/quality/assessor.py`

```
1. 创建 QualityAssessor 实例，传入 DB_CONFIG

2. assessor.run() 执行以下评估:
   a. 统计保真度 — 年龄分布、科室就诊量、检验值分布
   b. 时间一致性 — 因果逆序事件数量（结果时间 < 申请时间）
   c. 跨系统关联率 — 各系统 patient_id 命中率
   d. 临床一致性 — 疾病组 vs 对照组检验值差异
   e. 缺陷场景命中率 — 预定义场景实际触发记录数

3. 将报告写入 Markdown 文件
```

报告包含表格和趋势描述，可直接用于文档或展示。

---

## reset — 删除数据库

### 用法

```bash
meddata-gen reset [选项]
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--yes` | flag | False | 跳过确认提示 |

### 用法示例

```bash
# 交互式确认
meddata-gen reset

# 强制删除，无需确认
meddata-gen reset --yes
```

### 实现逻辑

**源码位置**: `meddata_gen/cli.py:cmd_reset`

```
1. 如果未指定 --yes:
   - click.confirm() 提示用户确认
   - 用户选择 No 则 abort

2. _check_connection(config.DB_CONFIG)

3. orchestrator.drop_databases(config.DB_CONFIG)
   - 对每个数据库:
     - pg_terminate_backend() 强制断开连接
     - DROP DATABASE IF EXISTS
```

⚠️ **高危操作**，会删除 `config.DATABASES` 中定义的全部 7 个数据库。

---

## docs — 数据字典

### 用法

```bash
meddata-gen docs [选项]
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-o, --output` | string | `reports/data_dictionary.md` | 输出文件路径 |

### 用法示例

```bash
meddata-gen docs
meddata-gen docs -o docs/dd.md
```

### 实现逻辑

**源码位置**: `meddata_gen/cli.py:cmd_docs` → `meddata_gen/tools/data_dict.py`

```
1. 连接各数据库，读取 information_schema.columns
2. 提取表名、列名、数据类型、注释（COMMENT ON COLUMN）
3. 按数据库/表组织为 Markdown 表格
4. 写入输出文件
```

---

## 公共工具函数

### `_parse_modules(modules)`

**位置**: `cli.py:26`

解析 `--module` 参数的核心函数。

```python
def _parse_modules(modules: Tuple[str, ...]) -> list:
    # 输入: ("his,emr", "lis")
    # 输出: ["his", "emr", "lis"]
    # 支持 "all" 展开为全部模块
    # 去重保序
```

处理规则：
- 逗号分隔：`--module his,emr` → `['his', 'emr']`
- 多次传入：`--module his --module emr` → `['his', 'emr']`
- 自动去重：`--module his --module his` → `['his']`
- 大小写不敏感：`--module HIS` → `['his']`
- 未知模块报错并列出可选值

### `_resolve_scale(scale_arg)`

**位置**: `cli.py:46`

解析 `--scale` 参数。

```python
def _resolve_scale(scale_arg: str) -> float:
    # "tiny"  -> 0.01
    # "small" -> 0.10
    # "0.25"  -> 0.25
    # 负数或 0 报错
```

### `_check_connection(db_config)`

**位置**: `cli.py:61`

验证数据库连接，失败时打印红色错误并退出程序（exit code 1）。

---

## 典型工作流

### 工作流 1: 快速冒烟测试

```bash
# 1. 初始化数据库
meddata-gen init

# 2. 用 tiny 规模快速生成（约 50 患者，全表约 1 万行）
meddata-gen generate -s tiny --seed 42

# 3. 验证
meddata-gen verify
```

### 工作流 2: 事件驱动 + 规则引擎 + 质量评估

```bash
# 1. 一键执行（推荐：启用规则引擎）
meddata-gen run-all --mode event -s small --seed 42 --enable-rules

# 2. 生成质量报告
meddata-gen assess -o reports/quality.md
```

启用 `--enable-rules` 后：
- 患者会被分配与其年龄/性别匹配的基础疾病（90%）
- 科室选择按疾病画像自动匹配（95%）
- 挂号记录中会出现 ~8% 的退号/爽约
- 所有跨系统数据使用同一 patient_id / visit_id

### 工作流 3: CSV 输出（无需 PostgreSQL）

```bash
meddata-gen generate --mode event -s tiny --output-format csv --output-dir ./csv_data
ls ./csv_data/his_db/
# patients.csv  inpatient_visits.csv  outpatient_visits.csv  ...
```

### 工作流 4: 单模块调试

```bash
# 只生成 HIS 数据
meddata-gen init -m his
meddata-gen generate -m his -s small

# 基于 HIS 数据生成 LIS
meddata-gen generate -m lis -s small
```

### 工作流 5: 清空重来

```bash
meddata-gen reset --yes
meddata-gen run-all -s medium
```

---

## 退出码

| 场景 | 退出码 |
|------|--------|
| 成功 | 0 |
| 数据库连接失败 | 1 |
| Click 参数验证失败 | 2 |
| 用户取消 reset 确认 | 1 (abort) |
| 生成过程中异常 | 非 0（Python 异常栈） |
