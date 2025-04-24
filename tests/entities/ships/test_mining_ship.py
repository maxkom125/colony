import pytest
from pygame.math import Vector2
from src.entities.ships.mining_ship import MiningShip
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.enums import ShipState
from src import constants


def test_handle_arrival_unscanned_asteroid_goes_idle():
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
    miner = MiningShip(Vector2(10, 10))
    miner.set_target(asteroid)
    assert miner.state == ShipState.MOVING_TO_ASTEROID

    miner.handle_arrival(Planet(Vector2(0, 0), radius=1, color=(0, 0, 0)))
    assert miner.state == ShipState.IDLE
    assert miner.target is None


def test_handle_arrival_scanned_with_resources_starts_mining():
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
    asteroid.scanned = True
    # Ensure only one resource remains
    for res in list(asteroid.resources.keys()):
        asteroid.resources[res] = 0
    asteroid.resources[constants.RESOURCE_TYPES[0]] = 50

    miner = MiningShip(Vector2(10, 10))
    miner.set_target(asteroid)
    assert miner.state == ShipState.MOVING_TO_ASTEROID

    miner.handle_arrival(Planet(Vector2(0, 0), radius=1, color=(0, 0, 0)))
    assert miner.state == ShipState.MINING
    assert pytest.approx(miner.mining_timer) == constants.MINING_DURATION


def test_handle_arrival_scanned_empty_resources_returns_to_base():
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
    asteroid.scanned = True
    asteroid.resources = {res: 0 for res in asteroid.resources}

    miner = MiningShip(Vector2(10, 10))
    miner.set_target(asteroid)

    miner.handle_arrival(planet := Planet(Vector2(0, 0), radius=1, color=(0, 0, 0)))
    assert miner.state == ShipState.RETURNING_TO_BASE
    assert miner.target is planet


def test_update_actions_mining_and_transition():
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
    asteroid.scanned = True
    # Give some resource
    for res in list(asteroid.resources.keys()):
        asteroid.resources[res] = 0
    asteroid.resources[constants.RESOURCE_TYPES[0]] = constants.MINING_RATE * 2

    miner = MiningShip(Vector2(0, 0))
    miner.state = ShipState.MINING
    miner.target = asteroid
    miner.mining_timer = constants.MINING_DURATION
    # Clear cargo
    for k in miner.cargo:
        miner.cargo[k] = 0

    # Partial tick
    miner.update_actions(1.0, planet=None)
    assert miner.state == ShipState.MINING
    assert pytest.approx(miner.mining_timer) == constants.MINING_DURATION - 1.0
    assert pytest.approx(miner.cargo[constants.RESOURCE_TYPES[0]]) == constants.MINING_RATE * 1.0

    # Complete tick to trigger transition
    miner.update_actions(constants.MINING_DURATION, planet := Planet(Vector2(0, 0), radius=1, color=(0,0,0)))
    assert miner.state == ShipState.RETURNING_TO_BASE
    assert miner.target is planet


def test_update_actions_dumping_clears_cargo_and_increases_storage():
    planet = Planet(Vector2(0, 0), radius=1, color=(0,0,0))
    miner = MiningShip(Vector2(0, 0))
    miner.cargo = {"Tritanium": 10, "Credits": 5, "Plasma": 0}
    miner.state = ShipState.DUMPING
    miner.dumping_timer = constants.DUMPING_DURATION
    original_storage = planet.storage.copy()

    # Partial dumping
    miner.update_actions(1.0, planet)
    assert miner.state == ShipState.DUMPING
    assert miner.cargo["Tritanium"] == 10
    # Complete dumping
    miner.update_actions(constants.DUMPING_DURATION, planet)
    assert miner.state == ShipState.IDLE
    assert all(amount == 0 for amount in miner.cargo.values())
    assert planet.storage["Tritanium"] == original_storage["Tritanium"] + 10
    assert planet.storage["Credits"] == original_storage["Credits"] + 5 