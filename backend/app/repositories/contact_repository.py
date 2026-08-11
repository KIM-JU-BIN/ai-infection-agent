from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.access_log import AccessLog


class ContactRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_contacts(self, patient_id: str):

        # 조사 대상 환자의 모든 출입기록
        target_logs = (
            self.db.query(AccessLog)
            .filter(
                AccessLog.patient_id == patient_id
            )
            .all()
        )

        contacts = []

        for log in target_logs:

            same_place = (
                self.db.query(AccessLog)
                .filter(
                    AccessLog.location_id == log.location_id,

                    AccessLog.patient_id != patient_id,

                    AccessLog.enter_time < (
                        log.exit_time or log.enter_time
                    ),

                    or_(
                        AccessLog.exit_time == None,
                        AccessLog.exit_time > log.enter_time
                    )
                )
                .all()
            )

            contacts.extend(same_place)

        return contacts