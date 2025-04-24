import pytest
import pygame
from pygame.math import Vector2
from src import constants
from src.hud import (
    get_construction_button_rects,
    draw_ship_statuses,
    draw_planet_storage,
    draw_zoom_level,
    draw_mining_priorities,
    draw_construction_buttons
)
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.ships.mining_ship import MiningShip
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.enums import ShipState

# Dummy surface to capture blit calls
class DummySurface:
    def __init__(self):
        self.calls = []  # List of (surface, position)
    def blit(self, surf, pos):
        self.calls.append((surf, pos))

# Dummy text surface to simulate font.render output
class DummyTextSurface:
    def __init__(self, text):
        self._text = text
        self._width = len(text) * 10
        self._height = 20
        self._rect = pygame.Rect(0, 0, self._width, self._height)
    def get_width(self):
        return self._width
    def get_rect(self, **kwargs):
        rect = self._rect.copy()
        if 'bottomleft' in kwargs:
            rect.bottomleft = kwargs['bottomleft']
        if 'topleft' in kwargs:
            rect.topleft = kwargs['topleft']
        if 'topright' in kwargs:
            rect.topright = kwargs['topright']
        return rect

# Dummy font to record render calls
class DummyFont:
    def __init__(self):
        self.rendered = []  # List of (text, color)
    def render(self, text, aa, color):
        self.rendered.append((text, color))
        return DummyTextSurface(text)


def test_get_construction_button_rects_positions():
    font = DummyFont()
    scanner_rect, miner_rect = get_construction_button_rects(font)
    scanner_text = "[Build Scanner (50T, 100C)]"
    miner_text = "[Build Miner (100T, 50C)]"
    padding = 20
    scanner_width = len(scanner_text) * 10
    miner_width = len(miner_text) * 10
    total_width = scanner_width + padding + miner_width
    start_x = (constants.SCREEN_WIDTH - total_width) // 2
    button_y = constants.SCREEN_HEIGHT - 40
    assert scanner_rect.bottomleft == (start_x, button_y)
    assert miner_rect.bottomleft == (start_x + scanner_width + padding, button_y)


def test_draw_ship_statuses_sparse():
    surface = DummySurface()
    font = DummyFont()
    # Setup a scanning scanner ship
    scanner = ScannerShip(Vector2(0, 0))
    asteroid = Asteroid(Vector2(1, 1), radius=1, color=(0, 0, 0))
    asteroid.id = 42
    scanner.state = ShipState.SCANNING
    scanner.target = asteroid
    scanner.scan_timer = 3.3
    # Setup a mining ship
    miner = MiningShip(Vector2(0, 0))
    miner.state = ShipState.MINING
    miner.mining_timer = 4.5
    miner.cargo = {'Tritanium': 10, 'Credits': 0, 'Plasma': 0}

    draw_ship_statuses(surface, [scanner, miner], font)
    assert len(surface.calls) == 2
    texts = [surf._text for surf, _ in surface.calls]
    # Validate scanner entry
    assert texts[0].startswith("Ship 0 (ScannerShip): SCANNING")
    assert "(Scan: 3.3s)" in texts[0]
    assert "Target ID: 42" in texts[0]
    # Validate miner entry
    assert texts[1].startswith("Ship 1 (MiningShip): MINING")
    assert "(Mine: 4.5s)" in texts[1]
    assert "Cargo: 10" in texts[1]


def test_draw_planet_storage_and_zoom_level():
    surface = DummySurface()
    font = DummyFont()
    planet = Planet(Vector2(0, 0), radius=5, color=(0, 0, 0))
    # Draw storage
    draw_planet_storage(surface, planet, font)
    storage_texts = [surf._text for surf, _ in surface.calls]
    assert storage_texts == [
        "Tritanium: 200",
        "Credits: 200",
        "Plasma: 50"
    ]
    # Draw zoom level
    surface.calls.clear()
    draw_zoom_level(surface, Camera:=__import__('src.camera.camera', fromlist=['Camera']).Camera(), font)
    zoom_texts = [surf._text for surf, _ in surface.calls]
    assert len(zoom_texts) == 1
    assert zoom_texts[0].startswith("Zoom:")


def test_draw_mining_priorities_and_construction_buttons():
    surface = DummySurface()
    font = DummyFont()
    priorities = {"Tritanium": 1.0, "Credits": 0.5}
    draw_mining_priorities(surface, priorities, font)
    # First call is title, then one per priority
    texts = [surf._text for surf, _ in surface.calls]
    assert texts[0] == "Mining Priorities:"
    assert "Tritanium: 1.0" in texts
    assert "Credits: 0.5" in texts
    # Test construction buttons draw
    surface.calls.clear()
    draw_construction_buttons(surface, font)
    btn_texts = [surf._text for surf, _ in surface.calls]
    assert btn_texts == [
        "[Build Scanner (50T, 100C)]",
        "[Build Miner (100T, 50C)]"
    ]


def test_draw_ship_statuses_returning_and_dumping_and_no_target():
    surface = DummySurface()
    font = DummyFont()
    # Returning ship without explicit target id
    scanner = ScannerShip(Vector2(0, 0))
    scanner.state = ShipState.RETURNING_TO_BASE
    scanner.target = Planet(Vector2(0, 0), radius=1, color=(0,0,0))
    # Dumping ship
    miner = MiningShip(Vector2(0, 0))
    miner.state = ShipState.DUMPING
    miner.dumping_timer = 1.2
    miner.cargo = {'Tritanium': 5, 'Credits': 3, 'Plasma': 0}
    # Idle ship with no target
    idle_ship = ScannerShip(Vector2(0, 0))
    idle_ship.state = ShipState.IDLE
    idle_ship.target = None

    draw_ship_statuses(surface, [scanner, miner, idle_ship], font)
    texts = [surf._text for surf, _ in surface.calls]
    # RETURNING_TO_BASE should show 'Target ID: Planet'
    assert 'RETURNING_TO_BASE' in texts[0]
    assert 'Target ID: Planet' in texts[0]
    # DUMPING should show dump timer and cargo
    assert 'DUMPING' in texts[1]
    assert '(Dump:' in texts[1]
    assert 'Cargo: 8' in texts[1]  # total cargo 5+3
    # IDLE with no target should not include '->'
    assert 'IDLE' in texts[2]
    assert '->' not in texts[2] 