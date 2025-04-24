import pytest
from pygame.math import Vector2
from src.camera.camera import Camera


def test_world_to_screen_and_back_with_offset_and_zoom():
    cam = Camera()
    cam.offset = Vector2(50, -30)
    cam.zoom = 2.5
    world_pos = Vector2(10, -20)
    screen_pos = cam.world_to_screen(world_pos)
    result_world = cam.screen_to_world(screen_pos)
    assert result_world.x == pytest.approx(world_pos.x)
    assert result_world.y == pytest.approx(world_pos.y) 