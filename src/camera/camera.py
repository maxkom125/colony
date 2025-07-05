import pygame
from pygame.math import Vector2
from .. import constants

class Camera:
    def __init__(self, initial_offset=None, initial_zoom=1.0):
        self.offset = initial_offset if initial_offset is not None else Vector2(0, 0)
        self.zoom = initial_zoom
        # Ensure zoom starts within limits
        self.zoom = max(constants.MIN_ZOOM, min(constants.MAX_ZOOM, self.zoom))

    def world_to_screen(self, pos_vec: Vector2) -> Vector2:
        """Converts world coordinates to screen coordinates using camera state."""
        # Added check for dynamic screen size update
        screen_w = constants.SCREEN_WIDTH
        screen_h = constants.SCREEN_HEIGHT
        screen_x = (pos_vec.x - self.offset.x) * self.zoom + screen_w / 2
        screen_y = (pos_vec.y - self.offset.y) * self.zoom + screen_h / 2
        return Vector2(int(screen_x), int(screen_y))

    def screen_to_world(self, screen_pos_vec: Vector2) -> Vector2:
        """Converts screen coordinates to world coordinates using camera state."""
        # Added check for dynamic screen size update
        screen_w = constants.SCREEN_WIDTH
        screen_h = constants.SCREEN_HEIGHT
        world_x = (screen_pos_vec.x - screen_w / 2) / self.zoom + self.offset.x
        world_y = (screen_pos_vec.y - screen_h / 2) / self.zoom + self.offset.y
        return Vector2(world_x, world_y)

    def handle_zoom(self, zoom_direction: int, screen_mouse_pos: Vector2):
        """Updates zoom level and offset based on mouse wheel direction and position."""
        if zoom_direction == 0:
            return

        old_zoom = self.zoom
        
        # For zoom out, use screen center; for zoom in, use mouse position
        if zoom_direction < 0:  # Zooming out - use screen center
            zoom_point = Vector2(constants.SCREEN_WIDTH / 2, constants.SCREEN_HEIGHT / 2)
        else:  # Zooming in - use mouse position
            zoom_point = screen_mouse_pos
            
        world_zoom_pos_before = self.screen_to_world(zoom_point)

        # Apply zoom change
        if zoom_direction > 0:
            self.zoom = min(constants.MAX_ZOOM, self.zoom * 1.1)
        else:
            self.zoom = max(constants.MIN_ZOOM, self.zoom * 0.9)

        # If zoom didn't actually change (due to limits), do nothing
        if abs(self.zoom - old_zoom) < constants.EPSILON:
            return

        # Adjust offset to keep world zoom position fixed
        world_zoom_pos_after = self.screen_to_world(zoom_point)
        self.offset += world_zoom_pos_before - world_zoom_pos_after

    def handle_pan(self, screen_delta: Vector2):
        """Updates camera offset based on screen drag delta."""
        if self.zoom <= constants.EPSILON: # Avoid division by zero/very small zoom
            return
        # Convert screen delta to world delta
        world_delta = screen_delta / self.zoom
        # Move camera offset *opposite* to mouse drag
        self.offset -= world_delta 