# Contents for src/entities/ships/scanner_ship.py
import pygame
from pygame.math import Vector2
from .base_ship import Spaceship  # Inherit from base
from ... import constants  # Relative import
from ..asteroid import Asteroid  # Need these for type hints/checks
from ..planet import Planet


class ScannerShip(Spaceship):
    def __init__(self, position: Vector2, angle=0):
        # Use base ship size and scanner color
        super().__init__(position, constants.SHIP_SIZE, constants.SHIP_COLOR, angle)
        self.state = "idle"  # Explicitly start idle

    def update_actions(self, dt, planet=None):
        # Handle scanning timer
        if self.state == "scanning":
            if not self.target or not isinstance(self.target, Asteroid):
                self.state = "idle"
                return

            self.scan_timer -= dt
            if self.scan_timer <= 0:
                self.target.scanned = True
                self.state = "idle"

    def handle_arrival(self, planet):
        if self.state == "moving_to_asteroid" and isinstance(self.target, Asteroid):
            if not self.target.scanned:
                self.state = "scanning"
                self.scan_timer = constants.SCAN_DURATION  # Use SCAN_DURATION constant
            else:
                # Arrived at already scanned asteroid
                self.state = "idle"
                self.target = None
        else:
            # Arrived at base or while in a non-moving state? Go idle.
            self.state = "idle"
            self.target = None

    # Uses the default draw method from base_ship.Spaceship
