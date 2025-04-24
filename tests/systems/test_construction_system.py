import pytest
from pygame.math import Vector2

from src.systems.construction_system import attempt_construction
from src.entities.planet import Planet
from src import constants
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.ships.mining_ship import MiningShip

@pytest.fixture
def rich_planet(): # Renamed from भरपूर_ग्रह
    """Provides a planet with ample resources for building."""
    planet = Planet(Vector2(0, 0), radius=100, color=(0, 0, 255))
    planet.storage = {"Tritanium": 1000, "Credits": 1000, "Plasma": 500}
    return planet

@pytest.fixture
def poor_planet(): # Renamed from गरीब_ग्रह
    """Provides a planet with insufficient resources."""
    planet = Planet(Vector2(0, 0), radius=100, color=(255, 0, 0))
    # Set resources just below scanner cost
    planet.storage = {
        "Tritanium": constants.SCANNER_COST_TRITANIUM - 1,
        "Credits": constants.SCANNER_COST_CREDITS,
        "Plasma": 0
    }
    return planet


def test_construct_scanner_success(rich_planet):
    initial_tritanium = rich_planet.storage["Tritanium"]
    initial_credits = rich_planet.storage["Credits"]
    
    new_ship = attempt_construction(rich_planet, "scanner")
    
    assert isinstance(new_ship, ScannerShip)
    assert rich_planet.storage["Tritanium"] == initial_tritanium - constants.SCANNER_COST_TRITANIUM
    assert rich_planet.storage["Credits"] == initial_credits - constants.SCANNER_COST_CREDITS
    # Check spawn position roughly
    assert new_ship.position.distance_to(rich_planet.position) == pytest.approx(rich_planet.radius + 30)

def test_construct_miner_success(rich_planet):
    initial_tritanium = rich_planet.storage["Tritanium"]
    initial_credits = rich_planet.storage["Credits"]
    
    new_ship = attempt_construction(rich_planet, "miner")
    
    assert isinstance(new_ship, MiningShip)
    assert rich_planet.storage["Tritanium"] == initial_tritanium - constants.MINING_SHIP_COST_TRITANIUM
    assert rich_planet.storage["Credits"] == initial_credits - constants.MINING_SHIP_COST_CREDITS
    assert new_ship.position.distance_to(rich_planet.position) == pytest.approx(rich_planet.radius + 30)

def test_construct_fail_insufficient_resources(poor_planet):
    initial_storage = poor_planet.storage.copy()
    new_ship = attempt_construction(poor_planet, "scanner")
    assert new_ship is None
    assert poor_planet.storage == initial_storage # Storage unchanged

def test_construct_fail_unknown_type(rich_planet):
    initial_storage = rich_planet.storage.copy()
    new_ship = attempt_construction(rich_planet, "battleship")
    assert new_ship is None
    assert rich_planet.storage == initial_storage # Storage unchanged 