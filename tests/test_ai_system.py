import pytest
from pygame.math import Vector2
from src.systems.ai_system import assign_scanner_task, assign_miner_task
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.ships.mining_ship import MiningShip
from src.enums import ShipState


def test_assign_scanner_task_picks_nearest_unscanned():
    scanner = ScannerShip(Vector2(0, 0))
    a1 = Asteroid(Vector2(10, 0), radius=1, color=(0, 0, 0))
    a2 = Asteroid(Vector2(5, 0), radius=1, color=(0, 0, 0))
    # both unscanned by default
    assign_scanner_task(scanner, [a1, a2])
    assert scanner.target is a2
    assert scanner.state == ShipState.MOVING_TO_ASTEROID


def test_assign_scanner_task_no_unscanned_leaves_idle():
    scanner = ScannerShip(Vector2(0, 0))
    a1 = Asteroid(Vector2(10, 0), radius=1, color=(0, 0, 0))
    a2 = Asteroid(Vector2(5, 0), radius=1, color=(0, 0, 0))
    a1.scanned = True
    a2.scanned = True
    assign_scanner_task(scanner, [a1, a2])
    assert scanner.target is None
    assert scanner.state == ShipState.IDLE


def test_assign_miner_task_returns_to_base_when_full():
    planet = Planet(Vector2(0, 0), radius=5, color=(0, 0, 0))
    miner = MiningShip(Vector2(0, 0))
    # Fill cargo to capacity
    key = next(iter(miner.cargo.keys()))
    miner.cargo[key] = miner.cargo_capacity
    assert miner.get_cargo_total() >= miner.cargo_capacity
    assign_miner_task(miner, [], planet, {})
    assert miner.target is planet
    assert miner.state == ShipState.RETURNING_TO_BASE


def test_assign_miner_task_no_suitable_and_empty_stays_idle():
    planet = Planet(Vector2(0, 0), radius=5, color=(0, 0, 0))
    miner = MiningShip(Vector2(0, 0))
    # asteroid has no resources
    a = Asteroid(Vector2(10, 0), radius=1, color=(1, 1, 1))
    a.scanned = True
    # empty resources
    for k in a.resources:
        a.resources[k] = 0
    assert miner.get_cargo_total() == 0
    assign_miner_task(miner, [a], planet, {"Tritanium": 1.0})
    assert miner.target is None
    assert miner.state == ShipState.IDLE


def test_assign_miner_task_fallback_return_with_partial_cargo():
    planet = Planet(Vector2(0, 0), radius=5, color=(0, 0, 0))
    miner = MiningShip(Vector2(0, 0))
    # set some cargo
    miner.cargo["Tritanium"] = 10
    a = Asteroid(Vector2(10, 0), radius=1, color=(1, 1, 1))
    a.scanned = True
    for k in a.resources:
        a.resources[k] = 0
    assert miner.get_cargo_total() > 0
    assign_miner_task(miner, [a], planet, {"Tritanium": 1.0})
    assert miner.target is planet
    assert miner.state == ShipState.RETURNING_TO_BASE


def test_assign_miner_task_selects_best_scored_asteroid():
    planet = Planet(Vector2(0, 0), radius=5, color=(0, 0, 0))
    miner = MiningShip(Vector2(0, 0))
    # prepare asteroids
    a1 = Asteroid(Vector2(10, 0), radius=1, color=(0, 0, 0))
    a2 = Asteroid(Vector2(20, 0), radius=1, color=(0, 0, 0))
    for a in (a1, a2):
        a.scanned = True
        # one resource Tritanium
        for k in a.resources:
            a.resources[k] = 0
        a.resources["Tritanium"] = 100
    priorities = {"Tritanium": 1.0}
    assign_miner_task(miner, [a1, a2], planet, priorities)
    assert miner.target is a1
    assert miner.state == ShipState.MOVING_TO_ASTEROID


def test_assign_miner_task_considers_priorities():
    planet = Planet(Vector2(0, 0), radius=5, color=(0, 0, 0))
    miner = MiningShip(Vector2(0, 0))
    a1 = Asteroid(Vector2(10, 0), radius=1, color=(0, 0, 0))
    a2 = Asteroid(Vector2(10, 0), radius=1, color=(0, 0, 0))
    # asteroid1 has Tritanium; asteroid2 has Credits
    for a in (a1, a2):
        a.scanned = True
        for k in a.resources:
            a.resources[k] = 0
    a1.resources["Tritanium"] = 100
    a2.resources["Credits"] = 100
    priorities = {"Tritanium": 0.1, "Credits": 1.0}
    assign_miner_task(miner, [a1, a2], planet, priorities)
    assert miner.target is a2
    assert miner.state == ShipState.MOVING_TO_ASTEROID 