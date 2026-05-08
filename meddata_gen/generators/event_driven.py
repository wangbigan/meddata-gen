"""EventDrivenGenerator: 事件驱动的数据生成器。

复用 HISMixin 的基础字典生成方法（departments/staff/drugs/patients/beds），
然后用事件模型生成患者就诊旅程（inpatient/outpatient），跨系统自动产生一致的数据。

用法:
    gen = EventDrivenGenerator(DB_CONFIG, seed=42)
    gen.generate_departments()
    gen.generate_staff(200)
    gen.generate_drugs(500)
    gen.generate_patients(5000)
    gen.generate_beds()
    gen.generate_journeys(inpatient_count=8000, outpatient_count=20000)
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional

from meddata_gen.core.base import BaseGenerator
from meddata_gen.core.events import EventContext, TimelineEngine
from meddata_gen.core.journey_builder import JourneyBuilder
from meddata_gen.core.materializer import Materializer
from meddata_gen.core.handlers import (
    register_bingan_handlers,
    register_ecg_handlers,
    register_emr_handlers,
    register_his_handlers,
    register_icu_handlers,
    register_lis_handlers,
    register_ris_handlers,
)
from meddata_gen.generators.his import HISMixin
from meddata_gen.seed_data import DEPARTMENTS, ICD10_DIAGNOSES
from meddata_gen.clinical.disease_profiles import random_disease_profile, select_profile_for_icd
from meddata_gen.quality.defect_engine import ScenarioDefectEngine
from meddata_gen import config
from meddata_gen.output.base import OutputWriter


class EventDrivenGenerator(BaseGenerator, HISMixin):
    """事件驱动的统一数据生成器。

    继承 BaseGenerator 获取连接管理和缺陷注入工具，
    继承 HISMixin 获取基础字典数据生成能力。
    """

    def __init__(
        self,
        db_config: dict,
        seed: Optional[int] = None,
        writer: Optional[OutputWriter] = None,
    ) -> None:
        super().__init__(db_config, seed=seed)
        self.timeline = TimelineEngine()
        self.journey_builder = JourneyBuilder()

        # 场景化缺陷引擎（默认从配置读取，空列表表示禁用）
        scenarios = getattr(config, "QUALITY_SCENARIOS", [])
        defect_engine = ScenarioDefectEngine(scenarios) if scenarios else None
        self.materializer = Materializer(writer=writer, defect_engine=defect_engine)

        # 注册所有系统的事件处理器
        register_his_handlers(self.materializer)
        register_lis_handlers(self.materializer)
        register_ris_handlers(self.materializer)
        register_emr_handlers(self.materializer)
        register_bingan_handlers(self.materializer)
        register_icu_handlers(self.materializer)
        register_ecg_handlers(self.materializer)

        # ID 计数器（跨旅程唯一）
        self._visit_counter = [0]
        self._outpatient_counter = [0]

        # 共享状态：跨所有 EventContext 的全局计数器（避免 order_id 等重复）
        self._shared_state = {}

    # ------------------------------------------------------------------
    # 旅程生成（核心入口）
    # ------------------------------------------------------------------

    def generate_journeys(
        self,
        inpatient_count: int = 8000,
        outpatient_count: int = 20000,
    ) -> None:
        """生成住院和门诊患者旅程，并写入数据库。"""
        print(f"\n[EventDriven] 生成 {inpatient_count} 条住院旅程 + {outpatient_count} 条门诊旅程")

        # 住院
        for i in range(inpatient_count):
            ctx = self._create_inpatient_context(i)
            events = self.journey_builder.build(ctx)
            self.materializer.materialize(events, ctx)
            if (i + 1) % 500 == 0:
                print(f"  ...住院旅程 {(i + 1)}/{inpatient_count}")

        # 门诊
        for i in range(outpatient_count):
            ctx = self._create_outpatient_context(i)
            events = self.journey_builder.build(ctx)
            self.materializer.materialize(events, ctx)
            if (i + 1) % 2000 == 0:
                print(f"  ...门诊旅程 {(i + 1)}/{outpatient_count}")

        # 一次性 flush 所有缓冲数据
        self.materializer.flush(self.db_config)
        self.materializer.clear()

    # ------------------------------------------------------------------
    # Context 构建
    # ------------------------------------------------------------------

    def _create_inpatient_context(self, index: int) -> EventContext:
        """为单个住院患者创建就诊上下文。"""
        patient = random.choice(self.patients) if self.patients else self._mock_patient(index)
        doctor = self._pick_doctor()

        # 随机选择疾病画像（30% 概率）或随机诊断
        if random.random() < 0.30:
            icd_code, profile = random_disease_profile()
            diagnosis_name = profile.name
            diagnosis_icd = icd_code
        else:
            diagnosis = random.choice(ICD10_DIAGNOSES)
            diagnosis_name = diagnosis[1]
            diagnosis_icd = diagnosis[0]
            profile = select_profile_for_icd(diagnosis_icd)

        # 科室：优先使用疾病画像，否则随机
        if profile and profile.typical_departments:
            dept = random.choice(profile.typical_departments)
        else:
            dept = self._pick_clinical_dept()

        self._visit_counter[0] += 1
        visit_id = f"IV{str(self._visit_counter[0]).zfill(7)}"

        # 入院时间：2023-01-01 ~ 2024-12-20（留出院时间空间）
        admission_time = self._random_admission_time()

        # LOS：优先使用疾病画像分布
        if profile and profile.los_distribution:
            los_choices = [d for d, _ in profile.los_distribution]
            los_weights = [w for _, w in profile.los_distribution]
            los = random.choices(los_choices, weights=los_weights)[0]
        else:
            los = random.choices(
                range(1, 61),
                weights=[15] * 3 + [20] * 7 + [15] * 10 + [10] * 15 + [5] * 20 + [3] * 5,
            )[0]
        discharge_time = admission_time + timedelta(days=los)

        return EventContext(
            patient_id=patient[0],
            patient_name=patient[2] if len(patient) > 2 else "未知",
            gender=patient[3] if len(patient) > 3 else "U",
            birthday=patient[4] if len(patient) > 4 else datetime(1980, 1, 1),
            visit_id=visit_id,
            visit_type="inpatient",
            admission_time=admission_time,
            discharge_time=discharge_time,
            department_id=dept,
            attending_doctor_id=doctor,
            primary_diagnosis=diagnosis_name,
            primary_icd=diagnosis_icd,
            disease_profile=profile,
            state=self._shared_state,
        )

    def _create_outpatient_context(self, index: int) -> EventContext:
        """为单个门诊患者创建就诊上下文。"""
        patient = random.choice(self.patients) if self.patients else self._mock_patient(index)
        doctor = self._pick_doctor()

        # 门诊更倾向于常见病画像（糖尿病等）
        if random.random() < 0.30:
            icd_code, profile = random_disease_profile()
            diagnosis_name = profile.name
            diagnosis_icd = icd_code
        else:
            diagnosis = random.choice(ICD10_DIAGNOSES)
            diagnosis_name = diagnosis[1]
            diagnosis_icd = diagnosis[0]
            profile = select_profile_for_icd(diagnosis_icd)

        # 科室
        if profile and profile.typical_departments:
            dept = random.choice(profile.typical_departments)
        else:
            dept = self._pick_outpatient_dept()

        self._outpatient_counter[0] += 1
        visit_id = f"OV{str(self._outpatient_counter[0]).zfill(7)}"

        visit_date = self._random_visit_date()
        visit_time = datetime.combine(
            visit_date, datetime.min.time()
        ) + timedelta(hours=random.randint(7, 21), minutes=random.randint(0, 59))

        return EventContext(
            patient_id=patient[0],
            patient_name=patient[2] if len(patient) > 2 else "未知",
            gender=patient[3] if len(patient) > 3 else "U",
            birthday=patient[4] if len(patient) > 4 else datetime(1980, 1, 1),
            visit_id=visit_id,
            visit_type="outpatient",
            visit_time=visit_time,
            department_id=dept,
            attending_doctor_id=doctor,
            primary_diagnosis=diagnosis_name,
            primary_icd=diagnosis_icd,
            disease_profile=profile,
            state=self._shared_state,
        )

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _pick_doctor(self) -> Optional[str]:
        if not self.staff:
            return None
        doctors = [s[0] for s in self.staff if s[10] == "医生"]
        return random.choice(doctors) if doctors else None

    def _pick_clinical_dept(self) -> Optional[str]:
        depts = [d["id"] for d in self.departments if d.get("ward") == "Y"]
        return random.choice(depts) if depts else None

    def _pick_outpatient_dept(self) -> Optional[str]:
        depts = [d["id"] for d in self.departments if d.get("outpatient") == "Y"]
        return random.choice(depts) if depts else None

    def _random_admission_time(self) -> datetime:
        """随机入院时间。"""
        start = datetime(2023, 1, 1)
        end = datetime(2024, 12, 20)
        delta = end - start
        return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

    def _random_visit_date(self) -> datetime.date:
        """随机门诊日期。"""
        start = datetime(2023, 1, 1)
        end = datetime(2024, 12, 31)
        delta = end - start
        return (start + timedelta(days=random.randint(0, delta.days))).date()

    def _mock_patient(self, index: int) -> tuple:
        """当 patients 列表为空时的降级方案。"""
        return (
            f"P{str(index + 1).zfill(6)}",
            f"MR{random.randint(100000, 999999)}",
            "患者" + str(index + 1),
            "M",
            datetime(1980, 1, 1),
        )
