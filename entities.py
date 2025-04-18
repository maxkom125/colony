import pygame
import constants
import random # Needed for resource generation
import math

class Planet:
    def __init__(self, world_x, world_y, radius, color):
        self.world_x = world_x
        self.world_y = world_y
        self.radius = radius
        self.color = color
        # Initialize storage for resources
        self.storage = {res_type: 0 for res_type in constants.RESOURCE_TYPES}

    def draw(self, surface, camera_offset_x, camera_offset_y, zoom_level):
        # Calculate screen coordinates based on world coordinates, camera offset, and zoom
        screen_x = int(self.world_x * zoom_level + camera_offset_x)
        screen_y = int(self.world_y * zoom_level + camera_offset_y)
        screen_radius = int(self.radius * zoom_level)

        # Ensure radius is at least 1 pixel to be visible when zoomed out
        if screen_radius < 1:
            screen_radius = 1 

        pygame.draw.circle(surface, self.color, (screen_x, screen_y), screen_radius)

class Asteroid:
    def __init__(self, world_x, world_y, radius, color):
        self.world_x = world_x
        self.world_y = world_y
        self.radius = radius
        self.initial_color = color

        # Choose one resource type based on weights
        chosen_resource = random.choices(constants.RESOURCE_TYPES, weights=constants.RESOURCE_WEIGHTS, k=1)[0]
        resource_amount = random.randint(constants.ASTEROID_MIN_RESOURCE_AMOUNT, constants.ASTEROID_MAX_RESOURCE_AMOUNT)

        # Initialize resources dict with only the chosen resource
        self.resources = {}
        for res_type in constants.RESOURCE_TYPES:
            self.resources[res_type] = resource_amount if res_type == chosen_resource else 0

        self.scanned = False

    def get_dominant_resource_color(self):
        if not self.resources:
            return self.initial_color

        # Find the resource with a non-zero amount (should be only one)
        dominant_resource = None
        for res, amount in self.resources.items():
            if amount > 0:
                dominant_resource = res
                break

        if dominant_resource == "Tritanium":
            return constants.TRITANIUM_COLOR
        elif dominant_resource == "Credits":
            return constants.CREDITS_COLOR
        elif dominant_resource == "Plasma":
            return constants.PLASMA_COLOR
        else:
            return constants.VISITED_ASTEROID_COLOR # Fallback or case where all are 0?

    def draw(self, surface, camera_offset_x, camera_offset_y, zoom_level, font):
        screen_x = int(self.world_x * zoom_level + camera_offset_x)
        screen_y = int(self.world_y * zoom_level + camera_offset_y)
        screen_radius = int(self.radius * zoom_level)

        if screen_radius < 1:
            screen_radius = 1

        # Determine draw color: initial, resource-based, or depleted
        is_depleted = self.scanned and not any(amount > 0 for amount in self.resources.values())

        if is_depleted:
            draw_color = constants.DEPLETED_ASTEROID_COLOR # Use red if scanned and empty
        elif self.scanned:
            draw_color = self.get_dominant_resource_color()
        else:
            draw_color = self.initial_color

        pygame.draw.circle(surface, draw_color, (screen_x, screen_y), screen_radius)

        # Draw resource text if scanned AND not depleted
        if self.scanned and not is_depleted:
            resource_text = ""
            dominant_res = None
            dominant_amount = 0
            for res, amount in self.resources.items():
                if amount > 0:
                    dominant_res = res
                    dominant_amount = amount
                    break

            if dominant_res:
                # Format amount as integer
                resource_text = f"{dominant_res[:1]}:{int(dominant_amount)}"
                text_surface = font.render(resource_text, True, constants.WHITE)
                text_rect = text_surface.get_rect(center=(screen_x, screen_y + screen_radius + 10))
                surface.blit(text_surface, text_rect)
        elif is_depleted: # Optional: Show "Depleted" or "0" text
            resource_text = "0"
            text_surface = font.render(resource_text, True, constants.DEPLETED_ASTEROID_COLOR)
            text_rect = text_surface.get_rect(center=(screen_x, screen_y + screen_radius + 10))
            surface.blit(text_surface, text_rect)

    # We might add a draw_resources method later for when is_scanned is True

class Spaceship:
    def __init__(self, world_x, world_y, size, color, angle=0):
        self.world_x = world_x
        self.world_y = world_y
        self.size = size # Represents the characteristic size (e.g., length/diameter)
        self.color = color
        self.angle = angle # Angle in radians for orientation
        self.speed = constants.SHIP_SPEED # Speed in world units per second
        self.target = None # Target entity (e.g., an Asteroid or Planet instance)
        # State definitions: idle, moving_to_asteroid, scanning, mining, returning_to_base, dumping
        self.state = "idle"
        self.scan_timer = 0.0 # Timer for scan duration
        # Timers for mining/dumping
        self.mining_timer = 0.0 # Timer for mining duration
        self.dumping_timer = 0.0 # Timer for dumping duration
        # Cargo attributes
        self.cargo_capacity = 0 # Max resource units this ship can hold (set in subclasses)
        self.cargo = {res_type: 0 for res_type in constants.RESOURCE_TYPES} # Current resources held

    def set_target(self, target_entity):
        self.target = target_entity
        # Determine state based on target type? Or handle in update?
        # For now, assume moving is the general transition
        # Specific transitions (e.g., to mining, scanning) happen on arrival in update()
        if isinstance(target_entity, Asteroid):
            self.state = "moving_to_asteroid"
        elif isinstance(target_entity, Planet): # Or check coordinates (0,0)
             self.state = "returning_to_base" # Assume target planet means return
        else:
             self.state = "idle" # Unknown target type

        # Reset timers when getting a new target
        self.scan_timer = 0.0
        self.mining_timer = 0.0
        self.dumping_timer = 0.0

    def get_cargo_total(self):
        """Returns the total amount of resources currently in cargo."""
        return sum(self.cargo.values())

    def _handle_movement(self, dt, obstacles, target_pos, arrival_threshold):
        """Helper function to handle movement and collision avoidance."""
        target_dx = target_pos[0] - self.world_x
        target_dy = target_pos[1] - self.world_y
        distance_to_target = math.hypot(target_dx, target_dy)

        if distance_to_target < arrival_threshold:
            return True # Arrived

        # --- Movement & Collision Avoidance Logic (extracted) ---
        if distance_to_target > 0:
            norm_target_dx = target_dx / distance_to_target
            norm_target_dy = target_dy / distance_to_target
        else:
            norm_target_dx, norm_target_dy = 0, 0

        lookahead_dist = self.speed * constants.AVOIDANCE_LOOKAHEAD_TIME
        intended_next_x = self.world_x + norm_target_dx * lookahead_dist
        intended_next_y = self.world_y + norm_target_dy * lookahead_dist

        from main import check_path_for_obstacles
        colliding_obstacle = check_path_for_obstacles((self.world_x, self.world_y),
                                                  (intended_next_x, intended_next_y),
                                                  obstacles,
                                                  self.target if isinstance(self.target, Asteroid) else None) # Don't ignore planet target

        move_dx, move_dy = 0, 0
        if colliding_obstacle:
            avoid_dx = self.world_x - colliding_obstacle.world_x
            avoid_dy = self.world_y - colliding_obstacle.world_y
            dist_avoid = math.hypot(avoid_dx, avoid_dy)
            if dist_avoid > 0:
                 avoid_dx /= dist_avoid; avoid_dy /= dist_avoid
            else: avoid_dx, avoid_dy = 0, 1

            tangent1_dx, tangent1_dy = -avoid_dy, avoid_dx
            tangent2_dx, tangent2_dy = avoid_dy, -avoid_dx
            dot1 = tangent1_dx * norm_target_dx + tangent1_dy * norm_target_dy
            dot2 = tangent2_dx * norm_target_dx + tangent2_dy * norm_target_dy

            if dot1 >= dot2: move_dx, move_dy = tangent1_dx, tangent1_dy
            else: move_dx, move_dy = tangent2_dx, tangent2_dy

            if abs(move_dx) < 1e-9 and abs(move_dy) < 1e-9:
                 move_dx, move_dy = avoid_dx, avoid_dy # Fallback

        else: # Normal Movement
            move_dx, move_dy = norm_target_dx, norm_target_dy

        # Apply movement
        self.world_x += move_dx * self.speed * dt
        self.world_y += move_dy * self.speed * dt

        # Update angle
        if abs(move_dx) > 1e-9 or abs(move_dy) > 1e-9:
            self.angle = math.atan2(move_dy, move_dx)

        return False # Not arrived

    def update(self, dt, obstacles, planet): # Pass planet for storage access

        # --- State Machine ---
        if self.state == "moving_to_asteroid":
            if not self.target or not isinstance(self.target, Asteroid):
                 self.state = "idle"; return # Target lost or invalid

            target_pos = (self.target.world_x, self.target.world_y)
            arrival_threshold = self.target.radius + 5
            arrived = self._handle_movement(dt, obstacles, target_pos, arrival_threshold)

            if arrived:
                 # print(f"DEBUG: {type(self).__name__} arrived at Asteroid {self.target}")
                 # Scanner starts scanning, Miner starts mining
                 if isinstance(self, MiningShip) and self.target.scanned:
                     # Check if asteroid has resources and ship has capacity
                     dominant_res = next((res for res, amount in self.target.resources.items() if amount > 0), None)
                     if dominant_res and self.get_cargo_total() < self.cargo_capacity:
                         self.state = "mining"
                         self.mining_timer = self.target.radius * constants.MINING_TIME_MULTIPLIER * constants.BASE_ACTION_TIME_UNIT
                         # print(f"DEBUG: MiningShip starting mining. Timer: {self.mining_timer:.2f}s")
                     else:
                         # print(f"DEBUG: Asteroid depleted or cargo full. Miner becoming idle.")
                         self.state = "idle"
                 elif not isinstance(self, MiningShip) and not self.target.scanned: # Scanner ship
                     self.state = "scanning"
                     self.scan_timer = self.target.radius * constants.SCAN_TIME_PER_RADIUS_UNIT
                     # print(f"DEBUG: Scanner starting scan. Timer: {self.scan_timer:.2f}s")
                 else: # Miner at unscanned/depleted/full, or Scanner at scanned
                     # print(f"DEBUG: Ship becoming idle upon arrival (no valid action).")
                     self.state = "idle"

        elif self.state == "scanning": # Only Scanner ships
            if not self.target or not isinstance(self.target, Asteroid):
                 self.state = "idle"; return # Target lost

            self.scan_timer -= dt
            if self.scan_timer <= 0:
                # print(f"DEBUG: Scan complete for {self.target}. Marking scanned.")
                self.target.scanned = True
                self.state = "idle"

        elif self.state == "mining": # Only Mining ships
            if not self.target or not isinstance(self.target, Asteroid):
                 self.state = "idle"; return # Target lost

            self.mining_timer -= dt
            mined_this_tick = self.speed * dt * 0.1 # Arbitrary mining rate factor - NEEDS BALANCING

            dominant_res = None
            dominant_amount = 0
            for res, amount in self.target.resources.items():
                if amount > 0:
                    dominant_res = res
                    dominant_amount = amount
                    break

            if not dominant_res: # Asteroid depleted
                # print(f"DEBUG: Asteroid {self.target} depleted during mining.")
                self.set_target(planet) # Target the planet to return
                return

            actual_mined = min(mined_this_tick, dominant_amount) # Don't mine more than available
            cargo_space = self.cargo_capacity - self.get_cargo_total()
            actual_taken = min(actual_mined, cargo_space) # Don't take more than capacity

            if actual_taken > 0:
                self.target.resources[dominant_res] -= actual_taken
                self.cargo[dominant_res] += actual_taken
                # print(f"DEBUG: Mined {actual_taken:.2f} {dominant_res}. Cargo: {self.get_cargo_total():.2f}/{self.cargo_capacity}")

            # Check end conditions
            cargo_full = self.get_cargo_total() >= self.cargo_capacity
            asteroid_depleted = self.target.resources[dominant_res] <= 0
            time_up = self.mining_timer <= 0

            if cargo_full or asteroid_depleted or time_up:
                 # print(f"DEBUG: Mining finished (CargoFull:{cargo_full}, Depleted:{asteroid_depleted}, TimeUp:{time_up}). Returning.")
                 self.set_target(planet) # Target the planet

        elif self.state == "returning_to_base":
            if not self.target or not isinstance(self.target, Planet): # Check if target is planet
                 # Fallback: if target isn't planet, manually set target coords to (0,0)
                 target_pos = (0, 0)
                 arrival_threshold = constants.PLANET_RADIUS + self.size # Arrive near planet edge
                 # We lost the Planet object ref if we didn't use set_target properly
                 # Need to ensure set_target(planet) was called.
                 # For now, assume target_pos is (0,0) if self.target isn't Planet
            else:
                 target_pos = (self.target.world_x, self.target.world_y)
                 arrival_threshold = self.target.radius + self.size

            arrived = self._handle_movement(dt, obstacles, target_pos, arrival_threshold)

            if arrived:
                # print(f"DEBUG: {type(self).__name__} arrived at Planet. Starting dumping.")
                self.state = "dumping"
                self.dumping_timer = constants.DUMPING_DURATION

        elif self.state == "dumping":
             self.dumping_timer -= dt
             if self.dumping_timer <= 0:
                 # print(f"DEBUG: Dumping complete. Transferring cargo to planet.")
                 total_dumped = 0
                 for res_type, amount in self.cargo.items():
                     if amount > 0:
                         planet.storage[res_type] += amount
                         total_dumped += amount
                         self.cargo[res_type] = 0 # Empty cargo
                 # print(f"DEBUG: Dumped {total_dumped:.2f} total resources.")
                 self.state = "idle"

        # Note: Idle state logic is now handled in main.py loop

    def draw(self, surface, camera_offset_x, camera_offset_y, zoom_level):
        # Calculate screen coordinates
        screen_x = int(self.world_x * zoom_level + camera_offset_x)
        screen_y = int(self.world_y * zoom_level + camera_offset_y)
        screen_size = int(self.size * zoom_level)

        if screen_size < 3: # Keep a minimum size for visibility
            screen_size = 3

        # Define triangle points relative to screen_x, screen_y based on angle and size
        # Point 1 (Nose)
        p1_x = screen_x + math.cos(self.angle) * screen_size * 0.6
        p1_y = screen_y + math.sin(self.angle) * screen_size * 0.6
        # Point 2 (Rear Left Wing)
        p2_angle = self.angle + math.pi * 0.8
        p2_x = screen_x + math.cos(p2_angle) * screen_size * 0.4
        p2_y = screen_y + math.sin(p2_angle) * screen_size * 0.4
        # Point 3 (Rear Right Wing)
        p3_angle = self.angle - math.pi * 0.8
        p3_x = screen_x + math.cos(p3_angle) * screen_size * 0.4
        p3_y = screen_y + math.sin(p3_angle) * screen_size * 0.4

        # Draw the triangle
        pygame.draw.polygon(surface, self.color, [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)])

# --- Mining Ship ---
class MiningShip(Spaceship):
    def __init__(self, world_x, world_y, angle=0):
        # Call parent constructor with Mining ship specific constants
        super().__init__(world_x, world_y, constants.MINING_SHIP_SIZE, constants.MINING_SHIP_COLOR, angle)
        # Set cargo capacity for Mining Ship
        self.cargo_capacity = constants.MINING_SHIP_CARGO_CAPACITY
        # Ensure initial state is set (though super() does it)
        self.state = "idle"

    def draw(self, surface, camera_offset_x, camera_offset_y, zoom_level):
        # Calculate screen coordinates
        screen_x = int(self.world_x * zoom_level + camera_offset_x)
        screen_y = int(self.world_y * zoom_level + camera_offset_y)
        screen_size = int(self.size * zoom_level)

        if screen_size < 4: # Keep a minimum size for visibility
            screen_size = 4

        # Define a different shape (e.g., a diamond or simple rectangle)
        half_size_x = screen_size * 0.5
        half_size_y = screen_size * 0.3

        # Points relative to center, rotated by self.angle
        points = [
            (-half_size_x, 0),           # Left corner
            (0, -half_size_y),         # Top corner
            (half_size_x, 0),          # Right corner
            (0, half_size_y)          # Bottom corner
        ]

        # Rotate points around the center (screen_x, screen_y)
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        rotated_points = []
        for x, y in points:
            rotated_x = screen_x + (x * cos_a - y * sin_a)
            rotated_y = screen_y + (x * sin_a + y * cos_a)
            rotated_points.append((rotated_x, rotated_y))

        # Draw the shape
        pygame.draw.polygon(surface, self.color, rotated_points)
