import pytest
from pygame.math import Vector2
from src.camera.camera import Camera
from src import constants


def test_world_to_screen_default():
    cam = Camera()
    # origin should map to screen center when offset=0 and zoom=1
    hw = constants.SCREEN_WIDTH / 2
    hh = constants.SCREEN_HEIGHT / 2
    screen_pos = cam.world_to_screen(Vector2(0, 0))
    assert screen_pos == Vector2(int(hw), int(hh))


def test_screen_to_world_inverse():
    cam = Camera()
    sp = Vector2(100, 200)
    world_pos = cam.screen_to_world(sp)
    # mapping back to screen should recover original screen pos
    sp2 = cam.world_to_screen(world_pos)
    assert sp2 == sp


def test_handle_pan_moves_offset():
    cam = Camera()
    cam.offset = Vector2(0, 0)
    cam.zoom = 1.0
    delta = Vector2(10, 20)
    cam.handle_pan(delta)
    # offset should move opposite to pan (minus world_delta)
    assert cam.offset == Vector2(-10, -20)


def test_handle_pan_ignores_when_zoom_zero():
    cam = Camera()
    cam.offset = Vector2(5, 5)
    # set zoom below epsilon
    cam.zoom = constants.EPSILON_SQ
    cam.handle_pan(Vector2(10, 10))
    assert cam.offset == Vector2(5, 5)


def test_handle_zoom_keeps_mouse_world_pos_fixed_on_zoom_in():
    cam = Camera(initial_offset=Vector2(100, 50), initial_zoom=1.0)
    sp = Vector2(300, 300)
    before = cam.screen_to_world(sp)
    cam.handle_zoom(1, sp)  # zoom in
    after = cam.screen_to_world(sp)
    assert pytest.approx(before.x, rel=1e-6) == after.x
    assert pytest.approx(before.y, rel=1e-6) == after.y
    # zoom should have increased
    assert cam.zoom > 1.0


def test_handle_zoom_keeps_mouse_world_pos_fixed_on_zoom_out():
    cam = Camera(initial_offset=Vector2(100, 50), initial_zoom=1.0)
    sp = Vector2(300, 300)
    before = cam.screen_to_world(sp)
    cam.handle_zoom(-1, sp)  # zoom out
    after = cam.screen_to_world(sp)
    assert pytest.approx(before.x, rel=1e-6) == after.x
    assert pytest.approx(before.y, rel=1e-6) == after.y
    # zoom should have decreased
    assert cam.zoom < 1.0


def test_handle_zoom_clamps_at_max_zoom():
    cam = Camera(initial_zoom=constants.MAX_ZOOM)
    cam.offset = Vector2(10, 20)
    old_offset = cam.offset.copy()
    cam.handle_zoom(1, Vector2(0, 0))
    assert cam.zoom == constants.MAX_ZOOM
    assert cam.offset == old_offset


def test_handle_zoom_clamps_at_min_zoom():
    cam = Camera(initial_zoom=constants.MIN_ZOOM)
    cam.offset = Vector2(10, 20)
    old_offset = cam.offset.copy()
    cam.handle_zoom(-1, Vector2(0, 0))
    assert cam.zoom == constants.MIN_ZOOM
    assert cam.offset == old_offset 