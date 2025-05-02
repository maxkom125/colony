import pygame
import sys

# Adjust imports for new structure
from src import constants
import random  # Import random module
import math  # Import math for trigonometric functions
from pygame.math import Vector2  # Import Vector2

# Import specific entity classes
from src.entities.planet import Planet
from src.entities.asteroid import Asteroid
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.ships.mining_ship import MiningShip

# Import the enum
from src.enums import ShipState

# from src.utils import find_nearest_asteroid # No longer needed here directly
# Import system modules
from src.systems import ai_system  # Import from new location
from src.systems import movement_system  # Import from new location
from src.systems import construction_system  # Import the new construction system
from src import hud  # Import the renamed hud module
from src.rendering import renderer  # Import the new renderer module
from src.camera.camera import Camera  # Import the new Camera class

# Import Fleet
from src.fleet import Fleet

# --- Global Camera State --- (REMOVED)
# camera_offset = Vector2(0, 0)
# zoom_level = 1.0

# from src.enums import ShipState # Keep this import

# --- Helper Functions ---
# (Coordinate helpers moved to renderer.py)

# --- Game Logic Helpers (Defined within main scope or separate module) ---
# (try_build_ship moved inside main())


def main():
    # global camera_offset, zoom_level  # REMOVED Globals

    # Initialize Pygame
    pygame.init()
    # Initialize Font
    try:
        ui_font = pygame.font.SysFont(None, constants.UI_FONT_SIZE)
    except Exception as e:
        print(f"Error initializing font: {e}")
        ui_font = pygame.font.Font(None, 30)  # Fallback basic font

    # Screen setup
    try:
        # screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Try fullscreen
        # Update constants with actual screen size if fullscreen is used
        constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = screen.get_size()
        print(f"Screen size set to: {constants.SCREEN_WIDTH}x{constants.SCREEN_HEIGHT}")
    except pygame.error as e:
        print(f"Error setting display mode: {e}. Falling back to windowed.")
        constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = 1280, 720  # Default fallback
        screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))

    pygame.display.set_caption(constants.GAME_TITLE)

    # Clock for controlling frame rate
    clock = pygame.time.Clock()

    # --- Create Fleet ---
    fleet = Fleet()  # Central registry

    # --- Create Camera Instance ---
    camera = Camera()

    # --- Game State Variables ---
    # (removed target assignments)

    # --- Calculate UI element rects once (using the actual font) ---
    scanner_button_rect, miner_button_rect = hud.get_construction_button_rects(ui_font)

    # --- Create Game World Objects ---
    central_planet = Planet(position=Vector2(0, 0))  # Uses constants internally
    asteroids = []
    max_gen_attempts = (
        constants.ASTEROID_COUNT * 10
    )  # Prevent infinite loop if space is too crowded
    attempts = 0
    while len(asteroids) < constants.ASTEROID_COUNT and attempts < max_gen_attempts:
        attempts += 1
        angle = random.uniform(0, 2 * math.pi)
        spawn_dist = random.uniform(
            constants.ASTEROID_SPAWN_RADIUS_MIN, constants.ASTEROID_SPAWN_RADIUS_MAX
        )
        cand_pos = Vector2(spawn_dist, 0).rotate_rad(angle)
        cand_radius = random.uniform(constants.ASTEROID_MIN_RADIUS, constants.ASTEROID_MAX_RADIUS)
        overlap = False
        for existing_asteroid in asteroids:
            if (
                cand_pos.distance_squared_to(existing_asteroid.position)
                < (cand_radius + existing_asteroid.radius + 5) ** 2
            ):
                overlap = True
                break
        if cand_pos.length_squared() < (cand_radius + constants.PLANET_RADIUS + 20) ** 2:
            overlap = True
        if not overlap:
            asteroids.append(
                Asteroid(
                    position=cand_pos,
                    radius=cand_radius,
                    color=constants.ASTEROID_COLOR,
                )
            )
    if len(asteroids) < constants.ASTEROID_COUNT:
        print(f"WARNING: Generated {len(asteroids)} asteroids...")

    # Create background stars (Generate positions in world coordinates)
    stars = []
    star_gen_radius = constants.ASTEROID_SPAWN_RADIUS_MAX * 1.5  # Generate stars a bit further out
    for _ in range(constants.STAR_COUNT):
        star_pos = Vector2(
            random.uniform(-star_gen_radius, star_gen_radius),
            random.uniform(-star_gen_radius, star_gen_radius),
        )
        star_radius = random.uniform(constants.STAR_MIN_RADIUS, constants.STAR_MAX_RADIUS)
        stars.append((star_pos, star_radius))  # Store world Vector2 and radius

    # --- Create initial ships AND add to Fleet and Admirals ---
    scanner1 = ScannerShip(
        position=Vector2(0, -constants.PLANET_RADIUS - 50), home_planet=central_planet
    )
    miner1 = MiningShip(
        position=Vector2(50, -constants.PLANET_RADIUS - 50), home_planet=central_planet
    )

    fleet.add_ship(scanner1)
    fleet.add_ship(miner1)
    # Initial miner assignments are handled by admiral logic (defaults to Random)

    # Game loop flag
    running = True
    panning = False  # Initialize panning state
    pan_start_pos = None  # Also initialize pan_start_pos
    # dragging_slider = None # Remove slider drag state

    # --- Main Game Loop ---
    while running:
        dt = clock.tick(constants.FPS) / 1000.0
        # Get current ships from fleet for rendering/global checks
        all_ships = fleet.get_all_ships()

        # --- Get assignment button rects for interaction ---
        current_assignment_buttons = hud.get_assignment_button_rects()

        # --- Recalculate total miners each frame --- (Now done inside Admiral if needed)
        # total_mining_ships = len(fleet.get_ships_by_type(MiningShip))

        # --- Event Handling ---
        mouse_pos_vec = Vector2(pygame.mouse.get_pos())  # Get mouse pos as Vector2
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False  # Allow exiting fullscreen with ESC
            elif event.type == pygame.MOUSEWHEEL:
                # Delegate zoom handling to camera object
                zoom_direction = event.y
                camera.handle_zoom(zoom_direction, mouse_pos_vec)
                # Remove old zoom logic

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # --- Check for Assignment Button Clicks ---
                    clicked_on_assignment_button = False
                    if current_assignment_buttons:
                        for category, buttons in current_assignment_buttons.items():
                            delta = 0
                            if buttons["+"] and buttons["+"].collidepoint(event.pos):
                                delta = 1
                            elif buttons["-"] and buttons["-"].collidepoint(event.pos):
                                delta = -1

                            if delta != 0:
                                # Call admiral to update targets
                                fleet.miner_admiral.adjust_ship_count_for_category(category, delta)
                                clicked_on_assignment_button = True
                                break  # Process only one button click per event
                        # REMOVED manual adjustment logic

                    if not clicked_on_assignment_button:
                        # --- Check for Build Button Clicks ---
                        if scanner_button_rect.collidepoint(event.pos):
                            new_ship = construction_system.attempt_construction(
                                central_planet, "scanner"
                            )
                            if new_ship:
                                fleet.add_ship(new_ship)  # Add to fleet
                        elif miner_button_rect.collidepoint(event.pos):
                            new_ship = construction_system.attempt_construction(
                                central_planet, "miner"
                            )
                            if new_ship:
                                fleet.add_ship(new_ship)  # Add to fleet

                elif event.button == 2:  # Panning
                    panning = True
                    pan_start_pos = mouse_pos_vec
            elif event.type == pygame.MOUSEBUTTONUP:
                # if event.button == 1: dragging_slider = None # Removed
                if event.button == 2:
                    panning = False
                    pan_start_pos = None
            elif event.type == pygame.MOUSEMOTION:
                # if dragging_slider: ... # Removed
                if panning and pan_start_pos:
                    pan_delta_screen = mouse_pos_vec - pan_start_pos
                    camera.handle_pan(pan_delta_screen)
                    pan_start_pos = mouse_pos_vec

        # --- Update Systems ---
        # Call Miner Admiral update/assignment
        fleet.give_orders(asteroids, central_planet)

        # Update individual ship states (movement, mining, scanning timers)
        fleet.update_ships(dt, [*asteroids, central_planet])

        # --- Rendering ---
        screen.fill(constants.BACKGROUND_COLOR)  # Use constants
        # Call the consolidated draw_frame function instead of individual stubs
        renderer.draw_frame(
            screen,
            ui_font,  # Pass the font needed by asteroid drawing
            camera,
            central_planet,
            asteroids,
            all_ships,  # Pass all ships
            stars,
        )

        # --- Draw HUD ---
        hud.draw_hud(screen, ui_font, fleet, central_planet, camera, all_ships)

        # Update Display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
