"""JourneyBuilder: 按临床流程编排患者就诊事件序列。

住院场景:
    admission → 入院记录 → 首次检验 → 检验结果 → 影像申请 → 影像报告
    → 每日医嘱/病程 → 手术(如需要) → 术后检验 → ICU(如需要)
    → ECG(如需要) → 出院 → 病案归档

门诊场景:
    outpatient_visit → 检验申请 → 结果 → 影像申请 → 开药
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List

from meddata_gen.core.events import EventContext, MedicalEvent, TimelineEngine
from meddata_gen.seed_data import ICD10_DIAGNOSES


class JourneyBuilder:
    """构建单次患者就诊的完整事件序列。"""

    def __init__(self) -> None:
        self.timeline = TimelineEngine()

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def build(self, ctx: EventContext) -> List[MedicalEvent]:
        """根据 visit_type 构建对应旅程。"""
        if ctx.visit_type == "inpatient":
            events = self._build_inpatient(ctx)
        else:
            events = self._build_outpatient(ctx)
        # 按时间排序
        events.sort(key=lambda e: e.timestamp)
        return events

    # ------------------------------------------------------------------
    # 住院旅程
    # ------------------------------------------------------------------

    def _build_inpatient(self, ctx: EventContext) -> List[MedicalEvent]:
        events: List[MedicalEvent] = []
        assert ctx.admission_time is not None
        assert ctx.discharge_time is not None

        # 1. 入院
        events.append(self._event(ctx, "admission", ctx.admission_time, "his"))

        # 2. 入院记录 (EMR) — 30-360 min 内
        t = self.timeline.schedule_after(ctx.admission_time, 0.5, 6.0)
        events.append(self._event(ctx, "emr_admission_record", t, "emr"))

        # 3. 首次检验申请 (LIS) — 概率从疾病画像读取，默认 95%
        lab_prob = ctx.disease_profile.order_lab_prob if ctx.disease_profile else 0.95
        if random.random() < lab_prob:
            t_order = self.timeline.schedule_after(ctx.admission_time, 2.0, 12.0)
            ev_lab = self._event(ctx, "order_lab", t_order, "lis", payload={"seq": 0})
            events.append(ev_lab)

            # 4. 检验结果 — 2-24h 后
            t_result = self.timeline.schedule_after(t_order, 2.0, 24.0)
            events.append(
                self._event(
                    ctx, "lab_result", t_result, "lis",
                    parent_id=ev_lab.event_id,
                    payload={"seq": 0},
                )
            )

        # 5. 影像申请 (RIS) — 概率从疾病画像读取，默认 40%
        img_prob = ctx.disease_profile.order_imaging_prob if ctx.disease_profile else 0.40
        if random.random() < img_prob:
            t_img = self.timeline.schedule_within(ctx.admission_time, ctx.discharge_time, 2.0)
            ev_img = self._event(ctx, "order_imaging", t_img, "ris")
            events.append(ev_img)

            # 6. 影像报告 — 2-48h 后
            t_img_rpt = self.timeline.schedule_after(t_img, 2.0, 48.0)
            t_img_rpt = min(t_img_rpt, ctx.discharge_time)
            events.append(
                self._event(
                    ctx, "imaging_report", t_img_rpt, "ris",
                    parent_id=ev_img.event_id,
                )
            )

        # 7. 每日医嘱 + 病程记录（住院期间每天）
        daily_times = self.timeline.schedule_daily(ctx.admission_time, ctx.discharge_time)
        for i, dt in enumerate(daily_times):
            events.append(self._event(ctx, "daily_orders", dt, "his", payload={"day": i + 1}))
            events.append(self._event(ctx, "daily_progress_note", dt, "emr", payload={"day": i + 1}))

        # 8. 手术 (EMR) — 使用疾病画像概率，默认 30%
        surgery_prob = ctx.disease_profile.surgery_prob if ctx.disease_profile else 0.30
        if random.random() < surgery_prob:
            t_sx = self.timeline.schedule_within(ctx.admission_time, ctx.discharge_time, 12.0)
            ev_sx = self._event(ctx, "surgery", t_sx, "emr")
            events.append(ev_sx)

            # 术后检验 — 1-6h 后
            t_post = self.timeline.schedule_after(t_sx, 1.0, 6.0)
            ev_post_lab = self._event(ctx, "order_lab", t_post, "lis", payload={"seq": 1, "reason": "post_op"})
            events.append(ev_post_lab)

            t_post_res = self.timeline.schedule_after(t_post, 2.0, 12.0)
            events.append(
                self._event(
                    ctx, "lab_result", t_post_res, "lis",
                    parent_id=ev_post_lab.event_id,
                    payload={"seq": 1, "reason": "post_op"},
                )
            )

        # 9. ICU 转入 — 使用疾病画像概率，默认 8%
        icu_prob = ctx.disease_profile.icu_prob if ctx.disease_profile else 0.08
        if random.random() < icu_prob:
            t_icu = self.timeline.schedule_within(ctx.admission_time, ctx.discharge_time, 1.0)
            ev_icu = self._event(ctx, "icu_admission", t_icu, "icu")
            events.append(ev_icu)

            # ICU 监护数据 — 在 ICU 期间每 1-4 小时一条
            icu_end = min(
                t_icu + timedelta(days=random.randint(1, 7)),
                ctx.discharge_time,
            )
            icu_t = t_icu
            idx = 0
            while icu_t < icu_end:
                events.append(
                    self._event(ctx, "monitoring_data", icu_t, "icu", payload={"seq": idx})
                )
                if random.random() < 0.05:
                    events.append(
                        self._event(ctx, "alarm", icu_t, "icu", payload={"seq": idx})
                    )
                if random.random() < 0.15:
                    events.append(
                        self._event(ctx, "blood_gas", icu_t, "icu", payload={"seq": idx})
                    )
                icu_t += timedelta(hours=random.uniform(1, 4))
                idx += 1

        # 10. ECG 检查 — 概率从疾病画像读取，默认 5%
        ecg_prob = ctx.disease_profile.ecg_prob if ctx.disease_profile else 0.05
        if random.random() < ecg_prob:
            t_ecg = self.timeline.schedule_within(ctx.admission_time, ctx.discharge_time, 1.0)
            ev_ecg = self._event(ctx, "ecg_exam", t_ecg, "ecg")
            events.append(ev_ecg)

            t_ecg_res = self.timeline.schedule_after(t_ecg, 0.5, 4.0)
            events.append(
                self._event(ctx, "ecg_analysis", t_ecg_res, "ecg", parent_id=ev_ecg.event_id)
            )

        # 11. 出院
        events.append(self._event(ctx, "discharge", ctx.discharge_time, "his"))

        # 12. 出院记录 (EMR) — 出院前 1-6h
        t_dc_rec = ctx.discharge_time - timedelta(hours=random.uniform(1, 6))
        if t_dc_rec > ctx.admission_time:
            events.append(self._event(ctx, "emr_discharge_record", t_dc_rec, "emr"))

        # 13. 病案归档 (BINGAN) — 出院后 1-48h
        t_bingan = self.timeline.schedule_after(ctx.discharge_time, 1.0, 48.0)
        events.append(self._event(ctx, "bingan_record", t_bingan, "bingan"))

        return events

    # ------------------------------------------------------------------
    # 门诊旅程
    # ------------------------------------------------------------------

    def _build_outpatient(self, ctx: EventContext) -> List[MedicalEvent]:
        events: List[MedicalEvent] = []
        assert ctx.visit_time is not None

        # 1. 门诊就诊
        events.append(self._event(ctx, "outpatient_visit", ctx.visit_time, "his"))

        # 2. 检验申请 — 门诊检验率 = 住院检验率 * 0.5，默认 30%
        lab_prob = ctx.disease_profile.order_lab_prob * 0.5 if ctx.disease_profile else 0.30
        if random.random() < lab_prob:
            t_order = self.timeline.schedule_after(ctx.visit_time, 0.5, 2.0)
            ev_lab = self._event(ctx, "order_lab", t_order, "lis", payload={"seq": 0})
            events.append(ev_lab)

            t_result = self.timeline.schedule_after(t_order, 1.0, 4.0)
            events.append(
                self._event(
                    ctx, "lab_result", t_result, "lis",
                    parent_id=ev_lab.event_id,
                    payload={"seq": 0},
                )
            )

        # 3. 影像申请 — 门诊影像率 = 住院影像率 * 0.5，默认 20%
        img_prob = ctx.disease_profile.order_imaging_prob * 0.5 if ctx.disease_profile else 0.20
        if random.random() < img_prob:
            t_img = self.timeline.schedule_after(ctx.visit_time, 0.5, 3.0)
            ev_img = self._event(ctx, "order_imaging", t_img, "ris")
            events.append(ev_img)

            t_img_rpt = self.timeline.schedule_after(t_img, 1.0, 6.0)
            events.append(
                self._event(
                    ctx, "imaging_report", t_img_rpt, "ris",
                    parent_id=ev_img.event_id,
                )
            )

        # 4. 开药 — 概率从疾病画像读取，默认 80%
        rx_prob = ctx.disease_profile.order_medication_prob if ctx.disease_profile else 0.80
        if random.random() < rx_prob:
            t_rx = self.timeline.schedule_after(ctx.visit_time, 0.3, 1.5)
            events.append(self._event(ctx, "order_medication", t_rx, "his"))

        # 5. 门诊病历 (EMR)
        t_emr = self.timeline.schedule_after(ctx.visit_time, 0.1, 0.5)
        events.append(self._event(ctx, "emr_outpatient_record", t_emr, "emr"))

        return events

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _event(
        ctx: EventContext,
        event_type: str,
        timestamp: datetime,
        source_system: str,
        parent_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> MedicalEvent:
        return MedicalEvent(
            event_type=event_type,
            timestamp=timestamp,
            source_system=source_system,
            patient_id=ctx.patient_id,
            visit_id=ctx.visit_id,
            parent_event_id=parent_id,
            payload=payload or {},
        )
