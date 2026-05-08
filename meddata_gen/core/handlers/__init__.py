"""事件处理器包：将 MedicalEvent 转换为各系统的数据库行。"""
from __future__ import annotations

from meddata_gen.core.handlers.his_handlers import register_his_handlers
from meddata_gen.core.handlers.lis_handlers import register_lis_handlers
from meddata_gen.core.handlers.ris_handlers import register_ris_handlers
from meddata_gen.core.handlers.emr_handlers import register_emr_handlers
from meddata_gen.core.handlers.bingan_handlers import register_bingan_handlers
from meddata_gen.core.handlers.icu_handlers import register_icu_handlers
from meddata_gen.core.handlers.ecg_handlers import register_ecg_handlers

__all__ = [
    "register_his_handlers",
    "register_lis_handlers",
    "register_ris_handlers",
    "register_emr_handlers",
    "register_bingan_handlers",
    "register_icu_handlers",
    "register_ecg_handlers",
]
