import math
import random
from pygame.math import Vector2

from .. import constants
from ..entities.planet import Planet
from ..entities.ships.scanner_ship import ScannerShip
from ..entities.ships.mining_ship import MiningShip

def attempt_construction(planet: Planet, ship_type: str):
    """Checks planet resources, deducts them, and creates a ship if possible.

    Args:
        planet: The planet instance attempting to build.
        ship_type: The type of ship to build ('scanner' or 'miner').

    Returns:
        The newly created ship object if successful, None otherwise.
    """
    costs = {}
    ShipClass = None

    if ship_type == "scanner":
        costs = {
            "Tritanium": constants.SCANNER_COST_TRITANIUM,
            "Credits": constants.SCANNER_COST_CREDITS,
        }
        ShipClass = ScannerShip
    elif ship_type == "miner":
        costs = {
            "Tritanium": constants.MINING_SHIP_COST_TRITANIUM,
            "Credits": constants.MINING_SHIP_COST_CREDITS,
        }
        ShipClass = MiningShip
    else:
        print(f"ERROR: Unknown ship type '{ship_type}' requested for construction.")
        return None

    if planet.has_resources(costs) and ShipClass:
        # Deduct resources first
        if planet.remove_resources(costs):
            # Create ship (slightly offset from planet edge)
            spawn_angle = random.uniform(0, 2 * math.pi)
            spawn_dist = planet.radius + 30 # Distance from planet center
            spawn_pos = planet.position + Vector2(spawn_dist, 0).rotate_rad(spawn_angle)
            new_ship = ShipClass(position=spawn_pos, angle=spawn_angle + math.pi) # Face away

            print(f"SUCCESS: Built {ship_type} ship! Planet resources remaining: T={planet.storage.get('Tritanium', 0)}, C={planet.storage.get('Credits', 0)}")
            return new_ship
        else:
            # This case should ideally not happen if has_resources is correct, but good for safety
            print(f"ERROR: Failed to remove resources for {ship_type} even after check passed.")
            return None
    else:
        print(f"FAILED: Not enough resources to build {ship_type}. Needed T={costs.get('Tritanium', 0)}, C={costs.get('Credits', 0)}. Have T={planet.storage.get('Tritanium', 0)}, C={planet.storage.get('Credits', 0)}")
        return None 