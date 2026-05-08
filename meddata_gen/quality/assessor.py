"""QualityAssessor: 数据质量评估器。

生成包含以下维度评估的 Markdown 报告：
- 统计保真度
- 时间一致性
- 跨系统关联率
- 临床一致性
- 缺陷场景命中率
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg2

from meddata_gen import config


class QualityAssessor:
    """质量评估器。"""

    def __init__(self, db_config: dict) -> None:
        self.db_config = db_config
        self.report_lines: List[str] = []

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def run(self) -> str:
        """执行全部评估并返回 Markdown 报告文本。"""
        self.report_lines = [
            "# meddata-gen 数据质量评估报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        self._assess_statistical_fidelity()
        self._assess_temporal_consistency()
        self._assess_cross_system_linkage()
        self._assess_clinical_coherence()
        self._assess_defect_scenarios()

        return "\n".join(self.report_lines)

    # ------------------------------------------------------------------
    # 1. 统计保真度
    # ------------------------------------------------------------------

    def _assess_statistical_fidelity(self) -> None:
        self._section("1. 统计保真度")

        # 患者年龄分布
        age_dist = self._query(
            "his_db",
            """
            SELECT
                CASE
                    WHEN birthday IS NULL THEN '未知'
                    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birthday)) < 18 THEN '0-17'
                    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birthday)) < 40 THEN '18-39'
                    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birthday)) < 60 THEN '40-59'
                    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birthday)) < 80 THEN '60-79'
                    ELSE '80+'
                END AS age_group,
                COUNT(*) AS cnt
            FROM patients
            GROUP BY age_group
            ORDER BY cnt DESC
            """,
        )
        self._table("患者年龄分布", ["年龄组", "人数", "占比"], self._with_pct(age_dist))

        # 科室住院量 TOP10
        dept_dist = self._query(
            "his_db",
            """
            SELECT admission_dept_id, COUNT(*) AS cnt
            FROM inpatient_visits
            WHERE admission_dept_id IS NOT NULL
            GROUP BY admission_dept_id
            ORDER BY cnt DESC
            LIMIT 10
            """,
        )
        self._table("住院量 TOP10 科室", ["科室ID", "人次"], dept_dist)

        # 常见检验项分布
        lab_dist = self._query(
            "lis_db",
            """
            SELECT item_name, COUNT(*) AS cnt,
                ROUND(AVG(result_num)::numeric, 2) AS avg_val,
                ROUND(STDDEV(result_num)::numeric, 2) AS std_val
            FROM routine_results
            WHERE result_num IS NOT NULL
            GROUP BY item_name
            ORDER BY cnt DESC
            LIMIT 10
            """,
        )
        self._table(
            "临检项分布 TOP10",
            ["项目名称", "记录数", "均值", "标准差"],
            lab_dist,
        )

    # ------------------------------------------------------------------
    # 2. 时间一致性
    # ------------------------------------------------------------------

    def _assess_temporal_consistency(self) -> None:
        self._section("2. 时间一致性")

        checks: List[Tuple[str, str, str]] = [
            (
                "lis_db",
                """
                SELECT COUNT(*) FROM routine_results r
                JOIN lab_orders o ON o.order_id = r.order_id
                WHERE r.report_time IS NOT NULL AND o.order_time IS NOT NULL
                  AND r.report_time < o.order_time
                """,
                "检验结果时间早于申请时间",
            ),
            (
                "his_db",
                """
                SELECT COUNT(*) FROM inpatient_visits
                WHERE discharge_time IS NOT NULL AND admission_time IS NOT NULL
                  AND discharge_time < admission_time
                """,
                "出院时间早于入院时间",
            ),
            (
                "lis_db",
                """
                SELECT COUNT(*) FROM specimens s
                JOIN lab_orders o ON o.order_id = s.order_id
                WHERE s.collect_time IS NOT NULL AND o.order_time IS NOT NULL
                  AND s.collect_time < o.order_time
                """,
                "标本采集时间早于申请时间",
            ),
        ]

        rows = []
        for db, sql, desc in checks:
            try:
                cnt = self._query_scalar(db, sql)
            except Exception as e:
                cnt = f"ERROR: {e}"
            rows.append((desc, str(cnt)))
        self._table("时间因果逆序检查", ["检查项", "异常记录数"], rows)

    # ------------------------------------------------------------------
    # 3. 跨系统关联率
    # ------------------------------------------------------------------

    def _assess_cross_system_linkage(self) -> None:
        self._section("3. 跨系统关联率")

        his_patients = self._query_set("his_db", "SELECT patient_id FROM patients")

        checks = [
            ("emr_db", "emr_documents", "patient_id"),
            ("bingan_db", "medical_records", "patient_id"),
            ("lis_db", "lab_orders", "patient_id"),
            ("lis_db", "routine_results", "patient_id"),
            ("ris_db", "exam_orders", "patient_id"),
            ("ecg_db", "ecg_exams", "patient_id"),
            ("icu_monitoring_db", "icu_admissions", "patient_id"),
        ]

        rows = []
        for db, table, col in checks:
            try:
                total = self._query_scalar(db, f"SELECT COUNT(*) FROM {table}")
                if total == 0:
                    rows.append((f"{db}.{table}", "0", "N/A", "N/A"))
                    continue
                src_ids = self._query_set(db, f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL")
                linked = len(src_ids & his_patients)
                rows.append((
                    f"{db}.{table}",
                    str(total),
                    str(linked),
                    f"{linked / total:.2%}" if total else "N/A",
                ))
            except Exception as e:
                rows.append((f"{db}.{table}", "ERROR", str(e), "N/A"))

        self._table(
            "跨系统 patient_id 关联率（→ his_db.patients）",
            ["表名", "总记录数", "关联命中数", "关联率"],
            rows,
        )

    # ------------------------------------------------------------------
    # 4. 临床一致性
    # ------------------------------------------------------------------

    def _assess_clinical_coherence(self) -> None:
        self._section("4. 临床一致性")

        # 疾病画像覆盖率：通过诊断关键词匹配简单估算
        disease_checks = [
            ("肺炎", "白细胞计数", "his_db", "inpatient_visits", "admission_diagnosis", "lis_db", "routine_results"),
            ("糖尿病", "空腹血糖", "his_db", "inpatient_visits", "admission_diagnosis", "lis_db", "biochem_results"),
            ("心肌梗死", "肌钙蛋白I", "his_db", "inpatient_visits", "admission_diagnosis", "lis_db", "biochem_results"),
        ]

        rows = []
        for disease, lab_item, his_db, his_table, diag_col, lab_db, lab_table in disease_checks:
            try:
                # 获取疾病组患者
                disease_pids = self._query_set(
                    his_db,
                    f"SELECT patient_id FROM {his_table} WHERE {diag_col} LIKE %s",
                    (f"%{disease}%",),
                )
                control_pids = self._query_set(
                    his_db,
                    f"SELECT patient_id FROM {his_table} WHERE {diag_col} IS NOT NULL AND {diag_col} NOT LIKE %s",
                    (f"%{disease}%",),
                )

                if not disease_pids:
                    rows.append((disease, lab_item, "0", "N/A", "N/A", "无患者"))
                    continue

                disease_avg = self._query_scalar(
                    lab_db,
                    f"""
                    SELECT COALESCE(AVG(result_num), 0)
                    FROM {lab_table}
                    WHERE item_name = %s AND patient_id = ANY(%s) AND result_num IS NOT NULL
                    """,
                    (lab_item, list(disease_pids)),
                )

                control_avg = self._query_scalar(
                    lab_db,
                    f"""
                    SELECT COALESCE(AVG(result_num), 0)
                    FROM {lab_table}
                    WHERE item_name = %s AND patient_id = ANY(%s) AND result_num IS NOT NULL
                    """,
                    (lab_item, list(control_pids)),
                ) if control_pids else 0

                rows.append((
                    disease,
                    lab_item,
                    str(len(disease_pids)),
                    f"{disease_avg:.2f}" if disease_avg else "N/A",
                    f"{control_avg:.2f}" if control_avg else "N/A",
                    "↑ 异常" if disease_avg and control_avg and disease_avg > control_avg * 1.2 else "—",
                ))
            except Exception as e:
                rows.append((disease, lab_item, "ERROR", str(e), "", ""))

        self._table(
            "疾病-检验一致性检查",
            ["疾病", "检验项", "患者数", "疾病组均值", "对照组均值", "差异方向"],
            rows,
        )

    # ------------------------------------------------------------------
    # 5. 缺陷场景命中率
    # ------------------------------------------------------------------

    def _assess_defect_scenarios(self) -> None:
        self._section("5. 缺陷场景命中率")

        scenarios = getattr(config, "QUALITY_SCENARIOS", [])
        if not scenarios:
            self.report_lines.append("\n> 当前未启用任何缺陷场景（QUALITY_SCENARIOS 为空）。\n")
            return

        rows = []
        for scenario in scenarios:
            try:
                where_clauses = ["1=1"]
                params: List[Any] = []

                if scenario.time_range:
                    # 启发式查找时间列
                    time_col = self._guess_time_column(scenario.target_systems[0], scenario.target_tables[0])
                    if time_col:
                        where_clauses.append(f"{time_col} BETWEEN %s AND %s")
                        params.extend(scenario.time_range)

                sql = f"""
                    SELECT COUNT(*) FILTER (WHERE {self._defect_condition(scenario)}),
                           COUNT(*)
                    FROM {scenario.target_tables[0]}
                    WHERE {' AND '.join(where_clauses)}
                """
                affected, total = self._query_one(
                    scenario.target_systems[0], sql, tuple(params) if params else None
                )
                rows.append((
                    scenario.name,
                    scenario.defect_type,
                    f"{scenario.rate:.0%}",
                    str(affected or 0),
                    str(total or 0),
                    f"{(affected / total):.2%}" if total else "N/A",
                ))
            except Exception as e:
                rows.append((scenario.name, scenario.defect_type, f"{scenario.rate:.0%}", "ERROR", str(e), "N/A"))

        self._table(
            "场景化缺陷命中率",
            ["场景名称", "缺陷类型", "设计比例", "实际命中数", "总记录数", "实际比例"],
            rows,
        )

    @staticmethod
    def _defect_condition(scenario) -> str:
        """根据缺陷类型构造 WHERE 条件（简化版）。"""
        if scenario.defect_type == "null":
            # 任一目标字段为 NULL
            return " OR ".join(f"{f} IS NULL" for f in scenario.target_fields)
        if scenario.defect_type == "foreign_key_mismatch":
            # 粗略检查：patient_id 以 P 开头且长度不对（简化）
            return " OR ".join(
                f"({f} IS NOT NULL AND {f} NOT IN (SELECT patient_id FROM his_db.patients))"
                for f in scenario.target_fields
            )
        if scenario.defect_type == "format_error":
            return " OR ".join(
                f"({f} IS NOT NULL AND {f}::text ~ '^[0-9]{2}/[0-9]{2}/[0-9]{4}')"
                for f in scenario.target_fields
            )
        if scenario.defect_type == "logic_error":
            return "1=0"  # 难以用 SQL 精确检测
        if scenario.defect_type == "duplicate":
            return " OR ".join(
                f"({f} IS NOT NULL AND {f}::text LIKE '% %')"
                for f in scenario.target_fields
            )
        return "1=0"

    def _guess_time_column(self, db: str, table: str) -> Optional[str]:
        """启发式猜测表中的时间列名。"""
        try:
            cols = self._query(
                db,
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                  AND data_type IN ('timestamp without time zone', 'timestamp with time zone', 'date')
                """,
                (table,),
            )
            for (col,) in cols:
                if "time" in col.lower():
                    return col
            return cols[0][0] if cols else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # 报告辅助
    # ------------------------------------------------------------------

    def _section(self, title: str) -> None:
        self.report_lines.append(f"\n## {title}\n")

    def _table(self, title: str, headers: List[str], rows: List[tuple]) -> None:
        self.report_lines.append(f"### {title}\n")
        self.report_lines.append("| " + " | ".join(headers) + " |")
        self.report_lines.append("|" + "|".join("---" for _ in headers) + "|")
        for row in rows:
            # 处理 None
            cells = [str(c) if c is not None else "" for c in row]
            self.report_lines.append("| " + " | ".join(cells) + " |")
        self.report_lines.append("")

    @staticmethod
    def _with_pct(rows: List[tuple]) -> List[tuple]:
        total = sum(r[1] for r in rows if isinstance(r[1], int)) or 1
        return [(r[0], str(r[1]), f"{r[1] / total:.1%}") for r in rows]

    # ------------------------------------------------------------------
    # 数据库查询辅助
    # ------------------------------------------------------------------

    def _query(self, db: str, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        cfg = self.db_config.copy()
        cfg["database"] = db
        conn = psycopg2.connect(**cfg)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            conn.close()

    def _query_scalar(self, db: str, sql: str, params: Optional[tuple] = None) -> Any:
        rows = self._query(db, sql, params)
        return rows[0][0] if rows else None

    def _query_one(self, db: str, sql: str, params: Optional[tuple] = None) -> tuple:
        rows = self._query(db, sql, params)
        return rows[0] if rows else (None, None)

    def _query_set(self, db: str, sql: str, params: Optional[tuple] = None) -> set:
        rows = self._query(db, sql, params)
        return set(r[0] for r in rows if r[0] is not None)
