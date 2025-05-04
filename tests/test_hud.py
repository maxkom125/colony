# DEPRECATED
# import pytest
# import pygame
# from pygame.math import Vector2
# from src import constants
# from src.hud import (
#     get_construction_button_rects,
#     draw_ship_statuses,
#     draw_planet_storage,
#     draw_zoom_level,
#     draw_miner_assignments,
#     get_assignment_button_rects,
#     draw_construction_buttons,
# )
# from src.entities.ships.scanner_ship import ScannerShip
# from src.entities.ships.mining_ship import MiningShip
# from src.entities.asteroid import Asteroid
# from src.entities.planet import Planet
# from src.entities.ships.base_ship import Ship
# from src.enums import ShipState
# from src.camera.camera import Camera
# from unittest.mock import patch, MagicMock
# from src.fleet import Fleet


# # Dummy surface to capture blit calls
# class DummySurface:
#     def __init__(self):
#         self.calls = []  # List of (surface, position)

#     def blit(self, surf, pos):
#         self.calls.append((surf, pos))


# # Dummy text surface to simulate font.render output
# class DummyTextSurface:
#     def __init__(self, text):
#         self._text = text
#         self._width = len(text) * 10
#         self._height = 20
#         self._rect = pygame.Rect(0, 0, self._width, self._height)

#     def get_width(self):
#         return self._width

#     def get_rect(self, **kwargs):
#         rect = self._rect.copy()
#         if "bottomleft" in kwargs:
#             rect.bottomleft = kwargs["bottomleft"]
#         if "topleft" in kwargs:
#             rect.topleft = kwargs["topleft"]
#         if "topright" in kwargs:
#             rect.topright = kwargs["topright"]
#         return rect


# # Dummy font to record render calls and simulate get_linesize
# class DummyFont:
#     def __init__(self):
#         self.rendered = []  # List of (text, color)

#     def render(self, text, aa, color):
#         self.rendered.append((text, color))
#         return DummyTextSurface(text)

#     def get_linesize(self):
#         return 18  # Return a plausible line size


# # Fixture to provide a mock pygame.draw module
# @pytest.fixture
# def mock_pygame_draw(monkeypatch):
#     calls = {"rect": []}

#     def fake_rect(surface, color, rect, **kwargs):
#         # Store rect as tuple for easier comparison
#         calls["rect"].append((color, (rect.left, rect.top, rect.width, rect.height), kwargs))

#     # Mock the draw module itself if it's directly imported
#     mock_draw_module = type("MockDraw", (), {"rect": fake_rect})
#     monkeypatch.setattr(pygame, "draw", mock_draw_module)
#     # If hud imports draw specifically, patch that too (might be needed)
#     try:
#         import src.hud

#         monkeypatch.setattr(src.hud.pygame, "draw", mock_draw_module)
#     except (ImportError, AttributeError):
#         pass  # Ignore if src.hud doesn't import pygame.draw that way
#     return calls


# @pytest.fixture
# def home_planet_fixture():
#     """Provides a reusable planet for ship home."""
#     return Planet(Vector2(0, 0))


# # Add miner_admiral fixture from conftest or define here if not global
# # Assuming miner_admiral fixture is available (e.g., imported or from conftest)
# @pytest.fixture
# def miner_admiral_fixture():  # Renamed to avoid conflict if imported
#     from src.systems.admirals.miner_admiral import MinerAdmiral

#     # If mocks are needed, reset them here
#     # MockMiningShip._next_id = 1
#     # MockAsteroid._next_id = 1000
#     return MinerAdmiral()


# def test_get_construction_button_rects_positions():
#     font = DummyFont()
#     scanner_rect, miner_rect = get_construction_button_rects(font)
#     scanner_text = "[Build Scanner (50T, 100C)]"
#     miner_text = "[Build Miner (100T, 50C)]"
#     padding = 20
#     scanner_width = len(scanner_text) * 10
#     miner_width = len(miner_text) * 10
#     total_width = scanner_width + padding + miner_width
#     start_x = (constants.SCREEN_WIDTH - total_width) // 2
#     button_y = constants.SCREEN_HEIGHT - 40
#     assert scanner_rect.bottomleft == (start_x, button_y)
#     assert miner_rect.bottomleft == (start_x + scanner_width + padding, button_y)


# def test_draw_ship_statuses_sparse():
#     surface = DummySurface()
#     font = DummyFont()
#     # Setup a scanning scanner ship
#     scanner = ScannerShip(Vector2(0, 0), home_planet=None)
#     asteroid = Asteroid(Vector2(1, 1), radius=1, color=(0, 0, 0))
#     asteroid.id = 42
#     scanner.state = ShipState.SCANNING
#     scanner.target = asteroid
#     scanner.scan_timer = 3.3
#     # Setup a mining ship
#     miner = MiningShip(Vector2(0, 0), home_planet=None)
#     miner.state = ShipState.MINING
#     miner.mining_timer = 4.5
#     miner.cargo = {"Tritanium": 10, "Credits": 0, "Plasma": 0}

#     draw_ship_statuses(surface, [scanner, miner], font)
#     assert len(surface.calls) == 2
#     texts = [surf._text for surf, _ in surface.calls]
#     # Validate scanner entry
#     assert texts[0].startswith("Ship 0 (ScannerShip): SCANNING")
#     assert "(Scan: 3.3s)" in texts[0]
#     # assert "Target ID: 42" in texts[0]
#     # Check for the updated target format
#     assert "Target: Asteroid 42" in texts[0]
#     # Validate miner entry
#     assert texts[1].startswith("Ship 1 (MiningShip): MINING")
#     assert "(Mine: 4.5s)" in texts[1]
#     assert "Cargo: 10" in texts[1]


# def test_draw_planet_storage_and_zoom_level():
#     surface = DummySurface()
#     font = DummyFont()
#     planet = Planet(Vector2(0, 0), radius=5, color=(0, 0, 0))
#     planet.add_resources({"Tritanium": 200, "Credits": 200, "Plasma": 50})
#     # Draw storage
#     draw_planet_storage(surface, planet, font)
#     storage_texts = [surf._text for surf, _ in surface.calls]
#     assert storage_texts == ["Tritanium: 200", "Credits: 200", "Plasma: 50"]
#     # Draw zoom level
#     surface.calls.clear()
#     draw_zoom_level(surface, Camera(), font)
#     zoom_texts = [surf._text for surf, _ in surface.calls]
#     assert len(zoom_texts) == 1
#     assert zoom_texts[0].startswith("Zoom:")


# # Use the specific admiral fixture
# def test_draw_miner_assignments(mock_pygame_draw, home_planet_fixture, miner_admiral_fixture):
#     surface = DummySurface()
#     font = DummyFont()
#     miner_admiral = miner_admiral_fixture  # Use the provided admiral instance

#     # --- Setup Ships and Add to Admiral ---
#     miner1 = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     miner1.id = 1  # Assign predictable IDs for clarity
#     miner1.state = ShipState.MOVING_TO_ASTEROID

#     miner2 = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     miner2.id = 2

#     miner3 = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     miner3.id = 3

#     miner_idle = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     miner_idle.id = 4
#     miner_idle.state = ShipState.IDLE  # Explicitly IDLE

#     scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)  # Non-miner
#     miner_returning = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     miner_returning.id = 5
#     miner_returning.set_target(home_planet_fixture)  # Make it RETURNING_TO_BASE

#     # Add miners to the admiral
#     miner_admiral.add_ship(miner1)
#     miner_admiral.add_ship(miner2)
#     miner_admiral.add_ship(miner3)
#     miner_admiral.add_ship(miner_idle)
#     miner_admiral.add_ship(miner_returning)

#     # --- Set Assignments within Admiral ---
#     # Assign miner1 and miner2 to Tritanium. Others stay in default 'Random'.
#     miner_admiral.update_ship_assignment(miner1.id, "Tritanium")
#     miner_admiral.update_ship_assignment(miner2.id, "Tritanium")
#     # miner3, miner_idle, miner_returning are implicitly in 'Random'

#     # --- Call the function with the admiral ---
#     draw_miner_assignments(surface, miner_admiral, font)

#     # --- Assertions ---
#     # Expected counts: Tritanium: 2, Credits: 0, Plasma: 0, Random: 3
#     # Idle: 1 (only miner_idle), Total Miners: 5
#     expected_renders = 1 + 4 + 1 + 1 + (4 * 2)  # Title + Categories + Idle + Total + Buttons
#     assert len(font.rendered) == expected_renders
#     rendered_texts = {text for text, color in font.rendered}

#     assert "Miner Assignments:" in rendered_texts
#     assert "Tritanium: 2" in rendered_texts
#     assert "Credits: 0" in rendered_texts
#     assert "Plasma: 0" in rendered_texts
#     assert "Random: 3" in rendered_texts  # miner3, miner_idle, miner_returning start here
#     assert "Idle: 5" in rendered_texts
#     assert "Total Miners: 5" in rendered_texts
#     # Check button text was rendered
#     assert "-" in rendered_texts
#     assert "+" in rendered_texts

#     # Check blitted surfaces (1 per render call)
#     assert len(surface.calls) == expected_renders

#     # Check drawn rects (4 categories * 2 buttons each = 8 rects)
#     rect_calls = mock_pygame_draw["rect"]
#     assert len(rect_calls) == 4 * 2

#     # Check that button rects were stored
#     stored_rects = get_assignment_button_rects()
#     assert stored_rects["Tritanium"]["+"] is not None
#     assert stored_rects["Tritanium"]["-"] is not None
#     assert stored_rects["Credits"]["+"] is not None
#     assert stored_rects["Credits"]["-"] is not None
#     assert stored_rects["Plasma"]["+"] is not None
#     assert stored_rects["Plasma"]["-"] is not None
#     assert stored_rects["Random"]["+"] is not None
#     assert stored_rects["Random"]["-"] is not None

#     # check idle count change
#     assert miner_admiral.get_idle_ship_count() == 5
#     miner1.state = ShipState.MOVING_TO_ASTEROID
#     miner2.state = ShipState.MINING
#     miner3.state = ShipState.MOVING_TO_ASTEROID
#     draw_miner_assignments(surface, miner_admiral, font)
#     assert len(font.rendered) == expected_renders * 2  # second call performed
#     rendered_texts = {text for text, color in font.rendered}
#     assert "Miner Assignments:" in rendered_texts
#     assert "Tritanium: 2" in rendered_texts
#     assert "Credits: 0" in rendered_texts
#     assert "Plasma: 0" in rendered_texts
#     assert "Random: 3" in rendered_texts  # miner3, miner_idle, miner_returning start here
#     assert "Idle: 2" in rendered_texts
#     assert "Total Miners: 5" in rendered_texts


# def test_draw_ship_statuses_returning_and_dumping_and_no_target(home_planet_fixture):
#     surface = DummySurface()
#     font = DummyFont()
#     # Returning ship without explicit target id
#     scanner = ScannerShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     scanner.state = ShipState.RETURNING_TO_BASE
#     scanner.target = home_planet_fixture
#     # Dumping ship
#     miner = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     miner.state = ShipState.DUMPING
#     miner.dumping_timer = 1.2
#     miner.cargo = {"Tritanium": 5, "Credits": 3, "Plasma": 0}
#     miner.target = None  # Dumping state target is None
#     # Idle ship with no target
#     idle_ship = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     idle_ship.state = ShipState.IDLE
#     idle_ship.target = None

#     draw_ship_statuses(surface, [scanner, miner, idle_ship], font)
#     texts = [surf._text for surf, _ in surface.calls]

#     # RETURNING_TO_BASE should show 'Target: Planet {id}'
#     # Get the expected ID from the fixture
#     expected_planet_id = home_planet_fixture.id
#     expected_target_text = f"Target: Planet {expected_planet_id}"
#     assert "RETURNING_TO_BASE" in texts[0]
#     # assert "Target ID: Planet" in texts[0]
#     assert expected_target_text in texts[0]

#     # DUMPING should show dump timer and cargo
#     assert "DUMPING" in texts[1]
#     assert "(Dump:" in texts[1]
#     assert "Cargo: 8" in texts[1]  # total cargo 5+3
#     # IDLE with no target should not include '->'
#     assert "IDLE" in texts[2]
#     assert "->" not in texts[2]


# def test_draw_construction_buttons():
#     """Test that draw_construction_buttons renders and blits the correct text."""
#     surface = DummySurface()
#     font = DummyFont()

#     draw_construction_buttons(surface, font)

#     # Check that font.render was called for both buttons
#     rendered_texts = [text for text, color in font.rendered]
#     assert "[Build Scanner (50T, 100C)]" in rendered_texts
#     assert "[Build Miner (100T, 50C)]" in rendered_texts

#     # Check that surface.blit was called twice (once for each button)
#     assert len(surface.calls) == 2
#     blitted_texts = [call[0]._text for call in surface.calls] # Get text from DummyTextSurface
#     assert "[Build Scanner (50T, 100C)]" in blitted_texts
#     assert "[Build Miner (100T, 50C)]" in blitted_texts


# # --- Test for draw_hud orchestrator --- 

# @patch("src.hud.draw_planet_storage")
# @patch("src.hud.draw_ship_statuses")
# @patch("src.hud.draw_zoom_level")
# @patch("src.hud.draw_construction_buttons")
# @patch("src.hud.draw_miner_assignments")
# def test_draw_hud_calls_sub_functions(
#     mock_draw_miner_assignments,
#     mock_draw_construction_buttons,
#     mock_draw_zoom_level,
#     mock_draw_ship_statuses,
#     mock_draw_planet_storage,
#     home_planet_fixture, # Need planet for arguments
#     miner_admiral_fixture # Need admiral for fleet
# ):
#     """Test that the main draw_hud function calls all its sub-drawing functions."""
#     # Create mock objects for arguments
#     mock_screen = DummySurface()
#     mock_font = DummyFont()
#     mock_planet = home_planet_fixture
#     mock_camera = MagicMock(spec=Camera)
#     # Create a mock Fleet containing the admiral
#     mock_fleet = MagicMock(spec=Fleet)
#     mock_fleet.miner_admiral = miner_admiral_fixture
#     mock_all_ships = [MagicMock(spec=Ship)] # Needs a list, content doesn't matter for this test

#     # Call the main HUD function
#     from src.hud import draw_hud # Import locally to ensure patches apply
#     draw_hud(mock_screen, mock_font, mock_fleet, mock_planet, mock_camera, mock_all_ships)

#     # Assert each sub-drawing function was called once with expected args
#     mock_draw_planet_storage.assert_called_once_with(mock_screen, mock_planet, mock_font)
#     mock_draw_ship_statuses.assert_called_once_with(mock_screen, mock_all_ships, mock_font)
#     mock_draw_zoom_level.assert_called_once_with(mock_screen, mock_camera, mock_font)
#     mock_draw_construction_buttons.assert_called_once_with(mock_screen, mock_font)
#     mock_draw_miner_assignments.assert_called_once_with(mock_screen, mock_fleet.miner_admiral, mock_font)


# def test_draw_ship_statuses_other_targets(home_planet_fixture):
#     """Test drawing status for ships targeting unknown objects (with/without ID)."""
#     surface = DummySurface()
#     font = DummyFont()

#     # --- Test Case 1: Target with ID (hits try block) ---
#     ship_with_target_id = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     mock_target_with_id = MagicMock()
#     mock_target_with_id.id = 999
#     ship_with_target_id.target = mock_target_with_id
#     ship_with_target_id.state = ShipState.MOVING_TO_POSITION # Any state requiring target display

#     # --- Test Case 2: Target without ID (hits except block) ---
#     ship_without_target_id = MiningShip(Vector2(0, 0), home_planet=home_planet_fixture)
#     # Create a mock that will raise AttributeError when .id is accessed
#     mock_target_without_id = MagicMock(spec=object) # spec=object ensures no default id
#     # Ensure accessing .id raises an error
#     del mock_target_without_id.id 
#     ship_without_target_id.target = mock_target_without_id
#     ship_without_target_id.state = ShipState.MOVING_TO_POSITION

#     # --- Call function with both ships ---
#     draw_ship_statuses(surface, [ship_with_target_id, ship_without_target_id], font)
#     texts = [surf._text for surf, _ in surface.calls]

#     # --- Assertions ---
#     assert len(texts) == 2
#     # Check case 1 (try block)
#     # The exact type name might vary slightly based on MagicMock internals
#     assert f"Target: <class 'unittest.mock.MagicMock'> {mock_target_with_id.id}" in texts[0]
#     # Check case 2 (except block)
#     assert "Target: Something wrong with target" in texts[1]
