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
        self.ships: dict[int, "Ship"] = {}

    def get_ship_count(self) -> int:
        """Returns the total number of ships managed by this admiral."""
        return len(self.ships)

    def add_ship(self, ship: "Ship"):
        """Adds a ship to the admiral's command. Raises DuplicateShipError if already present."""
        if ship.id in self.ships:
            # Use a more general warning message in the exception
            raise DuplicateShipError(f"{ship.type} {ship.id} already managed by this Admiral.")
        self.ships[ship.id] = ship
        ship.admiral = self
        # No return needed on success

    def remove_ship(self, ship_id: int):
        """Removes a ship by ID. Raises ShipNotFoundError if not found."""
        if ship_id not in self.ships:
            print(f"WARN: Attempted to remove non-existent ship {ship_id} from Admiral.")
            raise ShipNotFoundError(f"Ship {ship_id} not found in this Admiral's fleet.")
        del self.ships[ship_id]

    def issue_command_checks(self, ship: "Ship", accepted_states: list[ShipState] = None):
        """Check if the ship is in an accepted state before issuing a command."""
        if accepted_states is not None and ship.state not in accepted_states:
            print(f"DEBUG: {ship.type} {ship.id} is in state {ship.state}, not in accepted states. Skipping command.")
            return False
        return True

    def issue_command(self, ship: "Ship", accepted_states: list[ShipState] = None):
        """Issue an arrival command to a ship."""
        if not self.issue_command_checks(ship, accepted_states):
            return

        match ship.state:
            case ShipState.IDLE:
                self.issue_command_to_idle_ship(ship)
            case ShipState.RETURNING_TO_BASE:
                self.issue_refueling_command(ship)
            case ShipState.REFUELING:
                print(f"DEBUG: Refueling finished ({ship.fuel}/{ship.fuel_max_capacity}), going IDLE for {ship.type} {ship.id}")
                ship.set_state(ShipState.IDLE)
                ship.set_target(None)
            case _:
                # This should never happen
                print(
                    f"WARN: {ship.type} {ship.id} is in state {ship.state}, command issued. This should never happen!"
                )
                ship.set_state(ShipState.IDLE)
                ship.set_target(None)

    def issue_refueling_command(self, ship: "Ship"):
        """Issue a refueling command to a ship."""
        # ---- Checks ----
        if ship.home is None:
            print(f"ERROR: {ship.type} {ship.id} has no home planet set. This should never happen!")
            return
        if ship.target != ship.home:
            print(f"ERROR: {ship.type} {ship.id} is not returning to base. This should never happen!")
            return
        
        # ---- Logic ----
        print(f"DEBUG: Issue refueling command for {ship.type} {ship.id}")
        if ship.fuel >= ship.fuel_max_capacity:
            print(f"WARNING: Ship {ship.id} is already at max fuel! Going IDLE.")
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            return
        ship.set_state(ShipState.REFUELING)
        # ship.target should be set already to ship.home (Planet)

    def issue_command_to_idle_ship(self, ship: "Ship"):
        """Assign a task to a ship."""
        print(
            f"ERROR: This function ({self.__class__.__name__}.issue_command_to_idle_ship) should be never used! "
            f"It is done in different functions of subclasses that are called in fleet.give_orders."
        )
        pass
