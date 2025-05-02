# tests/systems/admirals/test_scanner_admiral.py
import pytest
import random
from unittest.mock import MagicMock, patch, call
from pygame.math import Vector2

# Objects to test
from src.systems.admirals.scanner_admiral import ScannerAdmiral
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.enums import ShipState
from src import constants


# --- Mock Classes ---

class MockScannerShip(MagicMock):
    _next_id = 200 # Start scanner IDs differently

    def __init__(self, ship_id=None, state=ShipState.IDLE, position=Vector2(0, 0), home_planet=None, target=None, **kwargs):
        super().__init__(spec=ScannerShip, **kwargs)
        if ship_id is not None:
            self.id = ship_id
            MockScannerShip._next_id = max(MockScannerShip._next_id, ship_id + 1)
        else:
            self.id = MockScannerShip._next_id
            MockScannerShip._next_id += 1
        self.state = state
        self.position = position
        self.home = home_planet
        self.target = target
        self.scan_range = constants.SCANNER_SCAN_RANGE # Include relevant attributes
        self.scan_rate = constants.SCANNER_SCAN_RATE
        self.scan_timer = 0.0
        self.admiral = None # Admiral will be set by add_ship
        # Mock methods called by ScannerAdmiral
        self.set_target = MagicMock()
        self.set_state = MagicMock()
        self.name = f"MockScanner_{self.id}" # For debugging


class MockAsteroid(MagicMock):
    _next_id = 1000

    def __init__(self, asteroid_id=None, position=Vector2(10, 10), scanned=False, radius=10, resources=None, **kwargs):
        super().__init__(spec=Asteroid, **kwargs)
        if asteroid_id is not None:
            self.id = asteroid_id
            MockAsteroid._next_id = max(MockAsteroid._next_id, asteroid_id + 1)
        else:
            self.id = MockAsteroid._next_id
            MockAsteroid._next_id += 1
        self.position = position
        self.scanned = scanned
        self.radius = radius
        # Add scan_points_remaining based on current logic
        self.scan_points_remaining = self.radius * constants.SCAN_POINTS_PER_RADIUS
        self.resources = resources or {"Tritanium": 100} # Keep resources for potential future use/compatibility
        self.name = f"MockAsteroid_{self.id}"


class MockPlanet(MagicMock):
    def __init__(self, planet_id=999, position=Vector2(0, 0), **kwargs):
        super().__init__(spec=Planet, **kwargs)
        self.id = planet_id
        self.position = position
        self.name = "MockPlanet"


# --- Fixtures ---

@pytest.fixture
def scanner_admiral():
    """Provides a fresh ScannerAdmiral instance for each test."""
    MockScannerShip._next_id = 200
    MockAsteroid._next_id = 1000
    return ScannerAdmiral()

@pytest.fixture
def mock_scanner(mock_planet):
    """Provides a default mock scanner ship with a home planet."""
    return MockScannerShip(home_planet=mock_planet, position=Vector2(1,1))

@pytest.fixture
def mock_planet():
    """Provides a mock planet."""
    return MockPlanet(position=Vector2(0,0))

@pytest.fixture
def mock_asteroid_unscanned():
    """Provides a default unscanned mock asteroid."""
    return MockAsteroid(position=Vector2(10, 10), scanned=False)

@pytest.fixture
def mock_asteroids(mock_asteroid_unscanned):
    """Provides a list containing one unscanned mock asteroid."""
    return [mock_asteroid_unscanned]

# --- Test Cases ---

def test_scanner_admiral_init(scanner_admiral):
    """Test ScannerAdmiral initializes correctly."""
    assert isinstance(scanner_admiral.ships, dict)
    assert len(scanner_admiral.ships) == 0
    assert scanner_admiral.get_ship_count() == 0

def test_add_ship_success(scanner_admiral, mock_scanner):
    """Test adding a valid ScannerShip."""
    scanner_admiral.add_ship(mock_scanner)
    assert scanner_admiral.get_ship_count() == 1
    assert mock_scanner.id in scanner_admiral.ships
    assert scanner_admiral.ships[mock_scanner.id] is mock_scanner
    assert mock_scanner.admiral is scanner_admiral # Check admiral reference is set

def test_add_ship_non_scanner_ignored(scanner_admiral, capsys):
    """Test adding a non-ScannerShip is ignored and logs a warning."""
    non_scanner = MagicMock(id=500) # Doesn't inherit/spec ScannerShip
    scanner_admiral.add_ship(non_scanner)
    captured = capsys.readouterr()
    assert scanner_admiral.get_ship_count() == 0
    assert f"WARN: Attempted to add non-ScannerShip {non_scanner.id}" in captured.out

def test_add_ship_duplicate_handled_by_base(scanner_admiral, mock_scanner, capsys):
    """Test adding a duplicate ScannerShip raises error from base and logs info."""
    scanner_admiral.add_ship(mock_scanner) # Add first time
    # Create another mock with the same ID
    duplicate_scanner = MockScannerShip(ship_id=mock_scanner.id)
    # Add the duplicate
    scanner_admiral.add_ship(duplicate_scanner)
    captured = capsys.readouterr()
    # Check state: only original scanner should be present
    assert scanner_admiral.get_ship_count() == 1
    assert scanner_admiral.ships[mock_scanner.id] is mock_scanner
    # Check that the base class error message was logged
    assert f"INFO: Ship {mock_scanner.id} already managed by this Admiral." in captured.out

def test_remove_ship_success(scanner_admiral, mock_scanner):
    """Test removing an existing ScannerShip."""
    scanner_admiral.add_ship(mock_scanner)
    scanner_admiral.remove_ship(mock_scanner.id)
    assert scanner_admiral.get_ship_count() == 0
    assert mock_scanner.id not in scanner_admiral.ships

def test_remove_ship_not_found_handled_by_base(scanner_admiral, capsys):
    """Test removing a non-existent ship ID raises error from base and logs info."""
    non_existent_id = 999
    scanner_admiral.remove_ship(non_existent_id)
    captured = capsys.readouterr()
    assert scanner_admiral.get_ship_count() == 0
    # Base class now raises ShipNotFoundError, check for warning log instead
    assert f"""Ship {non_existent_id} not found in this Admiral's fleet.""" in captured.out 

# --- Tests for issue_command --- #

@patch("src.systems.admirals.scanner_admiral.ScannerAdmiral.issue_scanning_command")
def test_issue_command_moving_to_scan(mock_issue_scanning, scanner_admiral, mock_scanner):
    """Test issue_command calls issue_scanning_command when state is MOVING_TO_SCAN."""
    mock_scanner.state = ShipState.MOVING_TO_SCAN
    scanner_admiral.add_ship(mock_scanner)

    scanner_admiral.issue_command(mock_scanner)

    mock_issue_scanning.assert_called_once_with(mock_scanner)


def test_issue_command_scanning_sets_idle(scanner_admiral, mock_scanner):
    """Test issue_command sets IDLE and clears target when state is SCANNING (current logic)."""
    mock_scanner.state = ShipState.SCANNING
    mock_scanner.target = MockAsteroid() # Give it a target
    scanner_admiral.add_ship(mock_scanner)
    mock_scanner.set_state.reset_mock()
    mock_scanner.set_target.reset_mock()

    scanner_admiral.issue_command(mock_scanner)

    # Verify the specific actions taken in the SCANNING case
    mock_scanner.set_state.assert_called_once_with(ShipState.IDLE)
    mock_scanner.set_target.assert_called_once_with(None)


@patch("src.systems.admirals.base_admiral.Admiral.issue_command") # Patch the superclass method
def test_issue_command_idle_calls_base(mock_super_issue_command, scanner_admiral, mock_scanner):
    """Test issue_command calls super().issue_command for IDLE state."""
    mock_scanner.state = ShipState.IDLE
    scanner_admiral.add_ship(mock_scanner)

    scanner_admiral.issue_command(mock_scanner)

    mock_super_issue_command.assert_called_once_with(mock_scanner)

# --- Tests for issue_scanning_command --- #

def test_issue_scanning_command_starts_scan(scanner_admiral, mock_scanner, mock_asteroid_unscanned):
    """Test issue_scanning_command sets state to SCANNING for a valid target."""
    mock_scanner.target = mock_asteroid_unscanned
    # Ensure asteroid is not scanned initially
    assert not mock_asteroid_unscanned.scanned
    scanner_admiral.add_ship(mock_scanner)
    mock_scanner.set_state.reset_mock() # Reset after add_ship

    scanner_admiral.issue_scanning_command(mock_scanner)

    mock_scanner.set_state.assert_called_once_with(ShipState.SCANNING)
    # Target should remain assigned
    mock_scanner.set_target.assert_not_called()

def test_issue_scanning_command_already_scanned_goes_idle(scanner_admiral, mock_scanner, mock_asteroid_unscanned):
    """Test issue_scanning_command goes IDLE if target is already scanned."""
    mock_asteroid_unscanned.scanned = True # Mark as scanned
    mock_scanner.target = mock_asteroid_unscanned
    scanner_admiral.add_ship(mock_scanner)
    mock_scanner.set_state.reset_mock()
    mock_scanner.set_target.reset_mock()

    scanner_admiral.issue_scanning_command(mock_scanner)

    mock_scanner.set_state.assert_called_once_with(ShipState.IDLE)
    mock_scanner.set_target.assert_called_once_with(None)

def test_issue_scanning_command_no_target_goes_idle(scanner_admiral, mock_scanner):
    """Test issue_scanning_command goes IDLE if ship has no target."""
    mock_scanner.target = None
    scanner_admiral.add_ship(mock_scanner)
    mock_scanner.set_state.reset_mock()
    mock_scanner.set_target.reset_mock()

    scanner_admiral.issue_scanning_command(mock_scanner)

    mock_scanner.set_state.assert_called_once_with(ShipState.IDLE)
    mock_scanner.set_target.assert_not_called() # Target was already None

def test_issue_scanning_command_invalid_target_goes_idle(scanner_admiral, mock_scanner, mock_planet):
    """Test issue_scanning_command goes IDLE if target is not an Asteroid."""
    mock_scanner.target = mock_planet # Invalid target type
    scanner_admiral.add_ship(mock_scanner)
    mock_scanner.set_state.reset_mock()
    mock_scanner.set_target.reset_mock()

    scanner_admiral.issue_scanning_command(mock_scanner)

    mock_scanner.set_state.assert_called_once_with(ShipState.IDLE)
    mock_scanner.set_target.assert_called_once_with(None) 

# --- Tests for assign_idle_scanners --- #

@patch("src.systems.admirals.scanner_admiral.ScannerAdmiral._find_nearest_unscanned_asteroid")
def test_assign_idle_scanners_assigns_nearest(mock_find_nearest, scanner_admiral):
    """Test assigning an idle scanner to the nearest unscanned asteroid."""
    idle_scanner = MockScannerShip(ship_id=201, state=ShipState.IDLE, position=Vector2(0,0))
    moving_scanner = MockScannerShip(ship_id=202, state=ShipState.MOVING_TO_SCAN, position=Vector2(500,500))
    target_asteroid = MockAsteroid(asteroid_id=1001, position=Vector2(10,0), scanned=False)
    other_asteroid = MockAsteroid(asteroid_id=1002, position=Vector2(100,0), scanned=False)
    # Add a targeted asteroid to ensure exclusion logic works
    targeted_asteroid = MockAsteroid(asteroid_id=1003, position=Vector2(5,5), scanned=False)
    moving_scanner.target = targeted_asteroid # This scanner targets 1003

    scanner_admiral.add_ship(idle_scanner)
    scanner_admiral.add_ship(moving_scanner)

    asteroids = [target_asteroid, other_asteroid, targeted_asteroid]
    mock_find_nearest.return_value = target_asteroid # Mock finding the closer one (1001)

    idle_scanner.set_state.reset_mock()
    idle_scanner.set_target.reset_mock()

    scanner_admiral.assign_idle_scanners(asteroids)

    # --- Custom Argument Verification --- 
    # 1. Assert the mock was called exactly once
    mock_find_nearest.assert_called_once()

    # 2. Get the arguments it was called with
    actual_args, actual_kwargs = mock_find_nearest.call_args

    # 3. Perform specific checks on the arguments
    # Check position (args[0])
    assert actual_args[0] == idle_scanner.position, "Incorrect position passed to mock"

    # Check the list of asteroids (args[1]) using set comparison
    # This verifies the same elements are present, regardless of order.
    assert set(actual_args[1]) == set(asteroids), "Incorrect set of asteroids passed to mock"

    # Check the set of excluded IDs (args[2])
    # target asteroid is appended!
    assert set(actual_args[2]) == set([targeted_asteroid.id, target_asteroid.id]), "Incorrect set of excluded IDs passed to mock"
    # --- End Custom Verification --- 

    # Verify the idle scanner was assigned the target and state changed
    idle_scanner.set_target.assert_called_once_with(target_asteroid)
    idle_scanner.set_state.assert_called_once_with(ShipState.MOVING_TO_SCAN)


def test_assign_idle_scanners_no_idle(scanner_admiral, mock_asteroids):
    """Test assign_idle_scanners does nothing if no scanners are IDLE."""
    scanner = MockScannerShip(state=ShipState.SCANNING) # Not IDLE
    scanner_admiral.add_ship(scanner)
    scanner.set_target.reset_mock()
    scanner.set_state.reset_mock()

    scanner_admiral.assign_idle_scanners(mock_asteroids)

    scanner.set_target.assert_not_called()
    scanner.set_state.assert_not_called()

def test_assign_idle_scanners_no_unscanned(scanner_admiral, mock_scanner):
    """Test assign_idle_scanners does nothing if no asteroids are unscanned."""
    scanner_admiral.add_ship(mock_scanner) # Idle scanner
    mock_scanner.set_target.reset_mock()
    mock_scanner.set_state.reset_mock()

    # All asteroids are scanned
    asteroids = [MockAsteroid(scanned=True), MockAsteroid(scanned=True)]

    # Patch the helper to ensure it's not called unnecessarily,
    # although the main function might filter asteroids list first.
    with patch("src.systems.admirals.scanner_admiral.ScannerAdmiral._find_nearest_unscanned_asteroid") as mock_find:
        scanner_admiral.assign_idle_scanners(asteroids)
        mock_find.assert_not_called() # Helper shouldn't be called if unscanned list is empty

    mock_scanner.set_target.assert_not_called()
    mock_scanner.set_state.assert_not_called()

@patch("src.systems.admirals.scanner_admiral.ScannerAdmiral._find_nearest_unscanned_asteroid")
def test_assign_idle_scanners_no_suitable_target(mock_find_nearest, scanner_admiral, mock_scanner):
    """Test assign_idle_scanners does nothing if _find_nearest returns None."""
    scanner_admiral.add_ship(mock_scanner) # Idle scanner
    mock_scanner.set_target.reset_mock()
    mock_scanner.set_state.reset_mock()

    asteroids = [MockAsteroid(scanned=False)] # Unscanned asteroid exists
    mock_find_nearest.return_value = None # But mock finding nothing

    scanner_admiral.assign_idle_scanners(asteroids)

    # _find_nearest should have been called
    mock_find_nearest.assert_called_once()
    # But ship state should not change
    mock_scanner.set_target.assert_not_called()
    mock_scanner.set_state.assert_not_called()

def test_assign_idle_scanners_multiple_idle_avoid_same_target(scanner_admiral):
    """Test that multiple idle scanners don't target the same asteroid in one cycle."""
    # Setup: Two idle scanners close to each other
    idle_scanner1 = MockScannerShip(ship_id=201, state=ShipState.IDLE, position=Vector2(0, 0))
    idle_scanner2 = MockScannerShip(ship_id=202, state=ShipState.IDLE, position=Vector2(1, 1)) # Slightly offset

    # One close, desirable asteroid, and one farther one
    close_asteroid = MockAsteroid(asteroid_id=1001, position=Vector2(10, 0), scanned=False)
    far_asteroid = MockAsteroid(asteroid_id=1002, position=Vector2(100, 0), scanned=False)

    scanner_admiral.add_ship(idle_scanner1)
    scanner_admiral.add_ship(idle_scanner2)

    asteroids = [close_asteroid, far_asteroid]

    idle_scanner1.set_state.reset_mock()
    idle_scanner1.set_target.reset_mock()
    idle_scanner2.set_state.reset_mock()
    idle_scanner2.set_target.reset_mock()

    # Act: Assign tasks
    scanner_admiral.assign_idle_scanners(asteroids)

    # Assertions:
    # We expect one scanner to get the close asteroid, the other to get the far one (or none if only one existed)
    # We don't know the iteration order, so check which scanner got which target.

    scanner1_target_call = idle_scanner1.set_target.call_args
    scanner2_target_call = idle_scanner2.set_target.call_args

    # Check that set_target was called exactly once for each scanner
    idle_scanner1.set_target.assert_called_once()
    idle_scanner2.set_target.assert_called_once()

    # Get the actual target objects they were called with
    scanner1_assigned_target = scanner1_target_call[0][0] if scanner1_target_call else None
    scanner2_assigned_target = scanner2_target_call[0][0] if scanner2_target_call else None

    # Ensure they were assigned different targets
    assert scanner1_assigned_target is not None, "Scanner 1 should have been assigned a target"
    assert scanner2_assigned_target is not None, "Scanner 2 should have been assigned a target"
    assert scanner1_assigned_target is not scanner2_assigned_target, "Scanners should not target the same asteroid"

    # Verify they were assigned the two available asteroids
    assigned_targets = {scanner1_assigned_target, scanner2_assigned_target}
    expected_targets = {close_asteroid, far_asteroid}
    assert assigned_targets == expected_targets, "Scanners were not assigned the expected set of asteroids"

    # Verify both states were set correctly
    idle_scanner1.set_state.assert_called_once_with(ShipState.MOVING_TO_SCAN)
    idle_scanner2.set_state.assert_called_once_with(ShipState.MOVING_TO_SCAN)

# --- Tests for _find_nearest_unscanned_asteroid --- #
# Note: This partially duplicates tests.utils.test_find_nearest_object, but tests the filter logic.

def test_find_nearest_unscanned_finds_closest(scanner_admiral):
    source_pos = Vector2(0, 0)
    a_near = MockAsteroid(position=(10, 0), scanned=False, asteroid_id=101)
    a_far = MockAsteroid(position=(100, 0), scanned=False, asteroid_id=102)
    a_scanned = MockAsteroid(position=(5, 0), scanned=True, asteroid_id=103) # Closer but scanned
    a_excluded = MockAsteroid(position=(1, 0), scanned=False, asteroid_id=104) # Closest but excluded
    asteroids = [a_far, a_near, a_scanned, a_excluded]
    excluded_ids = {104}

    nearest = scanner_admiral._find_nearest_unscanned_asteroid(source_pos, asteroids, excluded_ids)
    assert nearest is a_near

def test_find_nearest_unscanned_ignores_scanned(scanner_admiral):
    source_pos = Vector2(0, 0)
    a_far_unscanned = MockAsteroid(position=(100, 0), scanned=False, asteroid_id=101)
    a_near_scanned = MockAsteroid(position=(10, 0), scanned=True, asteroid_id=102)
    asteroids = [a_far_unscanned, a_near_scanned]
    excluded_ids = set()
    nearest = scanner_admiral._find_nearest_unscanned_asteroid(source_pos, asteroids, excluded_ids)
    assert nearest is a_far_unscanned

def test_find_nearest_unscanned_ignores_excluded(scanner_admiral):
    source_pos = Vector2(0, 0)
    a_far_unscanned = MockAsteroid(position=(100, 0), scanned=False, asteroid_id=101)
    a_near_excluded = MockAsteroid(position=(10, 0), scanned=False, asteroid_id=102)
    asteroids = [a_far_unscanned, a_near_excluded]
    excluded_ids = {102}
    nearest = scanner_admiral._find_nearest_unscanned_asteroid(source_pos, asteroids, excluded_ids)
    assert nearest is a_far_unscanned

def test_find_nearest_unscanned_no_match(scanner_admiral):
    source_pos = Vector2(0, 0)
    a_scanned = MockAsteroid(position=(10, 0), scanned=True, asteroid_id=101)
    a_excluded = MockAsteroid(position=(5, 0), scanned=False, asteroid_id=102)
    asteroids = [a_scanned, a_excluded]
    excluded_ids = {102}
    nearest = scanner_admiral._find_nearest_unscanned_asteroid(source_pos, asteroids, excluded_ids)
    assert nearest is None

def test_find_nearest_unscanned_empty_list(scanner_admiral):
    source_pos = Vector2(0, 0)
    asteroids = []
    excluded_ids = set()
    nearest = scanner_admiral._find_nearest_unscanned_asteroid(source_pos, asteroids, excluded_ids)
    assert nearest is None 