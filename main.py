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

# from src.utils import find_nearest_asteroid # No longer needed here directly
# Import system modules
from src import ai_systems
from src import movement_system

# --- Global Camera State --- (Moved outside main)
# We need these accessible by the helper functions
camera_offset = Vector2(0, 0)
zoom_level = 1.0


# --- Helper Functions --- (Moved outside main)
def world_to_screen(pos_vec: Vector2) -> Vector2:
    """Converts world coordinates (Vector2) to screen coordinates."""
    # Use global camera state
    screen_x = (pos_vec.x - camera_offset.x) * zoom_level + constants.SCREEN_WIDTH / 2
    screen_y = (pos_vec.y - camera_offset.y) * zoom_level + constants.SCREEN_HEIGHT / 2
    return Vector2(
        int(screen_x), int(screen_y)
    )  # Return Vector2 with integer coords for drawing


def screen_to_world(screen_pos_vec: Vector2) -> Vector2:
    """Converts screen coordinates (Vector2) to world coordinates."""
    # Use global camera state
    world_x = (
        screen_pos_vec.x - constants.SCREEN_WIDTH / 2
    ) / zoom_level + camera_offset.x
    world_y = (
        screen_pos_vec.y - constants.SCREEN_HEIGHT / 2
    ) / zoom_level + camera_offset.y
    return Vector2(world_x, world_y)


def main():
    global camera_offset, zoom_level  # Declare usage of global camera variables

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

    # Initialize Camera state (set initial offset based on screen size)
    camera_offset = Vector2(0, 0)  # Center world origin (0,0) initially
    zoom_level = 1.0  # Reset zoom level

    # Panning state variables
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
                # Zoom logic needs to update global zoom_level and adjust camera_offset
                zoom_direction = event.y
                if zoom_direction == 0:
                    continue

                old_zoom_level = zoom_level
                mouse_world_pos_before = screen_to_world(mouse_pos_vec)

                # Apply zoom
                if zoom_direction > 0:
                    zoom_level = min(constants.MAX_ZOOM, zoom_level * 1.1)
                else:
                    zoom_level = max(constants.MIN_ZOOM, zoom_level * 0.9)

                # Adjust camera offset to keep mouse world position fixed
                mouse_world_pos_after = screen_to_world(mouse_pos_vec)
                camera_offset += mouse_world_pos_before - mouse_world_pos_after

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
                # Convert screen delta to world delta (independent of zoom)
                pan_delta_world = pan_delta_screen / zoom_level
                camera_offset -= pan_delta_world  # Move camera opposite to mouse drag
                pan_start_pos = mouse_pos_vec  # Update pan start for next motion event

        # --- Prepare Data for Systems ---
        # Obstacles are the list of Asteroid objects + the Planet
        obstacles = asteroids + [central_planet]

        # --- Game Logic Phases ---

        # 1. AI Phase (Assign Tasks to Idle Ships)
        for ship in ships:
            if ship.state == "idle":
                # Use isinstance to check ship type for task assignment
                if isinstance(ship, MiningShip):
                    ai_systems.assign_miner_task(
                        ship, asteroids, central_planet
                    )  # Pass planet
                elif isinstance(ship, ScannerShip):
                    ai_systems.assign_scanner_task(ship, asteroids)
                # else: # Handle other potential ship types later
                #     pass

        # 2. Movement Phase (Update Position/Angle for Moving Ships)
        for ship in ships:
            if ship.state in ["moving_to_asteroid", "returning_to_base"]:
                # Call movement system to calculate next step
                # Note: Passing obstacles_data for now, will be refined later
                #       to pass simpler data structure as per TODO.
                # Note: movement_system currently determines target_pos and arrival_threshold
                #       based on ship.target. This will be decoupled later.
                new_pos_vec, new_angle, arrived = movement_system.update_ship_movement(
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
        screen.fill(constants.BLACK)

        # Draw background stars (Use world_to_screen)
        for star_pos, star_radius in stars:
            screen_pos = world_to_screen(star_pos)  # Convert world pos to screen pos
            scaled_radius = max(
                1, int(star_radius * zoom_level)
            )  # Scale radius by zoom
            # Basic culling: Check if the scaled circle is within screen bounds
            if (
                -scaled_radius < screen_pos.x < constants.SCREEN_WIDTH + scaled_radius
                and -scaled_radius
                < screen_pos.y
                < constants.SCREEN_HEIGHT + scaled_radius
            ):
                pygame.draw.circle(
                    screen, constants.STAR_COLOR, screen_pos, scaled_radius
                )  # Draw using int screen coords

        # Draw game elements using world_to_screen
        central_planet.draw(screen, world_to_screen, zoom_level)
        for asteroid in asteroids:
            asteroid.draw(screen, world_to_screen, zoom_level, ui_font)
        for ship in ships:
            ship.draw(screen, world_to_screen, zoom_level)
            # Draw target line using world_to_screen
            if ship.target:
                # Ensure target has position attribute (Planet or Asteroid)
                if hasattr(ship.target, "position"):
                    start_screen = world_to_screen(ship.position)
                    end_screen = world_to_screen(ship.target.position)
                    pygame.draw.line(
                        screen, constants.TARGET_LINE_COLOR, start_screen, end_screen, 1
                    )

        # Draw UI
        # ... (UI drawing logic remains the same) ...
        storage_y_offset = 10
        for resource_type, amount in central_planet.storage.items():
            color = constants.WHITE
            if resource_type == "Tritanium":
                color = constants.TRITANIUM_COLOR
            elif resource_type == "Credits":
                color = constants.CREDITS_COLOR
            elif resource_type == "Plasma":
                color = constants.PLASMA_COLOR
            text = f"{resource_type}: {int(amount)}"
            text_surface = ui_font.render(text, True, color)
            text_rect = text_surface.get_rect(topleft=(10, storage_y_offset))
            screen.blit(text_surface, text_rect)
            storage_y_offset += 20

        # Update Display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
