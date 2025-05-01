import math
import pytest
from pygame.math import Vector2
from src.systems.movement_system import update_ship_movement
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.ships.mining_ship import MiningShip
from src import constants # Import constants for arrival buffer

# A simple mock obstacle with position and radius
class DummyObstacle:
    def __init__(self, x: float, y: float, radius: float):
        self.position = Vector2(x, y)
        self.radius = radius


def test_no_target_returns_current_state() -> None:
    """Test that ship doesn't move without a target."""
    ship = ScannerShip(Vector2(10, 20), home_planet=None) # Home planet irrelevant here
    ship.position = Vector2(10, 20)
    ship.angle = 0.5
    ship.target = None

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=1.0, obstacles=[])

    assert new_pos == ship.position
    assert new_angle == ship.angle
    assert arrived is False


def test_arrival_to_asteroid() -> None:
    """Test arrival when ship starts just within the threshold of an asteroid."""
    asteroid = Asteroid(Vector2(100, 100), radius=10, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), home_planet=None) # Home planet irrelevant

    # Position ship just inside arrival threshold
    arrival_dist = ship.radius + asteroid.radius + constants.ARRIVAL_DISTANCE_BUFFER
    start_pos = asteroid.position + Vector2(arrival_dist * 0.9, 0) # 90% of the way
    ship.position = start_pos
    ship.angle = math.pi # Pointing left initially

    ship.set_target(asteroid)

    # Use small dt to ensure it doesn't overshoot if arrival check fails
    new_pos, new_angle, arrived = update_ship_movement(ship, dt=0.1, obstacles=[])

    assert arrived is True
    # Position and angle shouldn't change upon arrival detection
    assert new_pos == start_pos
    assert new_angle == ship.angle


def test_arrival_to_planet() -> None:
    """Test arrival when ship starts just within the threshold of a planet."""
    planet = Planet(Vector2(50, 50), radius=20, color=(0, 0, 0))
    ship = MiningShip(Vector2(0, 0), home_planet=planet) # Home planet is relevant

    # Position ship just inside arrival threshold
    arrival_dist = ship.radius + planet.radius + constants.ARRIVAL_DISTANCE_BUFFER
    start_pos = planet.position - Vector2(0, arrival_dist * 0.95) # 95% of the way, from below
    ship.position = start_pos
    ship.angle = math.pi / 2 # Pointing up initially

    ship.set_target(planet)

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=0.1, obstacles=[])

    assert arrived is True
    # Position and angle shouldn't change upon arrival detection
    assert new_pos == start_pos
    assert new_angle == ship.angle


def test_direct_movement_no_obstacles_reaches_target() -> None:
    """Test straight movement towards a target without obstacles."""
    # Target far enough to not arrive immediately
    target_pos = Vector2(100, 0)
    asteroid = Asteroid(target_pos, radius=1, color=(0, 0, 0))
    start_pos = Vector2(0, 0)
    ship = ScannerShip(start_pos, home_planet=None)
    ship.position = start_pos
    ship.angle = 0.0
    ship.set_target(asteroid)

    dt = 1.0
    new_pos, new_angle, arrived = update_ship_movement(ship, dt=dt, obstacles=[])

    # Movement should be directly towards the target
    expected_direction = (target_pos - start_pos).normalize()
    not_expected_pos = start_pos + expected_direction * ship.speed * dt
    # Movement should be less than expected as ship reaches target

    assert new_pos != start_pos # Ensure position actually changed
    assert new_pos.x != pytest.approx(not_expected_pos.x)
    assert new_pos.y == pytest.approx(not_expected_pos.y)

    # calculate at which point ship should have arrived
    expected_pos = target_pos - expected_direction * (ship.radius + asteroid.radius + constants.ARRIVAL_DISTANCE_BUFFER)
    assert new_pos.x == pytest.approx(expected_pos.x)
    assert new_pos.y == pytest.approx(expected_pos.y)
    assert new_angle == pytest.approx(math.atan2(expected_direction.y, expected_direction.x), abs=1e-6)
    assert arrived is True


def test_direct_movement_no_obstacles() -> None:
    """Test straight movement towards a target without obstacles."""
    # Target far enough to not arrive immediately
    target_pos = Vector2(300, 0)
    asteroid = Asteroid(target_pos, radius=1, color=(0, 0, 0))
    start_pos = Vector2(0, 0)
    ship = ScannerShip(start_pos, home_planet=None)
    ship.position = start_pos
    ship.angle = 0.0
    ship.set_target(asteroid)

    dt = 1.0
    new_pos, new_angle, arrived = update_ship_movement(ship, dt=dt, obstacles=[])

    # Movement should be directly towards the target
    expected_direction = (target_pos - start_pos).normalize()
    expected_pos = start_pos + expected_direction * ship.speed * dt

    assert new_pos != start_pos # Ensure position actually changed
    assert new_pos.x == pytest.approx(expected_pos.x)
    assert new_pos.y == pytest.approx(expected_pos.y)
    assert new_angle == pytest.approx(math.atan2(expected_direction.y, expected_direction.x), abs=1e-6)
    assert arrived is False


def test_avoidance_maneuver_changes_direction() -> None:
    """Test that the ship alters course to avoid a direct obstacle."""
    # Place target ahead
    asteroid = Asteroid(Vector2(200, 0), radius=1, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), home_planet=None)
    ship.position = Vector2(0, 0)
    ship.angle = 0.0
    ship.set_target(asteroid)

    # Obstacle directly in path at x=50
    obstacle = DummyObstacle(100, 0, radius=10)
    dt = 1.0
    # Provide the target itself as an obstacle to be ignored by avoidance check
    new_pos, new_angle, arrived = update_ship_movement(ship, dt=dt, obstacles=[obstacle]) # Target implicitly ignored

    # Avoidance should steer tangentially. Based on movement_system logic:
    # Obstacle is at (100,0). Ship at (0,0). Vector from obstacle = (-100, 0). Normalize = (-1, 0).
    # Tangent 1 = (-1,0).rotate(90) = (0, -1)
    # Tangent 2 = (-1,0).rotate(-90) = (0, 1)
    # Target direction = (1, 0).
    # Dot1 = (0, -1) . (1, 0) = 0
    # Dot2 = (0, 1) . (1, 0) = 0
    # dot1 >= dot2 is true, so move_vector = tangent1 = (0, -1)
    # Expected position is (0, -ship.speed * dt), angle is atan2(-1, 0) = -pi/2
    expected_pos = Vector2(0, -ship.speed * dt)

    assert new_pos.x == pytest.approx(expected_pos.x, abs=1e-6)
    assert new_pos.y == pytest.approx(expected_pos.y, abs=1e-6)
    assert new_angle == pytest.approx(-math.pi / 2, abs=1e-6)
    assert arrived is False


def test_update_ship_movement_unknown_target_type() -> None:
    """Test movement system handles non-entity targets gracefully."""
    # If target is not an Asteroid or Planet, movement should be no-op
    ship = ScannerShip(Vector2(1, 1), home_planet=None)
    ship.position = Vector2(1, 1)
    ship.angle = 1.23
    class DummyTarget: pass
    ship.target = DummyTarget() # Assign an unsupported type

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=1.0, obstacles=[])
    assert new_pos == ship.position
    assert new_angle == ship.angle
    assert arrived is False


def test_avoidance_when_obstacle_at_ship_position() -> None:
    """Test avoidance logic when the obstacle is exactly at the ship's position."""
    # Target to the right
    asteroid = Asteroid(Vector2(300, 0), radius=1, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), home_planet=None)
    ship.position = Vector2(0, 0)
    ship.angle = 0
    ship.set_target(asteroid)

    # Place a blocking obstacle at the ship's exact position
    obstacle = DummyObstacle(0, 0, radius=10)
    dt = 1.0
    new_pos, new_angle, arrived = update_ship_movement(
        ship, dt=dt, obstacles=[obstacle] # Target implicitly ignored
    )
    # Based on movement_system logic for this edge case:
    # avoid_direction defaults to (0, 1) -> up
    # tangent1 = (0, 1).rotate(90) = (-1, 0)
    # tangent2 = (0, 1).rotate(-90) = (1, 0)
    # target_direction = (1, 0)
    # dot1 = (-1, 0) . (1, 0) = -1
    # dot2 = (1, 0) . (1, 0) = 1
    # dot1 >= dot2 is false -> move_vector = tangent2 = (1, 0) -> right
    # Expected position = (ship.speed * dt, 0), angle = atan2(0, 1) = 0.0
    expected_pos = Vector2(ship.speed * dt, 0)

    assert new_pos.x == pytest.approx(expected_pos.x, abs=1e-6)
    assert new_pos.y == pytest.approx(expected_pos.y, abs=1e-6)
    assert new_angle == pytest.approx(0.0, abs=1e-6)
    assert arrived is False


def test_degenerate_zero_length_move_vector(monkeypatch) -> None:
    """Test the case where the target is exactly at the ship's position."""
    # Force arrival threshold to zero to bypass early arrival check
    monkeypatch.setattr(constants, 'ARRIVAL_DISTANCE_BUFFER', -1000) # Ensure target isn't arrived
    # Asteroid at same position with zero radius
    asteroid = Asteroid(Vector2(0, 0), radius=0, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), home_planet=None)
    ship.position = Vector2(0, 0)
    ship.angle = 0
    ship.set_target(asteroid)

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=1.0, obstacles=[])
    # Should fall into degenerate branch: distance_to_target is zero,
    # norm_target_vector is (0,0), move_vector is (0,0).
    # Final block results in no position change, no angle change, arrived=False.
    assert new_pos == ship.position
    assert new_angle == ship.angle
    assert arrived is False 