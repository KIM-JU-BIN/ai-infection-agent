from datetime import datetime

from app.database.db import SessionLocal
from app.repositories.contact_repository import ContactRepository
from app.models.access_log import AccessLog


def get_contacts(patient_id: str):
    """
    조사 대상 환자와 동선이 겹친 환자를 조회하고
    겹친 시간을 계산한다.
    """

    db = SessionLocal()

    try:

        repo = ContactRepository(db)

        target_logs = (
            db.query(AccessLog)
            .filter(AccessLog.patient_id == patient_id)
            .all()
        )

        contacts = repo.find_contacts(patient_id)

        result = []

        for contact in contacts:

            overlap_minutes = 0

            for target in target_logs:

                if target.location_id != contact.location_id:
                    continue

                target_exit = target.exit_time or datetime.now()
                contact_exit = contact.exit_time or datetime.now()

                start = max(target.enter_time, contact.enter_time)
                end = min(target_exit, contact_exit)

                if end > start:
                    overlap_minutes = int(
                        (end - start).total_seconds() / 60
                    )

            result.append({
                "patient_id": contact.patient_id,
                "location_id": contact.location_id,
                "enter_time": str(contact.enter_time),
                "exit_time": (
                    str(contact.exit_time)
                    if contact.exit_time else None
                ),
                "overlap_minutes": overlap_minutes
            })

        return {
            "success": True,
            "contacts": result
        }

    finally:
        db.close()