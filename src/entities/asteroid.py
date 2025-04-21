# Contents for src/entities/asteroid.py
import pygame
from pygame.math import Vector2
import random
from .. import constants  # Relative import


class Asteroid:
    _next_id = 0

    def __init__(self, position: Vector2, radius, color):
        self.id = Asteroid._next_id
        Asteroid._next_id += 1

        self.position = position
        self.radius = radius
        self.initial_color = color

        chosen_resource = random.choices(
            constants.RESOURCE_TYPES, weights=constants.RESOURCE_WEIGHTS, k=1
        )[0]
        resource_amount = random.randint(
            constants.ASTEROID_MIN_RESOURCE_AMOUNT,
            constants.ASTEROID_MAX_RESOURCE_AMOUNT,
        )

        self.resources = {}
        for res_type in constants.RESOURCE_TYPES:
            self.resources[res_type] = (
                resource_amount if res_type == chosen_resource else 0
            )

        self.scanned = False

    def get_dominant_resource_color(self):
        if not self.resources:
            return self.initial_color

        dominant_resource = next(
            (res for res, amount in self.resources.items() if amount > 0), None
        )

        if dominant_resource == "Tritanium":
            return constants.TRITANIUM_COLOR
        elif dominant_resource == "Credits":
            return constants.CREDITS_COLOR
        elif dominant_resource == "Plasma":
            return constants.PLASMA_COLOR
        else:
            return constants.VISITED_ASTEROID_COLOR

    def draw(self, surface, world_to_screen_func, zoom_level, font):
        screen_pos = world_to_screen_func(self.position)
        screen_radius = int(self.radius * zoom_level)

        if screen_radius < 1:
            screen_radius = 1

        is_depleted = self.scanned and not any(
            amount > 0 for amount in self.resources.values()
        )

        if is_depleted:
            draw_color = constants.DEPLETED_ASTEROID_COLOR
        elif self.scanned:
            draw_color = self.get_dominant_resource_color()
        else:
            draw_color = self.initial_color

        pygame.draw.circle(
            surface, draw_color, (int(screen_pos.x), int(screen_pos.y)), screen_radius
        )

        if self.scanned and not is_depleted:
            dominant_res = None
            dominant_amount = 0
            for res, amount in self.resources.items():
                if amount > 0:
                    dominant_res = res
                    dominant_amount = amount
                    break

            if dominant_res:
                resource_text = f"{dominant_res[:1]}:{int(dominant_amount)}"
                text_surface = font.render(resource_text, True, constants.WHITE)
                text_rect = text_surface.get_rect(
                    center=(int(screen_pos.x), int(screen_pos.y + screen_radius + 10))
                )
                surface.blit(text_surface, text_rect)
        elif is_depleted:
            resource_text = "0"
            text_surface = font.render(
                resource_text, True, constants.DEPLETED_ASTEROID_COLOR
            )
            text_rect = text_surface.get_rect(
                center=(int(screen_pos.x), int(screen_pos.y + screen_radius + 10))
            )
            surface.blit(text_surface, text_rect)
