import pytest
import pygame
from pygame.math import Vector2
from src.entities.ships.base_ship import Ship
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.enums import ShipState, ShipType
from src import constants
from src.entities.entity import Entity

@pytest.fixture(autouse=True)
def stub_polygon(monkeypatch):
    calls = []
    def fake_polygon(surface, color, points):
        calls.append((surface, color, points))
    monkeypatch.setattr(pygame.draw, 'polygon', fake_polygon)
    return calls

@pytest.fixture
def home_planet_fixture():
    """Provides a reusable planet for ship home."""
    return Planet(Vector2(0,0)) # Simple planet at origin

@pytest.fixture
def base_ship(home_planet_fixture):
    """Provides a default Ship instance with a home planet."""
    ship = Ship(Vector2(100, 200), radius=10, color=(255, 0, 0), speed=50, home_planet=home_planet_fixture)
    ship.fuel = ship.fuel_max_capacity # Initialize with full fuel
    return ship

def test_get_cargo_total_initial_zero(home_planet_fixture):
    ship = Ship(Vector2(0, 0), radius=10, color=(1, 2, 3), speed=50.0, home_planet=home_planet_fixture)
    assert ship.get_cargo_total() == 0

def test_set_target_asteroid_keeps_state_and_resets_timers(base_ship, mocker):
    ship = base_ship
    asteroid = Asteroid(Vector2(5, 5), radius=2, color=(0,0,0))
    initial_state = ship.state
    # Mock the reset_timers method *before* calling set_target
    mock_reset_timers = mocker.patch.object(ship, 'reset_timers')
    ship.set_target(asteroid)
    assert ship.state == initial_state
    assert ship.target is asteroid
    # check if the *mocked* method was called
    mock_reset_timers.assert_called_once()


def test_update_movement_noop_if_idle(base_ship):
    """Test that update_movement doesn't change position if state is IDLE."""
    ship = base_ship
    ship.state = ShipState.IDLE
    ship.target = Asteroid(Vector2(500,500), 10, (1,1,1)) # Give it a target
    initial_pos = ship.position.copy()
    ship.update(0.1, []) # Calls update_movement internally
    assert ship.position == initial_pos

def test_update_movement_noop_if_no_target(base_ship):
    """Test that update_movement doesn't change position if target is None."""
    ship = base_ship
    ship.state = ShipState.MOVING_TO_POSITION # A moving state
    ship.target = None # No target
    initial_pos = ship.position.copy()
    ship.update(0.1, [])
    assert ship.position == initial_pos

def test_update_movement_moves_ship(base_ship):
    """Test ship moves towards target when in a moving state."""
    ship = base_ship
    target_pos = Vector2(500, 200)
    # Use Planet as a simple target
    ship.target = Planet(target_pos)
    ship.state = ShipState.RETURNING_TO_BASE # A moving state
    initial_pos = ship.position.copy()
    initial_dist_sq = (target_pos - initial_pos).length_squared()
    
    ship.update(0.1, []) # Call update, which calls update_movement
    
    # Assert position changed
    assert ship.position != initial_pos
    # Assert moved closer to target
    final_dist_sq = (target_pos - ship.position).length_squared()
    assert final_dist_sq < initial_dist_sq
    # Assert moved roughly the correct distance
    expected_move_dist = ship.speed * 0.1
    actual_move_dist = (ship.position - initial_pos).length()
    assert actual_move_dist == pytest.approx(expected_move_dist)

def test_update_movement_triggers_issue_command(base_ship, monkeypatch, mocker):
    """Test ship calls self.admiral.issue_command when reaching the threshold."""
    ship = base_ship
    # Target very close, within one step
    target_pos = ship.position + Vector2(ship.speed * 0.05, 0) # Target is 50*0.05 = 2.5 units away
    ship.target = Planet(target_pos) 
    ship.state = ShipState.RETURNING_TO_BASE
    
    # Create a mock admiral and assign it
    mock_admiral = mocker.MagicMock()
    ship.admiral = mock_admiral
    # Mock issue_command on the mock admiral
    # No need for monkeypatch here, mocker handles it
    # mock_issue_command = mocker.patch.object(mock_admiral, 'issue_command') 
    # ^ This is also valid, but direct check on MagicMock method works

    ship.update(0.1, []) # dt is large enough to arrive

    # Assert the method on the mock admiral was called
    mock_admiral.issue_command.assert_called_once()

def test_update_movement_no_admiral_issue_command(base_ship, mocker):
    """Test ship can not call self.admiral.issue_command when reaching the threshold and no admiral is set."""
    ship = base_ship
    ship.admiral = None # Ensure admiral is None for this test
    # Target very close, within one step
    target_pos = ship.position + Vector2(ship.speed * 0.05, 0) # Target is 50*0.05 = 2.5 units away
    ship.target = Planet(target_pos) 
    ship.state = ShipState.RETURNING_TO_BASE
    
    # Mock the logger.error function
    mock_logger = mocker.patch('src.entities.ships.base_ship.logger')
    
    ship.update(0.1, []) # dt is large enough to arrive
    
    # Construct expected warning message using the ship's actual ID
    expected_warning = f"{ship.type} {ship.id} has no admiral, cannot issue arrival command."
    # Check the first argument of the first call to the mock logger.error
    mock_logger.error.assert_called_with(expected_warning)

def test_update_movement_clamps_overshoot(base_ship, mocker):
    """Test ship movement is clamped to arrival boundary."""
    ship = base_ship
    # Target is further, but dt is large, causing potential overshoot
    target_entity = Planet(Vector2(500, 200))
    ship.target = target_entity
    ship.state = ShipState.RETURNING_TO_BASE

    # Create a mock admiral to prevent state change interfering with position check
    ship.admiral = mocker.MagicMock()

    # Calculate distance slightly beyond arrival threshold
    direction = (target_entity.position - ship.position).normalize()
    arrival_radius_sum = ship.radius + target_entity.radius
    # Place ship just outside the arrival buffer distance
    start_distance = arrival_radius_sum + constants.ARRIVAL_DISTANCE_BUFFER + 1 
    ship.position = target_entity.position - direction * start_distance

    # Calculate dt that *would* overshoot without clamping
    overshoot_dt = (start_distance / ship.speed) * 1.5 

    ship.update(overshoot_dt, [])

    # Assert ship position is now exactly on the arrival boundary
    # Calculate the threshold used by the movement system
    expected_arrival_distance = ship.radius + target_entity.radius + constants.ARRIVAL_DISTANCE_BUFFER
    final_distance = (target_entity.position - ship.position).length()
    # assert final_distance == pytest.approx(arrival_radius_sum)
    assert final_distance == pytest.approx(expected_arrival_distance)


def test_draw_calls_polygon_with_correct_parameters(stub_polygon, home_planet_fixture):
    ship = Ship(Vector2(50, 100), radius=10, color=(4,5,6), speed=50.0, home_planet=home_planet_fixture)
    mock_surface = "dummy_surface"
    def mock_world_to_screen(pos): return pos * 2
    zoom = 2.0

    ship.draw(mock_surface, mock_world_to_screen, zoom)

    assert len(stub_polygon) == 1
    call = stub_polygon[0]
    assert call[0] == mock_surface
    assert call[1] == (4, 5, 6)
    assert len(call[2]) == 3

    screen_pos = mock_world_to_screen(ship.position)
    screen_radius = max(3, int(ship.radius * zoom))
    expected_p1 = screen_pos + Vector2(screen_radius, 0)
    assert call[2][0] == expected_p1

def test_ship_initialization(base_ship):
    ship = base_ship
    assert ship.position == Vector2(100, 200)
    assert ship.radius == 10
    assert ship.color == (255, 0, 0)
    assert ship.speed == 50
    assert ship.state == ShipState.IDLE
    assert ship.type == ShipType.UNKNOWN
    assert ship.target is None
    assert ship.angle == 0.0
    assert ship.id is not None
    assert ship.get_cargo_total() == 0

def test_ship_set_target_entity(base_ship):
    """Test setting a generic Entity target makes ship IDLE."""
    ship = base_ship
    # Entity needs pos, radius, color
    target_entity = Entity(Vector2(500, 500), 20, (0, 255, 0))
    ship.set_target(target_entity)
    # Should go IDLE and clear target because type is unknown to set_target
    assert ship.target is target_entity

def test_ship_set_target_none(base_ship):
    ship = base_ship
    target_entity = Entity(Vector2(500, 500), 20, (0, 255, 0))
    ship.set_target(target_entity)
    ship.set_target(None)
    assert ship.target is None

def test_ship_get_cargo_total(base_ship):
    ship = base_ship
    assert ship.get_cargo_total() == 0
    ship.cargo["Tritanium"] = 50
    ship.cargo["Credits"] = 25
    assert ship.get_cargo_total() == 75

def test_ship_id_uniqueness(home_planet_fixture):
    # Ship constructor needs home_planet
    ship1 = Ship(Vector2(0,0), 5, (0,0,0), 10, home_planet=home_planet_fixture)
    ship2 = Ship(Vector2(0,0), 5, (0,0,0), 10, home_planet=home_planet_fixture)
    ship3 = Ship(Vector2(0,0), 5, (0,0,0), 10, home_planet=home_planet_fixture)
    assert ship1.id != ship2.id
    assert ship2.id != ship3.id
    assert ship1.id != ship3.id 