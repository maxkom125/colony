import pytest
from pygame.math import Vector2
from src.entities.asteroid import Asteroid
from src.utils import (
    find_nearest_object,
    line_circle_intersection,
    check_path_for_obstacles
)

# Basic Mock Object for testing
class MockObject:
    def __init__(self, x, y, radius=10, value=None):
        self.position = Vector2(x, y)
        self.radius = radius
        self.value = value # Optional attribute for filtering

    def __repr__(self):
        return f"MockObject(pos={self.position}, radius={self.radius}, value={self.value})"

# --- Mock Asteroid Setup ---
# Create a helper function or fixture to create mock asteroids for resource tests
def create_mock_asteroid(x, y, scanned=True, resources=None):
    asteroid = Asteroid(Vector2(x, y), radius=10, color=(0,0,0)) # Use actual Asteroid class
    asteroid.scanned = scanned
    # Ensure resources dict is initialized
    if resources:
        # Only set provided resources, assume others are 0
        for res_type in asteroid.resources:
            asteroid.resources[res_type] = resources.get(res_type, 0)
    else:
        # Default to 0 if no resources provided
        for res_type in asteroid.resources:
            asteroid.resources[res_type] = 0
    return asteroid

# Tests will go here
def test_find_nearest_object_basic():
    """Tests finding the mathematically nearest object."""
    source_pos = Vector2(0, 0)
    targets = [
        MockObject(10, 0),   # Distance 10
        MockObject(-5, 0),   # Distance 5
        MockObject(0, 100)   # Distance 100
    ]
    # No filter needed, accept all
    no_filter = lambda obj: True

    nearest = find_nearest_object(source_pos, targets, no_filter)

    assert nearest is targets[1] # Should be the MockObject at (-5, 0) 

def test_find_nearest_object_with_filter():
    """Tests finding the nearest object that matches a filter."""
    source_pos = Vector2(0, 0)
    targets = [
        MockObject(10, 0, value="ignore"),    # Distance 10, wrong value
        MockObject(-20, 0, value="target"),  # Distance 20, correct value
        MockObject(0, 5, value="target"),    # Distance 5, correct value (closest)
        MockObject(0, 100, value="ignore")   # Distance 100, wrong value
    ]
    # Only accept objects with value == "target"
    target_filter = lambda obj: obj.value == "target"

    nearest = find_nearest_object(source_pos, targets, target_filter)

    assert nearest is not None # Make sure we found something
    assert nearest is targets[2] # Should be MockObject(0, 5, value="target")

def test_find_nearest_object_no_match():
    """Tests the case where no objects match the filter."""
    source_pos = Vector2(0, 0)
    targets = [
        MockObject(10, 0, value="ignore"),
        MockObject(-20, 0, value="other"),
    ]
    target_filter = lambda obj: obj.value == "target"

    nearest = find_nearest_object(source_pos, targets, target_filter)

    assert nearest is None # No object should match

def test_find_nearest_object_empty_list():
    """Tests the case where the target list is empty."""
    source_pos = Vector2(0, 0)
    targets = []
    no_filter = lambda obj: True

    nearest = find_nearest_object(source_pos, targets, no_filter)

    assert nearest is None # No object should be found 


# --- Tests for line_circle_intersection --- 

@pytest.mark.parametrize(
    "p1, p2, center, radius, expected", [
        # --- Intersecting Cases ---
        # Simple horizontal crossing
        (Vector2(-10, 0), Vector2(10, 0), Vector2(0, 0), 5, True),
        # Simple vertical crossing
        (Vector2(0, -10), Vector2(0, 10), Vector2(0, 0), 5, True),
        # Diagonal crossing
        (Vector2(-10, -10), Vector2(10, 10), Vector2(0, 0), 5, True),
        # Segment starts inside, ends outside
        (Vector2(1, 1), Vector2(10, 10), Vector2(0, 0), 5, True),
        # Segment starts outside, ends inside
        (Vector2(10, 10), Vector2(1, 1), Vector2(0, 0), 5, True),
        # Segment fully inside
        (Vector2(-1, -1), Vector2(1, 1), Vector2(0, 0), 5, True),
        # Tangent
        (Vector2(-10, 5), Vector2(10, 5), Vector2(0, 0), 5, True),
        # Endpoint on circle
        (Vector2(5, 0), Vector2(10, 0), Vector2(0, 0), 5, True),
        (Vector2(-10, 0), Vector2(-5, 0), Vector2(0, 0), 5, True),
        # Segment passes through center (already covered but explicit)
        (Vector2(-10, 0), Vector2(10, 0), Vector2(0, 0), 5, True),
        # Segment starts at center, ends outside
        (Vector2(0, 0), Vector2(10, 0), Vector2(0, 0), 5, True),
        # Segment starts outside, ends at center
        (Vector2(10, 0), Vector2(0, 0), Vector2(0, 0), 5, True),

        # --- Non-Intersecting Cases ---
        # Horizontal line outside
        (Vector2(-10, 10), Vector2(10, 10), Vector2(0, 0), 5, False),
        # Vertical line outside
        (Vector2(10, -10), Vector2(10, 10), Vector2(0, 0), 5, False),
        # Diagonal line outside
        (Vector2(10, 10), Vector2(20, 20), Vector2(0, 0), 5, False),
        # Line points towards circle but doesn't reach
        (Vector2(10, 0), Vector2(6, 0), Vector2(0, 0), 5, False),
        # Zero-length segment outside
        (Vector2(10, 10), Vector2(10, 10), Vector2(0, 0), 5, False),

        # --- Edge Cases ---
        # Zero-length segment inside
        (Vector2(1, 1), Vector2(1, 1), Vector2(0, 0), 5, True),
        # Zero-length segment on circle boundary
        (Vector2(5, 0), Vector2(5, 0), Vector2(0, 0), 5, True),
        # Zero-length segment at center (is inside)
        (Vector2(0, 0), Vector2(0, 0), Vector2(0, 0), 5, True),
    ]
)
def test_line_circle_intersection(p1, p2, center, radius, expected):
    """Tests line_circle_intersection with various scenarios."""
    assert line_circle_intersection(p1, p2, center, radius) == expected 


# --- Tests for check_path_for_obstacles --- 

def test_check_path_no_obstacles():
    """Tests path checking when the obstacles list is empty."""
    start_pos = Vector2(0, 0)
    end_pos = Vector2(100, 0)
    obstacles = []
    colliding_obstacle = check_path_for_obstacles(start_pos, end_pos, obstacles, None)
    assert colliding_obstacle is None

def test_check_path_clear():
    """Tests a path that is clearly not blocked by any obstacles."""
    start_pos = Vector2(0, 0)
    end_pos = Vector2(100, 0)
    obstacle = MockObject(50, 50, radius=10) # Obstacle far off the path
    obstacles = [obstacle]
    colliding_obstacle = check_path_for_obstacles(start_pos, end_pos, obstacles, None)
    assert colliding_obstacle is None

def test_check_path_blocked_single():
    """Tests a path directly blocked by a single obstacle."""
    start_pos = Vector2(0, 0)
    end_pos = Vector2(100, 0)
    obstacle = MockObject(50, 0, radius=10) # Obstacle directly on the path
    obstacles = [obstacle]
    colliding_obstacle = check_path_for_obstacles(start_pos, end_pos, obstacles, None)
    assert colliding_obstacle is obstacle # Should return the blocking obstacle 

def test_check_path_multiple_obstacles_selects_closest():
    """Path intersects multiple obstacles; should return the closest one."""
    start_pos = Vector2(0, 0)
    end_pos = Vector2(100, 0)
    obs_close = MockObject(30, 0, radius=10)
    obs_far = MockObject(70, 0, radius=10)
    obstacles = [obs_far, obs_close]
    result = check_path_for_obstacles(start_pos, end_pos, obstacles, None)
    assert result is obs_close


def test_check_path_with_ignore_target_obstacle():
    """Path blocked by ignored obstacle; should skip it and return the next closest."""
    start_pos = Vector2(0, 0)
    end_pos = Vector2(100, 0)
    obs1 = MockObject(30, 0, radius=10)
    obs2 = MockObject(70, 0, radius=10)
    obstacles = [obs1, obs2]
    result = check_path_for_obstacles(start_pos, end_pos, obstacles, obs1)
    assert result is obs2


def test_check_path_ignore_only_blocking_obstacle():
    """When ignoring the only blocking obstacle, should return None."""
    start_pos = Vector2(0, 0)
    end_pos = Vector2(100, 0)
    obs = MockObject(50, 0, radius=10)
    result = check_path_for_obstacles(start_pos, end_pos, [obs], obs)
    assert result is None


def test_check_path_start_inside_obstacle():
    """When starting inside an obstacle, should detect collision immediately."""
    start_pos = Vector2(0, 0)
    end_pos = Vector2(100, 0)
    obs = MockObject(0, 0, radius=5)
    result = check_path_for_obstacles(start_pos, end_pos, [obs], None)
    assert result is obs


def test_check_path_obstacle_detected_with_buffer():
    """Obstacle just outside path but within buffer should be detected."""
    start_pos = Vector2(0, 0)
    end_pos = Vector2(100, 0)
    # obstacle with radius 3 at y=8; radius+buffer=8 => tangent intersection
    obs = MockObject(50, 8, radius=3)
    result = check_path_for_obstacles(start_pos, end_pos, [obs], None)
    assert result is obs 