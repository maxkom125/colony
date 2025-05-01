# tests/systems/admirals/test_base_admiral.py
import pytest

# Objects to test
from src.systems.admirals.base_admiral import Admiral, DuplicateShipError, ShipNotFoundError

# Mock Ship class for testing
class MockShip:
    _next_id = 1
    def __init__(self, ship_id=None):
        if ship_id is not None:
            self.id = ship_id
            # Ensure _next_id doesn't reuse provided IDs if possible
            MockShip._next_id = max(MockShip._next_id, ship_id + 1) 
        else:
            self.id = MockShip._next_id
            MockShip._next_id += 1

@pytest.fixture
def admiral():
    """Provides a fresh Admiral instance for each test."""
    # Reset mock ship ID counter before each test
    MockShip._next_id = 1 
    return Admiral()

# --- Test Cases ---

def test_admiral_init(admiral):
    """Test that the Admiral initializes with an empty ships dictionary."""
    assert isinstance(admiral.ships, dict)
    assert len(admiral.ships) == 0
    assert admiral.get_ship_count() == 0

def test_add_ship_success(admiral):
    """Test adding a unique ship."""
    ship1 = MockShip()
    admiral.add_ship(ship1)
    assert admiral.get_ship_count() == 1
    assert ship1.id in admiral.ships
    assert admiral.ships[ship1.id] is ship1

def test_add_ship_multiple_unique(admiral):
    """Test adding multiple unique ships."""
    ship1 = MockShip()
    ship2 = MockShip()
    admiral.add_ship(ship1)
    admiral.add_ship(ship2)
    assert admiral.get_ship_count() == 2
    assert ship1.id in admiral.ships
    assert ship2.id in admiral.ships

def test_add_ship_duplicate_raises_error(admiral):
    """Test that adding a ship with a duplicate ID raises DuplicateShipError."""
    ship1 = MockShip(ship_id=10)
    ship2_duplicate_id = MockShip(ship_id=10) # Same ID
    
    admiral.add_ship(ship1) # Add first ship
    
    # Expect an error when adding the second ship with the same ID
    with pytest.raises(DuplicateShipError) as excinfo:
        admiral.add_ship(ship2_duplicate_id)
    
    assert f"Ship {ship1.id} already managed" in str(excinfo.value)
    # Ensure only the first ship is actually in the dictionary
    assert admiral.get_ship_count() == 1
    assert admiral.ships[ship1.id] is ship1

def test_remove_ship_success(admiral):
    """Test removing an existing ship."""
    ship1 = MockShip()
    admiral.add_ship(ship1)
    assert admiral.get_ship_count() == 1
    
    admiral.remove_ship(ship1.id)
    assert admiral.get_ship_count() == 0
    assert ship1.id not in admiral.ships

def test_remove_ship_not_found_raises_error(admiral):
    """Test that removing a non-existent ship ID raises ShipNotFoundError."""
    ship_id_to_remove = 999
    
    # Expect an error when trying to remove
    with pytest.raises(ShipNotFoundError) as excinfo:
        admiral.remove_ship(ship_id_to_remove)
        
    assert f"Ship {ship_id_to_remove} not found" in str(excinfo.value)
    assert admiral.get_ship_count() == 0 # Ensure no ships were added/removed inadvertently

def test_remove_correct_ship(admiral):
    """Test removing one ship when multiple exist."""
    ship1 = MockShip()
    ship2 = MockShip()
    admiral.add_ship(ship1)
    admiral.add_ship(ship2)
    assert admiral.get_ship_count() == 2
    
    admiral.remove_ship(ship1.id)
    assert admiral.get_ship_count() == 1
    assert ship1.id not in admiral.ships
    assert ship2.id in admiral.ships # Ensure ship2 is still there

def test_get_ship_count(admiral):
    """Test get_ship_count accurately reflects the number of ships."""
    assert admiral.get_ship_count() == 0
    ship1 = MockShip()
    admiral.add_ship(ship1)
    assert admiral.get_ship_count() == 1
    ship2 = MockShip()
    admiral.add_ship(ship2)
    assert admiral.get_ship_count() == 2
    admiral.remove_ship(ship1.id)
    assert admiral.get_ship_count() == 1
    admiral.remove_ship(ship2.id)
    assert admiral.get_ship_count() == 0 