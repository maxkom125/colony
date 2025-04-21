import math
from pygame.math import Vector2  # Import Vector2
from . import constants
from . import utils

# from . import entities # Old import
# Import specific entity classes needed for type hints / isinstance checks
from .entities.planet import Planet
from .entities.asteroid import Asteroid
from .entities.ships.base_ship import Spaceship


def update_ship_movement(ship: Spaceship, dt, obstacles: list):
    """Calculates the ship's new position and angle based on its target and obstacles.
    Returns: (new_position_vector, new_angle_radians, arrived) tuple.
    Does NOT modify the ship object directly.
    obstacles: List of actual obstacle objects (Asteroid, Planet).
    """
    # Determine target position and arrival threshold based on ship's target type
    target_pos_vec = None
    arrival_threshold = 0
    target_obstacle_to_ignore = None  # The actual target object to ignore

    if isinstance(ship.target, Asteroid):
        target_pos_vec = ship.target.position
        arrival_threshold = (
            ship.target.radius + constants.ARRIVAL_DISTANCE_BUFFER
        )  # Use buffer constant
        target_obstacle_to_ignore = ship.target  # Ignore the target Asteroid itself
    elif isinstance(ship.target, Planet):
        target_pos_vec = ship.target.position
        # Arrive near planet edge + buffer.
        # OLD: arrival_threshold = ship.target.radius + ship.size * 0.5 + constants.ARRIVAL_DISTANCE_BUFFER
        # NEW: Simplify - just use planet radius + double buffer for easier arrival
        arrival_threshold = ship.target.radius + constants.ARRIVAL_DISTANCE_BUFFER * 2
        target_obstacle_to_ignore = (
            ship.target
        )  # Ignore the planet itself when returning to base
    else:
        # No valid target or target is not Asteroid/Planet (e.g., target is None after dumping/idle)
        # Ship shouldn't be in a moving state without a target, but handle gracefully.
        return ship.position, ship.angle, False  # Return current Vector2 position

    # --- Core Movement Logic ---
    current_pos_vec = ship.position
    target_vector = target_pos_vec - current_pos_vec
    distance_to_target = target_vector.length()

    # Check for arrival before collision checks
    if distance_to_target < arrival_threshold:
        # Arrived: Return current position, current angle, and True
        return current_pos_vec, ship.angle, True

    # Calculate ideal movement direction (normalized vector towards target)
    norm_target_vector = Vector2(0, 0)
    if distance_to_target > constants.EPSILON:  # Avoid division by zero
        try:
            norm_target_vector = target_vector.normalize()
        except (
            ValueError
        ):  # Target vector was zero length despite distance check? Safety.
            print(
                f"WARN: Zero target vector in movement for ship {ship} to {ship.target}"
            )
            norm_target_vector = Vector2(0, 0)  # Stay put if target is current pos

    # --- Collision Avoidance Check ---
    # Calculate a point slightly ahead along the intended path
    lookahead_dist = min(
        distance_to_target, ship.speed * constants.AVOIDANCE_LOOKAHEAD_TIME
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
    if (
        move_vector.length_squared() > constants.EPSILON_SQ
    ):  # Only move if move_vector is valid
        # Normalize the final move vector before applying speed and dt
        final_move_direction = move_vector.normalize()
        new_pos_vec = current_pos_vec + final_move_direction * ship.speed * dt
        # Update angle based on the actual movement direction
        new_angle = math.atan2(final_move_direction.y, final_move_direction.x)
    else:
        # No movement calculated (e.g., target vector was zero, avoidance failed)
        new_pos_vec = current_pos_vec  # Stay in the current position
        new_angle = ship.angle  # Keep the current angle

    # Return new position (Vector2), new angle, and arrival status (False)
    return new_pos_vec, new_angle, False
