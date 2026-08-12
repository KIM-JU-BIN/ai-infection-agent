"""
ORM 모델 등록
Alembic autogenerate가 모든 모델을 인식하게 한다.
"""

from app.db.models.access_log import AccessLog
from app.db.models.emr_record import EmrRecord
from app.db.models.investigation_result import InvestigationResult
from app.db.models.location import Location
from app.db.models.patient import Patient
from app.db.models.sop_document import SopDocument


__all__ = [
    "AccessLog",
    "EmrRecord",
    "InvestigationResult",
    "Location",
    "Patient",
    "SopDocument",
]
