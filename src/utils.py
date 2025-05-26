import math
from pygame.math import Vector2  # Import Vector2
from src.enums import ResourceType
from src.logger import logger # Import the logger
from typing import TYPE_CHECKING

# Conditional imports for type hints to prevent circular dependency
if TYPE_CHECKING:
    from .entities.entity import Entity # Import base Entity if needed for the list type


def find_nearest_object(source_pos_vec: Vector2, target_objects: list['Entity'], filter_func):
    """Finds the nearest object in target_objects based on distance from source_pos_vec,
    considering only objects for which filter_func(obj) returns True.
    Assumes target_objects have a .position (Vector2) attribute.
    """
    min_dist_sq = float("inf")
    suitable_target = None

    for obj in target_objects:
        # Apply the filter function provided by the caller
        if not filter_func(obj):
            continue

        # Use Vector2 distance calculation
        try:
            dist_sq = source_pos_vec.distance_squared_to(obj.position)
        except AttributeError:
            logger.error(
                f"Target object {obj} (type: {type(obj)}) missing .position attribute in find_nearest_object"
            )
            continue  # Skip object if it doesn't have a position

        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            suitable_target = obj

    return suitable_target


def line_circle_intersection(
    p1_vec: Vector2, p2_vec: Vector2, circle_center_vec: Vector2, circle_radius
):
    """Checks if the line segment p1_vec-p2_vec intersects the circle."""
    # Use Vector2 directly
    r = circle_radius
    r_sq = r * r

    # --- Bounding Box Check ---
    # Expanded check for clarity
    min_x = min(p1_vec.x, p2_vec.x) - r
    max_x = max(p1_vec.x, p2_vec.x) + r
    min_y = min(p1_vec.y, p2_vec.y) - r
    max_y = max(p1_vec.y, p2_vec.y) + r
    if (
        circle_center_vec.x < min_x
        or circle_center_vec.x > max_x
        or circle_center_vec.y < min_y
        or circle_center_vec.y > max_y
    ):
        return False

    # --- Intersection Logic using Vector Math ---
    d = p2_vec - p1_vec  # Direction vector of segment
    f = p1_vec - circle_center_vec  # Vector from circle center to p1

    a = d.dot(d)
    b = 2 * f.dot(d)
    c = f.dot(f) - r_sq

    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        return False  # No real roots
    else:
        # Avoid division by zero if segment is a point
        if a < 1e-9:
            return c <= 1e-9  # Check if point is inside or on circle (with tolerance)

        discriminant = math.sqrt(discriminant)
        t1 = (-b - discriminant) / (2 * a)
        t2 = (-b + discriminant) / (2 * a)

        # Check if intersection parameter t is within segment bounds [0, 1]
        # or if segment starts inside the circle
        if (
            (0 <= t1 <= 1) or (0 <= t2 <= 1) or (t1 < 0 and t2 > 1)
        ):  # t1 < 0 and t2 > 1 means segment spans circle
            return True

        # Explicitly check endpoints (covers tangency precision issues)
        # If p1 is inside or very close to the circle
        if f.length_squared() <= r_sq + 1e-9:
            return True
        # If p2 is inside or very close to the circle
        if (p2_vec - circle_center_vec).length_squared() <= r_sq + 1e-9:
            return True

        return False  # No intersection on the segment


def check_path_for_obstacles(
    ship_pos_vec: Vector2, next_pos_vec: Vector2, obstacles, ignore_target_obstacle
):
    """Checks if the path segment intersects any obstacle objects (Asteroids/Planets).
    Returns the closest intersecting obstacle object, or None.
    obstacles: list of obstacle objects (e.g., Asteroid instances)
    ignore_target_obstacle: The specific obstacle object to ignore (e.g., the ship's target).
    """
    closest_obstacle = None
    min_dist_sq = float("inf")

    for obs in obstacles:
        # Ignore the specific target obstacle if provided
        if ignore_target_obstacle and obs == ignore_target_obstacle:
            continue

        # Check if the obstacle has position and radius
        try:
            obs_pos_vec = obs.position
            obs_radius = obs.radius
        except AttributeError:
            logger.error(
                f"Obstacle {obs} (type: {type(obs)}) missing position/radius in check_path_for_obstacles."
            )
            continue

        # Add a small buffer to the radius for collision detection
        buffer = 5  # Collision buffer
        if line_circle_intersection(
            ship_pos_vec, next_pos_vec, obs_pos_vec, obs_radius + buffer
        ):
            dist_sq = ship_pos_vec.distance_squared_to(obs_pos_vec)
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_obstacle = obs  # Return the object itself

    return closest_obstacle

def convert_resource_type_to_enum(resource_type: str | ResourceType) -> ResourceType:
    """Converts a resource type string to a ResourceType enum.
    If resource_type is already an enum, it is returned unchanged.
    If resource_type is a string, it is converted to an enum member.
    If resource_type is not a string or enum, a ValueError is raised.
    """
    if isinstance(resource_type, ResourceType):
        return resource_type
    elif isinstance(resource_type, str):
        try:
            return ResourceType(resource_type)
        except ValueError:
            raise ValueError(f"Invalid resource type: {resource_type}")

