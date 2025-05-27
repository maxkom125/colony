import math
import random
from pygame.math import Vector2

from .. import constants
from ..entities.planet import Planet
from ..entities.ships.scanner_ship import ScannerShip
from ..entities.ships.mining_ship import MiningShip
from ..enums import ResourceType, ShipType
from ..logger import logger  # Import the logger


def attempt_construction(planet: Planet, ship_type: ShipType, research_system=None):
    """Checks planet resources, deducts them, and creates a ship if possible.

    Args:
        planet: The planet instance attempting to build.
        ship_type: The type of ship to build (ShipType.SCANNER or ShipType.MINER).
        research_system: Optional ResearchSystem to apply research bonuses to new ships.

    Returns:
        The newly created ship object if successful, None otherwise.
    """
    costs = {}
    ShipClass = None

    if ship_type == ShipType.SCANNER:
        costs = {
            ResourceType.TRITANIUM: constants.SCANNER_COST_TRITANIUM,
            ResourceType.CREDITS: constants.SCANNER_COST_CREDITS,
        }
        ShipClass = ScannerShip
    elif ship_type == ShipType.MINER:
        costs = {
            ResourceType.TRITANIUM: constants.MINING_SHIP_COST_TRITANIUM,
            ResourceType.CREDITS: constants.MINING_SHIP_COST_CREDITS,
        }
        ShipClass = MiningShip
    else:
        logger.error(f"Unknown ship type '{ship_type}' requested for construction.")
        return None

    if planet.has_resources(costs) and ShipClass:
        # Deduct resources first
        if planet.remove_resources(costs):
            # Create ship (slightly offset from planet edge)
            spawn_angle = random.uniform(0, 2 * math.pi)
            spawn_dist = planet.radius + 30  # Distance from planet center
            spawn_pos = planet.position + Vector2(spawn_dist, 0).rotate_rad(spawn_angle)
            new_ship = ShipClass(
                position=spawn_pos, home_planet=planet
            )  # TODO: set angle fase away from planet

            # Apply research bonuses to the new ship if research system is provided
            if research_system:
                # Apply all current research bonuses to the new ship
                for research_name in research_system.get_available_research(ship_type):
                    multiplier = research_system.get_multiplier(research_name, ship_type)
                    if multiplier != 1.0:  # Only apply if there's actually a bonus
                        current_value = getattr(new_ship, research_name)
                        new_value = current_value * multiplier
                        if research_name == "cargo_capacity":
                            new_value = int(new_value)
                        setattr(new_ship, research_name, new_value)
                        logger.info(
                            f"Applied research bonus to new {ship_type.value} {new_ship.id} for {research_name}: {current_value:.2f} -> {new_value:.2f}"
                        )

            logger.info(
                f"SUCCESS: Built {ship_type.value} ship ID {new_ship.id}! Planet resources remaining: {planet.storage}"
            )
            return new_ship
        else:
            # This case should ideally not happen if has_resources is correct, but good for safety
            logger.error(
                f"Failed to remove resources for {ship_type.value} even after check passed. Planet: {planet.id}, Costs: {costs}"
            )
            return None
    else:
        logger.warning(
            f"FAILED: Not enough resources to build {ship_type.value}. Needed T={costs.get(ResourceType.TRITANIUM, 0)}, C={costs.get(ResourceType.CREDITS, 0)}. Have T={planet.storage.get(ResourceType.TRITANIUM, 0)}, C={planet.storage.get(ResourceType.CREDITS, 0)}"
        )
        return None
