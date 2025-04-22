# Import specific entity classes needed
from ..entities.asteroid import Asteroid
from ..entities.planet import Planet
from ..entities.ships.scanner_ship import ScannerShip
from ..entities.ships.mining_ship import MiningShip
from .. import utils
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
        # print(f"DEBUG: Scanner assigned target: {target_asteroid.id}")


def assign_miner_task(miner: MiningShip, asteroids: list[Asteroid], planet: Planet):
    """Finds the nearest scanned asteroid with resources OR returns to planet if full/no targets.
    Assigns the found target to the miner.
    """
    # Priority 1: Return to base if cargo is full
    if miner.get_cargo_total() >= miner.cargo_capacity:
        miner.set_target(planet)
        # print(f"DEBUG: Miner cargo full. Returning to Planet.")
        return

    # Priority 2: Find nearest suitable asteroid
    def miner_filter(asteroid):
        if not isinstance(asteroid, Asteroid) or not asteroid.scanned:
            return False
        # Check if it has *any* resources left
        return any(amount > 0 for amount in asteroid.resources.values())

    target_asteroid = utils.find_nearest_object(miner.position, asteroids, miner_filter)

    if target_asteroid:
        miner.set_target(target_asteroid)
        # print(f"DEBUG: Miner assigned target Asteroid {target_asteroid.id}")
    else:
        # Priority 3: No suitable asteroids found, return to base if carrying cargo
        if miner.get_cargo_total() > 0:
            miner.set_target(planet)
            # print(f"DEBUG: No suitable asteroids. Miner returning to Planet with cargo.")
        # else: Miner is idle, empty, and no targets - stays idle
        # print(f"DEBUG: No suitable asteroids and empty cargo. Miner remains idle.") 