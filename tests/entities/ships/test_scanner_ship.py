import pytest
from pygame.math import Vector2
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src import constants
from src.enums import ShipState


@pytest.fixture
def home_planet_fixture():
    """Provides a reusable planet for ship home."""
    return Planet(Vector2(100, 100))


# def test_handle_arrival_for_set_target_asteroid_without_task(home_planet_fixture):
#     asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
#     scanner = ScannerShip(Vector2(10, 10), home_planet=home_planet_fixture)
#     scanner.set_target(asteroid)
#     assert scanner.state == ShipState.MOVING_TO_ASTEROID
#     scanner.handle_arrival()
#     assert scanner.state == ShipState.IDLE
#     assert scanner.target is None
#     assert scanner.scan_timer == 0


def test_handle_arrival_for_set_target_asteroid_with_task(home_planet_fixture):
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
    scanner = ScannerShip(Vector2(10, 10), home_planet=home_planet_fixture)
    scanner.assign_scan_target(asteroid)
    assert scanner.state == ShipState.MOVING_TO_SCAN
    scanner.handle_arrival()
    assert scanner.state == ShipState.SCANNING
    assert scanner.target is asteroid
    assert scanner.scan_timer == constants.SCAN_DURATION
    

# def test_handle_arrival_scanned_resets_idle(home_planet_fixture):
#     asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
#     asteroid.scanned = True
#     scanner = ScannerShip(Vector2(10, 10), home_planet=home_planet_fixture)
#     scanner.set_target(asteroid)
#     assert scanner.state == ShipState.MOVING_TO_ASTEROID
#     scanner.handle_arrival()
#     assert scanner.state == ShipState.IDLE
#     assert scanner.target is None


def test_update_scanning_transitions(home_planet_fixture):
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
    scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)
    scanner.state = ShipState.SCANNING
    scanner.target = asteroid
    scanner.scan_timer = constants.SCAN_DURATION
    obstacles = []  # Dummy obstacles

    scanner.update(1.0, obstacles)
    assert scanner.state == ShipState.SCANNING
    assert pytest.approx(scanner.scan_timer) == constants.SCAN_DURATION - 1.0
    assert not asteroid.scanned

    scanner.update(constants.SCAN_DURATION, obstacles)
    assert scanner.state == ShipState.IDLE
    assert asteroid.scanned
    assert scanner.target is None


def test_update_scanning_without_target_goes_idle(home_planet_fixture):
    scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)
    scanner.state = ShipState.SCANNING
    scanner.target = None
    obstacles = []

    scanner.update(1.0, obstacles)
    assert scanner.state == ShipState.IDLE
