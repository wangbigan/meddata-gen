"""``meddata-gen`` 命令行入口。

子命令:
    init       创建数据库并初始化表结构
    generate   生成数据（支持按模块、按规模档位）
    run-all    一键执行 init + generate + verify
    verify     校验数据量与跨库关联率
    reset      删除全部数据库（高危）
    docs       生成 markdown 数据字典
"""
from __future__ import annotations

import sys
from typing import Optional, Tuple

import click
import psycopg2

from meddata_gen import config
from meddata_gen.core import orchestrator


# ----- 公共选项 -----

def _parse_modules(modules: Tuple[str, ...]) -> list:
    """规范化 --module 参数，支持 'all' 与多次传入。"""
    if not modules:
        return orchestrator.all_modules()
    parsed = []
    for m in modules:
        for piece in m.split(","):
            piece = piece.strip().lower()
            if piece == "all":
                return orchestrator.all_modules()
            if piece not in orchestrator.MODULE_DBS:
                raise click.BadParameter(
                    f"未知模块 '{piece}'，可选: {list(orchestrator.MODULE_DBS)} 或 all"
                )
            parsed.append(piece)
    # 去重保序
    seen = set()
    return [m for m in parsed if not (m in seen or seen.add(m))]


def _resolve_scale(scale_arg: str) -> float:
    """支持档位名（tiny/small/medium/full）或数字（如 0.25）。"""
    if scale_arg in config.SCALE_PROFILES:
        return config.SCALE_PROFILES[scale_arg]
    try:
        v = float(scale_arg)
        if v <= 0:
            raise ValueError
        return v
    except ValueError:
        raise click.BadParameter(
            f"scale 必须是档位名 {list(config.SCALE_PROFILES)} 或正浮点数"
        )


def _check_connection(db_config: dict) -> None:
    try:
        conn = psycopg2.connect(**db_config)
        conn.close()
    except Exception as e:
        click.secho(f"[ERROR] 数据库连接失败: {e}", fg="red")
        sys.exit(1)


# ----- 主命令 -----

@click.group(help="医院信息系统模拟数据生成器（HIS/EMR/LIS/RIS/ECG/ICU/病案）。")
@click.version_option(package_name="meddata-gen", prog_name="meddata-gen")
def main() -> None:
    pass


# ----- init -----

@main.command("init", help="创建数据库并初始化表结构。")
@click.option(
    "-m", "--module", "modules", multiple=True,
    help="目标模块（his/emr/bingan/lis/ris/ecg/icu/all），可多次指定；默认 all。",
)
@click.option("--dry-run", is_flag=True, help="只打印将执行的步骤，不写入数据库。")
def cmd_init(modules: Tuple[str, ...], dry_run: bool) -> None:
    target_modules = _parse_modules(modules)
    target_dbs = [orchestrator.MODULE_DBS[m] for m in target_modules]

    click.echo(f"目标模块: {target_modules}")
    click.echo(f"目标数据库: {target_dbs}")
    if dry_run:
        click.secho("[DRY-RUN] 跳过实际执行", fg="yellow")
        return

    _check_connection(config.DB_CONFIG)

    click.echo("\n=== 创建数据库 ===")
    orchestrator.create_databases(config.DB_CONFIG, dbs=target_dbs)

    click.echo("\n=== 初始化表结构 ===")
    for db in target_dbs:
        orchestrator.init_schema(config.DB_CONFIG, db)

    click.secho("\n[OK] 初始化完成", fg="green")


# ----- generate -----

@main.command("generate", help="生成模拟数据。")
@click.option(
    "-m", "--module", "modules", multiple=True,
    help="目标模块（默认 all）。生成非 HIS 模块时会自动先生成 HIS 状态。",
)
@click.option(
    "-s", "--scale", default="full", show_default=True,
    help="规模档位：tiny/small/medium/full 或自定义浮点数（如 0.25）。",
)
@click.option("--seed", type=int, default=None, help="随机种子，覆盖 config.RANDOM_SEED。")
@click.option("--dry-run", is_flag=True, help="仅打印计划，不实际生成。")
def cmd_generate(modules: Tuple[str, ...], scale: str, seed: Optional[int], dry_run: bool) -> None:
    target_modules = _parse_modules(modules)
    factor = _resolve_scale(scale)

    click.echo(f"目标模块: {target_modules}")
    click.echo(f"规模档位: {scale} (×{factor})")
    if seed is not None:
        click.echo(f"随机种子: {seed}")
    if dry_run:
        click.secho("[DRY-RUN] 跳过实际生成", fg="yellow")
        return

    _check_connection(config.DB_CONFIG)

    o = orchestrator.Orchestrator(config.DB_CONFIG, scale=factor, seed=seed)
    o.run(target_modules)
    click.secho("\n[OK] 生成完成", fg="green")


# ----- run-all -----

@main.command("run-all", help="一键执行 init + generate + verify。")
@click.option(
    "-s", "--scale", default="full", show_default=True,
    help="规模档位：tiny/small/medium/full 或自定义浮点数。",
)
@click.option("--seed", type=int, default=None, help="随机种子。")
@click.option("--skip-init", is_flag=True, help="跳过 init 阶段（数据库已存在时使用）。")
@click.option("--skip-verify", is_flag=True, help="跳过 verify 阶段。")
@click.pass_context
def cmd_run_all(ctx: click.Context, scale: str, seed: Optional[int], skip_init: bool, skip_verify: bool) -> None:
    if not skip_init:
        ctx.invoke(cmd_init, modules=(), dry_run=False)
    ctx.invoke(cmd_generate, modules=(), scale=scale, seed=seed, dry_run=False)
    if not skip_verify:
        ctx.invoke(cmd_verify)


# ----- verify -----

@main.command("verify", help="校验数据量、跨库关联率与字段缺失率。")
def cmd_verify() -> None:
    _check_connection(config.DB_CONFIG)

    click.echo("\n=== 各表行数 ===")
    for db_name in config.DATABASES:
        cfg = config.DB_CONFIG.copy()
        cfg["database"] = db_name
        conn = psycopg2.connect(**cfg)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            """SELECT tablename FROM pg_tables
               WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%'
               ORDER BY tablename"""
        )
        click.echo(f"\n  [{db_name}]")
        for (table,) in cur.fetchall():
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            click.echo(f"    {table}: {count:,} rows")
        cur.close()
        conn.close()

    click.echo("\n=== 跨库关联率（patient_id → his_db.patients） ===")
    cfg = config.DB_CONFIG.copy()
    cfg["database"] = "his_db"
    conn = psycopg2.connect(**cfg)
    cur = conn.cursor()
    cur.execute("SELECT patient_id FROM patients")
    his_patients = set(r[0] for r in cur.fetchall())
    cur.close()
    conn.close()

    checks = [
        ("emr_db", "emr_documents"),
        ("bingan_db", "medical_records"),
        ("lis_db", "lab_orders"),
        ("ris_db", "exam_orders"),
        ("ecg_db", "ecg_exams"),
        ("icu_monitoring_db", "icu_admissions"),
    ]
    for src_db, src_table in checks:
        cfg = config.DB_CONFIG.copy()
        cfg["database"] = src_db
        conn = psycopg2.connect(**cfg)
        cur = conn.cursor()
        cur.execute(f"SELECT patient_id FROM {src_table}")
        src_patients = [r[0] for r in cur.fetchall() if r[0]]
        linked = sum(1 for pid in src_patients if pid in his_patients)
        total = len(src_patients) or 1
        click.echo(f"  {src_db}.{src_table}: {linked / total:.2%} ({linked}/{total})")
        cur.close()
        conn.close()


# ----- reset -----

@main.command("reset", help="删除全部模拟数据库（高危）。")
@click.option("--yes", is_flag=True, help="跳过确认提示。")
def cmd_reset(yes: bool) -> None:
    if not yes:
        click.confirm(
            f"将删除以下数据库: {config.DATABASES}\n确认继续？",
            abort=True,
        )
    _check_connection(config.DB_CONFIG)
    orchestrator.drop_databases(config.DB_CONFIG)
    click.secho("[OK] 数据库已删除", fg="green")


# ----- docs -----

@main.command("docs", help="生成 markdown 数据字典。")
@click.option(
    "-o", "--output", default="reports/data_dictionary.md", show_default=True,
    help="输出 markdown 路径。",
)
def cmd_docs(output: str) -> None:
    from meddata_gen.tools import data_dict
    _check_connection(config.DB_CONFIG)
    data_dict.write_data_dictionary(config.DB_CONFIG, output)
    click.secho(f"[OK] 数据字典已生成: {output}", fg="green")


if __name__ == "__main__":
    main()
