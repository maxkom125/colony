import random
from collections import defaultdict
from pygame.math import Vector2
from ...entities.ships.mining_ship import MiningShip
from ...entities.asteroid import Asteroid
from ...entities.planet import Planet
from ...enums import ShipState, ResourceType
from ...utils import find_nearest_object, convert_resource_type_to_enum
from ... import constants
from .base_admiral import Admiral, DuplicateShipError, ShipNotFoundError
from ..movement_system import calc_fuel_needed_round_trip
from ...logger import logger  # Import the logger


class MinerAdmiral(Admiral):
    """Manages task assignments and state for all MiningShips."""

    def __init__(self):
        super().__init__()  # Call parent initializer
        # self.ships is inherited from Admiral, will store MiningShips
        self.ships: dict[int, MiningShip]

        self.ships_assignments = dict()  # {ship_id: category}
        self.assignments_ships = {
            category: [] for category in ResourceType.list_names()
        }  # {category: [ship_id]}
        self.free_ship_category = "Random"
        self.assignments_ships[self.free_ship_category] = []

    def add_ship(self, ship: MiningShip):
        """Registers a new miner under the admiral's command."""
        # Basic type check first
        if not isinstance(ship, MiningShip):
            logger.warning(f"Attempted to add non-MiningShip {ship.id} to MinerAdmiral.")
            return

        try:
            # Call super() within a try block
            super().add_ship(ship)
        except DuplicateShipError as e:
            # Base class failed (duplicate found), handle it (e.g., print warning)
            logger.info(f"During add_ship for {ship.id}: {e}")
            return  # Stop further execution in this method

        # --- If no exception, proceed with miner-specific logic ---
        self.assignments_ships[self.free_ship_category].append(ship.id)
        self.ships_assignments[ship.id] = self.free_ship_category
        self.update_ship_assignment(ship.id, self.free_ship_category)

    def remove_ship(self, ship_id: int):
        """Removes a miner using the base method and handles miner-specific cleanup."""
        # --- Check if ship exists FIRST ---
        if ship_id in self.ships:

            # --- Ship exists, proceed with cleanup ---
            self.update_ship_assignment(ship_id, None)  # Unassign from current category
            # self.assignments_ships should be handled by update_ship_assignment
            self.ships_assignments.pop(ship_id)

        # Now remove from the base class dictionary
        try:
            super().remove_ship(ship_id)
        except ShipNotFoundError as e:
            logger.info(f"During remove_ship for {ship_id}: {e}")
            return

        logger.debug(f"Miner {ship_id} removed.")

    # --- Helper methods for HUD/External Info ---
    def get_all_categories(self) -> list[str]:
        """Returns a list of all valid assignment categories."""
        return list(self.assignments_ships.keys())

    def get_ship_count_for_category(self, category: str) -> int:
        """Returns the number of ships currently in a specific category list."""
        return len(self.assignments_ships.get(category, []))

    def get_idle_ship_count(self) -> int:
        """Returns the number of managed miners currently in the IDLE state."""
        idle_count = 0
        for ship in self.ships.values():
            # Ensure it's a MiningShip before checking state (though should always be)
            if isinstance(ship, MiningShip) and ship.state == ShipState.IDLE:
                idle_count += 1
        return idle_count

    # --- Core Logic ---
    def adjust_ship_count_for_category(self, category: str, delta: int):
        """Adjusts the target number of miners for a category."""
        # --- Checks ---
        if category not in self.assignments_ships:
            logger.warning(f"Invalid category {category} for assignment update.")
            return

        free_miners_available = len(self.assignments_ships[self.free_ship_category])
        if delta > 0 and free_miners_available < delta:
            logger.warning(
                f"Not enough free miners to assign to {category}. "
                f"Requested: {delta}, Available: {free_miners_available}. Assigning {free_miners_available}."
            )
            delta = free_miners_available

        if delta == 0:
            logger.info(f"No change in assignment for {category} (delta is 0 or adjusted to 0).")
            return

        current_len = len(self.assignments_ships[category])
        potential_len = current_len + delta
        if potential_len < 0:
            logger.warning(
                f"Cannot assign less miners than 0. In {category} there are {current_len} miners."
            )
            return

        # --- Apply the change ---
        # Pick free ships to assign to category
        for _ in range(delta):
            if not self.assignments_ships[self.free_ship_category]:
                logger.warning(f"No free miners to assign to {category}.")
                continue

            # Pick a random free ship
            ship_id = random.choice(self.assignments_ships[self.free_ship_category])
            self.update_ship_assignment(ship_id, category)

        # Unassign miners from category for negative delta
        for _ in range(-delta):
            if not self.assignments_ships[category]:
                logger.warning(f"No miners to unassign from {category}.")
                continue
            ship_id = self.assignments_ships[category][-1]
            self.update_ship_assignment(ship_id, self.free_ship_category)

    def update_ship_assignment(self, ship_id: int, category: str | ResourceType | None):
        """Updates the assignment of a ship to a category."""
        current_assignment = self.ships_assignments[ship_id]
        ship = self.ships[ship_id]  # Get the ship object

        ship.set_state(ShipState.IDLE)
        ship.set_target(None)

        if current_assignment == category:
            # This should happen only in add_ship
            return

        # clean up old assignment
        self.assignments_ships[current_assignment].remove(ship_id)
        self.ships_assignments[ship_id] = None
        ship.set_resource_to_mine(None)

        # assign new category
        if category:
            if isinstance(category, ResourceType):
                category = category.name
            self.ships_assignments[ship_id] = category
            self.assignments_ships[category].append(ship_id)
            # resource to mine is set in miner_admiral.assign_task

    def issue_command(self, ship: MiningShip, accepted_states: list[ShipState] = None):
        """Issue a command to a ship.
        miner cycle:
        IDLE -> assign_task -> cycle
        cycle: MOVING_TO_ASTEROID -> MINING -> RETURNING_TO_BASE -> DUMPING (+REFUELING) -> IDLE -> MOVING_TO_ASTEROID
        """
        logger.debug(f"Issue command for Miner {ship.id} state: {ship.state}")
        if not self.issue_command_checks(ship, accepted_states):
            return

        match ship.state:
            case ShipState.MOVING_TO_ASTEROID:
                self.issue_mining_command(ship)
            case ShipState.MINING:
                self.issue_returning_to_base_command(ship)
            case ShipState.RETURNING_TO_BASE:
                self.issue_dumping_command(ship)
            case ShipState.DUMPING:
                if ship.fuel < ship.fuel_max_capacity:
                    super().issue_refueling_command(ship)
                else:
                    # Ready to start a new cycle
                    ship.set_state(ShipState.IDLE)
                    ship.set_target(None)
            case _:
                super().issue_command(ship)

    def issue_dumping_command(self, ship: MiningShip):
        """Issue a dumping command to a ship."""
        # ---- Checks ----
        if ship.target is None or not isinstance(ship.target, Planet):
            logger.warning(
                f"Miner {self.id} arrived at unknown target type {type(self.target)}. Going IDLE."
            )
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            return

        # ---- Dumping ----
        logger.debug(f"Miner {ship.id} arrived at Planet {ship.target.id}. Starting dump.")
        ship.set_state(ShipState.DUMPING)
        ship.dumping_timer = (
            0.0  # TODO: set timer here, depending on resource amount, make decreasing
        )

    def issue_mining_command(self, ship: MiningShip):
        """Issue a mining command to a ship."""
        # ---- Checks ----
        # TODO: more checks
        if ship.target is None:
            logger.error(
                f"Miner {ship.id} has no target, mining command issued. This should never happen!"
            )
            return
        if not isinstance(ship.target, Asteroid):
            logger.warning(
                f"Miner {self.id} arrived at unknown target type {type(self.target)}. Going IDLE."
            )
            return
        if not ship.target.scanned:
            logger.error(
                f"Miner {ship.id} cannot mine Asteroid {ship.target.id} because it is not scanned. This should never happen!"
            )
            return
        if ship.get_cargo_total() >= ship.cargo_capacity:
            logger.error(
                f"Miner {ship.id} cannot mine Asteroid {ship.target.id} because its cargo is full. This should never happen!"
            )
            return
        # check if ship really arrived at asteroid
        if (
            ship.position.distance_to(ship.target.position) - ship.get_arrival_threshold()
        ) > constants.EPSILON:
            logger.error(
                f"Miner {ship.id} has not arrived at target, mining command issued. This should never happen!"
            )
            return

        assigned_category = self.ships_assignments[ship.id]
        if assigned_category is None:
            logger.error(
                f"Miner {ship.id} has no assigned category, mining command issued. This should never happen!"
            )
            return
        if (
            assigned_category not in ResourceType.list_names()
            and assigned_category != self.free_ship_category
        ):
            logger.error(
                f"Miner {ship.id} has invalid assigned category {assigned_category}, mining command issued. This should never happen!"
            )
            return
        if (
            assigned_category != self.free_ship_category
            and ship.target.resources.get(convert_resource_type_to_enum(assigned_category), 0) <= 0
        ):
            logger.error(
                f"Miner {ship.id} cannot mine Asteroid {ship.target.id} because it has no {assigned_category}. This should never happen!"
            )
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            ship.set_resource_to_mine(None)
            return
        # ---- Mining ----
        ship.set_state(ShipState.MINING)
        ship.mining_timer = constants.MINING_DURATION
        logger.debug(f"Miner {ship.id} state set to MINING")

    def issue_returning_to_base_command(self, ship: MiningShip):
        """Issue a returning to base command to a ship."""
        # ---- Returning to base ----
        ship.set_target(ship.home)
        ship.set_state(ShipState.RETURNING_TO_BASE)
        ship.set_resource_to_mine(None)  # Clear resource target when returning
        logger.debug(
            f"Miner {ship.id} state set to RETURNING_TO_BASE, target: Planet {ship.home.id if ship.home else 'None'}"
        )

    def assign_idle_miners(self, asteroids: list[Asteroid]):
        """Assigns tasks to idle miners"""
        # 1. Identify Idle Miners
        idle_miners: list[int] = []
        for ship_id, miner in self.ships.items():
            if miner.state == ShipState.IDLE:
                # Check cargo isn't full - if so, send to base
                if miner.get_cargo_total() >= miner.cargo_capacity:
                    logger.debug(f"Miner {miner.id} cargo is full, returning to base.")
                    miner.set_target(miner.home)
                    miner.set_state(ShipState.RETURNING_TO_BASE)
                    continue  # Move to next miner
                idle_miners.append(ship_id)

        if not idle_miners:
            return  # No assignable idle miners

        # 2. Assign tasks to idle miners
        for ship_id in idle_miners:
            self.assign_task(ship_id, asteroids)

    def assign_task(self, ship_id: int, asteroids: list[Asteroid]):
        """Assign a task to a ship."""
        miner = self.ships[ship_id]
        category = self.ships_assignments[ship_id]

        # Find target
        target_asteroid, resource_to_mine = self._find_target_for_category(
            miner, category, asteroids
        )
        if target_asteroid:
            # Check if we have enough fuel to mine the asteroid
            fuel_needed = calc_fuel_needed_round_trip(miner, target_asteroid)
            if miner.fuel <= fuel_needed:
                logger.debug(
                    f"Miner {miner.id} has insufficient fuel to mine Asteroid {target_asteroid.id}. Returning to base."
                )
                self.issue_returning_to_base_command(miner)
            else:
                logger.debug(
                    f"Miner {miner.id} assigned to mine {resource_to_mine} from Asteroid {target_asteroid.id}"
                )
                miner.set_target(target_asteroid)
                miner.set_state(ShipState.MOVING_TO_ASTEROID)
                miner.set_resource_to_mine(resource_to_mine)
        else:
            # no target found, going IDLE
            logger.debug(
                f"Miner {miner.id} didn't find any asteroids to mine ({category}). Remaining IDLE."
            )
            miner.set_target(None)
            miner.set_state(ShipState.IDLE)
            miner.set_resource_to_mine(None)

    def _find_target_for_category(
        self, miner: MiningShip, category: str, asteroids: list[Asteroid]
    ) -> tuple[Asteroid | None, ResourceType | None]:  # Return target and resource_to_mine
        """Helper to find the best asteroid target for a given category."""
        target_asteroid: Asteroid | None = None
        resource_to_mine: ResourceType | None = None

        if category == self.free_ship_category:
            # Choose a *resource type* to target for this cycle
            chosen_resource_type = random.choice(ResourceType.list())
            # choose a random asteroid with the chosen resource type
            asteroids_with_resource = [
                a
                for a in asteroids
                if isinstance(a, Asteroid)
                and a.scanned
                and a.resources.get(chosen_resource_type, 0) > 0
            ]
            if asteroids_with_resource:
                target_asteroid = random.choice(asteroids_with_resource)
                resource_to_mine = chosen_resource_type
            # If no suitable asteroid found for the chosen type, target and resource_to_mine remain None

        elif category in ResourceType.list_names():
            target_asteroid = self._find_nearest_with_resource(miner.position, asteroids, category)
            if target_asteroid:
                resource_to_mine = convert_resource_type_to_enum(category)
            # If no target found, target and resource_to_mine remain None
        else:
            logger.warning(f"Invalid category {category} for asteroid assignment.")
            # target and resource_to_mine remain None

        return target_asteroid, resource_to_mine

    def _find_nearest_with_resource(
        self, position: Vector2, asteroids: list[Asteroid], resource_type: str | ResourceType
    ) -> Asteroid | None:
        """Finds the nearest asteroid from the list that contains the specified resource.
        Considers only asteroids that are already scanned.
        """
        try:
            resource_type = convert_resource_type_to_enum(resource_type)
        except ValueError:
            logger.warning(f"Invalid resource type: {resource_type}")
            return None

        def resource_filter(asteroid):
            if not isinstance(asteroid, Asteroid) or not asteroid.scanned:
                return False
            return asteroid.resources.get(resource_type, 0) > 0

        return find_nearest_object(position, asteroids, resource_filter)
