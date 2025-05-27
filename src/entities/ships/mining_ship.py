import pygame
import math
from typing import TYPE_CHECKING
from pygame.math import Vector2
from .base_ship import Ship  # New base class
from ... import constants  # Relative import
from ..asteroid import Asteroid  # Need these for type hints/checks
from ..planet import Planet
from ...enums import ShipState, ShipType, ResourceType  # Import the enum
from ...utils import convert_resource_type_to_enum
from ...logger import logger  # Import the logger

# Conditional import for type hinting to prevent circular dependency
if TYPE_CHECKING:
    from ...systems.admirals.miner_admiral import MinerAdmiral


class MiningShip(Ship):
    """Represents a ship specialized in mining asteroids."""

    def __init__(
        self, position: Vector2, home_planet: Planet, ship_id: int | None = None, *args, **kwargs
    ):
        # Use constants for mining ship specific values
        super().__init__(
            position,
            constants.MINING_SHIP_SIZE,
            constants.MINING_SHIP_COLOR,
            constants.MINER_SPEED,
            home_planet,
            ship_id,
            *args,
            **kwargs,
        )
        self.type = ShipType.MINER
        self.cargo_capacity = constants.MINING_SHIP_CARGO_CAPACITY
        self.mining_rate = constants.MINING_RATE
        self.admiral: "MinerAdmiral" | None = None
        self.resource_to_mine = None

    def set_resource_to_mine(self, resource: ResourceType | str | None):
        """Sets the resource to mine. Should be called by the admiral only!"""
        if resource is None:
            self.resource_to_mine = None
            return
        try:
            resource = convert_resource_type_to_enum(resource)
        except ValueError as e:
            logger.warning(f"Invalid resource type: {resource}. Error: {e}")
            return

        # ---- Checks ----
        if (
            resource not in ResourceType
        ):  # Should be caught by convert_resource_type_to_enum already
            logger.warning(f"Invalid resource type (post-conversion): {resource}")
            return
        if self.admiral is None:
            logger.error(f"MiningShip {self.id} has no admiral")
            return

        assigned_category_str = self.admiral.ships_assignments[self.id]
        if assigned_category_str != self.admiral.free_ship_category:
            if resource.value != assigned_category_str:
                logger.warning(
                    f"Ship {self.id} is assigned to {assigned_category_str} but attempted to set mine to {resource.value}"
                )
                return
            if self.id not in self.admiral.assignments_ships[assigned_category_str]:
                logger.warning(
                    f"Ship {self.id} is not in the list of ships assigned to mine {assigned_category_str}"
                )
                return
        # ---- Set ----
        self.resource_to_mine = resource

    def update(self, dt: float, obstacles: list[Asteroid | Planet]):
        """Updates the mining ship's state machine and actions."""
        super().update(dt, obstacles)

        if self.state == ShipState.MINING:
            # ---- Checks ----
            if self.admiral is None:
                logger.error(
                    f"{self.type} {self.id} in MINING state but has no admiral. Doing nothing."
                )
                return
            if self.resource_to_mine not in ResourceType.list():
                logger.warning(
                    f"{self.type} {self.id} in MINING state but resource to mine ({self.resource_to_mine}) is not in ResourceType.list()"
                )
                self.admiral.issue_command(self)
                return
            if self.target is None or not isinstance(self.target, Asteroid):
                logger.warning(
                    f"{self.type} {self.id} in MINING state but target ({self.target}) is not an Asteroid."
                )
                self.admiral.issue_command(self)
                return

            # ---- Mining ----
            free_space = self.cargo_capacity - self.get_cargo_total()
            if (
                self.target.resources.get(self.resource_to_mine, 0) > 0
                and free_space > constants.EPSILON
            ):
                max_available = self.target.resources[self.resource_to_mine]
                can_take = min(free_space, max_available)

                mined_amount = dt * self.mining_rate
                actual_mined = min(mined_amount, can_take)

                if actual_mined > 0:
                    self.cargo[self.resource_to_mine] += actual_mined
                    self.target.resources[self.resource_to_mine] -= actual_mined
                    self.mining_timer = can_take / max(self.mining_rate, constants.EPSILON)
                else:
                    # This case might happen if free_space or max_available is ~0
                    logger.warning(
                        f"{self.type} {self.id} mined 0 {self.resource_to_mine}. Free space: {free_space}, Max available: {max_available}. This might indicate an issue."
                    )
                    self.admiral.issue_command(self)
            else:
                logger.debug(
                    f"{self.type} {self.id} finished mining (Full or Depleted). " f"Returning home."
                )
                self.admiral.issue_command(self)  # Will set state to RETURNING_TO_BASE

        elif self.state == ShipState.DUMPING:
            self.dumping_timer += dt
            if self.dumping_timer >= constants.DUMPING_DURATION:
                logger.debug(f"Ship {self.id} finished dumping {self.cargo} at home planet.")
                self.home.add_resources(self.cargo)  # Planet already logs this
                for res_type in self.cargo:
                    self.cargo[res_type] = 0

                # End of cycle, admiral will issue 'moving to asteroid' command to idle ships
                # Going IDLE
                self.admiral.issue_command(self)

    def draw(self, surface, world_to_screen_func, zoom_level):
        """Draws the mining ship (diamond) using the base class helper for rotation."""
        # Calculate screen size using the base class helper
        screen_radius = self.get_radius_to_draw(zoom_level)

        # Define diamond points relative to (0,0)
        half_size_x = screen_radius * 0.5
        half_size_y = screen_radius * 0.3  # Keep the diamond aspect ratio
        relative_points = [
            Vector2(-half_size_x, 0),  # Left point
            Vector2(0, -half_size_y),  # Top point
            Vector2(half_size_x, 0),  # Right point
            Vector2(0, half_size_y),  # Bottom point
        ]

        # Calculate final screen points using the base class helper
        screen_points = self._calculate_rotated_screen_points(
            relative_points, world_to_screen_func, zoom_level
        )

        # Draw the polygon
        pygame.draw.polygon(surface, self.color, screen_points)

    def reset_timers(self):
        """Resets mining and dumping timers when state changes."""
        self.mining_timer = 0.0
        self.dumping_timer = 0.0
