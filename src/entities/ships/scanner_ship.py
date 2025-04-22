# Contents for src/entities/ships/scanner_ship.py
import pygame
from pygame.math import Vector2
from .base_ship import Spaceship  # Inherit from base
from ... import constants  # Relative import
from ..asteroid import Asteroid  # Need these for type hints/checks
from ..planet import Planet
from ...enums import ShipState # Import the enum


class ScannerShip(Spaceship):
    def __init__(self, position: Vector2, angle=0):
        # Use base ship size and scanner color
        super().__init__(position, constants.SHIP_SIZE, constants.SHIP_COLOR, angle)
        self.state = ShipState.IDLE # Use Enum

    def update_actions(self, dt, planet=None):
        # Handle scanning timer
        if self.state == ShipState.SCANNING: # Use Enum
            if not self.target or not isinstance(self.target, Asteroid):
                self.state = ShipState.IDLE # Use Enum
                return

            self.scan_timer -= dt
            if self.scan_timer <= 0:
                self.target.scanned = True
                self.state = ShipState.IDLE # Use Enum

    def handle_arrival(self, planet):
        if self.state == ShipState.MOVING_TO_ASTEROID and isinstance(self.target, Asteroid): # Use Enum
            if not self.target.scanned:
                self.state = ShipState.SCANNING # Use Enum
                self.scan_timer = constants.SCAN_DURATION
            else:
                # Arrived at already scanned asteroid
                self.state = ShipState.IDLE # Use Enum
                self.target = None
        else:
            # Arrived at base or while in a non-moving state? Go idle.
            self.state = ShipState.IDLE # Use Enum
            self.target = None

    # Uses the default draw method from base_ship.Spaceship
