import pytest
import pygame
from pygame.math import Vector2
from src.rendering.renderer import draw_frame
from src.camera.camera import Camera
from src import constants

# Dummy screen to capture fill calls
class DummyScreen:
    def __init__(self):
        self.filled = None
    def fill(self, color):
        self.filled = color

# Dummy entities with draw method that does nothing
class DummyPlanet:
    def __init__(self):
        self.draw_calls = []
    def draw(self, screen, world_to_screen, zoom):
        self.draw_calls.append((screen, zoom))

class DummyAsteroid:
    def __init__(self):
        self.draw_calls = []
    def draw(self, screen, world_to_screen, zoom, font):
        self.draw_calls.append((screen, zoom, font))

class DummyShip:
    def __init__(self, position, target=None):
        self.position = position
        self.target = target
        self.draw_calls = []
    def draw(self, screen, world_to_screen, zoom):
        self.draw_calls.append((screen, zoom))

@pytest.fixture(autouse=True)
def init_pygame(monkeypatch):
    # Initialize pygame if needed and stub draw functions
    pygame.display.init()
    # Capture calls to pygame.draw.circle and line
    calls = {'circle': [], 'line': []}
    def fake_circle(surface, color, pos, radius):
        calls['circle'].append((color, pos, radius))
    def fake_line(surface, color, start, end, width):
        calls['line'].append((color, start, end, width))
    monkeypatch.setattr(pygame.draw, 'circle', fake_circle)
    monkeypatch.setattr(pygame.draw, 'line', fake_line)
    return calls


def test_draw_frame_fills_screen(init_pygame):
    screen = DummyScreen()
    font = None
    camera = Camera()
    planet = DummyPlanet()
    asteroids = []
    ships = []
    stars = []

    draw_frame(screen, font, camera, planet, asteroids, ships, stars)

    assert screen.filled == constants.BLACK


def test_draw_frame_stars_and_culling(init_pygame):
    screen = DummyScreen()
    font = None
    camera = Camera()
    planet = DummyPlanet()
    asteroids = []
    ships = []
    # One star inside, one outside
    stars = [ (Vector2(0, 0), 1.0), (Vector2(-10000, -10000), 1.0) ]

    draw_frame(screen, font, camera, planet, asteroids, ships, stars)

    # Only one star should be drawn
    circle_calls = init_pygame['circle']
    assert len(circle_calls) == 1
    color, pos, radius = circle_calls[0]
    assert color == constants.STAR_COLOR
    assert radius == max(1, int(1.0 * camera.zoom))
    # pos should be centered at screen center
    center = Vector2(constants.SCREEN_WIDTH/2, constants.SCREEN_HEIGHT/2)
    assert pos == center


def test_draw_frame_lines(init_pygame):
    screen = DummyScreen()
    font = None
    camera = Camera()
    planet = DummyPlanet()
    asteroids = []
    # Create a ship with a target position
    target = type('T', (), {'position': Vector2(10, 0)})()
    ship = DummyShip(position=Vector2(0, 0), target=target)
    ships = [ship]
    stars = []

    draw_frame(screen, font, camera, planet, asteroids, ships, stars)

    # Line should be drawn between ship and target
    line_calls = init_pygame['line']
    assert len(line_calls) == 1
    color, start, end, width = line_calls[0]
    assert color == constants.TARGET_LINE_COLOR
    # start and end positions are world_to_screen of positions
    assert start == camera.world_to_screen(ship.position)
    assert end == camera.world_to_screen(target.position)
    assert width == 1


def test_entity_draw_methods_called(init_pygame):
    screen = DummyScreen()
    font = object()
    camera = Camera()
    planet = DummyPlanet()
    ast = DummyAsteroid()
    ship = DummyShip(position=Vector2(1,1))

    draw_frame(screen, font, camera, planet, [ast], [ship], [])

    # planet.draw called once
    assert len(planet.draw_calls) == 1
    # asteroid.draw called with font
    assert len(ast.draw_calls) == 1
    _, zoom, f = ast.draw_calls[0]
    assert zoom == camera.zoom
    assert f is font
    # ship.draw called once
    assert len(ship.draw_calls) == 1 