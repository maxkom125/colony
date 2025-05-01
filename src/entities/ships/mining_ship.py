import pygame
import math
from typing import TYPE_CHECKING
from pygame.math import Vector2
from .base_ship import Ship  # New base class
from ... import constants  # Relative import
from ..asteroid import Asteroid  # Need these for type hints/checks
from ..planet import Planet
from ...enums import ShipState, ShipType, ResourceType  # Import the enum


# Conditional import for type hinting to prevent circular dependency
if TYPE_CHECKING:
    from ...systems.admirals.miner_admiral import MinerAdmiral


class MiningShip(Ship):
    """Represents a ship specialized in mining asteroids."""

    def __init__(self, position: Vector2, home_planet: Planet, ship_id: int | None = None):
        # Use constants for mining ship specific values
        super().__init__(
            position,
            constants.MINING_SHIP_SIZE,
            constants.MINING_SHIP_COLOR,
            constants.MINER_SPEED,
            home_planet,
            ship_id,
        )
        self.type = ShipType.MINER
        self.cargo_capacity = constants.MINING_SHIP_CARGO_CAPACITY
        self.mining_rate = constants.MINING_RATE
        self.admiral: "MinerAdmiral" | None = None
        self.resource_to_mine = None

    def set_resource_to_mine(self, resource: ResourceType | None):
        """Sets the resource to mine. Should be called by the admiral only!"""
        # ---- Checks ----
        if resource is None:
            self.resource_to_mine = None
            return
        if resource not in ResourceType:
            print(f"WARN: Invalid resource type: {resource}")
            return
        if self.admiral is None:
            print(f"ERROR: MiningShip {self.id} has no admiral")
            return
        
        if self.admiral.ships_assignments[self.id] != self.admiral.free_ship_category:
            if resource != self.admiral.ships_assignments[self.id]:
                print(f"WARN: Ship {self.id} is not assigned to mine {resource}")
                return
            if self.id not in self.admiral.assignments_ships[resource]:
                print(f"WARN: Ship {self.id} is not in the list of ships assigned to mine {resource}")
                return
        # ---- Set ----
        self.resource_to_mine = resource

    def update(self, dt: float, obstacles: list[Asteroid | Planet]):
        """Updates the mining ship's state machine and actions."""
        super().update(dt, obstacles)

        if self.state == ShipState.MINING:
            # ---- Checks ----
            if self.admiral is None:
                print(f"ERROR: {self.type} {self.id} in MINING state but has no admiral. Going IDLE.")
                return
            if self.resource_to_mine not in ResourceType.list():
                print(
                    f"WARN: {self.type} {self.id} in MINING state but has no assigned category. Going IDLE."
                )
                self.admiral.issue_command(self)
                return
            if self.target is None or not isinstance(self.target, Asteroid):
                print(f"WARN: {self.type} {self.id} in MINING state but target is not an Asteroid. Going IDLE.")
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
                    self.mining_timer = can_take / self.mining_rate
                    print(
                        f"DEBUG: {self.type} {self.id} mined {actual_mined} {self.resource_to_mine}. "
                        f"Cargo: {self.cargo[self.resource_to_mine]}/{self.cargo_capacity}"
                    )
                else:
                    print(f"ERROR: {self.type} {self.id} mined 0 {self.resource_to_mine}. This should never happen!")
                    self.admiral.issue_command(self)
            else:
                print(
                    f"DEBUG: {self.type} {self.id} finished mining (Full or Depleted). "
                    f"Returning home."
                )
                self.admiral.issue_command(self) # Will set state to RETURNING_TO_BASE

        elif self.state == ShipState.DUMPING:
            self.dumping_timer += dt
            if self.dumping_timer >= constants.DUMPING_DURATION:
                print(f"DEBUG: Ship {self.id} finished dumping {self.cargo} at home planet.")
                self.home.add_resources(self.cargo)
                for res_type in self.cargo:
                    self.cargo[res_type] = 0
                self.set_state(ShipState.IDLE)
                self.target = None
                self.dumping_timer = 0.0

    def draw(self, surface, world_to_screen_func, zoom_level):
        # This draw method relies on self.angle
        screen_pos = world_to_screen_func(self.position)
        # Use self.radius inherited from Entity/Ship, which was set using constants.MINING_SHIP_SIZE
        screen_size = max(4, int(self.radius * zoom_level))

        half_size_x = screen_size * 0.5
        half_size_y = screen_size * 0.3

        points = [
            Vector2(-half_size_x, 0),
            Vector2(0, -half_size_y),
            Vector2(half_size_x, 0),
            Vector2(0, half_size_y),
        ]

        rotated_points = []
        for p in points:
            # Assumes self.angle exists (will add to base Ship)
            rotated_p = p.rotate_rad(self.angle)
            screen_p = screen_pos + rotated_p
            rotated_points.append(screen_p)

        pygame.draw.polygon(surface, self.color, rotated_points)

    def reset_timers(self):
        """Resets mining and dumping timers when state changes."""
        self.mining_timer = 0.0
        self.dumping_timer = 0.0
