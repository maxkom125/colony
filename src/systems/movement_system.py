import math
from pygame.math import Vector2
from typing import TYPE_CHECKING, Union  # Add Union import

from .. import constants
from .. import utils

# Conditional imports to break circular dependency
if TYPE_CHECKING:
    # Import specific entity classes needed for type hints / isinstance checks
    from ..entities.planet import Planet
    from ..entities.asteroid import Asteroid
    from ..entities.ships.base_ship import Ship


# Type hint using string literals for Ship, Asteroid, and Planet
def update_ship_movement(
    ship: "Ship", dt: float, obstacles: list[Union["Asteroid", "Planet"]]
) -> tuple[Vector2, float, bool]:
    """Calculates the ship's new position and angle based on its target and obstacles.
    Returns: (new_position_vector, new_angle_radians, arrived) tuple.
    Does NOT modify the ship object directly.
    obstacles: List of actual obstacle objects (Asteroid, Planet).
    """
    target_pos_vec = None
    arrival_threshold = 0
    target_obstacle_to_ignore = None  # The actual target object to ignore

    # --- Determine Target Info and Calculate Arrival Threshold ---
    # Use sum of radii + buffer for arrival detection
    if ship.target and hasattr(ship.target, "position") and hasattr(ship.target, "radius"):
        target_pos_vec = ship.target.position
        target_obstacle_to_ignore = ship.target
        # Calculate threshold based on both radii + buffer
        arrival_threshold = ship.get_arrival_threshold()
    else:
        # No target, return current position and angle
        print(f"WARN: Ship {ship.id} has no target, returning current position and angle.")
        return ship.position, ship.angle, False

    # --- Core Movement Logic ---
    current_pos_vec = ship.position
    target_vector = target_pos_vec - current_pos_vec
    distance_to_target = target_vector.length()

    # Check for arrival using the correct threshold
    if distance_to_target <= arrival_threshold:  # Use <= for robustness
        # Arrived: Return current position, current angle, and True
        return current_pos_vec, ship.angle, True

    # Calculate ideal movement direction (normalized vector towards target)
    norm_target_vector = Vector2(0, 0)
    if distance_to_target > constants.EPSILON:  # Avoid division by zero
        try:
            norm_target_vector = target_vector.normalize()
        except ValueError:  # Target vector was zero length despite distance check? Safety.
            print(f"WARN: Zero target vector in movement for ship {ship} to {ship.target}")
            norm_target_vector = Vector2(0, 0)  # Stay put if target is current pos

    # --- Pre-calculate potential move distance ---
    potential_move_dist = ship.speed * dt
    if ship.fuel <= constants.EPSILON:
        potential_move_dist *= constants.NO_FUEL_MULTIPLIER
    distance_to_arrival_point = distance_to_target - arrival_threshold

    # --- Check if this move step will reach or cross the arrival threshold ---
    if potential_move_dist >= distance_to_arrival_point and distance_to_arrival_point > 0:
        # Clamp movement to the arrival threshold
        # Calculate the position exactly on the threshold
        clamped_move_dist = distance_to_arrival_point
        new_pos_vec = current_pos_vec + norm_target_vector * clamped_move_dist
        # Angle towards the target
        new_angle = math.atan2(norm_target_vector.y, norm_target_vector.x)
        # Return the clamped position and signal arrival
        return new_pos_vec, new_angle, True

    # --- Collision Avoidance Check (if not arriving this step) ---
    # Calculate a point slightly ahead along the intended path
    lookahead_dist = min(
        distance_to_target, ship.speed * max(constants.AVOIDANCE_LOOKAHEAD_TIME, dt * 2)
    )  # Don't look beyond target
    intended_next_pos_vec = current_pos_vec + norm_target_vector * lookahead_dist

    # Use the updated utils function which takes objects
    closest_obstacle_object = utils.check_path_for_obstacles(
        current_pos_vec,
        intended_next_pos_vec,
        obstacles,  # Pass the list of actual obstacle objects
        target_obstacle_to_ignore,  # Pass the specific target object to ignore
    )

    move_vector = Vector2(0, 0)  # Initialize move vector
    # --- Determine Actual Move Vector (Avoidance or Direct) ---
    if closest_obstacle_object:
        # --- Avoidance Maneuver ---
        obs_pos_vec = closest_obstacle_object.position
        # Vector from obstacle center to ship's current position
        vector_from_obstacle = current_pos_vec - obs_pos_vec

        # Normalize the vector pointing away from the obstacle
        # If ship is exactly at obstacle center, pick an arbitrary direction (e.g., up)
        if vector_from_obstacle.length_squared() > constants.EPSILON_SQ:
            avoid_direction = vector_from_obstacle.normalize()
        else:
            avoid_direction = Vector2(0, 1)  # Default escape upwards

        # Calculate tangent vectors (rotate avoid_direction by +/- 90 degrees)
        tangent1_vector = avoid_direction.rotate(90)
        tangent2_vector = avoid_direction.rotate(-90)

        # Choose the tangent direction that is generally closer to the original target direction
        dot1 = tangent1_vector.dot(norm_target_vector)
        dot2 = tangent2_vector.dot(norm_target_vector)

        # Steer tangentially
        if dot1 >= dot2:
            move_vector = tangent1_vector
        else:
            move_vector = tangent2_vector

        # Fallback: If tangents are somehow zero or parallel to target, move directly away
        if move_vector.length_squared() < constants.EPSILON_SQ:
            move_vector = avoid_direction

    else:  # No obstacle detected in the path
        # --- Normal Movement ---
        move_vector = norm_target_vector

    # --- Calculate Final Position and Angle ---
    # Apply movement based on the determined move_vector
    if move_vector.length_squared() > constants.EPSILON_SQ:  # Only move if move_vector is valid
        # Normalize the final move vector before applying speed and dt
        final_move_direction = move_vector.normalize()
        # Apply the *full* potential move distance calculated earlier
        new_pos_vec = current_pos_vec + final_move_direction * potential_move_dist
        # Update angle based on the actual movement direction
        new_angle = math.atan2(final_move_direction.y, final_move_direction.x)
    else:
        # No movement calculated (e.g., target vector was zero, avoidance failed)
        new_pos_vec = current_pos_vec  # Stay in the current position
        new_angle = ship.angle  # Keep the current angle

    # Return new position (Vector2), new angle, and arrival status (False)
    return new_pos_vec, new_angle, False


def calc_fuel_needed_round_trip(ship: "Ship", target: "Asteroid | Planet"):
    """Approximates the fuel needed to scan the asteroid and return to base.
    WARNING: This is an approximation and not very accurate!"""
    # ---- Checks ----
    if ship.home is None:
        print(f"ERROR: Scanner {ship.id} has no home planet set. This should never happen!")
        return 0

    # ---- Logic ----
    # Calculate fuel needed for the round trip
    distance = ship.position.distance_to(target.position)
    distance += target.position.distance_to(ship.home.position)
    # ---- Calculate fuel needed ----
    fuel_needed = distance * ship.fuel_consumption_rate
    return fuel_needed