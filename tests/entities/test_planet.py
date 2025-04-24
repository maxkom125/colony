import pygame
from pygame.math import Vector2
from src.entities.planet import Planet
from src import constants
# Remove ship imports - no longer needed here
# from src.entities.ships.scanner_ship import ScannerShip
# from src.entities.ships.mining_ship import MiningShip
import pytest


@pytest.fixture
def basic_planet():
    """Provides a basic planet instance for testing."""
    return Planet(Vector2(100, 100), radius=50, color=(1, 2, 3))


def test_initial_storage_values(basic_planet):
    # Planet storage is initialized to hardcoded values
    assert basic_planet.storage == {
        "Tritanium": 200,
        "Credits": 200,
        "Plasma": 50
    }

# --- Tests for add_resources --- 

def test_add_resources_positive(basic_planet):
    initial_tritanium = basic_planet.storage["Tritanium"]
    initial_credits = basic_planet.storage["Credits"]
    basic_planet.add_resources({"Tritanium": 50, "Credits": 10})
    assert basic_planet.storage["Tritanium"] == initial_tritanium + 50
    assert basic_planet.storage["Credits"] == initial_credits + 10

def test_add_resources_negative_ignored(basic_planet):
    initial_tritanium = basic_planet.storage["Tritanium"]
    basic_planet.add_resources({"Tritanium": -50})
    assert basic_planet.storage["Tritanium"] == initial_tritanium # Should not change

def test_add_resources_unknown_ignored(basic_planet):
    initial_storage = basic_planet.storage.copy()
    basic_planet.add_resources({"Unobtanium": 100})
    assert basic_planet.storage == initial_storage # Should not change

# --- Tests for has_resources --- 

def test_has_resources_sufficient_single(basic_planet):
    assert basic_planet.has_resources({"Tritanium": 150})

def test_has_resources_sufficient_multiple(basic_planet):
    assert basic_planet.has_resources({"Tritanium": 150, "Credits": 100})

def test_has_resources_insufficient_single(basic_planet):
    assert not basic_planet.has_resources({"Tritanium": 250})

def test_has_resources_insufficient_one_of_multiple(basic_planet):
    assert not basic_planet.has_resources({"Tritanium": 150, "Credits": 250})

def test_has_resources_unknown_resource(basic_planet):
    # Should implicitly be False as storage.get defaults to 0
    assert not basic_planet.has_resources({"Unobtanium": 1})

def test_has_resources_empty_request(basic_planet):
    assert basic_planet.has_resources({}) # Should always be True

# --- Tests for remove_resources --- 

def test_remove_resources_success(basic_planet):
    initial_tritanium = basic_planet.storage["Tritanium"]
    initial_credits = basic_planet.storage["Credits"]
    costs = {"Tritanium": 50, "Credits": 20}
    
    result = basic_planet.remove_resources(costs)
    
    assert result is True
    assert basic_planet.storage["Tritanium"] == initial_tritanium - 50
    assert basic_planet.storage["Credits"] == initial_credits - 20

def test_remove_resources_fail_insufficient(basic_planet):
    initial_storage = basic_planet.storage.copy()
    costs = {"Tritanium": 500}

    result = basic_planet.remove_resources(costs)

    assert result is False
    assert basic_planet.storage == initial_storage # Storage unchanged

def test_remove_resources_fail_one_of_multiple(basic_planet):
    initial_storage = basic_planet.storage.copy()
    costs = {"Tritanium": 50, "Credits": 500}

    result = basic_planet.remove_resources(costs)

    assert result is False
    assert basic_planet.storage == initial_storage # Storage unchanged

def test_remove_resources_empty_request(basic_planet):
    initial_storage = basic_planet.storage.copy()
    result = basic_planet.remove_resources({})
    assert result is True # Removing nothing is successful
    assert basic_planet.storage == initial_storage # Storage unchanged

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