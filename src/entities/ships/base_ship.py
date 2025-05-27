# Contents for src/entities/ships/base_ship.py
import pygame
import itertools  # For generating unique IDs
from pygame.math import Vector2
from ... import constants  # Relative import
from ..entity import Entity  # Inherit from Entity
from ...enums import ShipState, ShipType, ResourceType
from ..asteroid import Asteroid
from ..planet import Planet
from ...systems.movement_system import update_ship_movement
from typing import TYPE_CHECKING
from ...logger import logger  # Import the logger

if TYPE_CHECKING:
    from ...systems.admirals.base_admiral import Admiral


class Ship(Entity):
    """Base class for all player-controlled ships."""

    # Class variable to generate unique IDs
    _id_counter = itertools.count(1)

    def __init__(
        self,
        position: Vector2,
        radius: int,
        color: tuple,
        speed: float,
        home_planet: Planet,
        ship_id: int | None = None,
        *args,
        **kwargs,
    ):
        # Use passed-in values, defaults should be handled by subclasses using constants
        assigned_id = ship_id if ship_id is not None else next(Ship._id_counter)
        super().__init__(position, radius, color, assigned_id)

        self.speed = speed
        self.home: Planet = home_planet
        self.target: Entity | None = None
        self.state = ShipState.IDLE
        self.type = ShipType.UNKNOWN
        self.angle = 0.0  # Add angle property, default to 0 rad

        self.admiral: "Admiral" | None = None  # Will be set when added to fleet

        # Timers - may or may not be used by all subclasses
        self.scan_timer = 0.0
        self.mining_timer = 0.0
        self.dumping_timer = 0.0

        # Cargo - relevant for mining/transport ships
        self.cargo_capacity = 0
        self.fuel_max_capacity = constants.BASE_FUEL_MAX_CAPACITY
        if "fuel" not in kwargs:
            self.fuel = 0
        else:
            self.fuel = kwargs["fuel"]
        self.fuel_consumption_rate = constants.BASE_FUEL_CONSUMPTION_RATE
        self.fuel_refill_rate = constants.BASE_FUEL_REFILL_RATE
        self.cargo = {res_type: 0 for res_type in ResourceType.list()}  # Use enum list here

    def set_target(self, target_entity: Entity | None):
        """Sets the ship's target and initial state for moving."""
        self.target = target_entity
        self.reset_timers()

    def get_cargo_total(self) -> int:
        """Returns the total amount of resources currently in the cargo hold."""
        return sum(self.cargo.values())

    def update(self, dt: float, obstacles: list[Asteroid | Planet]):
        """Base update loop. Calls movement update. Subclasses add state actions."""
        self.update_movement(dt, obstacles)
        self.refill_fuel(dt)
        # Subclasses will add their state-specific action logic here
        # by overriding this method and calling super().update(dt)

    def burn_fuel(self, distance: float):
        """Burn fuel amount corresponding to cover distance"""
        if distance <= 0:
            logger.debug(f"{self.type} {self.id}: Burn no fuel: distance is 0!")
            return

        fuel_to_burn = self.fuel_consumption_rate * distance
        if fuel_to_burn > self.fuel:
            self.fuel = 0
        else:
            self.fuel -= fuel_to_burn

        return

    def refill_fuel(self, dt: float):
        # --- Helper function for this context ---
        def _issue_command_refueling_context():
            self.admiral.issue_command(self, accepted_states=[ShipState.REFUELING])

        # --- Original Checks ---
        is_refilling = self.state in ShipState.refilling_ship_states()

        if not is_refilling:
            return  # Not in a state for fuel refill
        # Check if we need to refuel in other states
        if self.fuel >= self.fuel_max_capacity and self.state != ShipState.REFUELING:
            logger.debug(
                f"{self.type} {self.id} already at max fuel, in {self.state}. Skipping refueling."
            )
            return  # Already at max fuel, nothing to do

        if self.admiral is None:
            logger.error(f"{self.type} {self.id} has no admiral! This should never happen!")
            return

        # Check if target is a Planet
        if type(self.target) is not Planet:
            logger.error(
                f"{self.type} {self.id} tried to refuel from a non-planet ({self.target.id}). This should never happen!"
            )
            _issue_command_refueling_context()
            return  # Not a planet, nothing to refill from

        # Check if target is the home planet
        if self.target != self.home:
            logger.error(
                f"{self.type} {self.id} is refilling from a non-home planet ({self.target.id}). This should never happen!"
            )
            _issue_command_refueling_context()
            return

        if not hasattr(self.target, "storage"):
            # TODO: add function name ref: logging %(funcName)
            logger.error(f"Refill target {type(self.target)} has no storage attribute!")
            _issue_command_refueling_context()
            return

        # Check if the planet has plasma to spare
        if self.target.storage.get(ResourceType.PLASMA, 0) <= 0:
            logger.warning(
                f"{self.type} {self.id} is refilling from a planet with no plasma to spare: {self.target.storage}"
            )
            _issue_command_refueling_context()
            return  # No plasma to spare, nothing to do # TODO: hud notification

        # --- Refill Logic ---
        fuel_needed = self.fuel_max_capacity - self.fuel
        if fuel_needed <= constants.EPSILON:
            _issue_command_refueling_context()  # Refilling finished or not needed
            return

        max_available = (
            self.target.storage.get(ResourceType.PLASMA, 0)
            * constants.PLASMA_TO_FUEL_CONVERSION_RATE
        )
        can_take = min(fuel_needed, max_available)

        potential_refill_amount = self.fuel_refill_rate * dt
        actual_refilled = min(potential_refill_amount, can_take)
        # --- Check if this refill will reach max fuel capacity
        if actual_refilled > 0:
            self.fuel += actual_refilled
            self.target.storage[ResourceType.PLASMA] -= (
                actual_refilled / constants.PLASMA_TO_FUEL_CONVERSION_RATE
            )
            # TODO: refueling timer (like mining_timer)
        else:
            logger.error(
                f"{self.type} {self.id} refilled 0 fuel. Fuel needed: {fuel_needed}, Max available: {max_available}, Potential: {potential_refill_amount}, Can take: {can_take}. This might indicate an issue."
            )
            _issue_command_refueling_context()

    def update_movement(self, dt: float, obstacles: list[Asteroid | Planet]):
        """Handles moving the ship towards its target and checks for arrival."""
        # --- Checks ---
        if not self.target:  # No target, nothing to move towards
            return

        # Check if actually in a moving state using the constant set
        is_moving = self.state in ShipState.moving_ship_states()  # Use the enum method

        if not is_moving:
            return  # Not in a state where movement occurs

        # --- Movement ---
        initial_position = self.position
        self.position, self.angle, ship_arrived = update_ship_movement(self, dt, obstacles)
        self.burn_fuel((self.position - initial_position).length())
        if ship_arrived:
            if self.admiral:
                self.admiral.issue_command(self)
            else:
                logger.error(f"{self.type} {self.id} has no admiral, cannot issue arrival command.")
                return

    def get_arrival_threshold(self):
        if self.target and hasattr(self.target, "radius"):
            return self.radius + self.target.radius + constants.ARRIVAL_DISTANCE_BUFFER
        else:
            logger.warning(
                f"{self.type} {self.id} has no target (or target missing radius), returning 0 arrival threshold. Target: {self.target}"
            )
            return 0

    def handle_arrival(self):
        """DEPRECATED."""
        logger.warning("DEPRECATED: handle_arrival is deprecated")

    def set_state(self, new_state: ShipState):
        """Sets the ship's state and resets any relevant timers."""
        self.state = new_state
        self.reset_timers()

    def reset_timers(self):
        """Resets timers when state changes. Base class does nothing."""
        pass

    def _calculate_rotated_screen_points(
        self, relative_points: list[Vector2], world_to_screen_func, zoom_level
    ) -> list[Vector2]:
        """Helper to calculate rotated and translated screen points for drawing."""
        screen_pos = world_to_screen_func(self.position)
        rotated_screen_points = []
        for p_rel in relative_points:
            # Rotate point around (0,0) using self.angle
            p_rot = p_rel.rotate_rad(self.angle)
            # Translate rotated point to screen position
            p_screen = screen_pos + p_rot
            rotated_screen_points.append(p_screen)
        return rotated_screen_points

    def get_radius_to_draw(self, zoom_level) -> int:
        """Helper to get the radius to draw for the ship."""
        return max(3, int(self.radius * zoom_level))

    def draw(self, surface, world_to_screen_func, zoom_level):
        """Draws the base ship shape (triangle) using the helper method."""
        screen_radius = self.get_radius_to_draw(zoom_level)

        # Define base triangle points relative to (0,0)
        p1_rel = Vector2(screen_radius, 0)
        p2_rel = Vector2(-screen_radius * 0.6, screen_radius * 0.7)
        p3_rel = Vector2(-screen_radius * 0.6, -screen_radius * 0.7)
        relative_points = [p1_rel, p2_rel, p3_rel]

        # Calculate final screen points using the helper
        screen_points = self._calculate_rotated_screen_points(
            relative_points, world_to_screen_func, zoom_level
        )

        # Draw the polygon
        pygame.draw.polygon(surface, self.color, screen_points)
