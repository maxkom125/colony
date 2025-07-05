# Contents for src/entities/planet.py
import pygame
from pygame.math import Vector2
from .entity import Entity # Import the new base class
from .. import constants  # Relative import
from ..enums import ResourceType
from ..logger import logger # Import the logger


class Planet(Entity):
    """Represents the player's home base."""
    def __init__(self, position: Vector2, radius: int | None = None, color: tuple[int, int, int] | None = None, entity_id: int | None = None):
        # Use constants for radius and color
        if radius is None:
            radius = constants.PLANET_RADIUS
        if color is None:
            color = constants.PLANET_COLOR
        super().__init__(position, radius, color, entity_id)
        self.scanned = True # Planets are always visible

        # Storage for resources dumped by miners
        self.storage = {res_type: 0 for res_type in ResourceType.list()}

    def has_resources(self, resource_dict: dict[ResourceType, int]) -> bool:
        """Checks if the planet has enough of the specified resources."""
        for resource_type, amount_needed in resource_dict.items():
            if self.storage.get(resource_type, 0) < amount_needed:
                return False
        return True

    def remove_resources(self, resource_dict: dict[ResourceType, int]) -> bool:
        """Removes the specified resources from storage.

        Returns True if successful (all resources were present in sufficient
        quantity), False otherwise (storage remains unchanged).
        Assumes check using has_resources was potentially done before.
        """
        # Double-check affordability before removing
        if not self.has_resources(resource_dict):
            logger.error(f"remove_resources called for {resource_dict} but insufficient funds.")
            return False

        # If affordable, deduct
        for resource_type, amount_to_remove in resource_dict.items():
            self.storage[resource_type] -= amount_to_remove
            logger.info(f"Removed {amount_to_remove} {resource_type}. New total: {self.storage[resource_type]}")
        return True

    def add_resources(self, resources_to_add: dict[ResourceType, int]):
        """Adds resources to the planet's storage."""
        for resource_type, amount in resources_to_add.items():
            if resource_type in self.storage:
                if amount < 0:
                    logger.warning(f"Attempted to add negative amount ({amount}) of {resource_type}. Ignoring.")
                    continue
                self.storage[resource_type] += amount
                logger.info(f"Added {amount} {resource_type} to planet. New total: {self.storage[resource_type]}")
            else:
                logger.warning(f"Attempted to add unknown resource type '{resource_type}'.")

    def draw(self, surface, world_to_screen_func, zoom_level):
        # Simple circle drawing
        screen_pos = world_to_screen_func(self.position)
        screen_radius = max(1, int(self.radius * zoom_level))
        pygame.draw.circle(surface, self.color, screen_pos, screen_radius)

    # update() method is inherited from Entity (currently does nothing)
 