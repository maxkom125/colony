import math
import pytest
from pygame.math import Vector2
from src.systems.movement_system import update_ship_movement
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.ships.mining_ship import MiningShip

# A simple mock obstacle with position and radius
class DummyObstacle:
    def __init__(self, x, y, radius):
        self.position = Vector2(x, y)
        self.radius = radius


def test_no_target_returns_current_state():
    ship = ScannerShip(Vector2(10, 20), angle=0.5)
    ship.position = Vector2(10, 20)
    ship.angle = 0.5
    ship.target = None

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=1.0, obstacles=[])

    assert new_pos == ship.position
    assert new_angle == ship.angle
    assert arrived is False


def test_arrival_to_asteroid():
    asteroid = Asteroid(Vector2(0, 0), radius=5, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), angle=1.0)
    ship.set_target(asteroid)

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=1.0, obstacles=[asteroid])

    assert new_pos == Vector2(0, 0)
    assert new_angle == ship.angle
    assert arrived is True


def test_arrival_to_planet():
    planet = Planet(Vector2(0, 0), radius=10, color=(0, 0, 0))
    ship = MiningShip(Vector2(0, 0), angle=2.0)
    ship.set_target(planet)

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=1.0, obstacles=[planet])

    assert new_pos == Vector2(0, 0)
    assert new_angle == ship.angle
    assert arrived is True


def test_direct_movement_no_obstacles():
    # Target far enough to not arrive immediately
    asteroid = Asteroid(Vector2(100, 0), radius=1, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), angle=0.0)
    ship.set_target(asteroid)

    dt = 1.0
    new_pos, new_angle, arrived = update_ship_movement(ship, dt=dt, obstacles=[])

    # Movement should be directly towards the target
    expected_direction = (asteroid.position - Vector2(0, 0)).normalize()
    expected_pos = Vector2(0, 0) + expected_direction * ship.speed * dt

    assert new_pos == expected_pos
    assert new_angle == pytest.approx(math.atan2(expected_direction.y, expected_direction.x), abs=1e-6)
    assert arrived is False


def test_avoidance_maneuver_changes_direction():
    # Place target ahead
    asteroid = Asteroid(Vector2(100, 0), radius=1, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), angle=0.0)
    ship.set_target(asteroid)

    # Obstacle directly in path at x=50
    obstacle = DummyObstacle(50, 0, radius=10)
    dt = 1.0
    new_pos, new_angle, arrived = update_ship_movement(ship, dt=dt, obstacles=[obstacle, asteroid])

    # Avoidance should steer tangentially (downwards in this scenario)
    # Expect movement in negative y-direction
    assert new_pos.x == pytest.approx(0.0, abs=1e-6)
    assert new_pos.y == pytest.approx(-ship.speed * dt, abs=1e-6)
    assert new_angle == pytest.approx(-math.pi / 2, abs=1e-6)
    assert arrived is False


def test_update_ship_movement_unknown_target_type():
    # If target is not an Asteroid or Planet, movement should be no-op
    ship = ScannerShip(Vector2(1, 1), angle=1.23)
    ship.position = Vector2(1, 1)
    ship.angle = 1.23
    class Dummy: pass
    ship.target = Dummy()

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=1.0, obstacles=[])
    assert new_pos == ship.position
    assert new_angle == ship.angle
    assert arrived is False


def test_avoidance_when_obstacle_at_ship_position():
    # If obstacle center coincides with ship, fallback avoidance tangential to the target (to the right)
    asteroid = Asteroid(Vector2(100, 0), radius=1, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), angle=0)
    ship.set_target(asteroid)
    # Place a blocking obstacle at the ship's exact position
    obstacle = DummyObstacle(0, 0, radius=10)
    dt = 1.0
    new_pos, new_angle, arrived = update_ship_movement(
        ship, dt=dt, obstacles=[obstacle, asteroid]
    )
    # Expect movement to the right (positive x) and angle pointing right (0 radians)
    assert new_pos.x == pytest.approx(ship.speed * dt)
    assert new_pos.y == pytest.approx(0.0)
    assert new_angle == pytest.approx(0.0)
    assert arrived is False


def test_degenerate_zero_length_move_vector(monkeypatch):
    import src.constants as c
    # Force arrival threshold to zero to bypass early arrival
    monkeypatch.setattr(c, 'ARRIVAL_DISTANCE_BUFFER', 0)
    # Asteroid at same position with zero radius
    asteroid = Asteroid(Vector2(0, 0), radius=0, color=(0, 0, 0))
    ship = ScannerShip(Vector2(0, 0), angle=0)
    ship.set_target(asteroid)

    new_pos, new_angle, arrived = update_ship_movement(ship, dt=1.0, obstacles=[])
    # Should fall into degenerate branch: no movement, no arrival
    assert new_pos == ship.position
    assert new_angle == ship.angle
    assert arrived is False 