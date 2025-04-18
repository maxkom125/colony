import pygame
import sys
import constants
import random # Import random module
import math   # Import math for trigonometric functions
from entities import Planet, Asteroid, Spaceship # Import Planet, Asteroid, and Spaceship classes
from entities import MiningShip # Import MiningShip

def find_nearest_asteroid(ship, asteroids):
    # Finds the nearest asteroid matching the ship's criteria (scanned/unscanned, resources)
    min_dist_sq = float('inf')
    suitable_target = None

    is_miner = isinstance(ship, MiningShip)

    for asteroid in asteroids:
        if is_miner:
            # Miner needs SCANNED asteroids with resources
            if not asteroid.scanned:
                continue
            # Check if it actually has any resources left
            has_resources = any(amount > 0 for amount in asteroid.resources.values())
            if not has_resources:
                continue
        else: # Scanner needs UNSCANNED asteroids
            if asteroid.scanned:
                continue

        # Common distance check
        dx = asteroid.world_x - ship.world_x
        dy = asteroid.world_y - ship.world_y
        dist_sq = dx*dx + dy*dy

        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            suitable_target = asteroid

    return suitable_target

def line_circle_intersection(p1, p2, circle_center, circle_radius):
    """Checks if the line segment p1-p2 intersects the circle."""
    # Use input types directly, avoid explicit float conversion unless needed
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    cx, cy = circle_center[0], circle_center[1]
    r = circle_radius
    r_sq = r * r # Pre-calculate squared radius

    # --- Bounding Box Check ---
    # Find the bounding box of the line segment
    min_x = min(x1, x2)
    max_x = max(x1, x2)
    min_y = min(y1, y2)
    max_y = max(y1, y2)

    # Check if the circle's bounding box overlaps the segment's bounding box
    if max_x < cx - r or min_x > cx + r or max_y < cy - r or min_y > cy + r:
        return False # No overlap possible

    # --- Original Intersection Logic (slightly adjusted) ---
    dx = x2 - x1
    dy = y2 - y1

    # Handle segment is a point
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return (x1 - cx)**2 + (y1 - cy)**2 <= r_sq

    fx = x1 - cx
    fy = y1 - cy

    a = dx*dx + dy*dy
    b = 2*(fx*dx + fy*dy)
    c = fx*fx + fy*fy - r_sq # Use squared radius here

    discriminant = b*b - 4*a*c

    if discriminant < 0:
        return False # No real roots
    else:
        # Avoid division by zero / very small 'a'
        if a < 1e-9:
             # Check if the point (segment) starts inside the circle
             return c <= 0

        # We have potential intersection points, need to check if they fall on the segment [0,1]
        discriminant = math.sqrt(discriminant)
        t1 = (-b - discriminant) / (2*a)
        t2 = (-b + discriminant) / (2*a)

        # Check if either intersection point parameter t is within segment bounds [0, 1]
        if (0 <= t1 <= 1) or (0 <= t2 <= 1):
            return True

        # Check case where segment is entirely within the circle
        # This happens if both t values are outside [0, 1] but the segment starts inside
        if (t1 < 0 and t2 > 1) or (t2 < 0 and t1 > 1):
             return c <= 0 # Check if start point is inside

        # Check if start or end point is exactly on the circle boundary within tolerance
        # This covers cases where the line is tangent and t might be slightly outside [0,1] due to precision
        # Check start point distance squared
        if abs(c) < 1e-9: # (x1-cx)^2 + (y1-cy)^2 - r^2 is close to 0
             return True
        # Check end point distance squared: (x2-cx)^2 + (y2-cy)^2 - r^2
        end_dist_sq = (x2-cx)**2 + (y2-cy)**2
        if abs(end_dist_sq - r_sq) < 1e-9:
             return True


        return False # No intersection on the segment

def check_path_for_obstacles(ship_pos, next_pos, obstacles, ignore_target):
    """Checks if the path segment intersects any obstacle, returning the closest one."""
    closest_obstacle = None
    min_dist_sq = float('inf')

    for obstacle in obstacles:
        if obstacle == ignore_target:
            continue

        buffer = 5 # Collision buffer
        if line_circle_intersection(ship_pos, next_pos, (obstacle.world_x, obstacle.world_y), obstacle.radius + buffer):
            dx = obstacle.world_x - ship_pos[0]
            dy = obstacle.world_y - ship_pos[1]
            dist_sq = dx*dx + dy*dy
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_obstacle = obstacle

    return closest_obstacle

def main():
    # Initialize Pygame
    pygame.init()
    # Initialize Font
    ui_font = pygame.font.SysFont(None, constants.UI_FONT_SIZE)

    # Screen setup
    screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    pygame.display.set_caption(constants.GAME_TITLE)

    # Clock for controlling frame rate
    clock = pygame.time.Clock()

    # Camera state
    # Center the camera initially on the planet (world 0,0)
    camera_offset_x = constants.SCREEN_WIDTH / 2
    camera_offset_y = constants.SCREEN_HEIGHT / 2
    initial_camera_offset_x = camera_offset_x # Store initial offset for parallax calculation
    initial_camera_offset_y = camera_offset_y
    zoom_level = 1.0
    panning = False
    pan_start_pos = None

    # Create game objects
    central_planet = Planet(0, 0, constants.PLANET_RADIUS, constants.PLANET_COLOR)
    asteroids = []
    max_gen_attempts = constants.ASTEROID_COUNT * 10 # Prevent infinite loop if space is too crowded
    attempts = 0
    while len(asteroids) < constants.ASTEROID_COUNT and attempts < max_gen_attempts:
        attempts += 1
        # Generate candidate position and radius
        angle = random.uniform(0, 2 * math.pi)
        spawn_dist = random.uniform(constants.ASTEROID_SPAWN_RADIUS_MIN, constants.ASTEROID_SPAWN_RADIUS_MAX)
        cand_x = spawn_dist * math.cos(angle)
        cand_y = spawn_dist * math.sin(angle)
        cand_radius = random.uniform(constants.ASTEROID_MIN_RADIUS, constants.ASTEROID_MAX_RADIUS)

        # Check for overlap with existing asteroids
        overlap = False
        for existing_asteroid in asteroids:
            dist_sq = (cand_x - existing_asteroid.world_x)**2 + (cand_y - existing_asteroid.world_y)**2
            min_dist = cand_radius + existing_asteroid.radius + 5 # Add a small buffer
            if dist_sq < min_dist**2:
                overlap = True
                break # Overlaps with this one, no need to check further

        # Also check overlap with central planet (optional but good practice)
        dist_to_planet_sq = cand_x**2 + cand_y**2
        min_dist_planet = cand_radius + constants.PLANET_RADIUS + 20 # Buffer from planet
        if dist_to_planet_sq < min_dist_planet**2:
            overlap = True

        # If no overlap, create and add the asteroid
        if not overlap:
            asteroids.append(Asteroid(cand_x, cand_y, cand_radius, constants.ASTEROID_COLOR))

    if len(asteroids) < constants.ASTEROID_COUNT:
        print(f"WARNING: Could only generate {len(asteroids)} non-overlapping asteroids after {max_gen_attempts} attempts.")

    # Create background stars (positions only, relative to screen initially)
    stars = []
    for _ in range(constants.STAR_COUNT):
        # Store initial screen position for parallax calculation
        stars.append((random.randint(0, constants.SCREEN_WIDTH),
                      random.randint(0, constants.SCREEN_HEIGHT)))

    # Create initial spaceship(s)
    # Place it near the planet, e.g., slightly above
    ships = [
        Spaceship(0, -constants.PLANET_RADIUS - 50, constants.SHIP_SIZE, constants.SHIP_COLOR, angle=-math.pi/2), # Original Scanner
        MiningShip(50, -constants.PLANET_RADIUS - 50, angle=-math.pi/2) # New Mining Ship (offset slightly)
    ]

    # Game loop flag
    running = True

    while running:
        # Calculate delta time (time since last frame) for physics updates
        dt = clock.tick(constants.FPS) / 1000.0 # Convert milliseconds to seconds

        # --- Event Handling ---
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Zooming with mouse wheel
            elif event.type == pygame.MOUSEWHEEL:
                zoom_direction = event.y
                if zoom_direction == 0: # Should not happen, but safety first
                    continue

                # Store old zoom
                old_zoom_level = zoom_level

                # Calculate new zoom
                zoom_delta = zoom_direction * 0.1
                new_zoom_level = max(constants.MIN_ZOOM, min(constants.MAX_ZOOM, zoom_level + zoom_delta))

                # Check if zoom actually changed
                if abs(new_zoom_level - old_zoom_level) < 1e-9:
                     continue

                # Determine the screen point that should remain fixed
                if zoom_direction > 0: # Zooming In
                    fixed_screen_point_x, fixed_screen_point_y = mouse_pos
                else: # Zooming Out
                    fixed_screen_point_x = constants.SCREEN_WIDTH / 2
                    fixed_screen_point_y = constants.SCREEN_HEIGHT / 2

                # Calculate the world coordinates corresponding to the fixed screen point BEFORE zoom
                world_x_before = (fixed_screen_point_x - camera_offset_x) / old_zoom_level
                world_y_before = (fixed_screen_point_y - camera_offset_y) / old_zoom_level

                # Calculate the new camera offset needed to keep the world point at the fixed screen point AFTER zoom
                new_camera_offset_x = fixed_screen_point_x - world_x_before * new_zoom_level
                new_camera_offset_y = fixed_screen_point_y - world_y_before * new_zoom_level

                # Apply the new zoom and offset
                zoom_level = new_zoom_level
                camera_offset_x = new_camera_offset_x
                camera_offset_y = new_camera_offset_y

            # Panning with middle mouse button
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2: # Middle mouse button
                    panning = True
                    pan_start_pos = mouse_pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    panning = False
                    pan_start_pos = None
            elif event.type == pygame.MOUSEMOTION:
                if panning and pan_start_pos:
                    dx = mouse_pos[0] - pan_start_pos[0]
                    dy = mouse_pos[1] - pan_start_pos[1]
                    camera_offset_x += dx
                    camera_offset_y += dy
                    pan_start_pos = mouse_pos # Update start for continuous panning

        # --- Camera Boundary Checks (Placeholder) ---
        # Add logic here to clamp camera_offset_x/y based on world size and zoom level
        # e.g., camera_offset_x = max(min_offset_x, min(camera_offset_x, max_offset_x))
        # Need world dimensions defined first.

        # --- Game Logic ---
        # Update ships
        for ship in ships:
            # Pass planet for storage access and dumping target
            ship.update(dt, asteroids, central_planet)

            # AI: Assign task if idle
            if ship.state == "idle":
                target_asteroid = find_nearest_asteroid(ship, asteroids)
                if target_asteroid:
                    ship.set_target(target_asteroid)
                # else: remain idle if no suitable asteroid found

        # --- Drawing ---
        screen.fill(constants.BLACK) # Clear screen with black

        # Draw background stars with parallax
        # Calculate camera displacement from initial position
        cam_delta_x = camera_offset_x - initial_camera_offset_x
        cam_delta_y = camera_offset_y - initial_camera_offset_y
        for star_x_initial, star_y_initial in stars:
            # Apply parallax effect based on camera displacement
            star_x = int(star_x_initial + cam_delta_x * constants.STAR_PARALLAX_FACTOR)
            star_y = int(star_y_initial + cam_delta_y * constants.STAR_PARALLAX_FACTOR)

            # Basic screen wrapping (optional)
            star_x %= constants.SCREEN_WIDTH
            star_y %= constants.SCREEN_HEIGHT

            pygame.draw.circle(screen, constants.STAR_COLOR, (star_x, star_y), constants.STAR_RADIUS)

        # Draw game elements applying camera transform
        central_planet.draw(screen, camera_offset_x, camera_offset_y, zoom_level)
        for asteroid in asteroids:
            asteroid.draw(screen, camera_offset_x, camera_offset_y, zoom_level, ui_font)
        for ship in ships:
            ship.draw(screen, camera_offset_x, camera_offset_y, zoom_level)

        # --- Draw UI ---
        # Display Planet Storage in top-left corner
        storage_y_offset = 10
        for resource_type, amount in central_planet.storage.items():
            # Use resource-specific colors or default white
            color = constants.WHITE
            if resource_type == "Tritanium": color = constants.TRITANIUM_COLOR
            elif resource_type == "Credits": color = constants.CREDITS_COLOR
            elif resource_type == "Plasma": color = constants.PLASMA_COLOR

            # Format amount as integer for display
            text = f"{resource_type}: {int(amount)}"
            text_surface = ui_font.render(text, True, color)
            text_rect = text_surface.get_rect(topleft=(10, storage_y_offset))
            screen.blit(text_surface, text_rect)
            storage_y_offset += 20 # Move down for the next resource line

        # --- Update Display ---
        pygame.display.flip()

        # --- Frame Rate Control (moved dt calculation to top of loop) ---
        # clock.tick(constants.FPS)

    # Quit Pygame
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
