import pygame
import math
from pygame.math import Vector2
from .base_ship import Spaceship  # Inherit from base
from ... import constants  # Relative import
from ..asteroid import Asteroid  # Need these for type hints/checks
from ..planet import Planet


class MiningShip(Spaceship):
    def __init__(self, position: Vector2, angle=0):
        super().__init__(
            position, constants.MINING_SHIP_SIZE, constants.MINING_SHIP_COLOR, angle
        )
        self.cargo_capacity = constants.MINING_SHIP_CARGO_CAPACITY
        self.state = "idle"  # Explicitly start idle

    def update_actions(self, dt, planet=None):
        # Handle mining and dumping timers
        if self.state == "mining":
            if not self.target or not isinstance(self.target, Asteroid):
                self.state = "idle"
                return

            self.mining_timer -= dt
            mined_this_tick = constants.MINING_RATE * dt  # Use MINING_RATE constant

            dominant_res = next(
                (res for res, amount in self.target.resources.items() if amount > 0),
                None,
            )

            if not dominant_res:
                if planet:
                    self.set_target(planet)
                else:
                    self.state = "idle"
                return

            actual_mined = min(mined_this_tick, self.target.resources[dominant_res])
            cargo_space = self.cargo_capacity - self.get_cargo_total()
            actual_taken = min(actual_mined, cargo_space)

            if actual_taken > 0:
                self.target.resources[dominant_res] -= actual_taken
                self.cargo[dominant_res] += actual_taken

            cargo_full = self.get_cargo_total() >= self.cargo_capacity
            asteroid_depleted = self.target.resources[dominant_res] <= 0
            time_up = self.mining_timer <= 0

            if cargo_full or asteroid_depleted or time_up:
                if planet:
                    self.set_target(planet)
                else:
                    self.state = "idle"

        elif self.state == "dumping":
            if not planet:
                print("ERROR: Cannot dump without planet reference!")
                self.state = "idle"
                return

            self.dumping_timer -= dt
            if self.dumping_timer <= 0:
                total_dumped = 0
                for res_type, amount in self.cargo.items():
                    if amount > 0:
                        if hasattr(planet, "storage") and res_type in planet.storage:
                            planet.storage[res_type] += amount
                        else:
                            print(
                                f"ERROR: Planet missing storage or resource type {res_type}!"
                            )
                        total_dumped += amount
                        self.cargo[res_type] = 0
                self.state = "idle"

    def handle_arrival(self, planet):
        if self.state == "moving_to_asteroid" and isinstance(self.target, Asteroid):
            if self.target.scanned:
                dominant_res = next(
                    (
                        res
                        for res, amount in self.target.resources.items()
                        if amount > 0
                    ),
                    None,
                )
                if dominant_res and self.get_cargo_total() < self.cargo_capacity:
                    self.state = "mining"
                    self.mining_timer = (
                        constants.MINING_DURATION
                    )  # Use MINING_DURATION constant
                else:
                    self.set_target(planet)
            else:
                self.state = "idle"

        elif self.state == "returning_to_base" and isinstance(self.target, Planet):
            if self.get_cargo_total() > 0:
                self.state = "dumping"
                self.dumping_timer = constants.DUMPING_DURATION
            else:
                self.state = "idle"
        else:
            # Arrived while in a non-moving state? Go idle.
            self.state = "idle"
            self.target = None

    def draw(self, surface, world_to_screen_func, zoom_level):
        # Override draw method for a different shape
        screen_pos = world_to_screen_func(self.position)
        screen_size = int(self.size * zoom_level)

        if screen_size < 4:
            screen_size = 4

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
            rotated_p = p.rotate_rad(self.angle)
            screen_p = screen_pos + rotated_p
            rotated_points.append(screen_p)

        pygame.draw.polygon(surface, self.color, rotated_points)
