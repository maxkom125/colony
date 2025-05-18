import pytest
from pygame.math import Vector2
from src.entities.ships.mining_ship import MiningShip
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.enums import ShipState, ResourceType
from src import constants
from unittest.mock import MagicMock


@pytest.fixture
def home_planet_fixture():
    """Provides a reusable planet for ship home."""
    return Planet(Vector2(100, 100))  # Position doesn't matter much here


# def test_handle_arrival_unscanned_asteroid_goes_idle(home_planet_fixture):
#     asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
#     miner = MiningShip(Vector2(10, 10), home_planet=home_planet_fixture)

#     miner.handle_arrival()
#     assert miner.state == ShipState.IDLE
#     assert miner.target is None


# def test_handle_arrival_scanned_with_resources_starts_mining(home_planet_fixture):
#     asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
#     asteroid.scanned = True
#     resource_type = ResourceType.list()[0]
#     asteroid.resources = {res: 0 for res in ResourceType.list()}
#     asteroid.resources[resource_type] = 50

#     miner = MiningShip(Vector2(10, 10), home_planet=home_planet_fixture)

#     mock_admiral = MagicMock()
#     mock_admiral.ships_assignments = {miner.id: resource_type}
#     miner.admiral = mock_admiral

#     miner.set_target(asteroid)
#     assert miner.state == ShipState.MOVING_TO_ASTEROID
#     assert miner.get_assigned_category() == resource_type

#     miner.handle_arrival()
#     assert miner.state == ShipState.MINING
#     assert miner.get_assigned_category() == resource_type
#     assert miner.mining_timer == 0.0


# def test_handle_arrival_scanned_empty_resources_returns_to_base(home_planet_fixture):
#     asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
#     asteroid.scanned = True
#     asteroid.resources = {res: 0 for res in asteroid.resources}

#     miner = MiningShip(Vector2(10, 10), home_planet=home_planet_fixture)

#     mock_admiral = MagicMock()
#     mock_admiral.ships_assignments = {miner.id: ResourceType.list()[0]}
#     miner.admiral = mock_admiral

#     miner.set_target(asteroid)
#     assert miner.state == ShipState.MOVING_TO_ASTEROID

#     miner.handle_arrival()
#     assert miner.state == ShipState.IDLE
#     assert miner.target is None
#     assert miner.get_assigned_category() is not None


def test_update_mining_and_transition(home_planet_fixture):
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
    asteroid.scanned = True
    resource_type = ResourceType.list()[0]
    asteroid.resources[resource_type] = constants.MINING_RATE * 2

    miner = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)

    mock_admiral = MagicMock()
    mock_admiral.ships_assignments = {miner.id: resource_type}
    mock_admiral.issue_command = MagicMock(side_effect=lambda ship: (
        ship.set_target(ship.home),
        ship.set_state(ShipState.RETURNING_TO_BASE),
        ship.set_resource_to_mine(None)
    ))
    miner.admiral = mock_admiral

    miner.state = ShipState.MINING
    miner.resource_to_mine = resource_type
    miner.target = asteroid
    miner.mining_timer = 0.0
    for k in miner.cargo:
        miner.cargo[k] = 0

    # Use the home planet from the fixture
    planet = home_planet_fixture
    # Dummy obstacles list
    obstacles = []

    miner.update(1.0, obstacles)
    assert miner.state == ShipState.MINING
    expected_mined = constants.MINING_RATE * 1.0
    assert pytest.approx(miner.cargo[resource_type]) == expected_mined
    assert (
        pytest.approx(asteroid.resources[resource_type])
        == (constants.MINING_RATE * 2) - expected_mined
    )

    miner.update(1.1, obstacles)
    assert miner.state == ShipState.MINING
    miner.update(0.1, obstacles)
    assert miner.state == ShipState.RETURNING_TO_BASE
    assert miner.target is planet
    assert miner.resource_to_mine is None


def test_update_dumping_completes_and_transitions(home_planet_fixture):
    planet = home_planet_fixture
    initial_tritanium = planet.storage[
        ResourceType.TRITANIUM
    ]  # Get initial amount from fixture/default
    initial_credits = planet.storage[ResourceType.CREDITS]

    miner = MiningShip(Vector2(0, 0), home_planet=planet)
    miner.fuel = miner.fuel_max_capacity # Add fuel

    # Add a mock admiral
    mock_admiral = MagicMock()
    # Define what issue_command should do for this test context
    def issue_command_side_effect(ship):
        ship.set_state(ShipState.IDLE)
        ship.set_target(None)
    mock_admiral.issue_command = MagicMock(side_effect=issue_command_side_effect)
    miner.admiral = mock_admiral

    miner.state = ShipState.DUMPING
    miner.target = None
    miner.dumping_timer = 0.0
    # Use multiple cargo types as originally intended
    miner.cargo = {ResourceType.TRITANIUM: 10, ResourceType.CREDITS: 5, ResourceType.PLASMA: 0}
    cargo_to_dump = miner.cargo.copy()  # Keep copy for assertion
    obstacles = []

    # Update for less than duration
    miner.update(constants.DUMPING_DURATION / 2, obstacles)
    assert miner.state == ShipState.DUMPING
    assert miner.cargo == cargo_to_dump  # Cargo not cleared yet
    assert (
        planet.storage[ResourceType.TRITANIUM] == initial_tritanium
    )  # Planet storage not updated yet
    assert planet.storage[ResourceType.CREDITS] == initial_credits

    # Update for remaining duration + a bit more
    miner.update(constants.DUMPING_DURATION / 2 + 0.1, obstacles)

    # Check all cargo types are zero
    assert all(amount == 0 for amount in miner.cargo.values())
    # Check planet storage increased correctly for each dumped resource
    assert planet.storage[ResourceType.TRITANIUM] == initial_tritanium + cargo_to_dump[ResourceType.TRITANIUM]
    assert planet.storage[ResourceType.CREDITS] == initial_credits + cargo_to_dump[ResourceType.CREDITS]
    assert miner.state == ShipState.IDLE
