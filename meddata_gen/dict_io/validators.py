"""字典 Excel 单元格值的解析与校验。

每列依据 ``DictColumn.excel_type`` 进行类型转换:
    text     → str.strip()
    int      → 整数(允许 "123" / 123 / 123.0)
    decimal  → float
    bool     → bool(接受 TRUE/FALSE/是/否/1/0 等)

附加校验:
    required          必填,空值返回错误
    enum_values       值必须在枚举集合内
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from meddata_gen.dict_io.schemas import DictColumn, DictTable


_TRUTHY = {"true", "yes", "y", "1", "是", "T", "真"}
_FALSY = {"false", "no", "n", "0", "否", "F", "假"}


def _is_blank(raw: Any) -> bool:
    if raw is None:
        return True
    if isinstance(raw, str) and not raw.strip():
        return True
    return False


def parse_value(col: DictColumn, raw: Any) -> Tuple[Any, Optional[str]]:
    """解析单个 Excel 单元格的值。

    Args:
        col: 列定义
        raw: openpyxl 读到的原始值 (None / str / int / float / bool / datetime)

    Returns:
        (cleaned, error_msg)
        - error_msg is None 表示校验通过,cleaned 是类型转换后的值
        - error_msg 不为 None 表示校验失败,cleaned 仍返回原始值供日志展示
    """
    if _is_blank(raw):
        if col.required:
            return None, f"必填列 '{col.cn_name}' 不可为空"
        return None, None

    excel_type = col.excel_type

    if excel_type == "text":
        cleaned: Any = str(raw).strip() if not isinstance(raw, str) else raw.strip()
    elif excel_type == "int":
        try:
            if isinstance(raw, bool):
                return raw, f"'{col.cn_name}' 必须是整数,当前: {raw!r}"
            cleaned = int(raw) if isinstance(raw, int) else int(float(str(raw).strip()))
        except (ValueError, TypeError):
            return raw, f"'{col.cn_name}' 必须是整数,当前: {raw!r}"
    elif excel_type == "decimal":
        try:
            if isinstance(raw, bool):
                return raw, f"'{col.cn_name}' 必须是数字,当前: {raw!r}"
            cleaned = float(raw) if isinstance(raw, (int, float)) else float(str(raw).strip())
        except (ValueError, TypeError):
            return raw, f"'{col.cn_name}' 必须是数字,当前: {raw!r}"
    elif excel_type == "bool":
        if isinstance(raw, bool):
            cleaned = raw
        else:
            token = str(raw).strip()
            if token in _TRUTHY or token.lower() in {x.lower() for x in _TRUTHY}:
                cleaned = True
            elif token in _FALSY or token.lower() in {x.lower() for x in _FALSY}:
                cleaned = False
            else:
                return raw, f"'{col.cn_name}' 必须是 TRUE/FALSE,当前: {raw!r}"
    else:
        return raw, f"未知字段类型: {excel_type}"

    if col.enum_values and excel_type == "text" and cleaned not in col.enum_values:
        return raw, (
            f"'{col.cn_name}' 必须是 {list(col.enum_values)} 之一,当前: {raw!r}"
        )

    return cleaned, None


def parse_row(
    table: DictTable, raw_values_by_name: Dict[str, Any]
) -> Tuple[Tuple[Any, ...], List[str]]:
    """按表定义解析一整行。

    Returns:
        (cleaned_tuple, error_messages)
        - cleaned_tuple 长度与 table.columns 一致
        - error_messages 非空表示该行存在校验错误
    """
    cleaned: List[Any] = []
    errors: List[str] = []
    for col in table.columns:
        raw = raw_values_by_name.get(col.name)
        value, err = parse_value(col, raw)
        cleaned.append(value)
        if err:
            errors.append(err)
    return tuple(cleaned), errors


def primary_key_index(table: DictTable) -> int:
    """返回主键列在 columns 元组里的索引位置。"""
    for idx, col in enumerate(table.columns):
        if col.primary_key:
            return idx
    raise ValueError(f"字典表 {table.name} 未定义主键")
