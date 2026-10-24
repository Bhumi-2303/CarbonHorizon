import pytest
from unittest.mock import MagicMock, patch

from app.db.seed_carbon_factors import seed_carbon_factors
from app.db.init_db import seed_habit_definitions, init_db
from seed_habits import seed_habit_definitions as standalone_seed_habits


def test_seed_carbon_factors_default_commits():
    db = MagicMock()
    # First test: no existing factors -> inserts all 14 factors and commits once
    db.query().filter().first.return_value = None
    seed_carbon_factors(db)
    assert db.add.call_count == 14
    assert db.commit.call_count == 1

    # Second test: factors already exist -> updates existing, adds 0, commits once
    db.reset_mock()
    existing_mock = MagicMock()
    db.query().filter().first.return_value = existing_mock
    seed_carbon_factors(db)
    assert db.add.call_count == 0
    assert db.commit.call_count == 1


def test_seed_carbon_factors_skips_commit_when_disabled():
    db = MagicMock()
    db.query().filter().first.return_value = None
    seed_carbon_factors(db, commit=False)
    assert db.add.call_count == 14
    assert db.commit.call_count == 0


def test_seed_habit_definitions_default_commits():
    db = MagicMock()
    db.query().filter().first.return_value = None
    seed_habit_definitions(db)
    assert db.add.call_count == 5
    assert db.commit.call_count == 1

    db.reset_mock()
    existing_mock = MagicMock()
    db.query().filter().first.return_value = existing_mock
    seed_habit_definitions(db)
    assert db.add.call_count == 0
    assert db.commit.call_count == 1


def test_seed_habit_definitions_skips_commit_when_disabled():
    db = MagicMock()
    db.query().filter().first.return_value = None
    seed_habit_definitions(db, commit=False)
    assert db.add.call_count == 5
    assert db.commit.call_count == 0


def test_init_db_success():
    db = MagicMock()
    with patch("app.db.init_db.seed_carbon_factors") as mock_scf, \
         patch("app.db.init_db.seed_habit_definitions") as mock_shd:
        init_db(db)
        mock_scf.assert_called_once_with(db, commit=False)
        mock_shd.assert_called_once_with(db, commit=False)
        db.commit.assert_called_once()
        db.rollback.assert_not_called()
        # Externally supplied session must NOT be closed by init_db
        db.close.assert_not_called()


def test_init_db_carbon_factors_failure_rolls_back():
    db = MagicMock()
    with patch(
        "app.db.init_db.seed_carbon_factors",
        side_effect=RuntimeError("Seeder failure in carbon factors"),
    ) as mock_scf, patch("app.db.init_db.seed_habit_definitions") as mock_shd:
        with pytest.raises(RuntimeError, match="Seeder failure in carbon factors"):
            init_db(db)

        mock_scf.assert_called_once_with(db, commit=False)
        mock_shd.assert_not_called()
        db.rollback.assert_called_once()
        db.commit.assert_not_called()
        db.close.assert_not_called()


def test_init_db_habit_definitions_failure_rolls_back():
    db = MagicMock()
    with patch("app.db.init_db.seed_carbon_factors") as mock_scf, \
         patch(
             "app.db.init_db.seed_habit_definitions",
             side_effect=ValueError("Seeder failure in habits"),
         ) as mock_shd:
        with pytest.raises(ValueError, match="Seeder failure in habits"):
            init_db(db)

        mock_scf.assert_called_once_with(db, commit=False)
        mock_shd.assert_called_once_with(db, commit=False)
        db.rollback.assert_called_once()
        db.commit.assert_not_called()
        db.close.assert_not_called()


def test_init_db_internal_session_closed_on_success():
    with patch("app.db.init_db.SessionLocal") as mock_session_cls, \
         patch("app.db.init_db.seed_carbon_factors") as mock_scf, \
         patch("app.db.init_db.seed_habit_definitions") as mock_shd:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        init_db()  # no db passed -> internally created session

        mock_scf.assert_called_once_with(mock_session, commit=False)
        mock_shd.assert_called_once_with(mock_session, commit=False)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()


def test_init_db_internal_session_closed_and_rolled_back_on_failure():
    with patch("app.db.init_db.SessionLocal") as mock_session_cls, \
         patch(
             "app.db.init_db.seed_carbon_factors",
             side_effect=RuntimeError("Seeding crashed"),
         ):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        with pytest.raises(RuntimeError, match="Seeding crashed"):
            init_db()

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()


def test_standalone_seed_habits_wrapper():
    # Calling wrapper with db
    db = MagicMock()
    with patch("seed_habits._seed_habit_definitions") as mock_shd:
        standalone_seed_habits(db, commit=True)
        mock_shd.assert_called_once_with(db, commit=True)

    # Calling wrapper without db (manages own session)
    with patch("seed_habits.SessionLocal") as mock_session_cls, \
         patch("seed_habits._seed_habit_definitions") as mock_shd:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        standalone_seed_habits()

        mock_shd.assert_called_once_with(mock_session, commit=True)
        mock_session.close.assert_called_once()
