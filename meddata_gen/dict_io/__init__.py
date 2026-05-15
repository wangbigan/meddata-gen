"""字典导入/导出模块。

提供:
    - ``schemas``         字典表元数据(模板生成、Excel 校验、入库 SQL 的单一来源)
    - ``template_builder`` 生成 Excel 空模板
    - ``importer``        读取用户填写的 Excel,校验并入库 (待实现)
    - ``builtin_loader``  将 seed_data.py 内置字典写入数据库 (待实现)
"""
from meddata_gen.dict_io.schemas import (
    DICT_TABLES,
    DictColumn,
    DictTable,
    get_table,
    tables_for_database,
)
from meddata_gen.dict_io.template_builder import build_template

__all__ = [
    "DICT_TABLES",
    "DictColumn",
    "DictTable",
    "get_table",
    "tables_for_database",
    "build_template",
]
