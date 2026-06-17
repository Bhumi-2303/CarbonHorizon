import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.carbon_assessment import CarbonAssessment

def test_user_creation_integrity(db):
    user = User(
        email="test_integrity@example.com",
        password_hash="hashed_pass_123",
        full_name="Integrity User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.email == "test_integrity@example.com"

    # Test unique constraint on email
    duplicate_user = User(
        email="test_integrity@example.com",
        password_hash="different_hash",
        full_name="Duplicate User",
    )
    db.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_relationship_integrity_assessment_cascade(db):
    # Create user
    user = User(
        email="cascade@example.com",
        password_hash="xyz",
        full_name="Cascade User"
    )
    db.add(user)
    db.commit()
    
    # Create assessment for user
    assessment = CarbonAssessment(
        user_id=user.id,
        transport_emission=100.0,
        total_emission=100.0
    )
    db.add(assessment)
    db.commit()

    assert assessment.id is not None
    
    # Check relationship
    assert len(user.carbon_assessments) == 1
    assert user.carbon_assessments[0].id == assessment.id
    
    # Testing cascading deletes or integrity
    db.delete(user)
    db.commit()
    
    # Ensure assessment is also deleted or unlinked
    deleted_assessment = db.query(CarbonAssessment).filter_by(id=assessment.id).first()
    assert deleted_assessment is None
