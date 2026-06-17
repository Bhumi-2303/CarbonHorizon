"""
ReportService — report generation business logic.
No logic implemented yet; method stubs only.
"""
from sqlalchemy.orm import Session

import uuid
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate


class ReportService:

    @staticmethod
    def get_by_id(db: Session, report_id: uuid.UUID) -> Report | None:
        return db.query(Report).filter(Report.id == report_id).first()

    @staticmethod
    def list_by_org(
        db: Session, organization_id: str | uuid.UUID, skip: int = 0, limit: int = 100
    ) -> list[Report]:
        if isinstance(organization_id, str):
            organization_id = uuid.UUID(organization_id)
        return db.query(Report).filter(Report.user_id == organization_id).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, payload: ReportCreate, user_id: str | uuid.UUID) -> Report:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        db_obj = Report(
            user_id=user_id,
            title=payload.title if hasattr(payload, 'title') else "Default Title",
            content=payload.content if hasattr(payload, 'content') else "Default Content"
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(db: Session, report: Report, payload: ReportUpdate) -> Report:
        if hasattr(payload, 'title') and payload.title:
            report.title = payload.title
        if hasattr(payload, 'content') and payload.content:
            report.content = payload.content
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def delete(db: Session, report: Report) -> None:
        db.delete(report)
        db.commit()
