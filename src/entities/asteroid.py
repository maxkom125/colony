# Contents for src/entities/asteroid.py
import pygame
from pygame.math import Vector2
import random
from .entity import Entity
from .. import constants  # Relative import
from ..enums import ResourceType


class Asteroid(Entity):
    """Represents a mineable asteroid."""

    def __init__(self, position: Vector2, radius: int, color: tuple, entity_id: int | None = None):
        # Use entity_id from base class
        super().__init__(position, radius, constants.ASTEROID_COLOR, entity_id)
        self.initial_color = constants.ASTEROID_COLOR

        chosen_res = random.choices(ResourceType.list(), weights=ResourceType.weights(), k=1)[0]
        resource_amount = random.randint(
            constants.ASTEROID_MIN_RESOURCE_AMOUNT,
            constants.ASTEROID_MAX_RESOURCE_AMOUNT,
        )
        self.resources = {res_type: 0 for res_type in ResourceType.list()}
        self.resources[chosen_res] = resource_amount
        
        self.scanned = False
        self.scan_points_remaining = self.calculate_scan_points_remaining()

    def calculate_scan_points_remaining(self):
        return self.radius * constants.SCAN_POINTS_PER_RADIUS + constants.MINIMUM_SCAN_POINTS

    def get_dominant_resource_color(self):
        if not self.resources:
            return constants.VISITED_ASTEROID_COLOR
        dominant_resource = next((
            res for res, amount in self.resources.items() if amount > 0
        ), None)
        if dominant_resource == "Tritanium": return constants.TRITANIUM_COLOR
        if dominant_resource == "Credits": return constants.CREDITS_COLOR
        if dominant_resource == "Plasma": return constants.PLASMA_COLOR
        return constants.VISITED_ASTEROID_COLOR

    def draw(self, surface, world_to_screen_func, zoom_level, font):
        screen_pos = world_to_screen_func(self.position)
        screen_radius = max(1, int(self.radius * zoom_level))

        is_depleted = self.scanned and not any(amount > 0 for amount in self.resources.values())

        draw_color = self.initial_color
        if is_depleted: draw_color = constants.DEPLETED_ASTEROID_COLOR
        elif self.scanned: draw_color = self.get_dominant_resource_color()

        pygame.draw.circle(surface, draw_color, screen_pos, screen_radius)

        if self.scanned and not is_depleted:
            dominant_res = next((res for res, amount in self.resources.items() if amount > 0), None)
            if dominant_res:
                amount = self.resources[dominant_res]
                resource_text = f"{dominant_res[:1]}:{int(amount)}"
                text_surface = font.render(resource_text, True, constants.WHITE)
                text_rect = text_surface.get_rect(center=(screen_pos.x, screen_pos.y + screen_radius + 10))
                surface.blit(text_surface, text_rect)
        elif is_depleted:
            resource_text = "0"
            text_surface = font.render(resource_text, True, constants.DEPLETED_ASTEROID_COLOR)
            text_rect = text_surface.get_rect(center=(screen_pos.x, screen_pos.y + screen_radius + 10))
            surface.blit(text_surface, text_rect)

    # update() method is inherited from Entity (currently does nothing)
 