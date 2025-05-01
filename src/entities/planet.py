# Contents for src/entities/planet.py
import pygame
from pygame.math import Vector2
from .entity import Entity # Import the new base class
from .. import constants  # Relative import
from ..enums import ResourceType


class Planet(Entity):
    """Represents the player's home base."""
    def __init__(self, position: Vector2, radius: int | None = None, color: tuple | None = None, entity_id: int | None = None):
        # Use constants for radius and color
        if radius is None:
            radius = constants.PLANET_RADIUS
        if color is None:
            color = constants.PLANET_COLOR
        super().__init__(position, radius, color, entity_id)
        self.scanned = True # Planets are always visible

        # Storage for resources dumped by miners
        self.storage = {res_type: 0 for res_type in ResourceType.list()}
        # Add starting resources if needed
        # self.storage["Tritanium"] = 200 # Example

    def has_resources(self, resource_dict: dict) -> bool:
        """Checks if the planet has enough of the specified resources."""
        for resource_type, amount_needed in resource_dict.items():
            if self.storage.get(resource_type, 0) < amount_needed:
                return False
        return True

    def remove_resources(self, resource_dict: dict) -> bool:
        """Removes the specified resources from storage.

        Returns True if successful (all resources were present in sufficient
        quantity), False otherwise (storage remains unchanged).
        Assumes check using has_resources was potentially done before.
        """
        # Double-check affordability before removing
        if not self.has_resources(resource_dict):
            print(f"ERROR: remove_resources called for {resource_dict} but insufficient funds.")
            return False

        # If affordable, deduct
        for resource_type, amount_to_remove in resource_dict.items():
            self.storage[resource_type] -= amount_to_remove
            print(f"INFO: Removed {amount_to_remove} {resource_type}. New total: {self.storage[resource_type]}")
        return True

    def add_resources(self, resources_to_add: dict):
        """Adds resources to the planet's storage."""
        for resource_type, amount in resources_to_add.items():
            if resource_type in self.storage:
                if amount < 0:
                    print(f"Warning: Attempted to add negative amount ({amount}) of {resource_type}. Ignoring.")
                    continue
                self.storage[resource_type] += amount
                print(f"INFO: Added {amount} {resource_type} to planet. New total: {self.storage[resource_type]}")
            else:
                print(f"Warning: Attempted to add unknown resource type '{resource_type}'.")

    def draw(self, surface, world_to_screen_func, zoom_level):
        # Simple circle drawing
        screen_pos = world_to_screen_func(self.position)
        screen_radius = max(1, int(self.radius * zoom_level))
        pygame.draw.circle(surface, self.color, screen_pos, screen_radius)

        # Optionally draw stored resources if needed
        if zoom_level > 0.4: # Only draw text if zoomed in enough
            font = pygame.font.SysFont(None, max(10, int(14 * zoom_level)))
            y_offset = screen_radius + 5
            for res_type, amount in self.storage.items():
                if amount > 0:
                    res_color = (220, 220, 220) # Default white/gray
                    text = font.render(f"{res_type}: {amount}", True, res_color)
                    text_rect = text.get_rect(center=(screen_pos.x, screen_pos.y + y_offset))
                    surface.blit(text, text_rect)
                    y_offset += text.get_height()
    
    # update() method is inherited from Entity (currently does nothing)
 