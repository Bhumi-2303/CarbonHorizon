import pytest
import uuid
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
    user = User(id=uuid.uuid4(), email="report@example.com", password_hash="hash", full_name="Report User")
    db.add(user)
    db.commit()
    
    payload = MockReportCreate()
    report = ReportService.create(db, payload=payload, user_id=str(user.id))
    
    assert report.id is not None
    assert report.title == "Annual Carbon Report"
    assert report.content == "You saved 10kg CO2e this year."
    
    # Test get_by_id with valid ID
    fetched = ReportService.get_by_id(db, report.id)
    assert fetched is not None
    assert fetched.title == "Annual Carbon Report"

    # Test list_by_org
    listed = ReportService.list_by_org(db, str(user.id))
    assert len(listed) == 1
    assert listed[0].id == report.id

    # Test update
    update_payload = MockReportUpdate()
    updated = ReportService.update(db, report, update_payload)
    assert updated.title == "Updated Title"
    assert updated.content == "Updated content"

    # Test delete
    ReportService.delete(db, updated)
    assert ReportService.get_by_id(db, report.id) is None

def test_invalid_report_id(db):
    invalid_id = uuid.uuid4()
    report = ReportService.get_by_id(db, invalid_id)
    assert report is None
