from ...enums import ShipState
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...entities.ships.base_ship import Ship


# --- Custom Exceptions ---
class DuplicateShipError(ValueError):
    """Raised when trying to add a ship that is already managed."""

    pass


class ShipNotFoundError(KeyError):  # Inherit from KeyError as it's about a missing key
    """Raised when trying to remove or access a ship that is not managed."""

    pass


class Admiral:
    """Base class for all admirals."""

    def __init__(self):
        self.ships: dict[int, 'Ship'] = {}

    def get_ship_count(self) -> int:
        """Returns the total number of ships managed by this admiral."""
        return len(self.ships)

    def add_ship(self, ship: 'Ship'):
        """Adds a ship to the admiral's command. Raises DuplicateShipError if already present."""
        if ship.id in self.ships:
            # Use a more general warning message in the exception
            raise DuplicateShipError(f"Ship {ship.id} already managed by this Admiral.")
        self.ships[ship.id] = ship
        ship.admiral = self
        # No return needed on success

    def remove_ship(self, ship_id: int):
        """Removes a ship by ID. Raises ShipNotFoundError if not found."""
        if ship_id not in self.ships:
            print(f"WARN: Attempted to remove non-existent ship {ship_id} from Admiral.")
            raise ShipNotFoundError(f"Ship {ship_id} not found in this Admiral's fleet.")
        del self.ships[ship_id]

    def issue_command(self, ship: 'Ship'):
        """Issue an arrival command to a ship."""
        match ship.state:
            case ShipState.IDLE:
                self.issue_command_to_idle_ship(ship)
            case _:
                # This should never happen
                print(f"WARN: {ship.type} {ship.id} is in state {ship.state}, command issued. This should never happen!")
                ship.set_state(ShipState.IDLE)
                ship.target = None

    def issue_command_to_idle_ship(self, ship: 'Ship'):
        """Assign a task to a ship."""
        print(f"ERROR: This function ({self.__class__.__name__}.issue_command_to_idle_ship) should be overridden by subclasses.")
        pass

