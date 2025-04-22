# Contents for src/entities/planet.py
import pygame
from pygame.math import Vector2
from .. import constants  # Relative import


class Planet:
    def __init__(self, position: Vector2, radius, color):
        self.position = position
        self.radius = radius
        self.color = color
        # Initialize storage with starting resources
        self.storage = {
            "Tritanium": 200, 
            "Credits": 200, 
            "Plasma": 50
            } 
        # {res_type: 0 for res_type in constants.RESOURCE_TYPES} # Old initialization

    def draw(self, surface, world_to_screen_func, zoom_level):
        screen_pos = world_to_screen_func(self.position)
        screen_radius = int(self.radius * zoom_level)

        if screen_radius < 1:
            screen_radius = 1

        pygame.draw.circle(
            surface, self.color, (int(screen_pos.x), int(screen_pos.y)), screen_radius
        )
 