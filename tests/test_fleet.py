# tests/test_fleet.py
import pytest
from pygame.math import Vector2

from src.fleet import Fleet
from src.entities.ships.base_ship import Ship
from src.entities.ships.mining_ship import MiningShip
from src.entities.ships.scanner_ship import ScannerShip
from src.enums import ShipState
from src.entities.planet import Planet

@pytest.fixture
def home_planet_fixture():
    return Planet(Vector2(0,0))

@pytest.fixture
def fleet_with_ships(home_planet_fixture):
    fleet = Fleet()
    scanner = ScannerShip(Vector2(10,10), home_planet=home_planet_fixture)
    miner1 = MiningShip(Vector2(20,20), home_planet=home_planet_fixture)
    miner2 = MiningShip(Vector2(30,30), home_planet=home_planet_fixture) # Another miner
    miner_idle = MiningShip(Vector2(40,40), home_planet=home_planet_fixture) # Explicitly idle
    miner_idle.state = ShipState.IDLE
    miner2.state = ShipState.MINING # Make miner2 not idle

    initial_ships = [scanner, miner1, miner2, miner_idle]
    for ship in initial_ships:
        fleet.add_ship(ship)
        
    return fleet, initial_ships

def test_fleet_init():
    fleet = Fleet()
    assert fleet.get_all_ships() == []

def test_add_ship(fleet_with_ships, home_planet_fixture):
    fleet, initial_ships = fleet_with_ships
    assert len(fleet.get_all_ships()) == len(initial_ships)
    new_ship = ScannerShip(Vector2(10,10), home_planet=home_planet_fixture)
    fleet.add_ship(new_ship)
    assert len(fleet.get_all_ships()) == len(initial_ships) + 1
    assert new_ship in fleet.get_all_ships()

def test_add_ship_duplicate(fleet_with_ships):
    fleet, initial_ships = fleet_with_ships
    ship_to_add_again = initial_ships[0]
    initial_count = len(fleet.get_all_ships())
    fleet.add_ship(ship_to_add_again) # Try adding again
    assert len(fleet.get_all_ships()) == initial_count # Count shouldn't change

def test_remove_ship(fleet_with_ships):
    fleet, initial_ships = fleet_with_ships
    ship_to_remove = initial_ships[1].id # Remove miner1
    initial_count = len(fleet.get_all_ships())
    fleet.remove_ship(ship_to_remove)
    assert len(fleet.get_all_ships()) == initial_count - 1
    assert ship_to_remove not in fleet.ships.keys()
    assert ship_to_remove not in fleet.miner_admiral.ships_assignments.keys()
    assert ship_to_remove not in fleet.miner_admiral.ships.keys()
    # assert ship_to_remove not in fleet.scanner_admiral.ships.keys()

def test_remove_ship_not_found(fleet_with_ships, home_planet_fixture):
    fleet, _ = fleet_with_ships
    non_existent_ship = ScannerShip(Vector2(100,100), home_planet=home_planet_fixture)
    initial_count = len(fleet.get_all_ships())
    # Should not raise error, maybe print warning (tested manually)
    fleet.remove_ship(non_existent_ship)
    assert len(fleet.get_all_ships()) == initial_count # Count shouldn't change

def test_get_all_ships(fleet_with_ships):
    fleet, initial_ships = fleet_with_ships
    all_ships = fleet.get_all_ships()
    assert len(all_ships) == len(initial_ships)
    assert all(ship in all_ships for ship in initial_ships)

def test_get_ships_by_type(fleet_with_ships):
    fleet, initial_ships = fleet_with_ships
    # Expect 1 scanner, 3 miners
    scanners = fleet.get_ships_by_type(ScannerShip)
    miners = fleet.get_ships_by_type(MiningShip)
    baseships = fleet.get_ships_by_type(Ship) # Get all

    assert len(scanners) == 1
    assert isinstance(scanners[0], ScannerShip)
    assert len(miners) == 3
    assert all(isinstance(m, MiningShip) for m in miners)
    assert len(baseships) == len(initial_ships)
