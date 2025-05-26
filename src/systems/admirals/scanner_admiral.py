import random
from pygame.math import Vector2

from ...entities.ships.scanner_ship import ScannerShip
from ...entities.asteroid import Asteroid
from ...enums import ShipState
from ...utils import find_nearest_object
from .base_admiral import Admiral, DuplicateShipError, ShipNotFoundError
from typing import TYPE_CHECKING
from ...systems.movement_system import calc_fuel_needed_round_trip
from ...logger import logger # Import the logger

if TYPE_CHECKING:
    from ...entities.entity import Entity


class ScannerAdmiral(Admiral):
    """Manages task assignments and state for all ScannerShips."""

    def __init__(self):
        super().__init__()
        self.ships: dict[int, ScannerShip]  # Type hint for clarity

    def add_ship(self, ship: ScannerShip):
        """Registers a new scanner under the admiral's command."""
        if not isinstance(ship, ScannerShip):
            logger.warning(f"Attempted to add non-ScannerShip {ship.id} to ScannerAdmiral.")
            return

        try:
            super().add_ship(ship)
        except DuplicateShipError as e:
            logger.info(f"During add_ship for {ship.id}: {e}")
            return
        # No scanner-specific assignment categories needed for now

    def remove_ship(self, ship_id: int):
        """Removes a scanner using the base method."""
        # No scanner-specific cleanup needed currently
        try:
            super().remove_ship(ship_id)
        except ShipNotFoundError as e:
            logger.info(f"During remove_ship for {ship_id}: {e}")
            return
        logger.debug(f"Scanner {ship_id} removed.")

    # --- Core Logic ---

    def issue_command(self, ship: ScannerShip, accepted_states: list[ShipState] = None):
        """Handles state transitions based on arrival or completion."""
        logger.debug(f"Issue command for Scanner {ship.id} state: {ship.state}")
        if not self.issue_command_checks(ship, accepted_states):
            return

        match ship.state:
            case ShipState.MOVING_TO_SCAN:
                # Arrived at potential scan target
                self.issue_scanning_command(ship)
            case ShipState.SCANNING:
                # Scan finished (handled internally by ship.update), potentially go idle
                # fleet.give_orders will assign idle scanners to new targets later
                logger.debug(f"Scanner {ship.id} finished scanning. Going IDLE.")
                ship.set_state(ShipState.IDLE)
                ship.set_target(None)
                # Next step: fleet.give_orders -> scanner_admiral.assign_idle_scanners
            case _:
                # For other states, use the base Admiral logic
                super().issue_command(ship, accepted_states)

    def issue_scanning_command(self, ship: ScannerShip):
        """Issues a command to start scanning if conditions are met."""
        # ---- Checks ----
        target = ship.target

        # 1. Check if target exists
        if not target:
            logger.warning(
                f"Scanner {ship.id} arrived at destination but target is missing. Going IDLE."
            )
            ship.set_state(ShipState.IDLE)
            # No need to clear target, it's already None
            return

        # 2. Check if target is an Asteroid
        if not isinstance(target, Asteroid):
            logger.debug(
                f"Scanner {ship.id} arrived at non-asteroid target {type(target).__name__} {target.id if target else 'None'}. Going IDLE."
            )
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            return

        # 3. Check if the Asteroid target is already scanned
        if target.scanned:
            logger.debug(
                f"Scanner {ship.id} arrived at already scanned Asteroid {target.id}. Going IDLE."
            )
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            return

        # ---- Logic ----
        # All checks passed, proceed with scanning
        logger.debug(f"Scanner {ship.id} arrived at unscanned Asteroid {target.id}. Starting scan.")
        ship.set_state(ShipState.SCANNING)
        # Keep the target assigned while scanning

    def _get_valid_scan_targets(self, asteroids: list[Asteroid]):
        """Find out relevant scan targets.
        Relevant targets MUST BE:
        1. Asteroid instance
        2. Unscanned
        3. Not targeted by other scanners"""

        # Get IDs of asteroids currently targeted by scanners
        currently_targeted_ids = {
            ship.target.id
            for ship in self.ships.values()
            if ship.target and isinstance(ship.target, Asteroid)
        }

        return [
            a
            for a in asteroids
            if isinstance(a, Asteroid) and (not a.scanned) and (a.id not in currently_targeted_ids)
        ]

    def assign_idle_scanners(self, asteroids: list[Asteroid]):
        """Assigns unscanned asteroids to idle scanners, avoiding already targeted ones."""
        idle_scanners: list[ScannerShip] = [
            ship for ship in self.ships.values() if ship.state == ShipState.IDLE
        ]

        if not idle_scanners:
            return  # No idle scanners to assign

        asteroids_to_scan = self._get_valid_scan_targets(asteroids)

        if not asteroids_to_scan:
            logger.debug("No asteroids available or valid to scan for any scanner.")
            return

        # Improved assignment: nearest unscanned AND untargeted asteroid
        for scanner in idle_scanners:
            target_asteroid = self._find_nearest_valid_asteroid(
                scanner.position,
                scanner.scan_range - scanner.radius,
                asteroids_to_scan,
            )

            if target_asteroid:
                # check if we have enough fuel to scan the asteroid and return to base
                fuel_needed = calc_fuel_needed_round_trip(scanner, target_asteroid)
                if scanner.fuel < fuel_needed: # Strict inequality
                    logger.debug(f"Scanner {scanner.id} (fuel: {scanner.fuel:.1f}) insufficient for Asteroid {target_asteroid.id} (needs: {fuel_needed:.1f}). Returning to base.")
                    scanner.set_state(ShipState.RETURNING_TO_BASE)
                    scanner.set_target(scanner.home)
                    continue # Try next scanner
                
                scanner.set_target(target_asteroid)
                scanner.set_state(ShipState.MOVING_TO_SCAN)
                # Remove from local list for this assignment cycle
                asteroids_to_scan.remove(target_asteroid)
                logger.debug(f"Scanner {scanner.id} assigned to scan Asteroid {target_asteroid.id}")
            else:
                logger.debug(f"No suitable untargeted scan target found for Scanner {scanner.id}.")
                # Scanner remains IDLE
    
    def _find_nearest_valid_asteroid(
        self,
        position: Vector2,
        max_radius: float,
        asteroids: list[Asteroid],
    ) -> Asteroid | None:
        """Finds the nearest asteroid, with radius < max_radius"""

        def target_filter(asteroid):
            return asteroid.radius <= max_radius

        return find_nearest_object(position, asteroids, target_filter)
