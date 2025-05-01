import random
# Import specific entity classes needed
from ..entities.asteroid import Asteroid
from ..entities.planet import Planet
from ..entities.ships.base_ship import Ship # Import base for type hint
from ..entities.ships.scanner_ship import ScannerShip
from ..entities.ships.mining_ship import MiningShip
from .. import utils
from .. import constants # Need resource types
from ..enums import ShipState # Import the enum


def assign_scanner_task(scanner: ScannerShip, asteroids: list[Asteroid]):
    """Finds the nearest unscanned asteroid and assigns it to the scanner."""

    def scanner_filter(asteroid):
        # Check type just in case list contains other things
        return isinstance(asteroid, Asteroid) and not asteroid.scanned

    target_asteroid = utils.find_nearest_object(
        scanner.position, asteroids, scanner_filter
    )

    if target_asteroid:
        scanner.set_target(target_asteroid)
        scanner.set_state(ShipState.MOVING_TO_ASTEROID)
        print(f"DEBUG: Scanner assigned target: {target_asteroid.id}")

# REMOVED old assign_miner_task function. Logic moved to MinerAdmiral. 