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
from src.systems import ai_system # Import from new location
from src.systems import movement_system # Import from new location
from src import hud # Import the renamed hud module
from src.rendering import renderer # Import the new renderer module
from src.camera.camera import Camera # Import the new Camera class

# --- Global Camera State --- (REMOVED)
# camera_offset = Vector2(0, 0)
# zoom_level = 1.0

# from src.enums import ShipState # Keep this import

# --- Helper Functions --- (REMOVED)

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
        screen = pygame.display.set_mode(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        )

    pygame.display.set_caption(constants.GAME_TITLE)

    # Clock for controlling frame rate
    clock = pygame.time.Clock()

    # --- Create Camera Instance ---
    camera = Camera()

    # Initialize Panning state variables (these are local to main loop)
    panning = False
    pan_start_pos = None

    # --- Create Game World Objects ---
    central_planet = Planet(
        position=Vector2(0, 0),
        radius=constants.PLANET_RADIUS,
        color=constants.PLANET_COLOR,
    )
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
        cand_radius = random.uniform(
            constants.ASTEROID_MIN_RADIUS, constants.ASTEROID_MAX_RADIUS
        )
        overlap = False
        for existing_asteroid in asteroids:
            if (
                cand_pos.distance_squared_to(existing_asteroid.position)
                < (cand_radius + existing_asteroid.radius + 5) ** 2
            ):
                overlap = True
                break
        if (
            cand_pos.length_squared()
            < (cand_radius + constants.PLANET_RADIUS + 20) ** 2
        ):
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
    star_gen_radius = (
        constants.ASTEROID_SPAWN_RADIUS_MAX * 1.5
    )  # Generate stars a bit further out
    for _ in range(constants.STAR_COUNT):
        star_pos = Vector2(
            random.uniform(-star_gen_radius, star_gen_radius),
            random.uniform(-star_gen_radius, star_gen_radius),
        )
        star_radius = random.uniform(
            constants.STAR_MIN_RADIUS, constants.STAR_MAX_RADIUS
        )
        stars.append((star_pos, star_radius))  # Store world Vector2 and radius

    # Create initial ships
    ships = [
        ScannerShip(
            position=Vector2(0, -constants.PLANET_RADIUS - 50), angle=-math.pi / 2
        ),  # Use ScannerShip
        MiningShip(
            position=Vector2(50, -constants.PLANET_RADIUS - 50), angle=-math.pi / 2
        ),
    ]

    # Game loop flag
    running = True

    # --- Main Game Loop ---
    while running:
        dt = clock.tick(constants.FPS) / 1000.0

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
                # Remove old zoom logic:
                # old_zoom_level = zoom_level
                # def screen_to_world_local(screen_pos_vec: Vector2) -> Vector2:
                #     ...
                # mouse_world_pos_before = screen_to_world_local(mouse_pos_vec)
                # ... apply zoom ...
                # def screen_to_world_local_after(screen_pos_vec: Vector2) -> Vector2:
                #     ...
                # mouse_world_pos_after = screen_to_world_local_after(mouse_pos_vec)
                # camera_offset += mouse_world_pos_before - mouse_world_pos_after

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2:  # Right-click for panning
                    panning = True
                    pan_start_pos = mouse_pos_vec
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    panning = False
                    pan_start_pos = None
            elif event.type == pygame.MOUSEMOTION and panning and pan_start_pos:
                pan_delta_screen = mouse_pos_vec - pan_start_pos
                # Delegate panning to camera object
                camera.handle_pan(pan_delta_screen)
                pan_start_pos = mouse_pos_vec # Update pan start for next motion event
                # Remove old pan logic:
                # pan_delta_world = pan_delta_screen / zoom_level
                # camera_offset -= pan_delta_world

        # --- Prepare Data for Systems ---
        # Obstacles are the list of Asteroid objects + the Planet
        obstacles = asteroids + [central_planet]

        # --- Game Logic Phases ---

        # 1. AI Phase (Assign Tasks to Idle Ships)
        for ship in ships:
            if ship.state == ShipState.IDLE: # Use Enum
                # Use isinstance to check ship type for task assignment
                if isinstance(ship, MiningShip):
                    ai_system.assign_miner_task( # Use new module name
                        ship, asteroids, central_planet
                    )  # Pass planet
                elif isinstance(ship, ScannerShip):
                    ai_system.assign_scanner_task(ship, asteroids) # Use new module name
                # else: # Handle other potential ship types later
                #     pass

        # 2. Movement Phase (Update Position/Angle for Moving Ships)
        for ship in ships:
            # Check state using Enum members
            if ship.state in [ShipState.MOVING_TO_ASTEROID, ShipState.RETURNING_TO_BASE]:
                # Call movement system to calculate next step
                new_pos_vec, new_angle, arrived = movement_system.update_ship_movement( # Use new module name
                    ship, dt, obstacles
                )
                # Apply results using Vector2
                ship.position = new_pos_vec
                ship.angle = new_angle

                # Handle arrival
                if arrived:
                    ship.handle_arrival(
                        central_planet
                    )  # Pass planet ref if needed by handler

        # 3. Action Phase (Update Timers, Resources for Ships)
        for ship in ships:
            ship.update_actions(dt, central_planet)  # Pass planet for dumping

        # --- Drawing Phase ---
        # Call the main drawing function from the renderer module
        # Pass the camera object instead of offset/zoom
        renderer.draw_frame(
            screen,
            ui_font,
            camera, # Pass camera object
            # camera_offset, # Removed
            # zoom_level, # Removed
            central_planet,
            asteroids,
            ships,
            stars
        )

        # --- Draw HUD using functions from hud module ---
        # HUD is drawn *after* the world frame
        hud.draw_planet_storage(screen, central_planet, ui_font)
        hud.draw_ship_statuses(screen, ships, ui_font)
        # Pass camera object to draw_zoom_level
        hud.draw_zoom_level(screen, camera, ui_font)
        # hud.draw_zoom_level(screen, zoom_level, ui_font) # Old call

        # Update Display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
