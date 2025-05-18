# Contents for src/entities/ships/scanner_ship.py
import pygame
from pygame.math import Vector2
from .base_ship import Ship  # Correct import from base_ship
from ... import constants  # Relative import
from ..asteroid import Asteroid  # Need these for type hints/checks
from ..planet import Planet
from ...enums import ShipState, ShipType  # Import the enum
from ..entity import Entity  # For target type hint
from typing import TYPE_CHECKING

# Add type hint for the specific admiral
if TYPE_CHECKING:
    from ...systems.admirals.scanner_admiral import ScannerAdmiral


class ScannerShip(Ship):
    """A ship designed for scanning celestial objects."""

    def __init__(self, position: Vector2, home_planet: Planet, ship_id: int | None = None, *args, **kwargs):
        # Use constants for scanner ship specific values
        super().__init__(
            position,
            constants.SHIP_SIZE,
            constants.SHIP_COLOR,
            constants.SCANNER_SPEED,
            home_planet,  # Pass home_planet
            ship_id,
            *args, **kwargs
        )
        self.type = ShipType.SCANNER
        self.scan_range = constants.SCANNER_SCAN_RANGE
        self.scan_timer = 0.0
        # Add scan rate
        self.scan_rate = constants.SCANNER_SCAN_RATE
        self.admiral: "ScannerAdmiral" | None = None  # Type hint specific admiral
        # Scanner specific states could be added here
        # self.state = ShipState.IDLE # Inherited state is sufficient for now

    def update(self, dt: float, obstacles: list[Entity]):
        """Updates the scanner ship's state and movement."""
        super().update(dt, obstacles)  # Base class handles movement & arrival check

        if self.state == ShipState.SCANNING:
            # ---- Checks ----
            if not self.target:
                print(f"WARN: Scanner {self.id} lost target while SCANNING. Going IDLE.")
                self.set_state(ShipState.IDLE)
                return

            # Ensure target is an Asteroid and has scan points attribute
            if not isinstance(self.target, Asteroid) or not hasattr(
                self.target, "scan_points_remaining"
            ):
                print(
                    f"WARN: Scanner {self.id} scanning invalid target {type(self.target).__name__} {self.target.id}. Going IDLE."
                )
                self.set_state(ShipState.IDLE)
                self.set_target(None)
                return

            # ---- Scanning Logic ----
            if self.target.scan_points_remaining > constants.EPSILON:
                scan_amount = dt * self.scan_rate
                self.target.scan_points_remaining -= min(
                    scan_amount, self.target.scan_points_remaining
                )
                # Update timer for UI based on remaining points
                self.scan_timer = self.target.scan_points_remaining / max(
                    self.scan_rate, constants.EPSILON
                )
            else:
                # Target is fully scanned or was already scanned
                self.target.scan_points_remaining = 0  # Ensure clamped
                self.target.scanned = True
                self.scan_timer = 0.0  # Ensure timer shows 0
                print(
                    f"DEBUG: Ship {self.id} finished scanning Asteroid {self.target.id}. "
                    f"Resources: {self.target.resources}"
                )
                self.admiral.issue_command(self)

        # MOVING_TO_POSITION is handled entirely by base class update_movement
        # If specific arrival logic is needed, it should be in handle_arrival
        # elif self.state == ShipState.MOVING_TO_POSITION:
        #     pass # Base class handles movement and arrival

    def get_arrival_threshold(self):
        if self.state in [ShipState.MOVING_TO_SCAN, ShipState.IDLE]:
            return self.scan_range
        else:
            return super().get_arrival_threshold()

    # Explicitly define draw, using the base class implementation
    def draw(self, surface, world_to_screen_func, zoom_level):
        """Draws the scanner ship using the base class draw method."""
        super().draw(surface, world_to_screen_func, zoom_level)

    def reset_timers(self):
        """Resets the scan timer when state changes."""
        self.scan_timer = 0.0
