import pytest
from pygame.math import Vector2
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src import constants
from src.enums import ShipState


def test_handle_arrival_unscanned_sets_scanning():
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
    scanner = ScannerShip(Vector2(10, 10))
    scanner.set_target(asteroid)
    # Ensure initial state is MOVING_TO_ASTEROID
    assert scanner.state == ShipState.MOVING_TO_ASTEROID

    # Arrival on unscanned asteroid should start scanning
    scanner.handle_arrival(Planet(Vector2(0,0), radius=1, color=(0,0,0)))
    assert scanner.state == ShipState.SCANNING
    assert pytest.approx(scanner.scan_timer) == constants.SCAN_DURATION


def test_handle_arrival_scanned_resets_idle():
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1,2,3))
    asteroid.scanned = True
    scanner = ScannerShip(Vector2(10, 10))
    scanner.set_target(asteroid)
    assert scanner.state == ShipState.MOVING_TO_ASTEROID

    # Arrival on already scanned asteroid should idle and clear target
    scanner.handle_arrival(Planet(Vector2(0,0), radius=1, color=(0,0,0)))
    assert scanner.state == ShipState.IDLE
    assert scanner.target is None


def test_update_actions_scanning_transitions():
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1,2,3))
    scanner = ScannerShip(Vector2(0, 0))
    # Simulate scanning state
    scanner.state = ShipState.SCANNING
    scanner.target = asteroid
    scanner.scan_timer = constants.SCAN_DURATION

    # Partial update: remains scanning and timer decreases
    scanner.update_actions(1.0)
    assert scanner.state == ShipState.SCANNING
    assert pytest.approx(scanner.scan_timer) == constants.SCAN_DURATION - 1.0
    assert not asteroid.scanned

    # Complete update: timer expires, asteroid marked scanned, state idle
    scanner.update_actions(constants.SCAN_DURATION)
    assert scanner.state == ShipState.IDLE
    assert asteroid.scanned


def test_update_actions_scanning_without_target_goes_idle():
    scanner = ScannerShip(Vector2(0, 0))
    scanner.state = ShipState.SCANNING
    scanner.target = None

    scanner.update_actions(1.0)
    assert scanner.state == ShipState.IDLE 