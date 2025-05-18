import pygame
from pygame.math import Vector2
from src.entities.planet import Planet
from src import constants
from src.enums import ResourceType
# Remove ship imports - no longer needed here
# from src.entities.ships.scanner_ship import ScannerShip
# from src.entities.ships.mining_ship import MiningShip
import pytest


@pytest.fixture
def basic_planet():
    """Provides a basic planet instance for testing."""
    return Planet(Vector2(0,0), radius=5, color=(0,0,0))


# Fixture to initialize pygame font module
@pytest.fixture(scope="module", autouse=True)
def pygame_font_init():
    pygame.font.init()
    yield
    pygame.font.quit() # Optional cleanup


def test_initial_storage_values(basic_planet):
    # Planet storage is initialized to zero for all resource types
    assert basic_planet.storage == {res_type: 0 for res_type in ResourceType.list()}

# --- Tests for add_resources --- 

def test_add_resources_positive(basic_planet):
    initial_tritanium = basic_planet.storage[ResourceType.TRITANIUM]
    initial_credits = basic_planet.storage[ResourceType.CREDITS]
    basic_planet.add_resources({ResourceType.TRITANIUM: 50, ResourceType.CREDITS: 10})
    assert basic_planet.storage[ResourceType.TRITANIUM] == initial_tritanium + 50
    assert basic_planet.storage[ResourceType.CREDITS] == initial_credits + 10

def test_add_resources_negative_ignored(basic_planet):
    initial_tritanium = basic_planet.storage[ResourceType.TRITANIUM]
    basic_planet.add_resources({ResourceType.TRITANIUM: -50})
    assert basic_planet.storage[ResourceType.TRITANIUM] == initial_tritanium # Should not change

def test_add_resources_unknown_ignored(basic_planet):
    initial_storage = basic_planet.storage.copy()
    basic_planet.add_resources({"Unobtanium": 100})
    assert basic_planet.storage == initial_storage # Should not change

# --- Tests for has_resources --- 

def test_has_resources_sufficient(basic_planet):
    basic_planet.add_resources({ResourceType.TRITANIUM: 100, ResourceType.CREDITS: 50})
    assert basic_planet.has_resources({ResourceType.TRITANIUM: 100})
    assert basic_planet.has_resources({ResourceType.CREDITS: 50})

def test_has_resources_insufficient(basic_planet):
    assert not basic_planet.has_resources({ResourceType.TRITANIUM: 100})
    basic_planet.add_resources({ResourceType.TRITANIUM: 100, ResourceType.CREDITS: 50})
    assert not basic_planet.has_resources({ResourceType.TRITANIUM: 150})
    assert not basic_planet.has_resources({ResourceType.CREDITS: 100})
    assert not basic_planet.has_resources({ResourceType.PLASMA: 100})
    assert not basic_planet.has_resources({ResourceType.TRITANIUM: 100, ResourceType.CREDITS: 250})

def test_has_resources_unknown_resource(basic_planet):
    # Should implicitly be False as storage.get defaults to 0
    assert not basic_planet.has_resources({"Unobtanium": 1})

def test_has_resources_empty_request(basic_planet):
    assert basic_planet.has_resources({}) # Should always be True
    assert basic_planet.has_resources({ResourceType.TRITANIUM: 0})

# --- Tests for remove_resources --- 

def test_remove_resources_success(basic_planet):
    # Add some resources first to test removal
    basic_planet.add_resources({ResourceType.TRITANIUM: 100, ResourceType.CREDITS: 50})
    initial_tritanium = basic_planet.storage[ResourceType.TRITANIUM]
    initial_credits = basic_planet.storage[ResourceType.CREDITS]
    costs = {ResourceType.TRITANIUM: 50, ResourceType.CREDITS: 20}
    
    result = basic_planet.remove_resources(costs)
    
    assert result is True
    assert basic_planet.storage[ResourceType.TRITANIUM] == initial_tritanium - costs[ResourceType.TRITANIUM]
    assert basic_planet.storage[ResourceType.CREDITS] == initial_credits - costs[ResourceType.CREDITS]

def test_remove_resources_fail_insufficient(basic_planet):
    initial_storage = basic_planet.storage.copy()
    costs = {ResourceType.TRITANIUM: 500}

    result = basic_planet.remove_resources(costs)

    assert result is False
    assert basic_planet.storage == initial_storage # Storage unchanged

def test_remove_resources_fail_one_of_multiple(basic_planet):
    initial_storage = basic_planet.storage.copy()
    costs = {ResourceType.TRITANIUM: 50, ResourceType.CREDITS: 500}

    result = basic_planet.remove_resources(costs)

    assert result is False
    assert basic_planet.storage == initial_storage # Storage unchanged

def test_remove_resources_empty_request(basic_planet):
    initial_storage = basic_planet.storage.copy()
    result = basic_planet.remove_resources({})
    assert result is True # Removing nothing is successful
    assert basic_planet.storage == initial_storage # Storage unchanged

def test_remove_resources_insufficient(basic_planet):
    # Starts with 0, trying to remove should fail
    initial_storage = basic_planet.storage.copy()
    costs = {ResourceType.TRITANIUM: 50} # Try to remove from 0
    result = basic_planet.remove_resources(costs)

    assert result is False
    assert basic_planet.storage == initial_storage # Storage should not change

def test_remove_resources_unknown_type(basic_planet):
    # Should implicitly be False as storage.get defaults to 0
    assert not basic_planet.has_resources({"Unobtanium": 1})

# --- Tests for draw (unchanged) --- 

def test_draw_does_not_error(monkeypatch, basic_planet):
    # Use the fixture
    # Create dummy surface and stub world_to_screen
    surface = pygame.Surface((100, 100))
    def fake_w2s(v): return Vector2(int(v.x), int(v.y))
    # Monkeypatch pygame.draw.circle to verify called
    called = []
    monkeypatch.setattr(pygame.draw, 'circle', lambda s, col, pos, r: called.append((col, pos, r)))
    basic_planet.draw(surface, fake_w2s, 2.0)
    # Should have drawn exactly one circle
    assert len(called) == 1
    col, pos, r = called[0]
    assert col == basic_planet.color
    assert r == int(basic_planet.radius * 2.0) 