import pygame
from pygame.math import Vector2
from .. import constants

# Import types for hinting
from ..entities.planet import Planet
from ..entities.asteroid import Asteroid
from ..entities.ships.base_ship import Spaceship
from ..camera.camera import Camera # Import Camera for type hint

# --- Main Drawing Function ---

def draw_frame(
    screen,
    font,
    camera: Camera, # Accept Camera object
    planet: Planet,
    asteroids: list[Asteroid],
    ships: list[Spaceship],
    stars: list[tuple[Vector2, float]],
):
    """Draws a single frame of the game world (excluding HUD)."""

    screen.fill(constants.BLACK)

    # --- Draw Background Stars ---
    for star_pos, star_radius in stars:
        # Use camera method for coordinate conversion
        screen_pos = camera.world_to_screen(star_pos)
        # Use camera zoom for scaling
        scaled_radius = max(1, int(star_radius * camera.zoom))
        # Basic culling
        if (
            -scaled_radius < screen_pos.x < constants.SCREEN_WIDTH + scaled_radius
            and -scaled_radius < screen_pos.y < constants.SCREEN_HEIGHT + scaled_radius
        ):
            pygame.draw.circle(
                screen, constants.STAR_COLOR, screen_pos, scaled_radius
            )

    # --- Draw Game Elements ---
    # Entity draw methods expect a callable for world_to_screen and the zoom level.
    # Pass the camera's method and zoom attribute directly.
    planet.draw(screen, camera.world_to_screen, camera.zoom)
    for asteroid in asteroids:
        asteroid.draw(screen, camera.world_to_screen, camera.zoom, font)
    for ship in ships:
        ship.draw(screen, camera.world_to_screen, camera.zoom)
        # Draw target line
        if ship.target and hasattr(ship.target, "position"):
            start_screen = camera.world_to_screen(ship.position)
            end_screen = camera.world_to_screen(ship.target.position)
            pygame.draw.line(
                screen, constants.TARGET_LINE_COLOR, start_screen, end_screen, 1
            ) 