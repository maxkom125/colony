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


def assign_miner_task(miner: MiningShip, asteroids: list[Asteroid], planet: Planet, priorities: dict):
    """Finds the best asteroid based on resources, distance, and priorities,
       or returns to planet if full/no targets.
    """
    # Priority 1: Return to base if cargo is full
    if miner.get_cargo_total() >= miner.cargo_capacity:
        miner.set_target(planet)
        return

    # Priority 2: Find best suitable asteroid
    suitable_asteroids = []
    for asteroid in asteroids:
        if isinstance(asteroid, Asteroid) and asteroid.scanned:
            # Check if it has *any* resources left
            if any(amount > 0 for amount in asteroid.resources.values()):
                suitable_asteroids.append(asteroid)

    if not suitable_asteroids:
        # Priority 3: No suitable asteroids found, return to base if carrying cargo
        if miner.get_cargo_total() > 0:
            miner.set_target(planet)
        # else: Miner is idle, empty, and no targets - stays idle
        return

    # Calculate score for each suitable asteroid
    best_target = None
    best_score = -1 # Initialize with a value lower than any possible score

    for asteroid in suitable_asteroids:
        distance = miner.position.distance_to(asteroid.position)
        # Find the dominant resource (the one it actually has)
        dominant_res = next((res for res, amount in asteroid.resources.items() if amount > 0), None)
        
        if dominant_res:
            priority = priorities.get(dominant_res, 0.0) # Get priority, default to 0 if somehow missing
            # Score formula: Higher priority is better, closer is better.
            # Add a small constant to distance to prevent division by zero and reduce impact of tiny distances.
            score = priority / (distance + 10.0)
            
            if score > best_score:
                best_score = score
                best_target = asteroid

    # Assign the best target found (if any)
    if best_target:
        miner.set_target(best_target)
        # print(f"DEBUG: Miner assigned target Asteroid {best_target.id} with score {best_score:.3f}")
    elif miner.get_cargo_total() > 0:
         # Fallback if scoring somehow failed but we have asteroids and cargo - return to base
         miner.set_target(planet)
    # Else: remain idle if no target chosen and no cargo 