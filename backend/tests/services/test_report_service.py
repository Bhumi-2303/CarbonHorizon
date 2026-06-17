import pytest
from app.services.report_service import ReportService
from app.models.report import Report
from app.models.user import User

class MockReportCreate:
    title = "Annual Carbon Report"
    content = "You saved 10kg CO2e this year."

class MockReportUpdate:
    title = "Updated Title"
    content = "Updated content"

def test_report_generation(db):
    user = User(email="report@example.com", password_hash="hash", full_name="Report User")
    db.add(user)
    db.commit()
    
    payload = MockReportCreate()
    report = ReportService.create(db, payload=payload, user_id=user.id)
    
    assert report.id is not None
    assert report.title == "Annual Carbon Report"
    assert report.content == "You saved 10kg CO2e this year."
    
def test_invalid_report_id(db):
    import uuid
    invalid_id = uuid.uuid4()
    report = ReportService.get_by_id(db, invalid_id)
    assert report is None
