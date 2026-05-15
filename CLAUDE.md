# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`meddata-gen` is a Python CLI tool that generates synthetic hospital data across 7 medical subsystems (HIS, EMR, LIS, RIS, ECG, ICU, 病案) into local PostgreSQL databases. The data includes configurable quality defects (nulls, cross-system linkage gaps, logic errors, format inconsistencies) for testing ETL pipelines.

## Common Commands

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# CLI entry points
meddata-gen --help
python -m meddata_gen --help

# One-shot: create DBs, generate data, verify
meddata-gen run-all --scale small

# Step by step
meddata-gen init --module his,emr
meddata-gen generate --scale 0.25 --seed 42
meddata-gen verify
meddata-gen docs -o reports/dd.md

# Generate data quality assessment report
meddata-gen assess -o reports/quality_report.md

# Reset everything
meddata-gen reset --yes

# Run tests
pytest
pytest --cov=meddata_gen --cov-report=term-missing
pytest path/to/test.py::test_name        # single test
```

## Architecture

### Dual-Mode Generation

The codebase supports two mutually exclusive generation modes:

**Legacy mode** (`--mode legacy`, default): Each subsystem Mixin generates its own tables independently. HIS runs first, then other modules receive HIS state via `_share_state()`. This is the original approach and is preserved for backward compatibility.

**Event mode** (`--mode event`): Uses an event-driven patient journey model where a single clinical encounter (inpatient or outpatient) produces a time-ordered sequence of events across all 7 systems. This is the preferred approach for new work.

### Legacy Mode: Generator Composition

`DataGenerator` (`__init__.py`) is composed via multiple inheritance:

```
DataGenerator(
    BaseGenerator,
    HISMixin, EMRMixin, BinganMixin,
    LISMixin, RISMixin, ECGMixin, ICUMixin
)
```

- **`BaseGenerator`** (`core/base.py`): DB connection/transaction management, batch insert (`_batch_insert`), and defect injection utilities (`_should_null`, `_should_link`, `_format_inconsistent_date`, `_maybe_logic_error`).
- **Subsystem Mixins** (`generators/*.py`): Each exposes `generate_*` methods that build rows and call `_batch_insert`. They store generated entities (e.g., `self.patients`, `self.staff`) as lists on the generator instance for cross-module sharing.
- **`core/orchestrator.py`**: Defines `MODULE_PIPELINES` per module and runs them in dependency order. HIS always runs first because it produces the canonical `patients`, `staff`, `departments`, `drugs` lists. Non-HIS modules receive HIS state via `_share_state()`.

### Event Mode: Patient Journey Pipeline

The event-driven architecture is the primary path for new features. It produces clinically coherent, time-ordered data across all systems from a single patient encounter.

**Data flow:** `JourneyBuilder` → `MedicalEvent[]` → `Materializer` → `EventHandler` → `OutputWriter`

- **`JourneyBuilder`** (`core/journey_builder.py`): Builds a chronological event sequence for a single encounter. Inpatient: admission → EMR records → lab orders/results → imaging → daily orders/notes → surgery (probabilistic) → ICU (probabilistic) → discharge → bingan. Outpatient: visit → labs (30%) → imaging (20%) → medications (80%).
- **`MedicalEvent`** (`core/events.py`): Atomic event with `event_type`, `timestamp`, `source_system`, `payload`, and `parent_event_id`. `TimelineEngine` guarantees temporal causality (child events are always after parents).
- **`EventContext`** (`core/events.py`): Per-encounter context carrying `patient_id`, `visit_id`, `admission_time`, `discharge_time`, `primary_diagnosis`, `attending_doctor_id`, `disease_profile`, and a `state` dict for cross-event ID sharing (e.g., lab order ID recorded by `order_lab` handler, retrieved by `lab_result` handler via `ctx.get_id()`).
- **`Materializer`** (`core/materializer.py`): Dispatches events to registered handlers, buffers rows by `(database, table)`, applies scenario-based defects, and flushes via `OutputWriter`.
- **Event Handlers** (`core/handlers/*.py`): Each handler is a function `(MedicalEvent, EventContext) → Optional[(db, table, columns, [rows])]`. Handlers are registered against `(source_system, event_type)` pairs.
- **`EventDrivenGenerator`** (`generators/event_driven.py`): Entry point. Two-phase generation:
  1. **Phase 1** (dictionary data): Connects to `his_db`, uses `BaseGenerator._batch_insert` directly to generate departments, staff, drugs, patients, beds.
  2. **Phase 2** (patient journeys): Creates `EventContext` per journey, builds events via `JourneyBuilder`, materializes via `Materializer` using its own `OutputWriter` (independent of BaseGenerator connection).

### Handler Contract (Critical)

Handlers return row data as:

```python
# Single result
(db_name, table_name, [col1, col2, ...], [(val1, val2, ...), ...])

# Or list of results for multiple tables
[
    (db_name, table1, [...], [...]),
    (db_name, table2, [...], [...]),
]
```

**The tuple count in each row MUST exactly match the schema column count.** `PostgresWriter._write_table()` validates this before insert, but mismatches are the most common source of generation failures. When adding or modifying a handler, verify the column list and tuple values against the corresponding `schema/*.sql` CREATE TABLE statement.

**Cross-journey ID uniqueness:** `EventDrivenGenerator` passes `self._shared_state` (a single dict) to all `EventContext` constructors. Without this, each journey gets isolated counters and IDs like `OR00000001` collide across patients.

### Output Writers

`OutputWriter` (`output/base.py`) is the abstraction for multi-format output:

- **`PostgresWriter`** (`output/postgres.py`): Buffers by database, opens one connection per DB, uses `executemany` with batch size 1000. Default for event mode.
- **`CSVWriter`** (`output/csv.py`): Writes to `output/{system}/{table}.csv`.
- **`FHIRBundleWriter`** (`output/fhir.py`): Generates FHIR R4 Bundle JSON per patient.

### Disease Profiles & Clinical Consistency

`clinical/disease_profiles.py` defines disease profiles (e.g., community-acquired pneumonia, acute MI, type 2 diabetes). Each profile specifies:
- Typical departments, LOS distribution, ICU/surgery probabilities
- Lab abnormality patterns (which items are high/low and by how much)
- Typical medications and imaging

`JourneyBuilder` uses the profile to drive encounter characteristics. Lab handlers use `clinical/lab_generator.py` to generate disease-aware values (e.g., pneumonia patients have elevated WBC/CRP).

### Quality Scenarios

`quality/scenarios.py` defines scenario-based defect injection (distinct from the uniform random defects in Legacy mode). Scenarios target specific time ranges, systems, and tables to simulate realistic data quality incidents (e.g., "LIS system upgrade outage" causing 95% null microbiology results during June 2023). The `ScenarioDefectEngine` (`quality/defect_engine.py`) is integrated into `Materializer.flush()`.

### Configuration

`meddata_gen/config.py` is the single source of truth for:

- **`DB_CONFIG`**: PostgreSQL connection (default `127.0.0.1:5432`).
- **`SYSTEM_SCALE`**: Row counts per table at "full" scale.
- **`SCALE_PROFILES`**: Named multipliers (`tiny`, `small`, `medium`, `full`) or raw floats.
- **`QUALITY`**: Defect rates (null rates, link rates, logic error rate, format inconsistency rate) per system.
- **`QUALITY_SCENARIOS`**: List of scenario objects; empty by default. Import `PREDEFINED_SCENARIOS` from `quality.scenarios` to enable.
- **`RANDOM_SEED`**: Set to an integer for reproducible runs, `None` for random.

### Schema & Seed Data

- **SQL schemas** live in `meddata_gen/schema/*.sql`. Loaded via `importlib.resources` in `orchestrator.schema_path()`.
- **Seed dictionaries** (departments, drugs, ICD-10, etc.) live in `meddata_gen/seed_data.py`.

## Key Files for Developers

| File | Purpose |
|------|---------|
| `meddata_gen/config.py` | DB connection, scale, quality settings |
| `meddata_gen/core/base.py` | BaseGenerator with defect injection & batch insert |
| `meddata_gen/core/orchestrator.py` | Pipeline definitions, DB init, legacy/event orchestration |
| `meddata_gen/core/events.py` | MedicalEvent, EventContext, TimelineEngine |
| `meddata_gen/core/journey_builder.py` | Inpatient/outpatient event sequence construction |
| `meddata_gen/core/materializer.py` | Event dispatch, buffering, defect application, flush |
| `meddata_gen/core/handlers/*.py` | Per-system event handlers (return rows matching schema) |
| `meddata_gen/generators/event_driven.py` | EventDrivenGenerator (Phase 1 dicts + Phase 2 journeys) |
| `meddata_gen/cli.py` | Click CLI (init, generate, run-all, verify, assess, reset, docs, dict-template, dict-import) |
| `meddata_gen/dict_io/` | 字典导入/导出模块 (schemas, template_builder, importer, validators, builtin_loader) |
| `meddata_gen/generators/*.py` | Per-subsystem Mixin generators (legacy mode only) |

## Dictionary Tables (字典表)

8 张字典表分布在 3 个数据库中,用于为主业务表提供可校验的主数据:

| 表名 | 数据库 | 说明 | 数据来源 |
|------|--------|------|----------|
| `diagnosis_dict` | his_db | ICD-10 诊断编码 | 内置(seed_data.ICD10_DIAGNOSES) |
| `surgery_dict` | his_db | ICD-9-CM3 手术编码 | 内置(硬编码 ~60 条) |
| `order_items_dict` | his_db | 医嘱项目主数据 | 内置(硬编码 ~40 条) |
| `charge_items_dict` | his_db | 收费项目主数据 | 内置(硬编码 ~45 条) |
| `lab_items_dict` | lis_db | 检验项目(含 LOINC) | 内置(seed_data.LAB_ITEMS) |
| `organism_dict` | lis_db | 微生物菌株 | 内置(seed_data.MICRO_ORGANISMS) |
| `antibiotic_dict` | lis_db | 抗生素 | 内置(seed_data.ANTIBIOTICS) |
| `exam_items_dict` | ris_db | RIS 检查项目 | 内置(seed_data.RIS_EXAM_TYPES) |

**导入方式:**
1. **自定义导入**: `dict-template` 导出 Excel → 用户填写 → `dict-import -f file.xlsx`
2. **内置示例**: `dict-import --use-builtin` (一键写入全部 8 张表)

`init` 完成后会提示先导入字典;`generate` 启动前会检查关键字典表是否为空并询问是否继续。

## Notes

- The project requires a running PostgreSQL instance. There is no Docker setup or in-memory fallback.
- When adding a new subsystem, add its schema SQL to `meddata_gen/schema/`, its Mixin to `generators/`, register the pipeline in `orchestrator.MODULE_PIPELINES`, and update `MODULE_DBS` and `SCHEMA_FILES`.
- When adding event-driven support for a new subsystem, add handlers to `core/handlers/`, register them in `handlers/__init__.py`, and add journey events in `journey_builder.py`.
- 新增字典表时,需要同时更新: `schema/*.sql` DDL、`dict_io/schemas.py` 元数据、`dict_io/builtin_loader.py` 内置数据、以及 `seed_data.py` (如果复用现有常量)。
