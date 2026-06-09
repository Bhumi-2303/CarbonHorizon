"""
EmissionService — carbon emission tracking business logic.
No logic implemented yet; method stubs only.
"""
from sqlalchemy.orm import Session

from app.models.emission import Emission
from app.schemas.emission import EmissionCreate, EmissionUpdate


class EmissionService:

    @staticmethod
    def get_by_id(db: Session, emission_id: int) -> Emission | None:
        raise NotImplementedError

    @staticmethod
    def list_by_org(
        db: Session, organization_id: int, skip: int = 0, limit: int = 100
    ) -> list[Emission]:
        raise NotImplementedError

    @staticmethod
    def create(db: Session, payload: EmissionCreate) -> Emission:
        raise NotImplementedError

    @staticmethod
    def update(db: Session, emission: Emission, payload: EmissionUpdate) -> Emission:
        raise NotImplementedError

    @staticmethod
    def delete(db: Session, emission: Emission) -> None:
        raise NotImplementedError
