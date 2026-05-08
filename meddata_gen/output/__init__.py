"""输出格式支持：PostgreSQL、CSV、FHIR R4。"""
from __future__ import annotations

from meddata_gen.output.base import OutputWriter
from meddata_gen.output.postgres import PostgresWriter
from meddata_gen.output.csv import CSVWriter
from meddata_gen.output.fhir import FHIRBundleWriter

__all__ = ["OutputWriter", "PostgresWriter", "CSVWriter", "FHIRBundleWriter"]
