"""内置字典加载器。

将项目 ``seed_data.py`` 中的常量 + 少量硬编码数据，通过 UPSERT 写入 8 张字典表。
供 ``meddata-gen dict-import --use-builtin`` 一键演示/验证使用。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import psycopg2

from meddata_gen import config
from meddata_gen.dict_io.importer import _build_upsert_sql, _connect
from meddata_gen.dict_io.schemas import DICT_TABLES, get_table
from meddata_gen.seed_data import (
    ANTIBIOTICS,
    ICD10_DIAGNOSES,
    LAB_ITEMS,
    MICRO_ORGANISMS,
    RIS_EXAM_TYPES,
)


# ---------- 内置数据补充(手术/医嘱/收费) ----------

_BUILTIN_SURGERIES: List[Tuple] = [
    ("47.0901", "腹腔镜下阑尾切除术", "三级", "DEPT011", 60, "全身麻醉"),
    ("47.1900", "阑尾切除术", "二级", "DEPT011", 45, "全身麻醉"),
    ("36.07", "冠状动脉旁路移植术", "四级", "DEPT012", 240, "全身麻醉"),
    ("36.06", "冠状动脉支架置入术", "三级", "DEPT012", 90, "局部麻醉"),
    ("39.9000", "外周动脉介入治疗", "三级", "DEPT037", 60, "局部麻醉"),
    ("85.41", "乳房单纯切除术", "三级", "DEPT011", 90, "全身麻醉"),
    ("85.43", "乳房根治性切除术", "四级", "DEPT011", 150, "全身麻醉"),
    ("50.2200", "肝部分切除术", "四级", "DEPT011", 180, "全身麻醉"),
    ("51.2300", "胆囊切除术", "三级", "DEPT011", 90, "全身麻醉"),
    ("51.8800", "胆总管探查术", "三级", "DEPT011", 120, "全身麻醉"),
    ("52.9500", "胰腺切除术", "四级", "DEPT011", 240, "全身麻醉"),
    ("53.9000", "腹股沟疝修补术", "二级", "DEPT011", 60, "椎管内麻醉"),
    ("54.5100", "腹腔镜下腹膜粘连松解术", "三级", "DEPT011", 90, "全身麻醉"),
    ("54.5900", "剖腹探查术", "三级", "DEPT011", 120, "全身麻醉"),
    ("55.0300", "肾切开引流术", "三级", "DEPT015", 90, "全身麻醉"),
    ("55.5100", "肾切除术", "四级", "DEPT015", 150, "全身麻醉"),
    ("56.0x00", "输尿管切开术", "三级", "DEPT015", 90, "全身麻醉"),
    ("57.4900", "膀胱部分切除术", "三级", "DEPT015", 120, "全身麻醉"),
    ("60.2900", "前列腺切除术", "三级", "DEPT015", 120, "全身麻醉"),
    ("60.6100", "经尿道前列腺电切术", "三级", "DEPT015", 90, "椎管内麻醉"),
    ("68.2900", "子宫切除术", "三级", "DEPT019", 120, "全身麻醉"),
    ("68.4100", "腹腔镜下子宫切除术", "四级", "DEPT019", 150, "全身麻醉"),
    ("74.1x00", "剖宫产术", "二级", "DEPT020", 60, "椎管内麻醉"),
    ("76.4600", "颌骨骨折切开复位内固定术", "三级", "DEPT026", 90, "全身麻醉"),
    ("77.0700", "关节切开术", "二级", "DEPT014", 60, "全身麻醉"),
    ("77.5900", "骨移植术", "三级", "DEPT014", 120, "全身麻醉"),
    ("78.5000", "骨折内固定术", "三级", "DEPT014", 90, "全身麻醉"),
    ("80.1600", "膝关节镜检查", "二级", "DEPT014", 45, "全身麻醉"),
    ("80.5100", "椎间盘切除术", "四级", "DEPT014", 180, "全身麻醉"),
    ("80.9900", "椎板切除术", "四级", "DEPT014", 180, "全身麻醉"),
    ("81.5200", "髋关节置换术", "四级", "DEPT014", 150, "全身麻醉"),
    ("81.5400", "膝关节置换术", "四级", "DEPT014", 150, "全身麻醉"),
    ("81.6200", "关节镜下滑膜切除术", "三级", "DEPT014", 90, "全身麻醉"),
    ("86.2200", "皮肤和皮下组织切除术", "一级", "DEPT011", 30, "局部麻醉"),
    ("86.5900", "清创缝合术", "一级", "DEPT011", 20, "局部麻醉"),
    ("01.2400", "颅骨钻孔引流术", "三级", "DEPT013", 90, "全身麻醉"),
    ("01.3900", "颅内肿瘤切除术", "四级", "DEPT013", 240, "全身麻醉"),
    ("01.5900", "脑室腹腔分流术", "三级", "DEPT013", 120, "全身麻醉"),
    ("32.2900", "肺叶切除术", "四级", "DEPT012", 180, "全身麻醉"),
    ("33.2300", "胸腔镜检查", "二级", "DEPT012", 60, "全身麻醉"),
    ("37.3300", "心包穿刺引流术", "二级", "DEPT012", 30, "局部麻醉"),
    ("38.0200", "颈动脉内膜剥脱术", "四级", "DEPT037", 180, "全身麻醉"),
    ("38.1800", "血管搭桥术", "四级", "DEPT037", 240, "全身麻醉"),
    ("43.4200", "贲门切除术", "四级", "DEPT011", 180, "全身麻醉"),
    ("43.8900", "胃大部切除术", "三级", "DEPT011", 120, "全身麻醉"),
    ("43.9900", "全胃切除术", "四级", "DEPT011", 180, "全身麻醉"),
    ("45.7300", "结肠部分切除术", "三级", "DEPT011", 150, "全身麻醉"),
    ("45.7600", "乙状结肠切除术", "三级", "DEPT011", 150, "全身麻醉"),
    ("46.3200", "肠造口术", "二级", "DEPT011", 60, "全身麻醉"),
    ("46.5200", "肠吻合术", "三级", "DEPT011", 120, "全身麻醉"),
    ("48.3500", "直肠前切除术", "四级", "DEPT011", 180, "全身麻醉"),
    ("48.6900", "直肠切除术", "三级", "DEPT011", 120, "全身麻醉"),
    ("48.7100", "痔切除术", "一级", "DEPT011", 30, "椎管内麻醉"),
    ("84.1000", "截肢术", "二级", "DEPT014", 90, "全身麻醉"),
]

_BUILTIN_ORDER_ITEMS: List[Tuple] = [
    # 药品类
    ("OI001", "青霉素G注射 80万U", "drug", "支", 1.50, "drugs"),
    ("OI002", "头孢曲松钠注射 1g", "drug", "支", 12.00, "drugs"),
    ("OI003", "左氧氟沙星注射 0.5g", "drug", "支", 18.50, "drugs"),
    ("OI004", "阿司匹林肠溶片 100mg", "drug", "片", 0.15, "drugs"),
    ("OI005", "氯吡格雷片 75mg", "drug", "片", 3.20, "drugs"),
    ("OI006", "阿托伐他汀钙片 20mg", "drug", "片", 2.80, "drugs"),
    ("OI007", "氨氯地平片 5mg", "drug", "片", 0.45, "drugs"),
    ("OI008", "二甲双胍片 0.5g", "drug", "片", 0.20, "drugs"),
    ("OI009", "胰岛素(诺和灵R) 10ml", "drug", "支", 35.00, "drugs"),
    ("OI010", "硝酸甘油片 0.5mg", "drug", "片", 0.10, "drugs"),
    ("OI011", "奥美拉唑注射 40mg", "drug", "支", 8.50, "drugs"),
    ("OI012", "帕瑞昔布钠注射 40mg", "drug", "支", 45.00, "drugs"),
    ("OI013", "地佐辛注射 5mg", "drug", "支", 28.00, "drugs"),
    ("OI014", "氯化钠注射液 0.9% 250ml", "drug", "瓶", 2.50, "drugs"),
    ("OI015", "葡萄糖注射液 5% 250ml", "drug", "瓶", 2.80, "drugs"),
    # 检验类
    ("OI100", "血常规", "lab", "项", 18.00, "lab_items_dict"),
    ("OI101", "尿常规", "lab", "项", 12.00, "lab_items_dict"),
    ("OI102", "大便常规", "lab", "项", 8.00, "lab_items_dict"),
    ("OI103", "生化全套", "lab", "项", 120.00, "lab_items_dict"),
    ("OI104", "凝血功能", "lab", "项", 45.00, "lab_items_dict"),
    ("OI105", "血气分析", "lab", "项", 65.00, "lab_items_dict"),
    ("OI106", "肿瘤标志物", "lab", "项", 180.00, "lab_items_dict"),
    ("OI107", "甲状腺功能", "lab", "项", 95.00, "lab_items_dict"),
    ("OI108", "糖化血红蛋白", "lab", "项", 35.00, "lab_items_dict"),
    ("OI109", "传染病筛查", "lab", "项", 85.00, "lab_items_dict"),
    ("OI110", "微生物培养+药敏", "lab", "项", 120.00, "lab_items_dict"),
    ("OI111", "D-二聚体", "lab", "项", 45.00, "lab_items_dict"),
    # 检查类
    ("OI200", "胸部正位片", "exam", "次", 45.00, "exam_items_dict"),
    ("OI201", "头颅CT平扫", "exam", "次", 280.00, "exam_items_dict"),
    ("OI202", "腹部CT增强", "exam", "次", 450.00, "exam_items_dict"),
    ("OI203", "头颅MRI平扫", "exam", "次", 550.00, "exam_items_dict"),
    ("OI204", "腹部超声", "exam", "次", 80.00, "exam_items_dict"),
    ("OI205", "心脏超声", "exam", "次", 150.00, "exam_items_dict"),
    ("OI206", "颈动脉超声", "exam", "次", 120.00, "exam_items_dict"),
    ("OI207", "冠状动脉CTA", "exam", "次", 1200.00, "exam_items_dict"),
    # 治疗/护理类
    ("OI300", "静脉输液", "treatment", "次", 8.00, ""),
    ("OI301", "肌肉注射", "treatment", "次", 3.00, ""),
    ("OI302", "吸氧", "treatment", "小时", 2.00, ""),
    ("OI303", "心电监护", "treatment", "日", 25.00, ""),
    ("OI304", "留置导尿", "treatment", "次", 15.00, ""),
    ("OI305", "换药(小)", "treatment", "次", 12.00, ""),
    ("OI306", "换药(大)", "treatment", "次", 25.00, ""),
    ("OI307", "拆线", "treatment", "次", 15.00, ""),
    ("OI308", "胸腔闭式引流", "treatment", "次", 80.00, ""),
    # 手术类
    ("OI400", "阑尾切除术", "surgery", "次", 800.00, "surgery_dict"),
    ("OI401", "胆囊切除术", "surgery", "次", 1200.00, "surgery_dict"),
    ("OI402", "剖宫产术", "surgery", "次", 600.00, "surgery_dict"),
    ("OI403", "髋关节置换术", "surgery", "次", 2500.00, "surgery_dict"),
    ("OI404", "冠状动脉旁路移植术", "surgery", "次", 5000.00, "surgery_dict"),
]

_BUILTIN_CHARGE_ITEMS: List[Tuple] = [
    ("C001", "床位费(普通病房)", "床位", "日", 45.00, "甲"),
    ("C002", "床位费(双人间)", "床位", "日", 120.00, "乙"),
    ("C003", "床位费(单人间)", "床位", "日", 200.00, "乙"),
    ("C004", "重症监护床位费", "床位", "日", 350.00, "甲"),
    ("C010", "诊查费(普通门诊)", "诊查", "次", 10.00, "甲"),
    ("C011", "诊查费(专家门诊)", "诊查", "次", 20.00, "甲"),
    ("C012", "诊查费(主任医师)", "诊查", "次", 30.00, "甲"),
    ("C013", "会诊费(院内)", "诊查", "次", 50.00, "甲"),
    ("C014", "会诊费(院外)", "诊查", "次", 200.00, "乙"),
    ("C020", "静脉输液", "治疗", "次", 8.00, "甲"),
    ("C021", "肌肉注射", "治疗", "次", 3.00, "甲"),
    ("C022", "静脉采血", "治疗", "次", 3.00, "甲"),
    ("C023", "吸氧", "治疗", "小时", 2.00, "甲"),
    ("C024", "心电监护", "治疗", "日", 25.00, "甲"),
    ("C025", "留置导尿", "治疗", "次", 15.00, "甲"),
    ("C026", "胸腔闭式引流", "治疗", "次", 80.00, "甲"),
    ("C030", "阑尾切除术", "手术", "次", 800.00, "甲"),
    ("C031", "胆囊切除术", "手术", "次", 1200.00, "甲"),
    ("C032", "剖宫产术", "手术", "次", 600.00, "甲"),
    ("C033", "髋关节置换术", "手术", "次", 2500.00, "甲"),
    ("C034", "冠状动脉旁路移植术", "手术", "次", 5000.00, "甲"),
    ("C040", "青霉素G注射", "药品", "支", 1.50, "甲"),
    ("C041", "头孢曲松钠注射", "药品", "支", 12.00, "乙"),
    ("C042", "左氧氟沙星注射", "药品", "支", 18.50, "乙"),
    ("C043", "阿司匹林肠溶片", "药品", "片", 0.15, "甲"),
    ("C044", "氯吡格雷片", "药品", "片", 3.20, "乙"),
    ("C045", "阿托伐他汀钙片", "药品", "片", 2.80, "乙"),
    ("C046", "二甲双胍片", "药品", "片", 0.20, "甲"),
    ("C047", "胰岛素(诺和灵R)", "药品", "支", 35.00, "甲"),
    ("C050", "一次性输液器", "材料", "套", 3.50, "甲"),
    ("C051", "一次性注射器", "材料", "支", 0.80, "甲"),
    ("C052", "留置针", "材料", "支", 15.00, "甲"),
    ("C060", "胸部正位片", "检查", "次", 45.00, "甲"),
    ("C061", "头颅CT平扫", "检查", "次", 280.00, "甲"),
    ("C062", "头颅MRI平扫", "检查", "次", 550.00, "甲"),
    ("C063", "腹部超声", "检查", "次", 80.00, "甲"),
    ("C070", "血常规", "检验", "项", 18.00, "甲"),
    ("C071", "尿常规", "检验", "项", 12.00, "甲"),
    ("C072", "生化全套", "检验", "项", 120.00, "甲"),
    ("C073", "凝血功能", "检验", "项", 45.00, "甲"),
    ("C074", "血气分析", "检验", "项", 65.00, "甲"),
]


# ---------- 数据转换函数 ----------

def _build_diagnosis_rows() -> List[Tuple]:
    """ICD10_DIAGNOSES → diagnosis_dict 行。"""
    # 简化的 category 映射,按首字母分类
    category_map: Dict[str, str] = {
        "A": "传染病和寄生虫病",
        "B": "传染病和寄生虫病",
        "C": "肿瘤",
        "D": "肿瘤/血液病",
        "E": "内分泌、营养和代谢疾病",
        "G": "神经系统疾病",
        "H": "眼和附器疾病",
        "I": "循环系统疾病",
        "J": "呼吸系统疾病",
        "K": "消化系统疾病",
        "L": "皮肤和皮下组织疾病",
        "M": "肌肉骨骼和结缔组织疾病",
        "N": "泌尿生殖系统疾病",
        "O": "妊娠、分娩和产褥期",
        "Q": "先天性畸形",
        "R": "症状、体征和临床异常",
        "S": "损伤",
        "T": "损伤/中毒",
        "Z": "影响健康状态的因素",
    }
    # 慢性/传染病清单(基于已知编码)
    infectious = {"A09", "A41", "B18", "B24", "J12", "J15"}
    chronic = {
        "E11", "E05", "E78", "I10", "I11", "I20", "I25", "I50", "I48",
        "J44", "J45", "J47", "K25", "K26", "K74", "K80", "M06", "M10",
        "M16", "M17", "M47", "M54", "N18", "N20", "N40", "D64",
        "G20", "G35", "G40", "Q21",
    }
    rows = []
    for code, name in ICD10_DIAGNOSES:
        cat = category_map.get(code[0], "其他")
        rows.append((code, name, cat, code in chronic, code in infectious))
    return rows


def _build_lab_rows() -> List[Tuple]:
    """LAB_ITEMS → lab_items_dict 行。"""
    specimen_map = {
        "routine": "blood",
        "biochem": "blood",
        "blood": "blood",
        "immuno": "blood",
        "molecular": "blood",
        "micro": "other",
    }
    # LOINC 编码(部分)
    loinc_map = {
        "WBC": "6690-2", "RBC": "789-8", "HGB": "718-7", "PLT": "777-3",
        "NEUT%": "737835-2", "LYMPH%": "736916-5", "GLU": "2345-7",
        "UREA": "3091-6", "CREA": "2160-0", "UA": "3084-1",
        "TC": "2093-3", "TG": "2571-8", "ALT": "1742-6", "AST": "1920-8",
        "TBIL": "1975-2", "ALB": "1751-7", "K": "2823-3", "Na": "2951-2",
        "PT": "6301-6", "INR": "6301-6", "APTT": "3173-2", "FIB": "3255-7",
        "D-Dimer": "33717-0", "HbA1c": "4548-4",
    }
    rows = []
    for category, items in LAB_ITEMS.items():
        for item in items:
            code, name, unit, ref_low, ref_high = item
            loinc = loinc_map.get(code, "")
            rows.append((
                code, name, category, loinc, unit,
                float(ref_low) if ref_low else None,
                float(ref_high) if ref_high else None,
                specimen_map.get(category, "other"),
                "",
            ))
    return rows


def _build_organism_rows() -> List[Tuple]:
    """MICRO_ORGANISMS → organism_dict 行。"""
    gram_map = {
        "大肠埃希菌": "negative", "肺炎克雷伯菌": "negative", "铜绿假单胞菌": "negative",
        "鲍曼不动杆菌": "negative", "金黄色葡萄球菌": "positive", "表皮葡萄球菌": "positive",
        "凝固酶阴性葡萄球菌": "positive", "粪肠球菌": "positive", "屎肠球菌": "positive",
        "肺炎链球菌": "positive", "化脓性链球菌": "positive", "流感嗜血杆菌": "negative",
        "阴沟肠杆菌": "negative", "产气肠杆菌": "negative", "变形杆菌": "negative",
        "普罗威登斯菌": "negative", "沙雷菌": "negative", "嗜麦芽窄食单胞菌": "negative",
        "洋葱伯克霍尔德菌": "negative", "白色念珠菌": "NA", "热带念珠菌": "NA",
        "光滑念珠菌": "NA", "克柔念珠菌": "NA", "近平滑念珠菌": "NA",
        "曲霉菌": "NA", "毛霉菌": "NA", "新型隐球菌": "NA",
        "结核分枝杆菌": "NA", "脆弱拟杆菌": "negative", "厌氧链球菌": "positive",
    }
    rows = []
    for code, name in MICRO_ORGANISMS:
        org_type = "fungus" if "念珠菌" in name or "霉菌" in name or "隐球菌" in name else (
            "bacteria" if "分枝杆菌" in name else "bacteria"
        )
        if "分枝杆菌" in name:
            org_type = "bacteria"
        rows.append((code, name, org_type, gram_map.get(name, "NA")))
    return rows


def _build_antibiotic_rows() -> List[Tuple]:
    """ANTIBIOTICS → antibiotic_dict 行。"""
    class_map = {
        "青霉素G": "β内酰胺类", "氨苄西林": "β内酰胺类", "哌拉西林": "β内酰胺类",
        "头孢唑林": "β内酰胺类-第一代头孢", "头孢呋辛": "β内酰胺类-第二代头孢",
        "头孢曲松": "β内酰胺类-第三代头孢", "头孢噻肟": "β内酰胺类-第三代头孢",
        "头孢他啶": "β内酰胺类-第三代头孢", "头孢吡肟": "β内酰胺类-第四代头孢",
        "头孢哌酮/舒巴坦": "β内酰胺类/β内酰胺酶抑制剂",
        "氨曲南": "单环β内酰胺类", "亚胺培南": "碳青霉烯类", "美罗培南": "碳青霉烯类",
        "厄他培南": "碳青霉烯类", "阿米卡星": "氨基糖苷类", "庆大霉素": "氨基糖苷类",
        "妥布霉素": "氨基糖苷类", "环丙沙星": "喹诺酮类", "左氧氟沙星": "喹诺酮类",
        "莫西沙星": "喹诺酮类", "四环素": "四环素类", "多西环素": "四环素类",
        "米诺环素": "四环素类", "替加环素": "甘氨酰环素类", "万古霉素": "糖肽类",
        "替考拉宁": "糖肽类", "利奈唑胺": "噁唑烷酮类", "达托霉素": "环脂肽类",
        "多粘菌素B": "多粘菌素类", "多粘菌素E": "多粘菌素类", "复方新诺明": "磺胺类",
        "克林霉素": "林可酰胺类", "红霉素": "大环内酯类", "阿奇霉素": "大环内酯类",
        "氯霉素": "酰胺醇类", "呋喃妥因": "硝基呋喃类", "磷霉素": "磷霉素类",
        "利福平": "利福霉素类", "夫西地酸": "甾体类", "甲硝唑": "硝基咪唑类",
    }
    rows = []
    for code, name in ANTIBIOTICS:
        rows.append((code, name, class_map.get(name, "")))
    return rows


def _build_exam_rows() -> List[Tuple]:
    """RIS_EXAM_TYPES → exam_items_dict 行(扁平化)。"""
    type_map = {
        "X光": "xray", "CT": "ct", "MRI": "mri", "超声": "us",
    }
    # 部位与造影剂映射(部分)
    contrast_map = {
        "胸部正位": False, "腹部平片": False, "头颅正侧位": False,
        "头颅增强": True, "胸部增强": True, "腹部增强": True,
        "盆腔增强": True, "冠状动脉CTA": True, "肺动脉CTA": True,
        "主动脉CTA": True, "泌尿系CTU": True, "肝脏三期增强": True,
        "胰腺增强CT": True, "肝脏MRI": True, "胰腺MRI": True,
        "盆腔MRI": True, "MRCP": True, "MRA": True, "超声造影": True,
    }
    price_map = {
        "X光": 45.0, "CT": 280.0, "MRI": 550.0, "超声": 80.0,
    }
    duration_map = {
        "X光": 5, "CT": 10, "MRI": 30, "超声": 15,
    }
    rows = []
    idx = 1
    for exam_type, items in RIS_EXAM_TYPES.items():
        db_type = type_map.get(exam_type, "xray")
        for item_name in items:
            code = f"EX{idx:03d}"
            part = item_name.split("(")[0].replace("CT", "").replace("MRI", "").replace("超声", "").replace("", "").strip() or ""
            # 简单部位推断
            if "胸" in item_name or "肺" in item_name:
                part = "胸部"
            elif "头" in item_name or "脑" in item_name or "颅" in item_name:
                part = "头部"
            elif "腹" in item_name or "肝" in item_name or "胰" in item_name or "脾" in item_name:
                part = "腹部"
            elif "颈" in item_name or "椎" in item_name:
                part = "颈部/脊柱"
            elif "膝" in item_name or "髋" in item_name or "肩" in item_name or "踝" in item_name:
                part = "四肢关节"
            elif "盆" in item_name:
                part = "盆腔"
            elif "乳腺" in item_name or "前列腺" in item_name:
                part = "其他"
            elif "心脏" in item_name or "冠脉" in item_name or "血管" in item_name:
                part = "心血管"
            contrast = contrast_map.get(item_name, "增强" in item_name or "造影" in item_name or "CTA" in item_name or "CTU" in item_name)
            price = price_map.get(exam_type, 100.0)
            if "增强" in item_name or "CTA" in item_name or "CTU" in item_name:
                price *= 1.5
            if "MRI" in item_name:
                price = 550.0
            rows.append((
                code, item_name, db_type, part,
                bool(contrast), round(price, 2), duration_map.get(exam_type, 10),
            ))
            idx += 1
    return rows


# ---------- 统一入库 ----------

def load_builtin_dicts() -> Dict[str, int]:
    """将内置示例字典写入各数据库,返回 {table_name: rows_written}。"""
    data_sources = {
        "diagnosis_dict": _build_diagnosis_rows(),
        "surgery_dict": _BUILTIN_SURGERIES,
        "order_items_dict": _BUILTIN_ORDER_ITEMS,
        "charge_items_dict": _BUILTIN_CHARGE_ITEMS,
        "lab_items_dict": _build_lab_rows(),
        "organism_dict": _build_organism_rows(),
        "antibiotic_dict": _build_antibiotic_rows(),
        "exam_items_dict": _build_exam_rows(),
    }

    stats: Dict[str, int] = {}
    db_connections: Dict[str, Any] = {}

    for table_name, rows in data_sources.items():
        table = get_table(table_name)
        if table is None:
            continue

        db_name = table.database
        if db_name not in db_connections:
            db_connections[db_name] = _connect(db_name)
            db_connections[db_name].autocommit = True

        conn = db_connections[db_name]
        cur = conn.cursor()
        sql = _build_upsert_sql(table)
        written = 0
        for row in rows:
            try:
                cur.execute(sql, row)
                written += 1
            except psycopg2.Error:
                # 冲突或其他错误,跳过(upsert 模式下不应频繁出现)
                pass
        cur.close()
        stats[table_name] = written

    for conn in db_connections.values():
        conn.close()

    return stats
