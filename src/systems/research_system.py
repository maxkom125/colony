"""
ResearchSystem: Manages researchable upgrades, their costs, levels, and application of effects.
"""

from src.enums import ShipType

class ResearchSystem:
    def __init__(self):
        """
        Initialize the research system with available research items, their current levels, and costs.
        """
        # Separate researchable upgrades for each ship type. 
        # Every key is the exact name of an attribute of the ship.
        self.miner_research_defs = {
            "ship_speed": {
                "display_name": "Miner Speed",
                "max_level": 5,
                "base_cost": {"Credits": 100, "Plasma": 50},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.15,
                "description": "Increases miner ships' movement speed by 15% per level."
            },
            "cargo_capacity": {
                "display_name": "Miner Cargo Capacity",
                "max_level": 5,
                "base_cost": {"Credits": 30, "Tritanium": 10},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.20,
                "description": "Increases miner ships' cargo capacity by 20% per level."
            },
            "mining_speed": {
                "display_name": "Mining Speed",
                "max_level": 5,
                "base_cost": {"Credits": 50, "Tritanium": 10},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.18,
                "description": "Increases mining speed by 18% per level."
            },
        }
        self.scanner_research_defs = {
            "ship_speed": {
                "display_name": "Scanner Speed",
                "max_level": 5,
                "base_cost": {"Credits": 100, "Plasma": 50},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.15,
                "description": "Increases scanner ships' movement speed by 15% per level."
            },
            "scan_rate": {
                "display_name": "Scan Speed",
                "max_level": 5,
                "base_cost": {"Credits": 50, "Tritanium": 10},
                "cost_multiplier": 2.0,
                "effect_per_level": 0.20,
                "description": "Increases scan speed by 20% per level."
            },
            "scan_range": {
                "display_name": "Scan Radius",
                "max_level": 3,
                "base_cost": {"Credits": 200},
                "cost_multiplier": 2.5,
                "effect_per_level": 0.25,
                "description": "Increases scanner ships' scan radius by 25% per level."
            },
        }
        self.miner_research_levels = {key: 0 for key in self.miner_research_defs.keys()}
        self.scanner_research_levels = {key: 0 for key in self.scanner_research_defs.keys()}
        # --- NEW: Use dict for ship_type -> research_levels and research_defs ---
        self.research_levels = {
            ShipType.MINER: self.miner_research_levels,
            ShipType.SCANNER: self.scanner_research_levels,
        }
        self.research_defs = {
            ShipType.MINER: self.miner_research_defs,
            ShipType.SCANNER: self.scanner_research_defs,
        }

    def get_level(self, research_name, ship_type):
        """
        Get the current level of a research item for a given ship type (ShipType enum).
        """
        return self.research_levels[ship_type].get(research_name, 0)

    def get_available_research(self, ship_type):
        """
        Return a list of available research item names for the given ship type.
        """
        return list(self.research_defs[ship_type].keys())

    def get_research_info(self, research_name, ship_type):
        """
        Return the definition/info for a research item for the given ship type.
        """
        return self.research_defs[ship_type].get(research_name, None)

    def get_next_level_cost(self, research_name, ship_type):
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
        return {k: int(v * multiplier) for k, v in info["base_cost"].items()}

    def can_research(self, research_name, ship_type, planet_storage):
        """
        Check if the research can be purchased (enough resources, not maxed out, etc).
        """
        info = self.get_research_info(research_name, ship_type)
        if not info:
            return False
        level = self.get_level(research_name, ship_type)
        if level >= info["max_level"]:
            return False
        next_cost = self.get_next_level_cost(research_name, ship_type)
        if not next_cost:
            return False
        for res, amount in next_cost.items():
            if planet_storage.get(res, 0) < amount:
                return False
        return True

    def get_multiplier(self, research_name, ship_type):
        """
        Returns the total multiplier for a given research and ship type (e.g., 1.3 for +30%).
        """
        info = self.get_research_info(research_name, ship_type)
        if not info:
            return 1.0
        return 1.0 + info["effect_per_level"]

    def apply_research_effects_to_fleet(self, fleet, ship_type, research_name):
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
            print(f"INFO: Applied research effect to {ship_type} {research_name}: {current_value} -> {new_value}")

    def attempt_research_purchase(self, research_name, ship_type, planet_storage, fleet=None):
        """
        Attempt to purchase a research upgrade for a given ship type. Deducts resources and increments level if possible.
        If fleet is provided, applies research effects for the selected research and ship type after purchase.
        Returns True if successful, False otherwise.
        """
        if not self.can_research(research_name, ship_type, planet_storage):
            return False
        next_cost = self.get_next_level_cost(research_name, ship_type)
        for res, amount in next_cost.items():
            if planet_storage.get(res, 0) < amount:
                return False
            planet_storage[res] -= amount
        self.research_levels[ship_type][research_name] += 1
        if fleet is not None:
            self.apply_research_effects_to_fleet(fleet, ship_type, research_name)
        return True 