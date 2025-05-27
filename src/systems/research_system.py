"""
ResearchSystem: Manages researchable upgrades, their costs, levels, and application of effects.
"""

from src.enums import ShipType, ResourceType
from src.logger import logger


class ResearchSystem:
    def __init__(self):
        """
        Initialize the research system with available research items, their current levels, and costs.
        """
        # Separate researchable upgrades for each ship type.
        # Every key is the exact name of an attribute of the ship.
        self.miner_research_defs: dict[str, dict] = {
            "speed": {
                "display_name": "Miner Speed",
                "max_level": 5,
                "base_cost": {ResourceType.CREDITS: 100, ResourceType.PLASMA: 50},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.15,
                "description": "Increases miner ships' movement speed by 15% per level.",
            },
            "cargo_capacity": {
                "display_name": "Miner Cargo Capacity",
                "max_level": 5,
                "base_cost": {ResourceType.CREDITS: 30, ResourceType.TRITANIUM: 10},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.20,
                "description": "Increases miner ships' cargo capacity by 20% per level.",
            },
            "mining_rate": {
                "display_name": "Mining Speed",
                "max_level": 5,
                "base_cost": {ResourceType.CREDITS: 50, ResourceType.TRITANIUM: 10},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.18,
                "description": "Increases mining speed by 18% per level.",
            },
            "fuel_max_capacity": {
                "display_name": "Miner Fuel Tank Capacity",
                "max_level": 4,
                "base_cost": {ResourceType.CREDITS: 150, ResourceType.TRITANIUM: 75},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.25,
                "description": "Increases miner fuel tank capacity by 25% per level.",
            },
            "fuel_consumption_rate": {
                "display_name": "Miner Fuel Efficiency",
                "max_level": 5,
                "base_cost": {ResourceType.CREDITS: 200, ResourceType.PLASMA: 100},
                "cost_multiplier": 2.2,
                "effect_per_level": -0.15,
                "description": "Reduces miner fuel consumption by 15% per level.",
            },
            "fuel_refill_rate": {
                "display_name": "Miner Refueling Speed",
                "max_level": 3,
                "base_cost": {ResourceType.CREDITS: 100, ResourceType.PLASMA: 50},
                "cost_multiplier": 2.5,
                "effect_per_level": 0.30,
                "description": "Increases miner refueling speed by 30% per level.",
            },
        }
        self.scanner_research_defs: dict[str, dict] = {
            "speed": {
                "display_name": "Scanner Speed",
                "max_level": 5,
                "base_cost": {ResourceType.CREDITS: 100, ResourceType.PLASMA: 50},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.15,
                "description": "Increases scanner ships' movement speed by 15% per level.",
            },
            "scan_rate": {
                "display_name": "Scan Speed",
                "max_level": 5,
                "base_cost": {ResourceType.CREDITS: 50, ResourceType.TRITANIUM: 10},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.20,
                "description": "Increases scan speed by 20% per level.",
            },
            "scan_range": {
                "display_name": "Scan Radius",
                "max_level": 3,
                "base_cost": {ResourceType.CREDITS: 200},
                "cost_multiplier": 2.5,
                "effect_per_level": 0.25,
                "description": "Increases scanner ships' scan radius by 25% per level.",
            },
            "fuel_max_capacity": {
                "display_name": "Scanner Fuel Tank Capacity",
                "max_level": 4,
                "base_cost": {ResourceType.CREDITS: 150, ResourceType.TRITANIUM: 75},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.25,
                "description": "Increases scanner fuel tank capacity by 25% per level.",
            },
            "fuel_consumption_rate": {
                "display_name": "Scanner Fuel Efficiency",
                "max_level": 5,
                "base_cost": {ResourceType.CREDITS: 200, ResourceType.PLASMA: 100},
                "cost_multiplier": 2.2,
                "effect_per_level": -0.15,
                "description": "Reduces scanner fuel consumption by 15% per level.",
            },
            "fuel_refill_rate": {
                "display_name": "Scanner Refueling Speed",
                "max_level": 3,
                "base_cost": {ResourceType.CREDITS: 100, ResourceType.PLASMA: 50},
                "cost_multiplier": 2.5,
                "effect_per_level": 0.30,
                "description": "Increases scanner refueling speed by 30% per level.",
            },
        }
        self.miner_research_levels: dict[str, int] = {
            key: 0 for key in self.miner_research_defs.keys()
        }
        self.scanner_research_levels: dict[str, int] = {
            key: 0 for key in self.scanner_research_defs.keys()
        }
        # --- NEW: Use dict for ship_type -> research_levels and research_defs ---
        self.research_levels: dict[ShipType, dict[str, int]] = {
            ShipType.MINER: self.miner_research_levels,
            ShipType.SCANNER: self.scanner_research_levels,
        }
        self.research_defs: dict[ShipType, dict[str, dict]] = {
            ShipType.MINER: self.miner_research_defs,
            ShipType.SCANNER: self.scanner_research_defs,
        }

    def get_level(self, research_name: str, ship_type: ShipType) -> int:
        """
        Get the current level of a research item for a given ship type (ShipType enum).
        """
        return self.research_levels[ship_type].get(research_name, 0)

    def get_available_research(self, ship_type: ShipType) -> list[str]:
        """
        Return a list of available research item names for the given ship type.
        """
        return list(self.research_defs[ship_type].keys())

    def get_research_info(self, research_name: str, ship_type: ShipType) -> dict | None:
        """
        Return the definition/info for a research item for the given ship type.
        """
        return self.research_defs[ship_type].get(research_name, None)

    def get_next_level_cost(
        self, research_name: str, ship_type: ShipType
    ) -> dict[ResourceType, int] | None:
        """
        Calculate the cost for the next level of a research item for the given ship type.
        Returns a dict of resource costs or None if maxed out.
        """
        info = self.get_research_info(research_name, ship_type)
        if not info:
            return None
        level = self.get_level(research_name, ship_type)
        if level >= info["max_level"]:
            return None
        multiplier = info["cost_multiplier"] ** level
        return {
            resource_type: int(amount * multiplier)
            for resource_type, amount in info["base_cost"].items()
        }

    def can_research(
        self, research_name: str, ship_type: ShipType, planet_storage: dict[ResourceType, int]
    ) -> bool:
        """
        Check if the research can be purchased (enough resources, not maxed out, etc).
        """
        info = self.get_research_info(research_name, ship_type)
        if not info:
            logger.debug(f"No research info found for {research_name} and {ship_type}")
            return False

        level = self.get_level(research_name, ship_type)

        if level >= info["max_level"]:
            logger.debug(f"Research {research_name} already at max level {info['max_level']}")
            return False

        next_cost = self.get_next_level_cost(research_name, ship_type)
        if not next_cost:
            logger.debug(f"No next level cost calculated for {research_name}")
            return False

        for resource_type, amount in next_cost.items():
            available = planet_storage.get(resource_type, 0)
            if available < amount:
                return False

        return True

    def get_multiplier(self, research_name: str, ship_type: ShipType) -> float:
        """
        Returns the total multiplier for a given research and ship type (e.g., 1.3 for +30%).
        """
        info = self.get_research_info(research_name, ship_type)
        if not info:
            return 1.0
        level = self.get_level(research_name, ship_type)
        return 1.0 + (info["effect_per_level"] * level)

    def apply_research_effects_to_fleet(
        self, fleet, ship_type: ShipType, research_name: str
    ) -> None:
        """
        Apply the effect of a specific research to all ships of the given type in the fleet.
        research_name is the exact attribute name to update.
        """
        multiplier = self.get_multiplier(research_name, ship_type)
        for ship in fleet.get_ships_by_type(ship_type):
            current_value = getattr(ship, research_name)
            new_value = current_value * multiplier
            if research_name == "cargo_capacity":
                new_value = int(new_value)
            setattr(ship, research_name, new_value)
            logger.info(
                f"Applied research effect to {ship_type} {ship.id} for {research_name}: {current_value:.2f} -> {new_value:.2f}"
            )

    def attempt_research_purchase(
        self,
        research_name: str,
        ship_type: ShipType,
        planet_storage: dict[ResourceType, int],
        fleet=None,
    ) -> bool:
        """
        Attempt to purchase a research upgrade for a given ship type. Deducts resources and increments level if possible.
        If fleet is provided, applies research effects for the selected research and ship type after purchase.
        Returns True if successful, False otherwise.
        """
        logger.debug(f"Attempting to purchase research {research_name} for {ship_type}")

        if not self.can_research(research_name, ship_type, planet_storage):
            logger.debug(
                f"Cannot research {research_name} for {ship_type} - can_research returned False"
            )
            return False

        next_cost = self.get_next_level_cost(research_name, ship_type)
        logger.debug(f"Proceeding with purchase. Cost: {next_cost}")

        for resource_type, amount in next_cost.items():
            available = planet_storage.get(resource_type, 0)
            if available < amount:
                logger.error(
                    f"Double-check failed: Insufficient {resource_type.value}: need {amount}, have {available}"
                )
                return False
            logger.debug(f"Deducting {amount} {resource_type.value} from planet storage")
            planet_storage[resource_type] -= amount

        old_level = self.research_levels[ship_type][research_name]
        self.research_levels[ship_type][research_name] += 1
        new_level = self.research_levels[ship_type][research_name]
        logger.info(
            f"Research {research_name} for {ship_type} upgraded from level {old_level} to {new_level}"
        )

        if fleet is not None:
            logger.debug(f"Applying research effects to fleet for {research_name}")
            self.apply_research_effects_to_fleet(fleet, ship_type, research_name)
        else:
            logger.debug("No fleet provided, skipping effect application")

        return True
