# src/entities/entity.py
import pygame
from pygame.math import Vector2
import itertools

class Entity:
    """Base class for all game objects with a position and appearance."""
    # Class variable to generate unique IDs across all entity types
    _id_counter = itertools.count(1)

    def __init__(self, position: Vector2, radius: int, color: tuple, entity_id: int | None = None):
        self.position = position
        self.radius = radius
        self.color = color
        # Assign a unique ID if one isn't provided
        self.id: int = entity_id if entity_id is not None else next(Entity._id_counter)

    def update(self, dt: float):
        """Placeholder for update logic common to all entities."""
        pass

    def draw(self, surface, world_to_screen_func, zoom_level):
        """Placeholder for drawing logic. Subclasses should implement."""
        # Basic circle drawing if not overridden
        screen_pos = world_to_screen_func(self.position)
        screen_radius = max(1, int(self.radius * zoom_level))
        pygame.draw.circle(surface, self.color, screen_pos, screen_radius)

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id) 