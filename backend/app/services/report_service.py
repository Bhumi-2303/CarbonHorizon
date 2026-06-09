"""
ReportService — report generation business logic.
No logic implemented yet; method stubs only.
"""
from sqlalchemy.orm import Session

from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate


class ReportService:

    @staticmethod
    def get_by_id(db: Session, report_id: int) -> Report | None:
        raise NotImplementedError

    @staticmethod
    def list_by_org(
        db: Session, organization_id: int, skip: int = 0, limit: int = 100
    ) -> list[Report]:
        raise NotImplementedError

    @staticmethod
    def create(db: Session, payload: ReportCreate) -> Report:
        raise NotImplementedError

    @staticmethod
    def update(db: Session, report: Report, payload: ReportUpdate) -> Report:
        raise NotImplementedError

    @staticmethod
    def delete(db: Session, report: Report) -> None:
        raise NotImplementedError
