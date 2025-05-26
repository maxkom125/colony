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
from ...logger import logger # Import the logger


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
        if potential_len < 0: # Should not happen if delta is positive or adjusted correctly
            logger.warning(
                f"Cannot assign less miners than 0 to {category}. Current: {current_len}, Delta: {delta}. Correcting delta."
            )
            delta = -current_len # This will make potential_len zero

        # --- Apply the change ---
        if delta > 0: # Assigning ships to the category
            for _ in range(delta):
                if not self.assignments_ships[self.free_ship_category]:
                    logger.warning(f"No free miners left to assign to {category} during multi-assignment.")
                    break # No more free ships
                ship_id = random.choice(self.assignments_ships[self.free_ship_category])
                self.update_ship_assignment(ship_id, category)
        elif delta < 0: # Unassigning ships from the category
            for _ in range(-delta):
                if not self.assignments_ships[category]:
                    logger.warning(f"No miners left to unassign from {category} during multi-unassignment.")
                    break # No more ships in this category
                ship_id = self.assignments_ships[category][-1] # Take the last one
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
                f"Miner {ship.id} arrived at unknown target type {type(ship.target) if ship.target else 'None'}. Going IDLE."
            )
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            return

        # ---- Dumping ----
        logger.debug(f"Miner {ship.id} arrived at Planet {ship.target.id}. Starting dump.")
        ship.set_state(ShipState.DUMPING)
        ship.dumping_timer = 0.0

    def issue_mining_command(self, ship: MiningShip):
        """Issue a mining command to a ship."""
        # ---- Checks ----
        if ship.target is None:
            logger.error(f"Miner {ship.id} has no target for mining command. This should never happen!")
            self.issue_returning_to_base_command(ship) # Send back to base
            return
        if not isinstance(ship.target, Asteroid):
            logger.warning(f"Miner {ship.id} arrived at non-asteroid target {type(ship.target)}. Going IDLE.")
            ship.set_state(ShipState.IDLE)
            ship.set_target(None)
            return
        if not ship.target.scanned:
            logger.error(f"Miner {ship.id} cannot mine unscanned Asteroid {ship.target.id}. This should never happen!")
            self.issue_returning_to_base_command(ship) # Send back to base
            return
        if ship.get_cargo_total() >= ship.cargo_capacity:
            logger.error(f"Miner {ship.id} cargo is full, cannot mine Asteroid {ship.target.id}. This should never happen!")
            self.issue_returning_to_base_command(ship) # Send back to base
            return
        
        dist_to_target = ship.position.distance_to(ship.target.position)
        arrival_threshold = ship.get_arrival_threshold()
        if dist_to_target > arrival_threshold + constants.EPSILON : # Add epsilon for float comparison
            logger.error(f"Miner {ship.id} (dist: {dist_to_target:.2f}) has not arrived at target {ship.target.id} (threshold: {arrival_threshold:.2f}), mining command issued. This should never happen!")
            # Potentially re-issue move command or send to base
            ship.set_state(ShipState.MOVING_TO_ASTEROID) # Re-affirm it needs to move
            return

        assigned_category_str = self.ships_assignments[ship.id]
        if assigned_category_str is None: # Should not happen if logic is correct
            logger.error(f"Miner {ship.id} has no assigned category for mining command. This should never happen!")
            self.issue_returning_to_base_command(ship)
            return

        # Ensure assigned category is a valid resource or the free category
        valid_resource_categories = ResourceType.list_names()
        if assigned_category_str not in valid_resource_categories and assigned_category_str != self.free_ship_category:
            logger.error(f"Miner {ship.id} has invalid assigned category '{assigned_category_str}' for mining. This should never happen!")
            self.issue_returning_to_base_command(ship)
            return

        # If assigned to a specific resource, check if the asteroid has it
        if assigned_category_str != self.free_ship_category:
            assigned_resource_enum = convert_resource_type_to_enum(assigned_category_str)
            if ship.target.resources.get(assigned_resource_enum, 0) <= 0:
                logger.error(f"Miner {ship.id} cannot mine Asteroid {ship.target.id}, it has no {assigned_category_str}. This should never happen!")
                # Ship should get a new target or go idle
                ship.set_state(ShipState.IDLE)
                ship.set_target(None)
                return
        
        # ---- Mining ----
        ship.set_state(ShipState.MINING)
        # mining_timer is now set within MiningShip.update based on resource availability
        logger.debug(f"Miner {ship.id} state set to MINING at Asteroid {ship.target.id}")

    def issue_returning_to_base_command(self, ship: MiningShip):
        """Issue a returning to base command to a ship."""
        # ---- Returning to base ----
        ship.set_target(ship.home)
        ship.set_state(ShipState.RETURNING_TO_BASE)
        ship.set_resource_to_mine(None) # Clear resource target when returning
        logger.debug(f"Miner {ship.id} state set to RETURNING_TO_BASE, target: Planet {ship.home.id if ship.home else 'None'}")

    def assign_idle_miners(self, asteroids: list[Asteroid]):
        """Assigns tasks to idle miners"""
        idle_miner_ids: list[int] = []
        for ship_id, miner in self.ships.items():
            if miner.state == ShipState.IDLE:
                if miner.get_cargo_total() >= miner.cargo_capacity:
                    logger.debug(f"Miner {miner.id} cargo is full ({miner.get_cargo_total()}/{miner.cargo_capacity}), sending to base.")
                    self.issue_returning_to_base_command(miner)
                    continue
                idle_miner_ids.append(ship_id)

        if not idle_miner_ids:
            return

        for ship_id in idle_miner_ids:
            self.assign_task(ship_id, asteroids)

    def assign_task(self, ship_id: int, asteroids: list[Asteroid]):
        """Assign a task to a ship."""
        miner = self.ships[ship_id]
        category = self.ships_assignments[ship_id]

        target_asteroid, resource_to_mine = self._find_target_for_category(
            miner, category, asteroids
        )

        if target_asteroid and resource_to_mine: # Ensure both are found
            fuel_needed = calc_fuel_needed_round_trip(miner, target_asteroid)
            if miner.fuel < fuel_needed: # Strict inequality: needs *more* than current fuel
                logger.debug(f"Miner {miner.id} (fuel: {miner.fuel:.1f}) insufficient for Asteroid {target_asteroid.id} (needs: {fuel_needed:.1f}). Returning to base.")
                self.issue_returning_to_base_command(miner)
            else:
                logger.debug(f"Miner {miner.id} assigned to mine {resource_to_mine.value} from Asteroid {target_asteroid.id}")
                miner.set_target(target_asteroid)
                miner.set_state(ShipState.MOVING_TO_ASTEROID)
                miner.set_resource_to_mine(resource_to_mine)
        else:
            logger.debug(f"Miner {miner.id} didn't find any suitable asteroids to mine for category '{category}'. Remaining IDLE.")
            miner.set_target(None) # Ensure target is cleared
            miner.set_state(ShipState.IDLE)
            miner.set_resource_to_mine(None)


    def _find_target_for_category(
        self, miner: MiningShip, category: str, asteroids: list[Asteroid]
    ) -> tuple[Asteroid | None, ResourceType | None]:
        target_asteroid: Asteroid | None = None
        resource_to_mine: ResourceType | None = None

        if category == self.free_ship_category:
            def random_asteroid_filter(obj):
                if not isinstance(obj, Asteroid) or not obj.scanned:
                    return False
                return any(amt > 0 for amt in obj.resources.values())

            target_asteroid = find_nearest_object(miner.position, asteroids, random_asteroid_filter)
            if target_asteroid:
                available_resources = [res for res, amt in target_asteroid.resources.items() if amt > 0]
                if available_resources:
                    resource_to_mine = random.choice(available_resources)
                else: # Should not happen if filter works
                    target_asteroid = None 
        elif category in ResourceType.list_names():
            target_asteroid = self._find_nearest_with_resource(miner.position, asteroids, category)
            if target_asteroid:
                try:
                    resource_to_mine = convert_resource_type_to_enum(category)
                except ValueError: # Should not happen if category is from ResourceType.list_names()
                    logger.error(f"Invalid resource category name '{category}' for enum conversion in _find_target_for_category.")
                    target_asteroid = None # Invalid state
        else:
            logger.warning(f"Invalid category '{category}' for asteroid assignment in _find_target_for_category.")

        return target_asteroid, resource_to_mine

    def _find_nearest_with_resource(
        self, position: Vector2, asteroids: list[Asteroid], resource_type: str | ResourceType
    ) -> Asteroid | None:
        """Finds the nearest asteroid from the list that contains the specified resource.
        Considers only asteroids that are already scanned.
        """
        try:
            resource_type_enum = convert_resource_type_to_enum(resource_type)
        except ValueError as e:
            logger.warning(f"Invalid resource type '{resource_type}' in _find_nearest_with_resource: {e}")
            return None

        def resource_filter(asteroid):
            if not isinstance(asteroid, Asteroid) or not asteroid.scanned:
                return False
            return asteroid.resources.get(resource_type, 0) > 0

        return find_nearest_object(position, asteroids, resource_filter)
