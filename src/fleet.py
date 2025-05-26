# src/fleet.py
from .entities import Ship
from .entities.ships.mining_ship import MiningShip
from .entities.ships.scanner_ship import ScannerShip
from .entities.asteroid import Asteroid
from .entities.planet import Planet
from .systems.admirals.miner_admiral import MinerAdmiral
from .systems.admirals.scanner_admiral import ScannerAdmiral
from .enums import ShipType
from .logger import logger # Import the logger


class Fleet:
    """A simple registry for all ship objects in the game."""

    def __init__(self):
        self.ships: dict[int, Ship] = {}
        self.miner_admiral = MinerAdmiral()
        self.scanner_admiral = ScannerAdmiral()

    def add_ship(self, ship: Ship):
        """Registers a ship in the central fleet registry and assigns to admiral."""
        if ship.id in self.ships:
            logger.warning(f"Ship with ID {ship.id} already exists in Fleet registry.")
            return
        self.ships[ship.id] = ship
        if isinstance(ship, MiningShip):
            self.miner_admiral.add_ship(ship)
        elif isinstance(ship, ScannerShip):
            self.scanner_admiral.add_ship(ship)
        else:
            logger.warning(f"Ship type {type(ship).__name__} has no dedicated admiral for ship ID {ship.id}.")

    def remove_ship(self, ship_id: int):
        """Removes a ship from the central fleet registry and relevant admiral."""
        ship_to_remove = self.ships.get(ship_id)

        if not ship_to_remove:
            logger.warning(f"Ship with ID {ship_id} not found in Fleet registry for removal.")
            return

        # Remove from the main fleet registry
        del self.ships[ship_id]

        # Remove from the appropriate admiral
        removed_from_admiral = False
        if isinstance(ship_to_remove, MiningShip):
            if ship_id in self.miner_admiral.ships: # Check if admiral actually has it
                self.miner_admiral.remove_ship(ship_id)
                removed_from_admiral = True
            else:
                logger.warning(f"MiningShip {ship_id} was in fleet but not found in MinerAdmiral.")
        elif isinstance(ship_to_remove, ScannerShip):
            if ship_id in self.scanner_admiral.ships: # Check if admiral actually has it
                self.scanner_admiral.remove_ship(ship_id)
                removed_from_admiral = True
            else:
                logger.warning(f"ScannerShip {ship_id} was in fleet but not found in ScannerAdmiral.")
        else:
            logger.debug(
                f"Ship {ship_id} (type: {type(ship_to_remove).__name__}) "
                "is not a known type for specific admiral removal or was not found in one."
            )
        
        if removed_from_admiral:
            logger.info(f"Ship {ship_id} (type: {type(ship_to_remove).__name__}) removed from fleet and relevant admiral.")
        else:
            # This implies it was removed from the fleet, but not from a specific admiral 
            # (either due to type or not being in the admiral's list).
            logger.info(f"Ship {ship_id} (type: {type(ship_to_remove).__name__}) removed from fleet. No specific admiral removal or not found in admiral.")


    def give_orders(self, asteroids: list[Asteroid], planet: Planet):
        """Gives orders to the Admirals to assign tasks to idle ships."""
        self.miner_admiral.assign_idle_miners(asteroids)
        self.scanner_admiral.assign_idle_scanners(asteroids)

    def update_ships(self, dt: float, obstacles: list[Asteroid | Planet]):
        """Updates all ships in the fleet."""
        for ship in self.ships.values():
            ship.update(dt, obstacles)

    def get_ship_by_id(self, ship_id: int) -> Ship | None:
        """Retrieves a ship by its ID."""
        return self.ships.get(ship_id)

    def get_all_ships(self) -> list[Ship]:
        """Returns a list of all registered ships."""
        return list(self.ships.values())

    def get_ships_by_type(self, ship_type: ShipType | type) -> list[Ship]:
        """Returns a list of ships matching the specified type."""
        if isinstance(ship_type, ShipType):
            ship_class = ship_type.ship_class
        else:
            ship_class = ship_type
        return [ship for ship in self.ships.values() if isinstance(ship, ship_class)]
