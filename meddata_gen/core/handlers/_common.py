"""Handler 公共辅助函数。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List, Optional


def next_id(prefix: str, counter_ref: list) -> str:
    """通过可变列表维护计数器，生成唯一 ID。

    用法: counter = [0]; next_id('IV', counter) -> 'IV0000001'
    """
    counter_ref[0] += 1
    width = {"IV": 7, "OV": 7, "OR": 8, "FE": 8, "LO": 7, "SP": 7,
             "EO": 7, "RE": 7, "EMR": 7, "DR": 7, "SR": 7, "NR": 7,
             "PN": 7, "MR": 7, "DI": 7, "BGS": 7, "TR": 7,
             "RR": 7, "BR": 7, "BLR": 7, "MC": 7, "AS": 7,
             "XR": 7, "CT": 7, "MRI": 7, "US": 7,
             "ECG": 7, "WF": 7, "EA": 7,
             "IA": 7, "MD": 7, "AL": 7, "BG": 7,
             "RG": 7, "ST": 7, "PP": 7, "BD": 7,
             "ED": 7, "CS": 7, "AR": 7,
             "RM": 7, "CV": 7, "IMG": 7,
             "HL": 7, "HE": 7,
             "VS": 7, "FB": 7, "CR": 7, "SR": 7, "IT": 7,
             "QD": 7, "TM": 7}.get(prefix, 7)
    return f"{prefix}{str(counter_ref[0]).zfill(width)}"


def choose_staff_by_job(staff_rows: list, job_type: str) -> Optional[tuple]:
    """从 staff 列表中按职称筛选。"""
    matched = [s for s in staff_rows if s[10] == job_type]
    return random.choice(matched) if matched else None


def random_cost(min_val: float = 2000, max_val: float = 150000) -> float:
    """生成住院总费用。"""
    return round(random.uniform(min_val, max_val), 2)


def compute_fee_breakdown(total_cost: float) -> dict:
    """将总费用拆分为各项费用明细。"""
    pre_payment = round(total_cost * random.uniform(0.25, 0.35), 2)
    balance = round(total_cost * random.uniform(0.05, 0.15), 2)
    insurance_pay = round(total_cost * random.uniform(0.40, 0.80), 2)
    self_pay = round(total_cost - insurance_pay, 2)
    return {
        "pre_payment": pre_payment,
        "balance": balance,
        "insurance_pay": insurance_pay,
        "self_pay": self_pay,
    }


def maybe(value, rate: float = 0.05):
    """以 rate 概率返回 None，否则返回 value。"""
    return None if random.random() < rate else value
