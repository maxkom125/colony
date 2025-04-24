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
        screen_pos = world_to_screen_func(self.position)
        screen_radius = int(self.radius * zoom_level)

        if screen_radius < 1:
            screen_radius = 1

        pygame.draw.circle(
            surface, self.color, (int(screen_pos.x), int(screen_pos.y)), screen_radius
        )
 