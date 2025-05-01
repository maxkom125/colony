# Contents for src/entities/ships/scanner_ship.py
import pygame
from pygame.math import Vector2
from .base_ship import Ship  # Correct import from base_ship
from ... import constants  # Relative import
from ..asteroid import Asteroid  # Need these for type hints/checks
from ..planet import Planet
from ...enums import ShipState, ShipType # Import the enum
from ..entity import Entity  # For target type hint
from ...systems.admirals.base_admiral import Admiral


class ScannerShip(Ship):
    """A ship designed for scanning celestial objects."""
    def __init__(self, position: Vector2, home_planet: Planet, ship_id: int | None = None):
        # Use constants for scanner ship specific values
        super().__init__(
            position, 
            constants.SHIP_SIZE, 
            constants.SHIP_COLOR, 
            constants.SCANNER_SPEED, 
            home_planet, # Pass home_planet
            ship_id
        )
        self.type = ShipType.SCANNER
        self.scan_range = constants.SCANNER_SCAN_RANGE
        self.scan_duration = constants.SCAN_DURATION
        self.scan_timer = 0.0
        # Temporary dummy admiral with issue_command method
        admiral = Admiral()
        admiral.add_ship(self) # self.admiral will be set here
        self.admiral.issue_command = lambda x: self.handle_arrival()
        # Scanner specific states could be added here
        # self.state = ShipState.IDLE # Inherited state is sufficient for now

    def update(self, dt: float, obstacles: list[Entity]):
        """Updates the scanner ship's state and movement."""
        super().update(dt, obstacles) # Base class handles movement & arrival check

        if self.state == ShipState.SCANNING:
            if self.target:
                self.scan_timer -= dt
                if self.scan_timer <= 0:
                    # Scan complete!
                    if hasattr(self.target, 'scanned'):
                        self.target.scanned = True
                        print(f"DEBUG: Ship {self.id} scanned {type(self.target).__name__} {self.target.id}. Resources: {self.target.resources}")
                    else:
                        print(f"WARN: Ship {self.id} finished scanning non-scannable target {type(self.target).__name__} {self.target.id}")
                    
                    # Go idle after scan completion, clear target
                    self.set_state(ShipState.IDLE)
                    self.target = None 
            else:
                 # Target lost mid-scan
                 print(f"WARN: Scanner {self.id} lost target while SCANNING. Going IDLE.")
                 self.set_state(ShipState.IDLE)

        # MOVING_TO_POSITION is handled entirely by base class update_movement
        # If specific arrival logic is needed, it should be in handle_arrival
        # elif self.state == ShipState.MOVING_TO_POSITION:
        #     pass # Base class handles movement and arrival

    def assign_scan_target(self, entity: Entity):
        """Assigns a target entity for the scanner to move towards and scan."""
        # TODO: handle with Admiral
        if hasattr(entity, 'scanned') and not entity.scanned and super().get_arrival_threshold() < self.scan_range:
            self.target = entity
            self.set_state(ShipState.MOVING_TO_SCAN)
        else:
            print(f"WARN: Cannot assign scan target to already scanned or non-scannable entity {entity.id}")

    def get_arrival_threshold(self):
        if self.state == ShipState.MOVING_TO_SCAN:
            return self.scan_range
        else:
            return super().get_arrival_threshold()
    
    def handle_arrival(self):
        # TODO: handle with Admiral
        if self.state == ShipState.MOVING_TO_SCAN and isinstance(self.target, Asteroid):
            if not self.target.scanned:
                print(f"DEBUG: Scanner {self.id} arrived at Asteroid {self.target.id}, starting scan.")
                self.set_state(ShipState.SCANNING)
                self.scan_timer = constants.SCAN_DURATION
                # Keep target while scanning
            else:
                # Arrived at already scanned asteroid
                print(f"DEBUG: Scanner {self.id} arrived at scanned Asteroid {self.target.id}, going idle.")

    # Uses the default draw method from base_ship.Spaceship

    def reset_timers(self):
        """Resets the scan timer when state changes."""
        self.scan_timer = 0.0
