"""字典表元数据 — 模板生成、Excel 校验、入库 SQL 的单一来源。

8 张字典表 (3 个 DB):
    his_db:  diagnosis_dict, surgery_dict, order_items_dict, charge_items_dict
    lis_db:  lab_items_dict, organism_dict, antibiotic_dict
    ris_db:  exam_items_dict
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


# ---------- 元数据模型 ----------

@dataclass(frozen=True)
class DictColumn:
    """字典表列定义。"""

    name: str                              # 英文列名 (= SQL/Excel 列名)
    cn_name: str                           # 中文表头
    excel_type: str                        # text / int / decimal / bool
    required: bool = False
    primary_key: bool = False
    description: str = ""                  # 字段说明 (Excel 第 3 行)
    enum_values: Tuple[str, ...] = ()      # 若非空,生成 Excel 数据有效性下拉


@dataclass(frozen=True)
class DictTable:
    """字典表定义。"""

    name: str                              # 表名 (= Excel sheet 名)
    cn_name: str                           # 中文名 (展示用)
    database: str                          # his_db / lis_db / ris_db
    description: str                       # 用途说明
    columns: Tuple[DictColumn, ...]
    sample_rows: Tuple[Tuple, ...] = ()    # 示例行,顺序与 columns 对齐


# ---------- 表定义 ----------

diagnosis_dict = DictTable(
    name="diagnosis_dict",
    cn_name="诊断字典",
    database="his_db",
    description="ICD-10 诊断编码字典,供 inpatient_visits / outpatient_visits / emr 诊断引用。",
    columns=(
        DictColumn("icd_code", "诊断编码", "text", required=True, primary_key=True,
                   description="ICD-10 编码"),
        DictColumn("diagnosis_name", "诊断名称", "text", required=True,
                   description="诊断中文全称"),
        DictColumn("category", "章节分类", "text",
                   description="ICD-10 章节(如:呼吸系统疾病)"),
        DictColumn("is_chronic", "是否慢性病", "bool",
                   description="TRUE/FALSE,慢性病标识"),
        DictColumn("is_infectious", "是否传染病", "bool",
                   description="TRUE/FALSE,法定传染病标识"),
    ),
    sample_rows=(
        ("J18.901", "肺炎,未特指", "呼吸系统疾病", False, True),
        ("I21.901", "急性心肌梗死", "循环系统疾病", False, False),
        ("E11.900", "2型糖尿病", "内分泌、营养和代谢疾病", True, False),
    ),
)


surgery_dict = DictTable(
    name="surgery_dict",
    cn_name="手术字典",
    database="his_db",
    description="ICD-9-CM3 手术操作编码字典,供 operation_schedules / 手术记录引用。",
    columns=(
        DictColumn("surgery_code", "手术编码", "text", required=True, primary_key=True,
                   description="ICD-9-CM3 编码"),
        DictColumn("surgery_name", "手术名称", "text", required=True,
                   description="手术名称"),
        DictColumn("surgery_level", "手术级别", "text",
                   description="一级/二级/三级/四级",
                   enum_values=("一级", "二级", "三级", "四级")),
        DictColumn("department_id", "对应科室ID", "text",
                   description="主刀科室(对应 departments.department_id)"),
        DictColumn("duration_min", "标准时长(分钟)", "int",
                   description="标准手术时长,整数,分钟"),
        DictColumn("anesthesia_type", "麻醉方式", "text",
                   description="如:全身麻醉/椎管内麻醉/局麻",
                   enum_values=("全身麻醉", "椎管内麻醉", "神经阻滞麻醉", "局部麻醉")),
    ),
    sample_rows=(
        ("47.0901", "腹腔镜下阑尾切除术", "三级", "D008", 60, "全身麻醉"),
        ("36.07", "冠状动脉旁路移植术", "四级", "D015", 240, "全身麻醉"),
        ("85.41", "乳房单纯切除术", "三级", "D020", 90, "全身麻醉"),
    ),
)


order_items_dict = DictTable(
    name="order_items_dict",
    cn_name="医嘱项目字典",
    database="his_db",
    description="医嘱项目主数据,供 orders / order_details 引用,串联药品/检验/检查/治疗。",
    columns=(
        DictColumn("item_code", "项目编码", "text", required=True, primary_key=True,
                   description="医嘱项目编码"),
        DictColumn("item_name", "项目名称", "text", required=True,
                   description="项目名称"),
        DictColumn("item_category", "项目类别", "text", required=True,
                   description="药品/检验/检查/治疗/手术",
                   enum_values=("drug", "lab", "exam", "treatment", "surgery")),
        DictColumn("unit", "计价单位", "text",
                   description="如:支/片/项/次"),
        DictColumn("standard_price", "标准价格", "decimal",
                   description="单价,小数(元)"),
        DictColumn("ref_table", "关联子字典表", "text",
                   description="关联子表名(drugs/lab_items_dict/exam_items_dict 等)"),
    ),
    sample_rows=(
        ("OI001", "青霉素G注射 80万U", "drug", "支", 1.50, "drugs"),
        ("OI100", "血常规", "lab", "项", 18.00, "lab_items_dict"),
        ("OI200", "胸部正位片", "exam", "次", 45.00, "exam_items_dict"),
        ("OI300", "静脉输液", "treatment", "次", 8.00, ""),
    ),
)


charge_items_dict = DictTable(
    name="charge_items_dict",
    cn_name="收费项目字典",
    database="his_db",
    description="收费项目主数据,供 fee_items / settlements 引用,医保乙类/丙类规则的载体。",
    columns=(
        DictColumn("charge_code", "收费编码", "text", required=True, primary_key=True,
                   description="收费项目编码"),
        DictColumn("charge_name", "收费名称", "text", required=True,
                   description="收费项目名称"),
        DictColumn("charge_type", "收费类别", "text", required=True,
                   description="床位/诊查/治疗/手术/药品/材料/检查/检验",
                   enum_values=("床位", "诊查", "治疗", "手术", "药品", "材料", "检查", "检验")),
        DictColumn("unit", "计价单位", "text",
                   description="如:日/次/项"),
        DictColumn("unit_price", "单价", "decimal", required=True,
                   description="单价,小数(元)"),
        DictColumn("insurance_flag", "医保类别", "text",
                   description="甲/乙/丙",
                   enum_values=("甲", "乙", "丙")),
    ),
    sample_rows=(
        ("C001", "床位费(单人间)", "床位", "日", 200.00, "乙"),
        ("C100", "诊查费(主任医师)", "诊查", "次", 30.00, "甲"),
        ("C200", "静脉输液", "治疗", "次", 8.00, "甲"),
        ("C300", "胸部正位片", "检查", "次", 45.00, "甲"),
    ),
)


lab_items_dict = DictTable(
    name="lab_items_dict",
    cn_name="检验项目字典",
    database="lis_db",
    description="检验项目主数据 (含 LOINC),供 lab_orders / 各类结果表引用。",
    columns=(
        DictColumn("item_code", "项目编码", "text", required=True, primary_key=True,
                   description="检验项目编码"),
        DictColumn("item_name", "项目名称", "text", required=True,
                   description="项目中文名"),
        DictColumn("item_category", "项目类别", "text", required=True,
                   description="routine/biochem/blood/immuno/molecular/micro",
                   enum_values=("routine", "biochem", "blood", "immuno", "molecular", "micro")),
        DictColumn("loinc_code", "LOINC编码", "text",
                   description="LOINC 标准编码"),
        DictColumn("unit", "结果单位", "text",
                   description="如:10^9/L、mmol/L"),
        DictColumn("ref_low", "参考下限", "decimal",
                   description="参考值下限"),
        DictColumn("ref_high", "参考上限", "decimal",
                   description="参考值上限"),
        DictColumn("specimen_type", "标本类型", "text",
                   description="blood/urine/stool/csf 等",
                   enum_values=("blood", "urine", "stool", "csf", "sputum", "other")),
        DictColumn("method", "检测方法", "text",
                   description="如:electrical impedance / hexokinase"),
    ),
    sample_rows=(
        ("LAB001", "白细胞计数", "routine", "6690-2", "10^9/L", 4.0, 10.0, "blood", "electrical impedance"),
        ("LAB100", "血糖", "biochem", "2345-7", "mmol/L", 3.9, 6.1, "blood", "hexokinase"),
        ("LAB200", "C反应蛋白", "biochem", "1988-5", "mg/L", 0.0, 10.0, "blood", "immunoturbidimetry"),
    ),
)


organism_dict = DictTable(
    name="organism_dict",
    cn_name="微生物字典",
    database="lis_db",
    description="微生物菌株字典,供 microbiology / antibiotic_sensitivity 引用。",
    columns=(
        DictColumn("organism_code", "菌株编码", "text", required=True, primary_key=True,
                   description="菌株编码"),
        DictColumn("organism_name", "菌株名称", "text", required=True,
                   description="菌株中文名"),
        DictColumn("organism_type", "菌种类型", "text",
                   description="bacteria/fungus/virus",
                   enum_values=("bacteria", "fungus", "virus", "parasite")),
        DictColumn("gram_stain", "革兰染色", "text",
                   description="positive/negative/NA",
                   enum_values=("positive", "negative", "NA")),
    ),
    sample_rows=(
        ("ORG001", "大肠埃希菌", "bacteria", "negative"),
        ("ORG002", "金黄色葡萄球菌", "bacteria", "positive"),
        ("ORG003", "白色念珠菌", "fungus", "NA"),
    ),
)


antibiotic_dict = DictTable(
    name="antibiotic_dict",
    cn_name="抗生素字典",
    database="lis_db",
    description="抗生素字典,供 antibiotic_sensitivity (药敏) 引用。",
    columns=(
        DictColumn("antibiotic_code", "抗生素编码", "text", required=True, primary_key=True,
                   description="抗生素编码"),
        DictColumn("antibiotic_name", "抗生素名称", "text", required=True,
                   description="抗生素中文名"),
        DictColumn("drug_class", "药物分类", "text",
                   description="β内酰胺/氨基糖苷/喹诺酮/大环内酯 等"),
    ),
    sample_rows=(
        ("AB001", "青霉素G", "β内酰胺类"),
        ("AB002", "头孢曲松", "β内酰胺类-第三代头孢"),
        ("AB003", "左氧氟沙星", "喹诺酮类"),
    ),
)


exam_items_dict = DictTable(
    name="exam_items_dict",
    cn_name="检查项目字典",
    database="ris_db",
    description="RIS 检查项目主数据,供 exam_orders / 各影像报告表引用。",
    columns=(
        DictColumn("exam_item_code", "检查项目编码", "text", required=True, primary_key=True,
                   description="检查项目编码"),
        DictColumn("exam_item_name", "检查项目名称", "text", required=True,
                   description="项目名称"),
        DictColumn("exam_type", "检查类型", "text", required=True,
                   description="xray/ct/mri/us/nm/intervention",
                   enum_values=("xray", "ct", "mri", "us", "nm", "intervention")),
        DictColumn("body_part", "检查部位", "text",
                   description="如:胸部/头部/腹部"),
        DictColumn("contrast_required", "是否需要造影剂", "bool",
                   description="TRUE/FALSE"),
        DictColumn("standard_price", "标准价格", "decimal",
                   description="单价(元)"),
        DictColumn("duration_min", "标准时长(分钟)", "int",
                   description="单次检查标准时长"),
    ),
    sample_rows=(
        ("EX001", "胸部正位片", "xray", "胸部", False, 45.00, 5),
        ("EX002", "头颅CT平扫", "ct", "头部", False, 280.00, 10),
        ("EX003", "腹部MRI增强", "mri", "腹部", True, 850.00, 30),
        ("EX004", "甲状腺超声", "us", "颈部", False, 120.00, 15),
    ),
)


# ---------- 注册表 ----------

DICT_TABLES: Tuple[DictTable, ...] = (
    diagnosis_dict,
    surgery_dict,
    order_items_dict,
    charge_items_dict,
    lab_items_dict,
    organism_dict,
    antibiotic_dict,
    exam_items_dict,
)


def get_table(name: str) -> Optional[DictTable]:
    """按名称查找字典表定义。"""
    for t in DICT_TABLES:
        if t.name == name:
            return t
    return None


def tables_for_database(database: str) -> Tuple[DictTable, ...]:
    """获取指定数据库下的所有字典表。"""
    return tuple(t for t in DICT_TABLES if t.database == database)
