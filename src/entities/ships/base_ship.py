# Contents for src/entities/ships/base_ship.py
import pygame
import itertools  # For generating unique IDs
from pygame.math import Vector2
from ... import constants  # Relative import
from ..entity import Entity  # Inherit from Entity
from ...enums import ShipState, ShipType, ResourceType
from ..asteroid import Asteroid
from ..planet import Planet
from ...systems.movement_system import update_ship_movement
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...systems.admirals.base_admiral import Admiral


class Ship(Entity):
    """Base class for all player-controlled ships."""

    # Class variable to generate unique IDs
    _id_counter = itertools.count(1)

    def __init__(
        self,
        position: Vector2,
        radius: int,
        color: tuple,
        speed: float,
        home_planet: Planet,
        ship_id: int | None = None,
    ):
        # Use passed-in values, defaults should be handled by subclasses using constants
        assigned_id = ship_id if ship_id is not None else next(Ship._id_counter)
        super().__init__(position, radius, color, assigned_id)

        self.speed = speed
        self.home: Planet = home_planet
        self.target: Entity | None = None
        self.state = ShipState.IDLE
        self.type = ShipType.UNKNOWN
        self.angle = 0.0  # Add angle property, default to 0 rad

        self.admiral: "Admiral" | None = None  # Will be set when added to fleet

        # Timers - may or may not be used by all subclasses
        self.scan_timer = 0.0
        self.mining_timer = 0.0
        self.dumping_timer = 0.0

        # Cargo - relevant for mining/transport ships
        self.cargo_capacity = 0
        self.cargo = {res_type: 0 for res_type in ResourceType.list()}  # Use enum list here

    def set_target(self, target_entity: Entity | None):
        """Sets the ship's target and initial state for moving."""
        self.target = target_entity
        self.reset_timers()

    def get_cargo_total(self) -> int:
        """Returns the total amount of resources currently in the cargo hold."""
        return sum(self.cargo.values())

    def update(self, dt: float, obstacles: list[Asteroid | Planet]):
        """Base update loop. Calls movement update. Subclasses add state actions."""
        self.update_movement(dt, obstacles)
        # Subclasses will add their state-specific action logic here
        # by overriding this method and calling super().update(dt)

    def update_movement(self, dt: float, obstacles: list[Asteroid | Planet]):
        """Handles moving the ship towards its target and checks for arrival."""
        # --- Checks ---
        if not self.target:  # No target, nothing to move towards
            return

        # Check if actually in a moving state using the constant set
        is_moving = self.state in constants.MOVING_SHIP_STATES  # Use the set

        if not is_moving:
            return  # Not in a state where movement occurs

        # --- Movement ---
        self.position, self.angle, ship_arrived = update_ship_movement(self, dt, obstacles)
        if ship_arrived:
            if self.admiral:
                self.admiral.issue_command(self)
            else:
                print(f"ERROR: Ship {self.id} has no admiral, cannot issue arrival command.")
                return

    def get_arrival_threshold(self):
        if self.target and hasattr(self.target, "radius"):
            return self.radius + self.target.radius + constants.ARRIVAL_DISTANCE_BUFFER
        else:
            print(
                f"WARN: Ship {self.id} has no target (or something wrong with target), returning 0 arrival threshold."
            )
            return 0

    def handle_arrival(self):
        """DEPRECATED."""
        print("DEPRECATED: handle_arrival is deprecated")

    def set_state(self, new_state: ShipState):
        """Sets the ship's state and resets any relevant timers."""
        self.state = new_state
        self.reset_timers()

    def reset_timers(self):
        """Resets timers when state changes. Base class does nothing."""
        pass

    def _calculate_rotated_screen_points(
        self, relative_points: list[Vector2], world_to_screen_func, zoom_level
    ) -> list[Vector2]:
        """Helper to calculate rotated and translated screen points for drawing."""
        screen_pos = world_to_screen_func(self.position)
        rotated_screen_points = []
        for p_rel in relative_points:
            # Rotate point around (0,0) using self.angle
            p_rot = p_rel.rotate_rad(self.angle)
            # Translate rotated point to screen position
            p_screen = screen_pos + p_rot
            rotated_screen_points.append(p_screen)
        return rotated_screen_points

    def get_radius_to_draw(self, zoom_level) -> int:
        """Helper to get the radius to draw for the ship."""
        return max(3, int(self.radius * zoom_level))

    def draw(self, surface, world_to_screen_func, zoom_level):
        """Draws the base ship shape (triangle) using the helper method."""
        screen_radius = self.get_radius_to_draw(zoom_level)

        # Define base triangle points relative to (0,0)
        p1_rel = Vector2(screen_radius, 0)
        p2_rel = Vector2(-screen_radius * 0.6, screen_radius * 0.7)
        p3_rel = Vector2(-screen_radius * 0.6, -screen_radius * 0.7)
        relative_points = [p1_rel, p2_rel, p3_rel]

        # Calculate final screen points using the helper
        screen_points = self._calculate_rotated_screen_points(
            relative_points, world_to_screen_func, zoom_level
        )

        # Draw the polygon
        pygame.draw.polygon(surface, self.color, screen_points)
