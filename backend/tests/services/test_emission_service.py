import pytest
from app.services.emission_service import EmissionService

def test_emission_service_stubs(db):
    with pytest.raises(NotImplementedError):
        EmissionService.get_by_id(db, 1)
        
    with pytest.raises(NotImplementedError):
        EmissionService.list_by_org(db, 1)
        
    with pytest.raises(NotImplementedError):
        EmissionService.create(db, None)
        
    with pytest.raises(NotImplementedError):
        EmissionService.update(db, None, None)
        
    with pytest.raises(NotImplementedError):
        EmissionService.delete(db, None)
