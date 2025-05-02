# src/fleet.py
from .entities import Ship
from .entities.ships.mining_ship import MiningShip
from .entities.ships.scanner_ship import ScannerShip
from .entities.asteroid import Asteroid
from .entities.planet import Planet
from .systems.admirals.miner_admiral import MinerAdmiral
from .systems.admirals.scanner_admiral import ScannerAdmiral


class Fleet:
    """A simple registry for all ship objects in the game."""

    def __init__(self):
        self.ships: dict[int, Ship] = {}
        self.miner_admiral = MinerAdmiral()
        self.scanner_admiral = ScannerAdmiral()

    def add_ship(self, ship: Ship):
        """Registers a ship in the central fleet registry and assigns to admiral."""
        if ship.id in self.ships:
            print(f"WARN: Ship with ID {ship.id} already exists in Fleet registry.")
            return
        self.ships[ship.id] = ship
        if isinstance(ship, MiningShip):
            self.miner_admiral.add_ship(ship)
        elif isinstance(ship, ScannerShip):
            self.scanner_admiral.add_ship(ship)
        else:
            print(f"WARN: Ship type {type(ship).__name__} has no dedicated admiral.")

    def remove_ship(self, ship_id: int):
        """Removes a ship from the central fleet registry and relevant admiral."""
        ship_found_in_fleet = False
        if ship_id in self.ships:
            del self.ships[ship_id]
            ship_found_in_fleet = True
        else:
            print(f"WARN: Ship with ID {ship_id} not found in Fleet registry for removal.")
            return

        if ship_id in self.miner_admiral.ships:
            self.miner_admiral.remove_ship(ship_id)
        elif ship_id in self.scanner_admiral.ships:
            self.scanner_admiral.remove_ship(ship_id)
        elif not ship_found_in_fleet:
            print(
                f"WARN: Ship {ship_id} not in main Fleet but "
                f"attempting admiral removal check. This should never happen!"
            )
            if ship_id in self.miner_admiral.ships:
                self.miner_admiral.remove_ship(ship_id)
            if ship_id in self.scanner_admiral.ships:
                self.scanner_admiral.remove_ship(ship_id)

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

    def get_ships_by_type(self, ship_type: type) -> list[Ship]:
        """Returns a list of ships matching the specified type."""
        return [ship for ship in self.ships.values() if isinstance(ship, ship_type)]
