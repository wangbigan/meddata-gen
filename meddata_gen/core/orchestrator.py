"""数据生成编排器：按模块运行流水线，跨模块复用 HIS 生成的核心状态。"""
from __future__ import annotations

from importlib import resources
from typing import Dict, Iterable, List, Optional, Tuple

import psycopg2

from meddata_gen import config

# ----- 模块 ↔ 数据库 ↔ schema 文件 -----

MODULE_DBS: Dict[str, str] = {
    "his": "his_db",
    "emr": "emr_db",
    "bingan": "bingan_db",
    "lis": "lis_db",
    "ris": "ris_db",
    "ecg": "ecg_db",
    "icu": "icu_monitoring_db",
}

SCHEMA_FILES: Dict[str, str] = {
    "his_db": "his_schema.sql",
    "emr_db": "emr_schema.sql",
    "bingan_db": "bingan_schema.sql",
    "lis_db": "lis_schema.sql",
    "ris_db": "ris_schema.sql",
    "ecg_db": "ecg_schema.sql",
    "icu_monitoring_db": "icu_schema.sql",
}

# ----- 模块流水线：(方法名, scale_key 或 None) -----
# scale_key=None 表示该方法不接收 count 参数

PipelineStep = Tuple[str, Optional[str]]

MODULE_PIPELINES: Dict[str, List[PipelineStep]] = {
    "his": [
        ("generate_departments", None),
        ("generate_staff", "physicians"),
        ("generate_drugs", "drugs"),
        ("generate_patients", "patients"),
        ("generate_inpatient_visits", "inpatients"),
        ("generate_outpatient_visits", "outpatients"),
        ("generate_orders", "orders"),
        ("generate_fee_items", "fee_items"),
        ("generate_beds", None),
    ],
    "emr": [
        ("generate_emr_documents", "emr_documents"),
        ("generate_progress_notes", "progress_notes"),
        ("generate_admission_records", "admission_records"),
        ("generate_discharge_records", "discharge_records"),
        ("generate_surgery_records", "surgery_records"),
        ("generate_nursing_records", "nursing_records"),
    ],
    "bingan": [
        ("generate_medical_records", "medical_records"),
        ("generate_bingan_diagnoses", "diagnoses"),
        ("generate_bingan_surgeries", "surgeries"),
        ("generate_tumor_registry", "tumors"),
    ],
    "lis": [
        ("generate_lab_orders", "lab_orders"),
        ("generate_specimens", "specimens"),
        ("generate_routine_results", "routine_results"),
        ("generate_biochem_results", "biochem_results"),
        ("generate_blood_results", "blood_results"),
        ("generate_microbiology", "microbiology"),
        ("generate_antibiotic_sensitivity", "antibiotic_sensitivity"),
    ],
    "ris": [
        ("generate_devices", "devices"),
        ("generate_exam_orders", "exam_orders"),
        ("generate_xray_reports", "xray_reports"),
        ("generate_ct_reports", "ct_reports"),
        ("generate_mri_reports", "mri_reports"),
        ("generate_ultrasound_reports", "ultrasound_reports"),
    ],
    "ecg": [
        ("generate_ecg_exams", "ecg_exams"),
        ("generate_ecg_waveforms", "waveforms"),
        ("generate_ecg_analyses", "analyses"),
    ],
    "icu": [
        ("generate_icu_admissions", "icu_admissions"),
        ("generate_monitoring_data", "monitoring_data"),
        ("generate_alarms", "alarms"),
        ("generate_blood_gas", "blood_gas"),
    ],
}

# 依赖 HIS 生成的核心实体（patients/staff/departments）
NON_HIS_MODULES = ["emr", "bingan", "lis", "ris", "ecg", "icu"]


def all_modules() -> List[str]:
    return list(MODULE_DBS.keys())


def schema_path(db_name: str) -> str:
    """返回 schema SQL 文件的绝对路径。"""
    fname = SCHEMA_FILES[db_name]
    return str(resources.files("meddata_gen").joinpath("schema", fname))


def _scaled_counts(system_db: str, scale: float) -> Dict[str, int]:
    base = config.SYSTEM_SCALE[system_db]
    return {k: max(1, int(v * scale)) for k, v in base.items()}


# ----- 数据库初始化 -----

def create_databases(db_config: dict, dbs: Iterable[str] = None) -> None:
    """创建数据库 + 写入 COMMENT ON DATABASE。"""
    dbs = list(dbs) if dbs else config.DATABASES
    conn = psycopg2.connect(**db_config)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        for db_name in dbs:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cur.fetchone():
                print(f"  [SKIP] 数据库 '{db_name}' 已存在")
            else:
                cur.execute(f"CREATE DATABASE {db_name} ENCODING 'UTF8'")
                print(f"  [OK] 数据库 '{db_name}' 创建成功")
            description = config.DATABASE_DESCRIPTIONS.get(db_name)
            if description:
                cur.execute(f"COMMENT ON DATABASE {db_name} IS %s", (description,))
                print(f"  [COMMENT] {db_name} → {description}")
    finally:
        cur.close()
        conn.close()


def init_schema(db_config: dict, db_name: str) -> None:
    """对指定数据库执行 schema SQL。"""
    from meddata_gen import DataGenerator

    gen = DataGenerator(db_config).connect(db_name)
    try:
        gen.execute_sql_file(schema_path(db_name))
        print(f"    [OK] {db_name} 表结构初始化完成")
    except Exception as e:
        gen.rollback()
        print(f"    [ERROR] {db_name}: {e}")
        raise
    finally:
        gen.close()


def drop_databases(db_config: dict, dbs: Iterable[str] = None) -> None:
    dbs = list(dbs) if dbs else config.DATABASES
    conn = psycopg2.connect(**db_config)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        for db_name in dbs:
            # 强制断开后删除
            cur.execute(
                """SELECT pg_terminate_backend(pid)
                   FROM pg_stat_activity
                   WHERE datname = %s AND pid <> pg_backend_pid()""",
                (db_name,),
            )
            cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
            print(f"  [OK] 数据库 '{db_name}' 已删除")
    finally:
        cur.close()
        conn.close()


# ----- 数据生成 -----

def _share_state(target, source) -> None:
    """复用 HIS 生成的核心实体到其他模块。"""
    target.patients = source.patients
    target.inpatients = source.inpatients
    target.outpatients = source.outpatients
    target.staff = source.staff
    target.departments = source.departments
    target.drugs = source.drugs


def run_module(
    db_config: dict,
    module: str,
    scale: float = 1.0,
    seed: Optional[int] = None,
    his_state=None,
):
    """运行单个模块的生成流水线，返回生成器实例（含累积状态）。"""
    from meddata_gen import DataGenerator

    if module not in MODULE_DBS:
        raise ValueError(f"未知模块: {module}（可选: {list(MODULE_DBS)}）")

    db_name = MODULE_DBS[module]
    counts = _scaled_counts(db_name, scale)

    gen = DataGenerator(db_config, seed=seed).connect(db_name)
    if module != "his":
        if his_state is None:
            raise RuntimeError(f"模块 '{module}' 需要 HIS 状态共享，但 his_state 未提供")
        _share_state(gen, his_state)

    try:
        for method_name, count_key in MODULE_PIPELINES[module]:
            method = getattr(gen, method_name)
            if count_key is None:
                method()
            else:
                method(counts[count_key])
        return gen
    except Exception:
        gen.rollback()
        gen.close()
        raise


class Orchestrator:
    """统一编排接口：按模块顺序生成，自动维护 HIS 状态共享。"""

    def __init__(self, db_config: dict, scale: float = 1.0, seed: Optional[int] = None):
        self.db_config = db_config
        self.scale = scale
        self.seed = seed
        self.his_state = None

    def run(self, modules: Iterable[str]) -> None:
        modules = list(modules)
        # HIS 永远第一个跑（其他模块依赖）
        if any(m != "his" for m in modules) and "his" not in modules:
            print("[INFO] 依赖检测：自动加入 his 作为前置模块")
            modules = ["his"] + modules
        elif "his" in modules:
            modules = ["his"] + [m for m in modules if m != "his"]

        for module in modules:
            print()
            print("=" * 60)
            print(f"  生成模块: {module}（数据库 {MODULE_DBS[module]}）")
            print("=" * 60)
            gen = run_module(
                self.db_config,
                module,
                scale=self.scale,
                seed=self.seed,
                his_state=self.his_state,
            )
            try:
                if module == "his":
                    self.his_state = gen
                    # 不要 close，他后面还要被复用为 his_state
                    # 但 his_state 仅持有 self.patients / staff / ... 的引用，连接可关闭
            finally:
                if module != "his":
                    gen.close()
        if self.his_state is not None:
            self.his_state.close()
