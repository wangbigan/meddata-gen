"""FHIRBundleWriter: 将关系型数据映射为 FHIR R4 Bundle JSON。

当前支持的核心资源映射:
- his_db.patients          -> Patient
- his_db.inpatient_visits  -> Encounter ( inpatient )
- his_db.outpatient_visits -> Encounter ( outpatient )
- lis_db.*_results         -> Observation
- ris_db.*_reports         -> DiagnosticReport
- his_db.orders (药品)      -> MedicationRequest
- emr_db.surgery_records   -> Procedure
- emr_db.admission_records -> ClinicalImpression (简化)

输出格式:
    每个患者一个 Bundle 文件: ``{output_dir}/{patient_id}.json``
"""
from __future__ import annotations

import json
import os
import uuid
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from meddata_gen.output.base import OutputWriter


# ------------------------------------------------------------------
# FHIR Resource builders
# ------------------------------------------------------------------

FHIR_DATE_FORMAT = "%Y-%m-%d"
FHIR_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S+08:00"


def _format_date(val) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime(FHIR_DATE_FORMAT)
    if isinstance(val, date):
        return val.strftime(FHIR_DATE_FORMAT)
    return str(val)


def _format_datetime(val) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime(FHIR_DATETIME_FORMAT)
    if isinstance(val, date):
        return val.strftime(FHIR_DATE_FORMAT)
    return str(val)


def _gender(val) -> str:
    if val in ("M", "男"):
        return "male"
    if val in ("F", "女"):
        return "female"
    return "unknown"


def _build_patient(resource_id: str, columns: List[str], row: tuple) -> dict:
    d = dict(zip(columns, row))
    name = d.get("name") or d.get("patient_name") or "Unknown"
    gender = _gender(d.get("gender"))
    birth_date = _format_date(d.get("birthday") or d.get("birth_date"))
    patient = {
        "resourceType": "Patient",
        "id": resource_id,
        "identifier": [{"system": "http://hospital.example/patient-id", "value": str(d.get("patient_id", resource_id))}],
        "name": [{"text": name}],
        "gender": gender,
    }
    if birth_date:
        patient["birthDate"] = birth_date
    phone = d.get("phone") or d.get("contact_phone")
    if phone:
        patient["telecom"] = [{"system": "phone", "value": str(phone)}]
    return patient


def _build_encounter(resource_id: str, columns: List[str], row: tuple, encounter_type: str = "inpatient") -> dict:
    d = dict(zip(columns, row))
    enc = {
        "resourceType": "Encounter",
        "id": resource_id,
        "identifier": [{"system": "http://hospital.example/visit-id", "value": str(d.get("visit_id", resource_id))}],
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP" if encounter_type == "inpatient" else "AMB",
        },
        "subject": {"reference": f"Patient/{d.get('patient_id')}"},
    }
    start = _format_datetime(d.get("admission_time") or d.get("visit_time"))
    end = _format_datetime(d.get("discharge_time"))
    period = {}
    if start:
        period["start"] = start
    if end:
        period["end"] = end
    if period:
        enc["period"] = period
    dept = d.get("admission_dept_id") or d.get("dept_id") or d.get("department_id")
    if dept:
        enc["serviceType"] = {"text": str(dept)}
    diag = d.get("admission_diagnosis") or d.get("diagnosis") or d.get("discharge_diagnosis") or d.get("primary_diagnosis")
    if diag:
        enc["reasonCode"] = [{"text": str(diag)}]
    return enc


def _build_observation(resource_id: str, columns: List[str], row: tuple) -> dict:
    d = dict(zip(columns, row))
    obs = {
        "resourceType": "Observation",
        "id": resource_id,
        "status": "final",
        "code": {"text": str(d.get("test_item", "Unknown"))},
        "subject": {"reference": f"Patient/{d.get('patient_id')}"},
    }
    order_id = d.get("order_id")
    if order_id:
        obs["basedOn"] = [{"reference": f"ServiceRequest/{order_id}"}]
    val = d.get("result_value")
    unit = d.get("unit")
    if val is not None:
        try:
            num_val = float(val)
            obs["valueQuantity"] = {"value": num_val, "unit": str(unit) if unit else None}
        except (ValueError, TypeError):
            obs["valueString"] = str(val)
    ref = d.get("reference_range")
    if ref:
        obs["referenceRange"] = [{"text": str(ref)}]
    flag = d.get("abnormal_flag")
    if flag and flag != "N":
        obs["interpretation"] = [{"coding": [{"code": flag, "display": "Abnormal"}]}]
    issued = _format_datetime(d.get("result_time"))
    if issued:
        obs["issued"] = issued
    return obs


def _build_diagnostic_report(resource_id: str, columns: List[str], row: tuple, modality: str = "unknown") -> dict:
    d = dict(zip(columns, row))
    rep = {
        "resourceType": "DiagnosticReport",
        "id": resource_id,
        "status": "final",
        "code": {"text": str(d.get("report_title")) if d.get("report_title") else modality},
        "subject": {"reference": f"Patient/{d.get('patient_id')}"},
    }
    issued = _format_datetime(d.get("report_time") or d.get("exam_time"))
    if issued:
        rep["issued"] = issued
    result_text = d.get("finding") or d.get("impression") or d.get("report_content")
    if result_text:
        rep["conclusion"] = str(result_text)
    return rep


def _build_medication_request(resource_id: str, columns: List[str], row: tuple) -> dict:
    d = dict(zip(columns, row))
    med = {
        "resourceType": "MedicationRequest",
        "id": resource_id,
        "status": "completed",
        "intent": "order",
        "subject": {"reference": f"Patient/{d.get('patient_id')}"},
        "encounter": {"reference": f"Encounter/{d.get('visit_id')}"},
    }
    item_name = d.get("item_name") or d.get("order_name") or "Unnamed Medication"
    med["medicationCodeableConcept"] = {"text": str(item_name)}
    authored = _format_datetime(d.get("start_time") or d.get("order_time"))
    if authored:
        med["authoredOn"] = authored
    return med


def _build_procedure(resource_id: str, columns: List[str], row: tuple) -> dict:
    d = dict(zip(columns, row))
    proc = {
        "resourceType": "Procedure",
        "id": resource_id,
        "status": "completed",
        "subject": {"reference": f"Patient/{d.get('patient_id')}"},
        "encounter": {"reference": f"Encounter/{d.get('visit_id')}"},
    }
    name = d.get("surgery_name") or d.get("procedure_name") or d.get("tube_type") or "Procedure"
    proc["code"] = {"text": str(name)}
    start = _format_datetime(d.get("surgery_date") or d.get("start_time") or d.get("intubation_time"))
    end = _format_datetime(d.get("end_time") or d.get("extubation_time"))
    if start or end:
        proc["performedPeriod"] = {}
        if start:
            proc["performedPeriod"]["start"] = start
        if end:
            proc["performedPeriod"]["end"] = end
    return proc


def _build_condition(resource_id: str, columns: List[str], row: tuple) -> dict:
    d = dict(zip(columns, row))
    cond = {
        "resourceType": "Condition",
        "id": resource_id,
        "subject": {"reference": f"Patient/{d.get('patient_id')}"},
        "encounter": {"reference": f"Encounter/{d.get('visit_id')}"},
    }
    name = d.get("diagnosis_name") or d.get("discharge_diagnosis") or "Condition"
    cond["code"] = {"text": str(name)}
    icd = d.get("diagnosis_icd")
    if icd:
        cond["code"]["coding"] = [{"system": "http://hl7.org/fhir/sid/icd-10", "code": str(icd)}]
    is_principal = d.get("is_principal") or d.get("is_primary")
    if is_principal == "Y" or is_principal == "1":
        cond["category"] = [{"coding": [{"code": "encounter-diagnosis", "display": "Encounter Diagnosis"}]}]
    return cond


def _build_icu_observation(resource_id: str, columns: List[str], row: tuple) -> dict:
    """ICU 监护数据映射为 Observation（生命体征）。"""
    d = dict(zip(columns, row))
    obs = {
        "resourceType": "Observation",
        "id": resource_id,
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
        "subject": {"reference": f"Patient/{d.get('patient_id')}"},
    }
    # 取第一个有值的生理指标作为 code
    for metric, code_text in [
        ("heart_rate", "Heart Rate"),
        ("blood_pressure_systolic", "Systolic BP"),
        ("spo2", "SpO2"),
        ("temperature", "Body Temperature"),
        ("respiration_rate", "Respiratory Rate"),
    ]:
        if d.get(metric) is not None:
            obs["code"] = {"text": code_text}
            obs["valueQuantity"] = {"value": float(d[metric])}
            if metric == "heart_rate":
                obs["valueQuantity"]["unit"] = "beats/min"
            elif metric == "blood_pressure_systolic":
                obs["valueQuantity"]["unit"] = "mmHg"
            elif metric == "spo2":
                obs["valueQuantity"]["unit"] = "%"
            elif metric == "temperature":
                obs["valueQuantity"]["unit"] = "C"
            elif metric == "respiration_rate":
                obs["valueQuantity"]["unit"] = "breaths/min"
            break
    else:
        obs["code"] = {"text": "ICU Monitoring"}
    issued = _format_datetime(d.get("monitor_time") or d.get("sample_time") or d.get("record_time"))
    if issued:
        obs["effectiveDateTime"] = issued
    return obs


# ------------------------------------------------------------------
# 表 -> 资源映射路由
# ------------------------------------------------------------------

_RESOURCE_ROUTERS = {
    "patients": ("Patient", _build_patient),
    "inpatient_visits": ("Encounter", lambda rid, cols, row: _build_encounter(rid, cols, row, "inpatient")),
    "outpatient_visits": ("Encounter", lambda rid, cols, row: _build_encounter(rid, cols, row, "outpatient")),
    "routine_results": ("Observation", _build_observation),
    "biochem_results": ("Observation", _build_observation),
    "blood_results": ("Observation", _build_observation),
    "xray_reports": ("DiagnosticReport", lambda rid, cols, row: _build_diagnostic_report(rid, cols, row, "X-Ray")),
    "ct_reports": ("DiagnosticReport", lambda rid, cols, row: _build_diagnostic_report(rid, cols, row, "CT")),
    "mri_reports": ("DiagnosticReport", lambda rid, cols, row: _build_diagnostic_report(rid, cols, row, "MRI")),
    "ultrasound_reports": ("DiagnosticReport", lambda rid, cols, row: _build_diagnostic_report(rid, cols, row, "Ultrasound")),
    "orders": ("MedicationRequest", _build_medication_request),
    "surgery_records": ("Procedure", _build_procedure),
    "lab_report_master": ("DiagnosticReport", lambda rid, cols, row: _build_diagnostic_report(rid, cols, row, "Laboratory")),
    "critical_values": ("Observation", _build_observation),
    "ecg_exams": ("DiagnosticReport", lambda rid, cols, row: _build_diagnostic_report(rid, cols, row, "ECG")),
    "ecg_analyses": ("Observation", _build_observation),
    "holter_records": ("DiagnosticReport", lambda rid, cols, row: _build_diagnostic_report(rid, cols, row, "Holter")),
    "stress_test_records": ("DiagnosticReport", lambda rid, cols, row: _build_diagnostic_report(rid, cols, row, "Stress Test")),
    "monitoring_data": ("Observation", _build_icu_observation),
    "blood_gas": ("Observation", _build_icu_observation),
    "intubation_records": ("Procedure", _build_procedure),
    "emr_diagnoses": ("Condition", _build_condition),
    "diagnoses": ("Condition", _build_condition),
}


# ------------------------------------------------------------------
# FHIRBundleWriter
# ------------------------------------------------------------------

class FHIRBundleWriter(OutputWriter):
    """将关系型数据映射为 FHIR R4 Bundle JSON，每患者一个文件。"""

    def __init__(self, output_dir: str = "output/fhir") -> None:
        self.output_dir = output_dir
        # buffers: (system, table) -> (columns, rows)
        self._buffers: Dict[Tuple[str, str], Tuple[List[str], List[tuple]]] = {}

    def write_rows(
        self,
        system: str,
        table: str,
        columns: List[str],
        rows: List[tuple],
    ) -> None:
        key = (system, table)
        if key not in self._buffers:
            self._buffers[key] = (columns, list(rows))
        else:
            existing_cols, existing_rows = self._buffers[key]
            if existing_cols != columns:
                raise ValueError(
                    f"列名不一致 for {system}.{table}: "
                    f"已有 {existing_cols}, 新传入 {columns}"
                )
            existing_rows.extend(rows)

    def finalize(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)

        # 按 patient_id 分组收集资源
        patient_resources: Dict[str, List[dict]] = defaultdict(list)
        # 记录已生成的 resource id，避免重复
        seen_ids: set = set()

        for (system, table), (columns, rows) in self._buffers.items():
            router = _RESOURCE_ROUTERS.get(table)
            if router is None:
                continue
            resource_type, builder = router

            for row in rows:
                d = dict(zip(columns, row))
                patient_id = d.get("patient_id")
                if not patient_id:
                    continue

                # 生成唯一 resource id
                if resource_type == "Patient":
                    base_id = patient_id
                else:
                    base_id = (
                        d.get("result_id")
                        or d.get("visit_id")
                        or d.get("order_id")
                        or d.get("document_id")
                        or d.get("record_id")
                        or d.get("note_id")
                        or d.get("fee_id")
                    )
                if base_id:
                    resource_id = f"{resource_type}-{base_id}"
                else:
                    resource_id = f"{resource_type}-{uuid.uuid4().hex[:8]}"

                if resource_id in seen_ids:
                    resource_id = f"{resource_id}-{uuid.uuid4().hex[:4]}"
                seen_ids.add(resource_id)

                resource = builder(resource_id, columns, row)
                patient_resources[str(patient_id)].append(resource)

        # 每个患者输出一个 Bundle
        total_bundles = 0
        for patient_id, resources in patient_resources.items():
            if not resources:
                continue
            bundle = {
                "resourceType": "Bundle",
                "id": f"bundle-{patient_id}",
                "meta": {"versionId": "1"},
                "type": "collection",
                "entry": [{"resource": r} for r in resources],
            }
            file_path = os.path.join(self.output_dir, f"{patient_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, indent=2)
            total_bundles += 1

        print(f"  [FHIRBundleWriter] {total_bundles} patient bundles written to {self.output_dir}")
        self._buffers.clear()
