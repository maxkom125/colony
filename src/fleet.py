# src/fleet.py
from .entities import Ship
from .entities.ships.mining_ship import MiningShip
from .entities.asteroid import Asteroid
from .entities.planet import Planet
from .systems.admirals.miner_admiral import MinerAdmiral

class Fleet:
    """A simple registry for all ship objects in the game."""
    def __init__(self):
        self.ships: dict[int, Ship] = {}
        self.miner_admiral = MinerAdmiral()

    def add_ship(self, ship: Ship):
        """Registers a ship in the central fleet registry."""
        if ship.id in self.ships:
            print(f"WARN: Ship with ID {ship.id} already exists in Fleet registry.")
            return
        self.ships[ship.id] = ship
        if isinstance(ship, MiningShip):
            self.miner_admiral.add_ship(ship)

    def remove_ship(self, ship_id: int):
        """Removes a ship from the central fleet registry."""
        if ship_id in self.ships:
            del self.ships[ship_id]
        else:
            print(f"WARN: Ship with ID {ship_id} not found in Fleet registry for removal.")
        if ship_id in self.miner_admiral.ships:
            self.miner_admiral.remove_ship(ship_id)

    def give_orders(self, asteroids: list[Asteroid], planet: Planet):
        """Gives orders to the Admirals."""
        self.miner_admiral.assign_idle_miners(asteroids)
        # Call Scanner Admiral update/assignment if it exists
        # scanner_admiral.assign_scan_tasks(entities_for_update)

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
