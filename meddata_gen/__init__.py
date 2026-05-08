"""meddata_gen: 医院信息系统模拟数据生成器。

从 meddata_gen 导入 DataGenerator 即可获得包含全部子系统生成方法的统一接口：

    from meddata_gen import DataGenerator
    gen = DataGenerator(DB_CONFIG).connect("his_db")
    gen.generate_patients(5000)

CLI 入口：``meddata-gen --help`` 或 ``python -m meddata_gen --help``。
"""

from meddata_gen.core.base import BaseGenerator
from meddata_gen.generators.his import HISMixin
from meddata_gen.generators.emr import EMRMixin
from meddata_gen.generators.bingan import BinganMixin
from meddata_gen.generators.lis import LISMixin
from meddata_gen.generators.ris import RISMixin
from meddata_gen.generators.ecg import ECGMixin
from meddata_gen.generators.icu import ICUMixin
from meddata_gen.generators.event_driven import EventDrivenGenerator


class DataGenerator(
    BaseGenerator,
    HISMixin,
    EMRMixin,
    BinganMixin,
    LISMixin,
    RISMixin,
    ECGMixin,
    ICUMixin,
):
    """组合全部子系统能力的统一数据生成器。"""


__all__ = ["DataGenerator", "BaseGenerator", "EventDrivenGenerator"]
__version__ = "0.1.0"
