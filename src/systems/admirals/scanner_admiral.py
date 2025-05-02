import random
from pygame.math import Vector2

from ...entities.ships.scanner_ship import ScannerShip
from ...entities.asteroid import Asteroid
from ...enums import ShipState
from ...utils import find_nearest_object
from .base_admiral import Admiral, DuplicateShipError, ShipNotFoundError
from typing import TYPE_CHECKING

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
            print(f"WARN: Attempted to add non-ScannerShip {ship.id} to ScannerAdmiral.")
            return

        try:
            super().add_ship(ship)
        except DuplicateShipError as e:
            print(f"INFO: {e}")
            return
        # No scanner-specific assignment categories needed for now

    def remove_ship(self, ship_id: int):
        """Removes a scanner using the base method."""
        # No scanner-specific cleanup needed currently
        try:
            super().remove_ship(ship_id)
        except ShipNotFoundError as e:
            print(f"INFO: {e}")
            return
        print(f"DEBUG: Scanner {ship_id} removed.")

    # --- Core Logic ---

    def issue_command(self, ship: ScannerShip):
        """Handles state transitions based on arrival or completion."""
        match ship.state:
            case ShipState.MOVING_TO_SCAN:
                # Arrived at potential scan target
                self.issue_scanning_command(ship)
            case ShipState.SCANNING:
                # Scan finished (handled internally by ship.update), potentially go idle
                # If scan finishes, ship update sets state to IDLE.
                # Base Admiral handles IDLE state by calling issue_command_to_idle_ship
                # So no specific action needed here for SCANNING completion.
                ship.set_state(ShipState.IDLE)
                ship.set_target(None)
                print(f"DEBUG: Scanner {ship.id} finished scanning. Going IDLE.")
                pass  # Let ship update handle completion -> IDLE
            case _:
                # For IDLE or other states, use the base Admiral logic
                super().issue_command(ship)

    def issue_scanning_command(self, ship: ScannerShip):
        """Issues a command to start scanning if conditions are met."""
        # ---- Checks ----
        target = ship.target

        # 1. Check if target exists
        if not target:
            print(
                f"WARN: Scanner {ship.id} arrived at destination but target is missing. Going IDLE."
            )
            ship.set_state(ShipState.IDLE)
            # No need to clear target, it's already None
            return

        # 2. Check if target is an Asteroid
        if not isinstance(target, Asteroid):
            print(
                f"DEBUG: Scanner {ship.id} arrived at non-asteroid target {type(target).__name__} {target.id}. Going IDLE."
            )
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            return

        # 3. Check if the Asteroid target is already scanned
        if target.scanned:
            print(
                f"DEBUG: Scanner {ship.id} arrived at already scanned Asteroid {target.id}. Going IDLE."
            )
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            return

        # ---- Logic ----
        # All checks passed, proceed with scanning
        print(f"DEBUG: Scanner {ship.id} arrived at unscanned Asteroid {target.id}. Starting scan.")
        ship.set_state(ShipState.SCANNING)
        # Keep the target assigned while scanning

    def issue_command_to_idle_ship(self, ship: ScannerShip):
        """Assigns a new scan target to an idle scanner."""
        # This will be triggered by the Fleet calling assign_idle_scanners,
        # which then calls this if a target is found.
        # The actual target finding happens in assign_idle_scanners.
        # If a target was successfully assigned to the ship *before* calling this,
        # the ship's state should already be MOVING_TO_SCAN.
        # If no target could be assigned, the ship remains IDLE.
        # We might reconsider if this function is truly needed, or if
        # assign_idle_scanners should directly set the state.
        # For now, let's assume assign_idle_scanners finds a target and sets state.
        print(
            f"DEBUG: issue_command_to_idle_ship called for Scanner {ship.id}. Task assignment expected from assign_idle_scanners."
        )
        pass  # Primary assignment logic is in assign_idle_scanners

    def assign_idle_scanners(self, asteroids: list[Asteroid]):
        """Assigns unscanned asteroids to idle scanners, avoiding already targeted ones."""
        idle_scanners: list[ScannerShip] = [
            ship for ship in self.ships.values() if ship.state == ShipState.IDLE
        ]

        if not idle_scanners:
            return  # No idle scanners to assign

        unscanned_asteroids: list[Asteroid] = [
            a for a in asteroids if isinstance(a, Asteroid) and not a.scanned
        ]

        # Get IDs of asteroids currently targeted by scanners
        currently_targeted_ids = {
            ship.target.id
            for ship in self.ships.values()
            if ship.target and isinstance(ship.target, Asteroid)
        }
        if not unscanned_asteroids:
            print("DEBUG: No unscanned asteroids left!")
            return

        # Improved assignment: nearest unscanned AND untargeted asteroid
        for scanner in idle_scanners:
            target_asteroid = self._find_nearest_unscanned_asteroid(
                scanner.position,
                unscanned_asteroids,
                currently_targeted_ids,  # Pass the set of already targeted asteroids
            )

            if target_asteroid:
                # Use set_target if available, otherwise direct assignment
                scanner.set_target(target_asteroid)

                scanner.set_state(ShipState.MOVING_TO_SCAN)
                # Add the newly assigned target to the set immediately
                # to prevent other idle scanners in *this* cycle from picking it.
                currently_targeted_ids.add(target_asteroid.id)
                print(f"DEBUG: Scanner {scanner.id} assigned to scan Asteroid {target_asteroid.id}")
            else:
                # No available unscanned & untargeted asteroids left
                print(f"DEBUG: No suitable untargeted scan target found for Scanner {scanner.id}.")
                # Scanner remains IDLE

    def _find_nearest_unscanned_asteroid(
        self, position: Vector2, asteroids: list[Asteroid], excluded_ids: set[int]
    ) -> Asteroid | None:
        """Finds the nearest unscanned asteroid, excluding specific IDs."""

        def target_filter(asteroid):
            # Must be an Asteroid, not scanned, and not in the excluded set
            return (
                isinstance(asteroid, Asteroid)
                and not asteroid.scanned
                and asteroid.id not in excluded_ids  # Use the passed set
            )

        return find_nearest_object(position, asteroids, target_filter)
