import pytest
from pygame.math import Vector2
from unittest.mock import MagicMock
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


# def test_handle_arrival_for_set_target_asteroid_with_task(home_planet_fixture):
#     asteroid = Asteroid(Vector2(0, 0), radius=5, color=(1, 2, 3))
#     scanner = ScannerShip(Vector2(10, 10), home_planet=home_planet_fixture)
#     scanner.assign_scan_target(asteroid)
#     assert scanner.state == ShipState.MOVING_TO_SCAN
#     scanner.handle_arrival()
#     assert scanner.state == ShipState.SCANNING
#     assert scanner.target is asteroid
#     assert scanner.scan_timer == constants.SCAN_DURATION


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
    # Setup
    asteroid_radius = 5
    scan_rate = constants.SCANNER_SCAN_RATE

    asteroid = Asteroid(Vector2(0, 0), radius=asteroid_radius, color=(1, 2, 3))
    initial_scan_points = asteroid.scan_points_remaining
    total_scan_time = (
        initial_scan_points / scan_rate if scan_rate > constants.EPSILON else float("inf")
    )

    scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)
    scanner.state = ShipState.SCANNING
    scanner.target = asteroid
    obstacles = []  # Dummy obstacles

    # --- Mock the Admiral ---
    mock_admiral = MagicMock()

    # Define the side effect for issue_command
    def admiral_issue_command_side_effect(ship):
        # This function will be called when ship.admiral.issue_command(ship) is invoked
        # We check the ship's state *before* modifying it, as the real admiral would
        if ship.state == ShipState.SCANNING:
            print("Mock Admiral: Detected SCANNING state, setting to IDLE and clearing target.")
            ship.set_state(ShipState.IDLE)
            ship.target = None
        else:
            # Optional: Handle unexpected calls if needed
            print(f"Mock Admiral: issue_command called with unexpected state {ship.state}")

    # Assign the mock admiral and its side effect
    scanner.admiral = mock_admiral
    mock_admiral.issue_command.side_effect = admiral_issue_command_side_effect
    # --- End Mocking ---

    # Simulate partial scan (e.g., 1 second)
    partial_time = 1.0

    scanner.update(partial_time, obstacles)
    expected_points_remaining_after_partial = initial_scan_points - (scan_rate * partial_time)

    assert scanner.state == ShipState.SCANNING, "Ship should still be scanning"
    assert not asteroid.scanned, "Asteroid should not be scanned yet"
    # Optionally check the calculated UI timer
    expected_timer_after_partial = (
        expected_points_remaining_after_partial / scan_rate
        if scan_rate > constants.EPSILON
        else float("inf")
    )
    assert (
        pytest.approx(scanner.scan_timer) == expected_timer_after_partial
    ), "UI Timer incorrect after partial scan"
    assert (
        asteroid.scan_points_remaining == expected_points_remaining_after_partial
    ), "Scan points remaining incorrect after partial scan"
    # Simulate remaining time to complete scan
    remaining_time = total_scan_time - partial_time
    if remaining_time < 0:
        pytest.fail("Remaining time calculation error")

    scanner.update(remaining_time + constants.EPSILON, obstacles)
    assert scanner.state == ShipState.SCANNING, "Ship should still be scanning"
    assert not asteroid.scanned, "Asteroid should not be scanned yet"
    assert pytest.approx(scanner.scan_timer) == 0, "UI Timer incorrect after full scan"
    assert asteroid.scan_points_remaining == 0, "Scan points remaining after full scan"
    mock_admiral.issue_command.assert_not_called()

    scanner.update(constants.EPSILON, obstacles)  # should trigger the end of the scan

    # --- Assertions ---
    # Check if the admiral's issue_command was called at the end
    mock_admiral.issue_command.assert_called_once_with(scanner)

    # The mock side effect should have handled these state changes:
    assert scanner.state == ShipState.IDLE, "Mock admiral should have set state to IDLE"
    assert scanner.target is None, "Mock admiral should have cleared target"

    # Verify asteroid state changes still occurred
    assert asteroid.scanned, "Asteroid should be scanned"
    assert asteroid.scan_points_remaining == 0, "Scan points should be zero"
    assert scanner.scan_timer == 0.0, "UI timer should be zero after scan completes"
    assert scanner.target is None, "Scanner target should be cleared"


def test_update_scanning_without_target_goes_idle(home_planet_fixture):
    scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)
    scanner.state = ShipState.SCANNING
    scanner.target = None
    obstacles = []

    scanner.update(1.0, obstacles)
    assert scanner.state == ShipState.IDLE


def test_update_scanning_invalid_target_goes_idle(home_planet_fixture):
    """Test that scanning a non-asteroid target sets state to IDLE."""
    scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)
    scanner.state = ShipState.SCANNING
    # Assign a Planet as an invalid target
    scanner.target = home_planet_fixture
    obstacles = []

    scanner.update(1.0, obstacles)

    assert scanner.state == ShipState.IDLE, "State should be IDLE after scanning invalid target"
    assert scanner.target is None, "Target should be cleared after scanning invalid target"


def test_get_arrival_threshold_moving_to_scan(home_planet_fixture):
    """Test arrival threshold when moving to scan."""
    scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)
    scanner.state = ShipState.MOVING_TO_SCAN
    # Assign a dummy target just to be safe, though state is key
    scanner.target = Asteroid(Vector2(100, 100), 10, (1, 1, 1))

    threshold = scanner.get_arrival_threshold()
    assert threshold == scanner.scan_range, "Threshold should equal scan_range when MOVING_TO_SCAN"


def test_get_arrival_threshold_not_moving_to_scan(home_planet_fixture):
    """Test arrival threshold when not moving to scan."""
    scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)
    # Test with IDLE state, could be any other non-MOVING_TO_SCAN state
    scanner.state = ShipState.IDLE

    # We need the base class threshold to compare. We can get it by calling the
    # super() method directly, or by creating a base Ship instance (less ideal).
    # Let's assume the base threshold is accessible/known or call super if possible.
    # For simplicity here, let's just check it's NOT the scan_range.
    # A better test might involve mocking super().get_arrival_threshold
    base_threshold = super(ScannerShip, scanner).get_arrival_threshold()

    threshold = scanner.get_arrival_threshold()
    assert (
        threshold != scanner.scan_range
    ), "Threshold should not equal scan_range for non-MOVING_TO_SCAN state"
    assert threshold == base_threshold, "Threshold should equal base class threshold"
