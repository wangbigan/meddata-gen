"""``meddata-gen`` 命令行入口。

子命令:
    init           创建数据库并初始化表结构
    generate       生成数据（支持按模块、按规模档位）
    run-all        一键执行 init + generate + verify
    verify         校验数据量与跨库关联率
    reset          删除全部数据库（高危）
    docs           生成 markdown 数据字典
    dict-template  导出字典数据填写模板（Excel）
"""
from __future__ import annotations

import os
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


# 需要预检查的关键字典表: (数据库, 表名, 中文名)
_KEY_DICT_TABLES = [
    ("his_db", "diagnosis_dict", "诊断字典"),
    ("his_db", "surgery_dict", "手术字典"),
    ("his_db", "order_items_dict", "医嘱项目字典"),
    ("his_db", "charge_items_dict", "收费项目字典"),
    ("lis_db", "lab_items_dict", "检验项目字典"),
    ("lis_db", "organism_dict", "微生物字典"),
    ("lis_db", "antibiotic_dict", "抗生素字典"),
    ("ris_db", "exam_items_dict", "检查项目字典"),
]


def _check_dicts_loaded() -> list:
    """检查关键字典表是否为空。返回 [(db, table, cn_name), ...] 的空表列表。"""
    empty: list = []
    for db_name, table_name, cn_name in _KEY_DICT_TABLES:
        cfg = config.DB_CONFIG.copy()
        cfg["database"] = db_name
        try:
            conn = psycopg2.connect(**cfg)
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public' AND tablename=%s",
                (table_name,),
            )
            exists = cur.fetchone()[0]
            if exists:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                if count == 0:
                    empty.append((db_name, table_name, cn_name))
            cur.close()
            conn.close()
        except Exception:
            # 表可能不存在(旧 schema),跳过
            pass
    return empty


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

    # 引导用户导入字典
    click.echo("")
    click.secho("─" * 60, fg="yellow")
    click.secho("⚠  字典表当前为空,请先完成字典初始化:", fg="yellow")
    click.echo("")
    click.echo("  方案 A (推荐): 自定义字典")
    click.echo("    1) meddata-gen dict-template -o dict_template.xlsx")
    click.echo("    2) 用 Excel 打开 dict_template.xlsx,按 sheet 填写")
    click.echo("    3) meddata-gen dict-import -f dict_template.xlsx")
    click.echo("")
    click.echo("  方案 B: 使用内置示例字典(适合演示/快速验证)")
    click.echo("    meddata-gen dict-import --use-builtin")
    click.echo("")
    click.echo("  完成字典加载后,执行: meddata-gen generate --scale small")
    click.secho("─" * 60, fg="yellow")


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
@click.option(
    "--mode", default="legacy", show_default=True,
    type=click.Choice(["legacy", "event"]),
    help="生成模式：legacy=传统按表填充，event=事件驱动患者旅程。",
)
@click.option(
    "--output-format", default="postgres", show_default=True,
    type=click.Choice(["postgres", "csv", "fhir"]),
    help="事件模式下的输出格式（legacy 模式忽略此选项）。",
)
@click.option(
    "--output-dir", default=None,
    help="CSV/FHIR 输出目录（默认 output/csv 或 output/fhir）。",
)
@click.option(
    "--enable-rules", is_flag=True,
    help="启用临床规则引擎（仅事件模式有效）。",
)
def cmd_generate(
    modules: Tuple[str, ...],
    scale: str,
    seed: Optional[int],
    dry_run: bool,
    mode: str,
    output_format: str,
    output_dir: Optional[str],
    enable_rules: bool,
) -> None:
    factor = _resolve_scale(scale)

    click.echo(f"模式: {mode}")
    if mode == "legacy":
        target_modules = _parse_modules(modules)
        click.echo(f"目标模块: {target_modules}")
    click.echo(f"规模档位: {scale} (×{factor})")
    if seed is not None:
        click.echo(f"随机种子: {seed}")
    if mode == "event":
        click.echo(f"输出格式: {output_format}")
        if output_dir:
            click.echo(f"输出目录: {output_dir}")
    if dry_run:
        click.secho("[DRY-RUN] 跳过实际生成", fg="yellow")
        return

    _check_connection(config.DB_CONFIG)

    # 字典表预检查
    empty_dicts = _check_dicts_loaded()
    if empty_dicts:
        click.secho("\n⚠  以下字典表为空,生成的数据可能不真实:", fg="yellow")
        for db, tbl, cn in empty_dicts:
            click.echo(f"   - {db}.{tbl} ({cn})")
        click.echo("\n  可执行以下命令加载内置示例字典:")
        click.echo("    meddata-gen dict-import --use-builtin")
        click.echo("\n  或先导出模板自行填写后导入:")
        click.echo("    meddata-gen dict-template -o dict_template.xlsx")
        if not click.confirm("\n是否仍要继续生成?", default=False):
            sys.exit(0)

    if mode == "event":
        orchestrator.run_event_driven(
            config.DB_CONFIG,
            scale=factor,
            seed=seed,
            output_format=output_format,
            output_dir=output_dir,
            enable_rules=enable_rules,
        )
    else:
        o = orchestrator.Orchestrator(config.DB_CONFIG, scale=factor, seed=seed)
        o.run(_parse_modules(modules))
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
@click.option(
    "--mode", default="legacy", show_default=True,
    type=click.Choice(["legacy", "event"]),
    help="生成模式：legacy=传统按表填充，event=事件驱动患者旅程。",
)
@click.option(
    "--output-format", default="postgres", show_default=True,
    type=click.Choice(["postgres", "csv", "fhir"]),
    help="事件模式下的输出格式（legacy 模式忽略此选项）。",
)
@click.option(
    "--output-dir", default=None,
    help="CSV/FHIR 输出目录（默认 output/csv 或 output/fhir）。",
)
@click.option(
    "--enable-rules", is_flag=True,
    help="启用临床规则引擎（仅事件模式有效）。",
)
@click.pass_context
def cmd_run_all(
    ctx: click.Context,
    scale: str,
    seed: Optional[int],
    skip_init: bool,
    skip_verify: bool,
    mode: str,
    output_format: str,
    output_dir: Optional[str],
    enable_rules: bool,
) -> None:
    if not skip_init:
        ctx.invoke(cmd_init, modules=(), dry_run=False)
    ctx.invoke(
        cmd_generate,
        modules=(),
        scale=scale,
        seed=seed,
        dry_run=False,
        mode=mode,
        output_format=output_format,
        output_dir=output_dir,
        enable_rules=enable_rules,
    )
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


# ----- assess -----

@main.command("assess", help="生成数据质量评估报告（Markdown）。")
@click.option(
    "-o", "--output", default="reports/quality_report.md", show_default=True,
    help="输出 markdown 路径。",
)
def cmd_assess(output: str) -> None:
    from meddata_gen.quality.assessor import QualityAssessor

    _check_connection(config.DB_CONFIG)
    assessor = QualityAssessor(config.DB_CONFIG)
    report = assessor.run()

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(report)
    click.secho(f"[OK] 质量评估报告已生成: {output}", fg="green")


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


# ----- dict-template -----

@main.command("dict-template", help="导出字典数据填写模板（Excel）。")
@click.option(
    "-o", "--output", default="dict_template.xlsx", show_default=True,
    help="输出 Excel 路径（.xlsx）。",
)
@click.option(
    "--include", "include_arg", default=None,
    help="只导出指定字典表，多个用逗号分隔；不指定则导出全部 8 张。",
)
@click.option(
    "--with-samples/--no-samples", default=True, show_default=True,
    help="是否带示例行（False 时仅保留表头）。",
)
def cmd_dict_template(output: str, include_arg: Optional[str], with_samples: bool) -> None:
    from meddata_gen.dict_io import DICT_TABLES, build_template

    include: Optional[list] = None
    if include_arg:
        include = [name.strip() for name in include_arg.split(",") if name.strip()]

    try:
        path = build_template(output, include=include, with_samples=with_samples)
    except ValueError as e:
        click.secho(f"[ERROR] {e}", fg="red")
        sys.exit(1)

    tables = [t for t in DICT_TABLES if include is None or t.name in include]
    click.secho(f"[OK] 字典模板已生成: {path}", fg="green")
    click.echo(f"  包含字典表 {len(tables)} 张:")
    for t in tables:
        click.echo(f"    - {t.name:<22} ({t.cn_name}, {t.database})")
    if with_samples:
        click.echo("\n  示例行已填入,黄色高亮。请按需修改/扩展后导入:")
    else:
        click.echo("\n  仅保留表头,请填写后导入:")
    click.echo(f"    meddata-gen dict-import -f {path}")


# ----- dict-import -----

@main.command("dict-import", help="导入字典数据（Excel）或加载内置示例字典。")
@click.option(
    "-f", "--file", "file_path", default=None,
    help="Excel 文件路径（与 --use-builtin 互斥）。",
)
@click.option(
    "--use-builtin", is_flag=True,
    help="使用项目内置示例字典直接写入（覆盖全部 8 张表）。",
)
@click.option(
    "--mode", default="upsert", show_default=True,
    type=click.Choice(["upsert", "replace", "append"]),
    help="导入模式：upsert=插入或更新, replace=先清空再写入, append=仅追加。",
)
@click.option(
    "--dry-run", is_flag=True,
    help="仅校验，不写入数据库。",
)
@click.option(
    "--system", default=None,
    type=click.Choice(["his", "lis", "ris"]),
    help="限定只导入指定子系统的字典。",
)
@click.option(
    "--report", "report_path", default=None,
    help="导入报告输出路径（.md）。",
)
@click.option(
    "--yes", is_flag=True,
    help="跳过 replace 模式的二次确认。",
)
def cmd_dict_import(
    file_path: Optional[str],
    use_builtin: bool,
    mode: str,
    dry_run: bool,
    system: Optional[str],
    report_path: Optional[str],
    yes: bool,
) -> None:
    from meddata_gen.dict_io.builtin_loader import load_builtin_dicts
    from meddata_gen.dict_io.importer import import_dicts

    if not file_path and not use_builtin:
        click.secho("[ERROR] 必须指定 -f <文件> 或 --use-builtin", fg="red")
        sys.exit(1)
    if file_path and use_builtin:
        click.secho("[ERROR] -f 与 --use-builtin 不能同时使用", fg="red")
        sys.exit(1)

    if mode == "replace" and not dry_run and not yes:
        click.confirm(
            "replace 模式将先 TRUNCATE 字典表,数据不可恢复。\n确认继续？",
            abort=True,
        )

    if not dry_run:
        _check_connection(config.DB_CONFIG)

    if use_builtin:
        click.echo("正在加载内置示例字典...")
        stats = load_builtin_dicts()
        click.secho("[OK] 内置字典加载完成", fg="green")
        click.echo("  各表写入行数:")
        for name, cnt in sorted(stats.items()):
            click.echo(f"    {name:<22} {cnt} 行")
        return

    report = import_dicts(
        file_path=file_path,
        mode=mode,
        dry_run=dry_run,
        system=system,
        report_path=report_path,
    )

    total_read = sum(r.rows_read for r in report.results)
    total_ok = sum(r.rows_ok for r in report.results)
    total_fail = sum(r.rows_failed for r in report.results)

    if dry_run:
        click.secho("[DRY-RUN] 仅校验,未写入数据库", fg="yellow")
    else:
        click.secho("[OK] 导入完成", fg="green")
    click.echo(f"  读入行: {total_read} | 通过: {total_ok} | 失败: {total_fail}")
    for r in report.results:
        click.echo(
            f"    {r.table_name:<22} R:{r.rows_read} OK:{r.rows_ok} "
            f"I:{r.rows_inserted} U:{r.rows_updated} F:{r.rows_failed}"
        )
    if report_path:
        click.echo(f"  报告已保存: {report_path}")
    if total_fail > 0:
        click.echo("")
        click.secho("错误详情:", fg="red")
        for r in report.results:
            if r.errors:
                click.secho(f"  [{r.table_name}]", fg="red")
                for e in r.errors[:20]:
                    click.echo(f"    - {e}")
                if len(r.errors) > 20:
                    click.echo(f"    ... 还有 {len(r.errors) - 20} 条")
        sys.exit(1)


if __name__ == "__main__":
    main()
