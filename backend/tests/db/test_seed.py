from app.db.seed_carbon_factors import seed_carbon_factors
from unittest.mock import MagicMock

def test_seed_carbon_factors():
    db = MagicMock()
    # first existing check returns None
    db.query().filter().first.return_value = None
    seed_carbon_factors(db)
    assert db.add.call_count > 0
    assert db.commit.call_count == 1
    
    db.reset_mock()
    # existing check returns an object
    existing_mock = MagicMock()
    db.query().filter().first.return_value = existing_mock
    seed_carbon_factors(db)
    assert db.add.call_count == 0
    assert db.commit.call_count == 1

