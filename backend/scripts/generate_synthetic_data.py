"""
가상 병원 데이터 생성 스크립트

생성 데이터:
- 환자 50명
- 병원 위치 10곳
- 병상 배정표
- RFID 출입 로그
- 확진자 중심 접촉 시나리오 4건

실행:
    python scripts/generate_synthetic_data.py
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker
from sqlalchemy import delete

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.logging import get_logger
from app.db.models.access_log import AccessLog
from app.db.models.bed_assignment import BedAssignment
from app.db.models.location import Location
from app.db.models.patient import Patient
from app.db.session import AsyncSessionLocal


logger = get_logger(__name__)


fake = Faker("ko_KR")

KST = timezone(timedelta(hours=9))

PATIENT_COUNT = 50
LOCATION_COUNT = 10

INDEX_PATIENT_IDENTIFIER = "P-0001"
INDEX_PATIENT_NAME = "김확진"

BASE_DATE = datetime(2026, 8, 1, 9, 0, tzinfo=KST)


DIAGNOSES = [
    "COVID-19",
    "폐렴",
    "인플루엔자",
    "요로감염",
    "장염",
    "고혈압",
    "당뇨",
    "천식",
    "수술 후 회복",
    "발열 원인 미상",
]


def random_sex() -> str:
    """
    성별 생성
    """

    return random.choice(["M", "F"])


def random_age() -> int:
    """
    나이 생성
    """

    return random.randint(18, 90)


def build_locations() -> list[Location]:
    """
    병원 위치 생성
    """

    location_specs = [
        ("WARD-3F-301", "301호 병실", "WARD_ROOM", "3F", 10.0, 10.0),
        ("WARD-3F-302", "302호 병실", "WARD_ROOM", "3F", 20.0, 10.0),
        ("WARD-3F-303", "303호 병실", "WARD_ROOM", "3F", 30.0, 10.0),
        ("WARD-3F-304", "304호 병실", "WARD_ROOM", "3F", 40.0, 10.0),
        ("WARD-3F-NS", "3층 간호스테이션", "NURSE_STATION", "3F", 25.0, 20.0),
        ("WARD-3F-TX", "3층 처치실", "TREATMENT_ROOM", "3F", 25.0, 30.0),
        ("WARD-3F-REST", "3층 휴게실", "LOUNGE", "3F", 45.0, 25.0),
        ("WARD-3F-ELEV", "3층 엘리베이터", "ELEVATOR", "3F", 5.0, 25.0),
        ("WARD-3F-HALL-A", "3층 복도 A", "HALLWAY", "3F", 15.0, 20.0),
        ("WARD-3F-HALL-B", "3층 복도 B", "HALLWAY", "3F", 35.0, 20.0),
    ]

    return [
        Location(
            location_code=code,
            name=name,
            location_type=location_type,
            floor=floor,
            building="본관",
            description=f"{name} 가상 위치",
            x_coord=x_coord,
            y_coord=y_coord,
        )
        for code, name, location_type, floor, x_coord, y_coord in location_specs
    ]


def build_patients() -> list[Patient]:
    """
    환자 50명 생성
    """

    patients: list[Patient] = []

    patients.append(
        Patient(
            patient_identifier=INDEX_PATIENT_IDENTIFIER,
            name=INDEX_PATIENT_NAME,
            age=42,
            sex="M",
            phone_number="010-0000-0001",
            address="서울특별시",
            current_diagnosis="COVID-19",
        )
    )

    for number in range(2, PATIENT_COUNT + 1):
        patients.append(
            Patient(
                patient_identifier=f"P-{number:04d}",
                name=fake.name(),
                age=random_age(),
                sex=random_sex(),
                phone_number=fake.phone_number(),
                address=fake.address(),
                current_diagnosis=random.choice(DIAGNOSES),
            )
        )

    return patients


def build_bed_assignments(
    *,
    patients: list[Patient],
    locations: list[Location],
) -> list[BedAssignment]:
    """
    병상 배정 데이터 생성
    """

    room_301 = find_location(locations, "WARD-3F-301")
    room_302 = find_location(locations, "WARD-3F-302")
    room_303 = find_location(locations, "WARD-3F-303")
    room_304 = find_location(locations, "WARD-3F-304")

    rooms = [room_301, room_302, room_303, room_304]

    assignments: list[BedAssignment] = []

    index_patient = patients[0]

    assignments.append(
        BedAssignment(
            patient_id=index_patient.id,
            location_id=room_301.id,
            admitted_at=BASE_DATE - timedelta(days=2),
            discharged_at=BASE_DATE + timedelta(days=3),
        )
    )

    contact_same_room_patients = [patients[1], patients[2]]

    for patient in contact_same_room_patients:
        assignments.append(
            BedAssignment(
                patient_id=patient.id,
                location_id=room_301.id,
                admitted_at=BASE_DATE - timedelta(days=1, hours=2),
                discharged_at=BASE_DATE + timedelta(days=1),
            )
        )

    for patient in patients[3:]:
        room = random.choice(rooms)
        admitted_at = BASE_DATE - timedelta(
            days=random.randint(0, 3),
            hours=random.randint(0, 12),
        )
        discharged_at = admitted_at + timedelta(days=random.randint(1, 5))

        assignments.append(
            BedAssignment(
                patient_id=patient.id,
                location_id=room.id,
                admitted_at=admitted_at,
                discharged_at=discharged_at,
            )
        )

    return assignments


def build_access_logs(
    *,
    patients: list[Patient],
    locations: list[Location],
) -> list[AccessLog]:
    """
    RFID 출입 로그 생성
    의도적 접촉 시나리오를 포함한다
    """

    logs: list[AccessLog] = []

    index_patient = patients[0]
    treatment_room = find_location(locations, "WARD-3F-TX")
    nurse_station = find_location(locations, "WARD-3F-NS")
    lounge = find_location(locations, "WARD-3F-REST")
    hallway_a = find_location(locations, "WARD-3F-HALL-A")
    elevator = find_location(locations, "WARD-3F-ELEV")

    scenario_time_1 = BASE_DATE + timedelta(hours=2)
    scenario_time_2 = BASE_DATE + timedelta(hours=5)
    scenario_time_3 = BASE_DATE + timedelta(hours=8)
    scenario_time_4 = BASE_DATE + timedelta(days=1, hours=1)

    logs.extend(
        [
            make_access_log(index_patient, treatment_room, scenario_time_1, "IN"),
            make_access_log(index_patient, treatment_room, scenario_time_1 + timedelta(minutes=20), "OUT"),
            make_access_log(patients[3], treatment_room, scenario_time_1 + timedelta(minutes=5), "IN"),
            make_access_log(patients[3], treatment_room, scenario_time_1 + timedelta(minutes=25), "OUT"),
            make_access_log(index_patient, nurse_station, scenario_time_2, "IN"),
            make_access_log(index_patient, nurse_station, scenario_time_2 + timedelta(minutes=10), "OUT"),
            make_access_log(patients[4], nurse_station, scenario_time_2 + timedelta(minutes=3), "IN"),
            make_access_log(patients[4], nurse_station, scenario_time_2 + timedelta(minutes=12), "OUT"),
            make_access_log(index_patient, lounge, scenario_time_3, "IN"),
            make_access_log(index_patient, lounge, scenario_time_3 + timedelta(minutes=30), "OUT"),
            make_access_log(patients[5], lounge, scenario_time_3 + timedelta(minutes=10), "IN"),
            make_access_log(patients[5], lounge, scenario_time_3 + timedelta(minutes=40), "OUT"),
            make_access_log(index_patient, elevator, scenario_time_4, "IN"),
            make_access_log(index_patient, elevator, scenario_time_4 + timedelta(minutes=2), "OUT"),
            make_access_log(patients[6], elevator, scenario_time_4 + timedelta(minutes=1), "IN"),
            make_access_log(patients[6], elevator, scenario_time_4 + timedelta(minutes=4), "OUT"),
        ]
    )

    movable_locations = [
        treatment_room,
        nurse_station,
        lounge,
        hallway_a,
        elevator,
    ]

    for patient in patients[7:]:
        visit_count = random.randint(2, 5)

        for _ in range(visit_count):
            location = random.choice(movable_locations)
            occurred_at = BASE_DATE + timedelta(
                days=random.randint(0, 2),
                hours=random.randint(0, 12),
                minutes=random.randint(0, 59),
            )

            logs.append(make_access_log(patient, location, occurred_at, "IN"))
            logs.append(
                make_access_log(
                    patient,
                    location,
                    occurred_at + timedelta(minutes=random.randint(5, 40)),
                    "OUT",
                )
            )

    return logs


def make_access_log(
    patient: Patient,
    location: Location,
    occurred_at: datetime,
    direction: str,
) -> AccessLog:
    """
    출입 로그 1건 생성
    """

    return AccessLog(
        patient_id=patient.id,
        location_id=location.id,
        occurred_at=occurred_at,
        event_type="RFID_SWIPE",
        direction=direction,
        source_system="SYNTHETIC_RFID",
        raw_payload=None,
    )


def find_location(
    locations: list[Location],
    location_code: str,
) -> Location:
    """
    위치 코드로 Location 찾기
    """

    for location in locations:
        if location.location_code == location_code:
            return location

    raise ValueError(f"위치를 찾을 수 없습니다: {location_code}")


async def clear_existing_data() -> None:
    """
    기존 합성 데이터 삭제
    """

    async with AsyncSessionLocal() as session:
        await session.execute(delete(AccessLog))
        await session.execute(delete(BedAssignment))
        await session.execute(delete(Location))
        await session.execute(delete(Patient))
        await session.commit()

    logger.info("기존 합성 데이터 삭제 완료.")


async def insert_patients_and_locations() -> tuple[list[Patient], list[Location]]:
    """
    환자와 위치 INSERT
    """

    patients = build_patients()
    locations = build_locations()

    async with AsyncSessionLocal() as session:
        session.add_all(patients)
        session.add_all(locations)
        await session.commit()

        for patient in patients:
            await session.refresh(patient)

        for location in locations:
            await session.refresh(location)

    logger.info(f"환자 {len(patients)}명 생성 완료.")
    logger.info(f"위치 {len(locations)}곳 생성 완료.")

    return patients, locations


async def insert_assignments_and_logs(
    *,
    patients: list[Patient],
    locations: list[Location],
) -> None:
    """
    병상 배정과 출입 로그 INSERT
    """

    assignments = build_bed_assignments(
        patients=patients,
        locations=locations,
    )
    access_logs = build_access_logs(
        patients=patients,
        locations=locations,
    )

    async with AsyncSessionLocal() as session:
        session.add_all(assignments)
        session.add_all(access_logs)
        await session.commit()

    logger.info(f"병상 배정 {len(assignments)}건 생성 완료.")
    logger.info(f"출입 로그 {len(access_logs)}건 생성 완료.")


async def main() -> None:
    """
    합성 데이터 생성 실행
    """

    random.seed(42)
    Faker.seed(42)

    await clear_existing_data()

    patients, locations = await insert_patients_and_locations()

    await insert_assignments_and_logs(
        patients=patients,
        locations=locations,
    )

    logger.info("합성 데이터 생성 완료.")
    logger.info("기준 확진자: patient_id=1, patient_identifier=P-0001")


if __name__ == "__main__":
    asyncio.run(main())
