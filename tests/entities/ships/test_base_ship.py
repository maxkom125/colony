import pytest
import pygame
from pygame.math import Vector2
from src.entities.ships.base_ship import Spaceship
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.enums import ShipState
from src import constants

@pytest.fixture(autouse=True)
def stub_polygon(monkeypatch):
    calls = []
    def fake_polygon(surface, color, points):
        calls.append((surface, color, points))
    monkeypatch.setattr(pygame.draw, 'polygon', fake_polygon)
    return calls


def test_get_cargo_total_initial_zero():
    ship = Spaceship(Vector2(0, 0), size=10, color=(1, 2, 3), angle=0)
    assert ship.get_cargo_total() == 0


def test_set_target_none_resets_state_and_target():
    ship = Spaceship(Vector2(0, 0), size=10, color=(1, 2, 3), angle=0)
    ship.target = Asteroid(Vector2(1,1), radius=1, color=(0,0,0))
    ship.state = ShipState.MOVING_TO_ASTEROID

    ship.set_target(None)
    assert ship.state == ShipState.IDLE
    assert ship.target is None


def test_set_target_asteroid_sets_moving_and_resets_timers():
    asteroid = Asteroid(Vector2(5, 5), radius=2, color=(0,0,0))
    ship = Spaceship(Vector2(0, 0), size=10, color=(1,2,3), angle=0)
    # Set some timers
    ship.scan_timer = 5.0
    ship.mining_timer = 5.0
    ship.dumping_timer = 5.0

    ship.set_target(asteroid)
    assert ship.state == ShipState.MOVING_TO_ASTEROID
    assert ship.target is asteroid
    assert ship.scan_timer == 0.0
    assert ship.mining_timer == 0.0
    assert ship.dumping_timer == 0.0


def test_set_target_planet_sets_returning_and_resets_timers():
    planet = Planet(Vector2(0, 0), radius=3, color=(0,1,2))
    ship = Spaceship(Vector2(0, 0), size=10, color=(1,2,3), angle=0)
    ship.scan_timer = ship.mining_timer = ship.dumping_timer = 5.0

    ship.set_target(planet)
    assert ship.state == ShipState.RETURNING_TO_BASE
    assert ship.target is planet
    assert ship.scan_timer == 0.0
    assert ship.mining_timer == 0.0
    assert ship.dumping_timer == 0.0


def test_set_target_unknown_sets_idle_and_resets_timers(monkeypatch):
    class Dummy: pass
    dummy = Dummy()
    ship = Spaceship(Vector2(0, 0), size=10, color=(1,2,3), angle=0)
    ship.scan_timer = ship.mining_timer = ship.dumping_timer = 5.0
    # Capture print to avoid noise
    monkeypatch.setattr('builtins.print', lambda *a, **k: None)
    ship.set_target(dummy)
    assert ship.state == ShipState.IDLE
    assert ship.target is dummy
    assert ship.scan_timer == 0.0
    assert ship.mining_timer == 0.0
    assert ship.dumping_timer == 0.0


def test_handle_arrival_resets_state_and_clears_target():
    ship = Spaceship(Vector2(0, 0), size=10, color=(1,2,3), angle=0)
    ship.target = Asteroid(Vector2(1,1), radius=1, color=(0,0,0))
    ship.state = ShipState.MOVING_TO_ASTEROID

    ship.handle_arrival(Planet(Vector2(0,0), radius=1, color=(0,0,0)))
    assert ship.state == ShipState.IDLE
    assert ship.target is None


def test_update_actions_base_noop():
    ship = Spaceship(Vector2(0, 0), size=10, color=(1,2,3), angle=0)
    ship.state = ShipState.MINING
    ship.scan_timer = 1.0
    ship.mining_timer = 2.0
    ship.dumping_timer = 3.0

    ship.update_actions(1.0)
    assert ship.state == ShipState.MINING
    assert ship.scan_timer == 1.0
    assert ship.mining_timer == 2.0
    assert ship.dumping_timer == 3.0


def test_draw_calls_polygon_with_correct_parameters(stub_polygon):
    ship = Spaceship(Vector2(0, 0), size=10, color=(4,5,6), angle=0)
    surface = object()
    def w2s(v): return Vector2(v.x, v.y)

    ship.draw(surface, w2s, zoom_level=1.0)
    calls = stub_polygon
    assert len(calls) == 1
    surf, color, points = calls[0]
    assert surf is surface
    assert color == ship.color
    assert isinstance(points, (list, tuple))
    assert len(points) == 3 