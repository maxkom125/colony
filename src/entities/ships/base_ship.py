# Contents for src/entities/ships/base_ship.py
import pygame
import math
from pygame.math import Vector2
from ... import constants  # Relative import
from ..asteroid import Asteroid  # Need these for type hints/checks
from ..planet import Planet


class Spaceship:
    def __init__(self, position: Vector2, size, color, angle=0):
        self.position = position
        self.size = size
        self.color = color
        self.angle = angle
        self.speed = constants.SHIP_SPEED
        self.target = None
        self.state = "idle"
        self.scan_timer = 0.0
        self.mining_timer = 0.0
        self.dumping_timer = 0.0
        self.cargo_capacity = 0  # Specific ships override this
        self.cargo = {res_type: 0 for res_type in constants.RESOURCE_TYPES}

    def set_target(self, target_entity):
        self.target = target_entity
        if not target_entity:
            self.state = "idle"
            return

        if isinstance(target_entity, Asteroid):
            self.state = "moving_to_asteroid"
        elif isinstance(target_entity, Planet):
            self.state = "returning_to_base"
        else:
            print(
                f"WARNING: Unknown target type {type(target_entity)}. Ship going idle."
            )
            self.state = "idle"

        self.scan_timer = 0.0
        self.mining_timer = 0.0
        self.dumping_timer = 0.0

    def get_cargo_total(self):
        return sum(self.cargo.values())

    def update_actions(self, dt, planet=None):
        # This base method handles common timer logic if any, but scanning/mining/dumping
        # logic is primarily handled in subclasses or specific state handlers.
        # Example: If we had a general cooldown timer, it could be handled here.
        pass  # Base ship doesn't perform actions on its own

    def handle_arrival(self, planet):
        # Base arrival logic: typically just go idle unless overridden
        # print(f"DEBUG: Base ship arrived at {self.target}. Going idle.")
        self.state = "idle"
        self.target = None  # Clear target on arrival if just idling

    def draw(self, surface, world_to_screen_func, zoom_level):
        # Default draw method (e.g., scanner ship)
        screen_pos = world_to_screen_func(self.position)
        screen_size = int(self.size * zoom_level)

        if screen_size < 3:
            screen_size = 3

        p1_offset = Vector2(screen_size * 0.6, 0).rotate_rad(self.angle)
        p1 = screen_pos + p1_offset
        p2_offset = Vector2(screen_size * 0.4, 0).rotate_rad(self.angle + math.pi * 0.8)
        p2 = screen_pos + p2_offset
        p3_offset = Vector2(screen_size * 0.4, 0).rotate_rad(self.angle - math.pi * 0.8)
        p3 = screen_pos + p3_offset

        pygame.draw.polygon(surface, self.color, [p1, p2, p3])
