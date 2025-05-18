# tests/systems/admirals/test_miner_admiral.py
import pytest
import random
from unittest.mock import MagicMock, patch
from collections import defaultdict
from pygame.math import Vector2

# Objects to test
from src.systems.admirals.miner_admiral import MinerAdmiral
from src.entities.ships.mining_ship import (
    MiningShip,
)  # We might need the real one or mock it
from src.entities.asteroid import Asteroid
from src.entities.planet import Planet
from src.enums import ShipState, ResourceType, ShipType
from src import constants


# --- Mock Classes ---
# Using MagicMock for simplicity, but could define simple classes too


class MockMiningShip(MagicMock):
    _next_id = 1

    def __init__(
        self,
        ship_id=None,
        state=ShipState.IDLE,
        cargo=0,
        capacity=100,
        position=(0, 0),
        home_planet=None,
        **kwargs,
    ):
        super().__init__(spec=MiningShip, **kwargs)  # Set spec for attribute checks
        if ship_id is not None:
            self.id = ship_id
            MockMiningShip._next_id = max(MockMiningShip._next_id, ship_id + 1)
        else:
            self.id = MockMiningShip._next_id
            MockMiningShip._next_id += 1
        self.state = state
        self._cargo = defaultdict(int, cargo if isinstance(cargo, dict) else {})  # Allow dict init
        self.cargo_capacity = capacity
        self.position = position
        self.home = home_planet  # Store mock home planet
        # Mock methods called by MinerAdmiral
        self.get_cargo_total = MagicMock(return_value=sum(self._cargo.values()))
        self.set_target = MagicMock()
        self.set_state = MagicMock()
        self.set_resource_to_mine = MagicMock()
        self.name = f"MockMiner_{self.id}"  # Add a name for potential debugging
        self.target = None
        self.type = ShipType.MINER
        self.fuel_max_capacity = constants.BASE_FUEL_MAX_CAPACITY
        self.fuel = self.fuel_max_capacity


class MockAsteroid(MagicMock):
    _next_id = 1000  # Start asteroid IDs higher

    def __init__(
        self,
        asteroid_id=None,
        position=Vector2(10, 10),
        scanned=True,
        resources=None,
        **kwargs,
    ):
        super().__init__(spec=Asteroid, **kwargs)
        if asteroid_id is not None:
            self.id = asteroid_id
            MockAsteroid._next_id = max(MockAsteroid._next_id, asteroid_id + 1)
        else:
            self.id = MockAsteroid._next_id
            MockAsteroid._next_id += 1
        self.position = position
        self.scanned = scanned
        self.resources = defaultdict(int, resources or {ResourceType.TRITANIUM: 100})  # Default resource
        self.name = f"MockAsteroid_{self.id}"
        if 'radius' not in kwargs:
            self.radius = 10 # Default radius if not specified


class MockPlanet(MagicMock):
    def __init__(self, planet_id=999, position=(0, 0), **kwargs):
        super().__init__(spec=Planet, **kwargs)
        self.id = planet_id
        self.position = position
        self.name = "MockPlanet"


# --- Fixtures ---


@pytest.fixture
def miner_admiral():
    """Provides a fresh MinerAdmiral instance for each test."""
    # Reset mock ID counters before each test if needed
    MockMiningShip._next_id = 1
    MockAsteroid._next_id = 1000
    return MinerAdmiral()


@pytest.fixture
def mock_miner(mock_planet):
    """Provides a default mock mining ship with a home planet."""
    return MockMiningShip(home_planet=mock_planet)


@pytest.fixture
def mock_planet():
    """Provides a mock planet."""
    return MockPlanet(planet_id=999)


@pytest.fixture
def mock_asteroid_tritanium():
    """Provides a mock asteroid with Tritanium."""
    return MockAsteroid(resources={ResourceType.TRITANIUM: 100})


@pytest.fixture
def mock_asteroids(mock_asteroid_tritanium):
    """Provides a list containing one mock asteroid."""
    return [mock_asteroid_tritanium]


# --- Test Cases ---


# Test Initialization
def test_miner_admiral_init(miner_admiral):
    """Test MinerAdmiral initializes correctly."""
    assert isinstance(miner_admiral.ships, dict)
    assert len(miner_admiral.ships) == 0
    assert miner_admiral.get_ship_count() == 0
    assert isinstance(miner_admiral.ships_assignments, dict)
    assert len(miner_admiral.ships_assignments) == 0
    assert isinstance(miner_admiral.assignments_ships, dict)
    # Check the expected keys are present
    expected_categories = ["Tritanium", "Credits", "Plasma", "Random"]
    assert list(miner_admiral.assignments_ships.keys()) == expected_categories
    for category in expected_categories:
        assert miner_admiral.assignments_ships[category] == []
    assert miner_admiral.free_ship_category == "Random"


# Test add_ship
def test_add_ship_success(miner_admiral, mock_miner):
    """Test adding a valid MiningShip."""
    miner_admiral.add_ship(mock_miner)
    assert miner_admiral.get_ship_count() == 1
    assert mock_miner.id in miner_admiral.ships
    assert miner_admiral.ships[mock_miner.id] is mock_miner
    assert miner_admiral.ships_assignments[mock_miner.id] == miner_admiral.free_ship_category
    assert mock_miner.id in miner_admiral.assignments_ships[miner_admiral.free_ship_category]
    assert len(miner_admiral.assignments_ships[miner_admiral.free_ship_category]) == 1
    mock_miner.set_state.assert_called_once()  # Verify call
    mock_miner.set_resource_to_mine.assert_not_called()  # Verify no call


def test_add_ship_non_miner_ignored(miner_admiral, capsys):
    """Test adding a non-MiningShip is ignored and logs a warning."""
    non_miner = MagicMock(id=500)  # Doesn't inherit/spec MiningShip
    miner_admiral.add_ship(non_miner)
    captured = capsys.readouterr()
    assert miner_admiral.get_ship_count() == 0
    assert non_miner.id not in miner_admiral.ships_assignments
    assert f"WARN: Attempted to add non-MiningShip {non_miner.id}" in captured.out
    for category in miner_admiral.assignments_ships:
        assert non_miner.id not in miner_admiral.assignments_ships[category]


def test_add_ship_duplicate_handled_by_base(miner_admiral, mock_miner, capsys):
    """Test adding a duplicate MiningShip raises error from base, logs info, and doesn't double-add."""
    miner_admiral.add_ship(mock_miner)  # Add first time

    # Create another mock with the same ID
    duplicate_miner = MockMiningShip(ship_id=mock_miner.id)

    # Add the duplicate
    miner_admiral.add_ship(duplicate_miner)
    captured = capsys.readouterr()

    # Check state: only original miner should be present
    assert miner_admiral.get_ship_count() == 1
    assert miner_admiral.ships[mock_miner.id] is mock_miner  # Still the original object
    assert miner_admiral.ships_assignments[mock_miner.id] == miner_admiral.free_ship_category
    assert len(miner_admiral.assignments_ships[miner_admiral.free_ship_category]) == 1
    assert mock_miner.id in miner_admiral.assignments_ships[miner_admiral.free_ship_category]

    # Check that the base class error message was logged
    assert f"INFO: {mock_miner.type} {mock_miner.id} already managed by this Admiral." in captured.out


# Test remove_ship
def test_remove_ship_success(miner_admiral, mock_miner):
    """Test removing an existing MiningShip."""
    miner_admiral.add_ship(mock_miner)
    initial_category = miner_admiral.ships_assignments[mock_miner.id]
    mock_miner.set_state.reset_mock()
    mock_miner.set_resource_to_mine.reset_mock()
    miner_admiral.remove_ship(mock_miner.id)

    assert miner_admiral.get_ship_count() == 0
    assert mock_miner.id not in miner_admiral.ships
    assert mock_miner.id not in miner_admiral.ships_assignments
    assert (
        mock_miner.id not in miner_admiral.assignments_ships[initial_category]
    )  # Check specific list
    mock_miner.set_state.assert_called_once()
    mock_miner.set_resource_to_mine.assert_called_once()

def test_remove_ship_not_found_handled_by_base(miner_admiral, capsys):
    """Test removing a non-existent ship ID raises error from base and logs info."""
    non_existent_id = 999
    miner_admiral.remove_ship(non_existent_id)
    captured = capsys.readouterr()

    assert miner_admiral.get_ship_count() == 0


def test_remove_correct_ship_from_assignment(miner_admiral):
    """Test removing one ship when multiple exist in different assignments."""
    miner1 = MockMiningShip(ship_id=1)
    miner2 = MockMiningShip(ship_id=2)
    miner_admiral.add_ship(miner1)
    miner_admiral.add_ship(miner2)

    # Manually move miner2 ID to 'Tritanium' for testing removal from a specific category
    miner_admiral.assignments_ships["Random"].remove(miner2.id)
    miner_admiral.assignments_ships["Tritanium"].append(miner2.id)
    miner_admiral.ships_assignments[miner2.id] = "Tritanium"

    assert miner_admiral.get_ship_count() == 2
    # Check IDs are in correct lists
    assert miner1.id in miner_admiral.assignments_ships["Random"]
    assert miner2.id in miner_admiral.assignments_ships["Tritanium"]

    # Remove miner 2 (from Tritanium category)
    miner_admiral.remove_ship(miner2.id)

    assert miner_admiral.get_ship_count() == 1
    assert miner2.id not in miner_admiral.ships
    assert miner2.id not in miner_admiral.ships_assignments
    # Check ID removed from list
    assert miner2.id not in miner_admiral.assignments_ships["Tritanium"]

    # Ensure miner1 is untouched
    assert miner1.id in miner_admiral.ships
    assert miner_admiral.ships_assignments[miner1.id] == "Random"
    # Check ID still in correct list
    assert miner1.id in miner_admiral.assignments_ships["Random"]


# Test adjust_ship_count_for_category (formerly update_assignments_ships)
@patch("src.systems.admirals.miner_admiral.random.choice")
def test_adjust_ship_count_increase_success(mock_random_choice, miner_admiral):
    """Test moving a free miner to a specific category using adjust_ship_count."""
    miner1 = MockMiningShip(ship_id=1)
    miner2 = MockMiningShip(ship_id=2)
    miner_admiral.add_ship(miner1)
    miner_admiral.add_ship(miner2)
    # Reset mocks after initial add_ship calls
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()
    miner2.set_state.reset_mock()
    miner2.set_resource_to_mine.reset_mock()

    # Mock random.choice to pick miner2 from the 'Random' list
    mock_random_choice.return_value = miner2.id

    assert len(miner_admiral.assignments_ships["Random"]) == 2
    assert len(miner_admiral.assignments_ships["Tritanium"]) == 0

    miner_admiral.adjust_ship_count_for_category("Tritanium", 1)

    mock_random_choice.assert_called_once_with(
        miner_admiral.assignments_ships["Random"]
    )  # Verify it chose from Random
    assert len(miner_admiral.assignments_ships["Random"]) == 1
    assert len(miner_admiral.assignments_ships["Tritanium"]) == 1

    # Check miner2 was moved
    assert miner2.id in miner_admiral.assignments_ships["Tritanium"]
    assert miner_admiral.ships_assignments[miner2.id] == "Tritanium"
    # Verify state/resource calls on the moved ship (miner2)
    miner2.set_state.assert_called_once_with(ShipState.IDLE)
    miner2.set_resource_to_mine.assert_called_once_with(None)
    assert miner2.target is None # Target should be cleared

    # Ensure miner1 is untouched
    assert miner1.id in miner_admiral.assignments_ships["Random"]
    assert miner_admiral.ships_assignments[miner1.id] == "Random"
    miner1.set_state.assert_not_called()
    miner1.set_resource_to_mine.assert_not_called()


@patch("src.systems.admirals.miner_admiral.random.choice")
def test_adjust_ship_count_increase_multiple(mock_random_choice, miner_admiral):
    """Test moving multiple free miners using adjust_ship_count."""
    miners = [MockMiningShip(ship_id=i) for i in range(1, 4)]  # IDs 1, 2, 3
    miner_map = {m.id: m for m in miners}
    for miner in miners:
        miner_admiral.add_ship(miner)
        # Reset mocks after add_ship
        miner.set_state.reset_mock()
        miner.set_resource_to_mine.reset_mock()

    # Mock random.choice to return IDs 2 then 3 from the 'Random' list
    mock_random_choice.side_effect = [2, 3]

    assert len(miner_admiral.assignments_ships["Random"]) == 3
    assert len(miner_admiral.assignments_ships["Credits"]) == 0

    miner_admiral.adjust_ship_count_for_category("Credits", 2)

    # Check random.choice calls
    assert mock_random_choice.call_count == 2
    # First call chooses from [1, 2, 3] (or permutation), returns 2
    # Second call chooses from [1, 3] (or permutation), returns 3
    # We can check the arguments more robustly if needed, but call_count is a good start

    assert len(miner_admiral.assignments_ships["Random"]) == 1
    assert len(miner_admiral.assignments_ships["Credits"]) == 2

    # Check miner 2 and 3 were moved
    assert set(miner_admiral.assignments_ships["Credits"]) == {2, 3}
    assert miner_admiral.ships_assignments[2] == "Credits"
    assert miner_admiral.ships_assignments[3] == "Credits"
    # Verify calls on moved ships (2 and 3)
    miner_map[2].set_state.assert_called_once_with(ShipState.IDLE)
    miner_map[2].set_resource_to_mine.assert_called_once_with(None)
    assert miner_map[2].target is None
    miner_map[3].set_state.assert_called_once_with(ShipState.IDLE)
    miner_map[3].set_resource_to_mine.assert_called_once_with(None)
    assert miner_map[3].target is None

    # Ensure miner 1 is untouched
    assert miner_admiral.assignments_ships["Random"] == [1]
    assert miner_admiral.ships_assignments[1] == "Random"
    miner_map[1].set_state.assert_not_called()
    miner_map[1].set_resource_to_mine.assert_not_called()


def test_adjust_ship_count_not_enough_free_miners(miner_admiral, capsys):
    """Test assigning more miners than free warns and assigns available."""
    miner1 = MockMiningShip(ship_id=1)
    miner_admiral.add_ship(miner1)  # Only one free miner
    # Reset mocks after add_ship
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()

    assert len(miner_admiral.assignments_ships["Random"]) == 1

    miner_admiral.adjust_ship_count_for_category("Plasma", 3)  # Request 3
    captured = capsys.readouterr()

    # Should only assign the 1 available miner
    assert len(miner_admiral.assignments_ships["Random"]) == 0
    assert len(miner_admiral.assignments_ships["Plasma"]) == 1
    assert miner_admiral.ships_assignments[miner1.id] == "Plasma"
    # Verify calls on moved ship (miner1)
    miner1.set_state.assert_called_once_with(ShipState.IDLE)
    miner1.set_resource_to_mine.assert_called_once_with(None)
    assert miner1.target is None
    assert "WARN: Not enough free miners to assign" in captured.out


def test_adjust_ship_count_invalid_category(miner_admiral, capsys):
    """Test adjusting assignment for an invalid category warns."""
    miner1 = MockMiningShip(ship_id=1)
    miner_admiral.add_ship(miner1)
    # Reset mocks after add_ship
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()

    miner_admiral.adjust_ship_count_for_category("Uranium", 1)  # Invalid category
    captured = capsys.readouterr()

    # State should not change
    assert len(miner_admiral.assignments_ships["Random"]) == 1
    assert miner1.id in miner_admiral.assignments_ships["Random"]
    assert miner_admiral.ships_assignments[miner1.id] == "Random"
    miner1.set_state.assert_not_called()
    miner1.set_resource_to_mine.assert_not_called()
    assert "WARN: Invalid category Uranium" in captured.out


def test_adjust_ship_count_delta_zero(miner_admiral, capsys):
    """Test adjusting assignment with delta = 0 logs info and does nothing."""
    miner1 = MockMiningShip(ship_id=1)
    miner_admiral.add_ship(miner1)
    # Reset mocks after add_ship
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()

    miner_admiral.adjust_ship_count_for_category("Tritanium", 0)
    captured = capsys.readouterr()

    # State should not change
    assert len(miner_admiral.assignments_ships["Random"]) == 1
    assert len(miner_admiral.assignments_ships["Tritanium"]) == 0
    assert miner_admiral.ships_assignments[miner1.id] == "Random"
    miner1.set_state.assert_not_called()
    miner1.set_resource_to_mine.assert_not_called()
    assert "INFO: No change in assignment for Tritanium" in captured.out


# --- Tests for Decreasing Assignments (Negative Delta) ---


def test_adjust_ship_count_decrease_success(miner_admiral):
    """Test moving a miner from a specific category back to Random."""
    miner1 = MockMiningShip(ship_id=1)
    miner2 = MockMiningShip(ship_id=2)
    miner_admiral.add_ship(miner1)
    miner_admiral.add_ship(miner2)

    # Assign miner2 to Tritanium first
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()
    miner2.set_state.reset_mock()
    miner2.set_resource_to_mine.reset_mock()
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        return_value=miner2.id,
    ) as mock_assign_choice:
        miner_admiral.adjust_ship_count_for_category("Tritanium", 1)
    assert miner_admiral.ships_assignments[miner2.id] == "Tritanium"
    assert miner_admiral.assignments_ships["Tritanium"] == [miner2.id]
    assert miner_admiral.assignments_ships["Random"] == [miner1.id]
    # Check calls during assignment
    miner2.set_state.assert_called_once_with(ShipState.IDLE)
    miner2.set_resource_to_mine.assert_called_once_with(None)
    assert miner2.target is None
    miner1.set_state.assert_not_called()
    # Reset mocks for the decrease check
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()
    miner2.set_state.reset_mock()
    miner2.set_resource_to_mine.reset_mock()

    # Now move one miner *back* from Tritanium (delta = -1)
    # The code removes the *last* element from the category list (miner2.id)
    miner_admiral.adjust_ship_count_for_category("Tritanium", -1)

    # Assert state after decrease
    assert len(miner_admiral.assignments_ships["Random"]) == 2
    assert len(miner_admiral.assignments_ships["Tritanium"]) == 0
    assert miner_admiral.ships_assignments[miner1.id] == "Random"
    assert miner_admiral.ships_assignments[miner2.id] == "Random"  # Miner 2 back to Random
    assert set(miner_admiral.assignments_ships["Random"]) == {1, 2}
    # Check calls during de-assignment (on miner2)
    miner2.set_state.assert_called_once_with(ShipState.IDLE)
    miner2.set_resource_to_mine.assert_called_once_with(None)
    assert miner2.target is None
    miner1.set_state.assert_not_called()
    miner1.set_resource_to_mine.assert_not_called()


def test_adjust_ship_count_decrease_multiple(miner_admiral):
    """Test moving multiple miners back to Random."""
    miners = [MockMiningShip(ship_id=i) for i in range(1, 4)]  # IDs 1, 2, 3
    miner_map = {m.id: m for m in miners}
    miner_ids = set(miner_map.keys())
    for miner in miners:
        miner_admiral.add_ship(miner)

    # Assign all 3 to Credits
    for miner in miners:
        miner.set_state.reset_mock()
        miner.set_resource_to_mine.reset_mock()
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        side_effect=[1, 2, 3],
    ) as mock_assign_choice:
        miner_admiral.adjust_ship_count_for_category("Credits", 3)
    assert miner_admiral.assignments_ships["Credits"] == [1, 2, 3]
    for ship_id in miner_ids:
        assert miner_admiral.ships_assignments[ship_id] == "Credits"
    # Reset mocks after assignment
    for miner in miners:
        miner.set_state.reset_mock()
        miner.set_resource_to_mine.reset_mock()

    # Move 2 back to Random (delta = -2) - removes 3 then 2 (LIFO)
    miner_admiral.adjust_ship_count_for_category("Credits", -2)

    # Assert final state
    assert len(miner_admiral.assignments_ships["Random"]) == 2
    assert len(miner_admiral.assignments_ships["Credits"]) == 1
    assert set(miner_admiral.assignments_ships["Random"]) == {2, 3}
    assert miner_admiral.assignments_ships["Credits"] == [1]
    assert miner_admiral.ships_assignments[1] == "Credits"
    assert miner_admiral.ships_assignments[2] == "Random"
    assert miner_admiral.ships_assignments[3] == "Random"

    # Check calls during de-assignment (on miners 2 and 3)
    miner_map[1].set_state.assert_not_called()
    miner_map[1].set_resource_to_mine.assert_not_called()
    miner_map[2].set_state.assert_called_once_with(ShipState.IDLE)
    miner_map[2].set_resource_to_mine.assert_called_once_with(None)
    assert miner_map[2].target is None
    miner_map[3].set_state.assert_called_once_with(ShipState.IDLE)
    miner_map[3].set_resource_to_mine.assert_called_once_with(None)
    assert miner_map[3].target is None


def test_adjust_ship_count_decrease_below_zero_warns(miner_admiral, capsys):
    """Test trying to remove more miners than assigned warns and does nothing."""
    miner1 = MockMiningShip(ship_id=1)
    miner_admiral.add_ship(miner1)

    # Assign the miner to Plasma
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        return_value=miner1.id,
    ):
        miner_admiral.adjust_ship_count_for_category("Plasma", 1)
    assert miner_admiral.ships_assignments[miner1.id] == "Plasma"
    # Reset mocks after assignment
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()

    assert len(miner_admiral.assignments_ships["Plasma"]) == 1

    # Try to remove 2 miners (delta = -2)
    miner_admiral.adjust_ship_count_for_category("Plasma", -2)
    captured = capsys.readouterr()

    # State should not change
    assert len(miner_admiral.assignments_ships["Random"]) == 0
    assert len(miner_admiral.assignments_ships["Plasma"]) == 1
    assert miner_admiral.ships_assignments[miner1.id] == "Plasma"
    miner1.set_state.assert_not_called()
    miner1.set_resource_to_mine.assert_not_called()
    assert "WARN: Cannot assign less miners than 0" in captured.out


def test_adjust_ship_count_decrease_from_empty_category(miner_admiral):
    """Test decreasing from an already empty category (should do nothing)."""
    miner1 = MockMiningShip(ship_id=1)  # Exists, but in Random
    miner_admiral.add_ship(miner1)
    miner1.set_state.reset_mock()
    miner1.set_resource_to_mine.reset_mock()

    assert len(miner_admiral.assignments_ships["Tritanium"]) == 0

    # Try to remove from empty Tritanium category (delta = -1)
    miner_admiral.adjust_ship_count_for_category("Tritanium", -1)

    # Should do nothing
    assert len(miner_admiral.assignments_ships["Random"]) == 1
    assert len(miner_admiral.assignments_ships["Tritanium"]) == 0
    assert miner_admiral.ships_assignments[miner1.id] == "Random"
    miner1.set_state.assert_not_called()
    miner1.set_resource_to_mine.assert_not_called()


# --- Tests for assign_idle_miners ---


# @patch('src.systems.admirals.miner_admiral.utils.find_nearest_with_resource') # Incorrect target
@patch(
    "src.systems.admirals.miner_admiral.MinerAdmiral._find_nearest_with_resource"
)  # Correct target
def test_assign_idle_miner_specific_category(mock_find_nearest, miner_admiral):
    """Test assigning an IDLE miner when a specific category is set."""
    miner = MockMiningShip(ship_id=1, state=ShipState.IDLE)
    miner_admiral.add_ship(miner)
    # Manually move to Tritanium category - Assume adjust_ship_count works from previous tests
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        return_value=miner.id,
    ):
        miner_admiral.adjust_ship_count_for_category("Tritanium", 1)
    miner.set_target.reset_mock()  # Reset mock after setup

    target_asteroid = MockAsteroid(asteroid_id=1001, resources={ResourceType.TRITANIUM: 50})
    asteroids = [target_asteroid]
    mock_find_nearest.return_value = target_asteroid

    miner_admiral.assign_idle_miners(asteroids)

    mock_find_nearest.assert_called_once_with(miner.position, asteroids, "Tritanium")
    miner.set_target.assert_called_once_with(target_asteroid)
    # We don't directly check state change here, but implicitly set_target should trigger it
    # miner.assign_task.assert_not_called() # Remove assign_task check


@patch("src.systems.admirals.miner_admiral.random.choice")
def test_assign_idle_miner_random_category(mock_random_choice, miner_admiral):
    """Test assigning an idle miner in the Random category."""
    miner = MockMiningShip(ship_id=1, state=ShipState.IDLE, cargo=10, capacity=100)
    miner_admiral.add_ship(miner)  # Starts in Random category
    miner.set_target.reset_mock()

    # Mock random.choice to return 'Plasma' then the target asteroid
    target_asteroid = MockAsteroid(asteroid_id=1001, resources={ResourceType.list()[1]: 50})
    chosen_resource = ResourceType.list()[1]  # Plasma
    # Side effect: First chooses category, second chooses asteroid from filtered list
    mock_random_choice.side_effect = [chosen_resource, target_asteroid]

    asteroids = [
        target_asteroid,  # Good target
        MockAsteroid(resources={ResourceType.TRITANIUM: 100}),  # Other resource
    ]

    miner_admiral.assign_idle_miners(asteroids)

    # Check random.choice calls
    assert mock_random_choice.call_count == 2
    # First call selects category
    assert mock_random_choice.call_args_list[0][0][0] == ResourceType.list()
    # Second call selects asteroid (should only be passed valid plasma asteroids)
    assert mock_random_choice.call_args_list[1][0][0] == [target_asteroid]

    # Check set_target was called with the selected asteroid
    miner.set_target.assert_called_once_with(target_asteroid)
    # miner.assign_task.assert_not_called() # Remove assign_task check


def test_assign_idle_miner_cargo_full(miner_admiral):
    """Test idle miner with full cargo gets sent to base."""
    miner = MockMiningShip(ship_id=1, state=ShipState.IDLE, cargo=100, capacity=100)
    miner.get_cargo_total.return_value = 100  # Ensure mock reflects full cargo
    miner_admiral.add_ship(miner)
    miner.set_target.reset_mock()

    asteroids = [MockAsteroid()]  # Doesn't matter which asteroids

    miner_admiral.assign_idle_miners(asteroids)

    # Should be sent to its own home planet
    miner.set_target.assert_called_once_with(miner.home)
    # The internal state update happens in the ship, we just check the target was set
    # assert miner.state == ShipState.RETURNING_TO_BASE # Remove direct state check
    # miner.assign_task.assert_not_called() # Remove assign_task check


def test_assign_idle_miners_no_idle_miners(miner_admiral):
    """Test assign_idle_miners does nothing if no miners are IDLE."""
    miner = MockMiningShip(ship_id=1, state=ShipState.MINING)  # Not IDLE
    miner_admiral.add_ship(miner)
    miner.set_target.reset_mock()
    miner.set_state.reset_mock()
    miner.set_resource_to_mine.reset_mock()
    miner.state = ShipState.MINING
    asteroids = [MockAsteroid()]

    miner_admiral.assign_idle_miners(asteroids)

    miner.set_target.assert_not_called()
    miner.set_state.assert_not_called()
    miner.set_resource_to_mine.assert_not_called()
    # miner.assign_task.assert_not_called() # Remove assign_task check


@patch("src.systems.admirals.miner_admiral.MinerAdmiral._find_nearest_with_resource")
def test_assign_idle_miner_no_suitable_asteroid(mock_find_nearest, miner_admiral):
    """Test miner remains IDLE if no suitable asteroid is found for its category."""
    miner = MockMiningShip(ship_id=1, state=ShipState.IDLE)
    miner_admiral.add_ship(miner)
    # Assign to Tritanium
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        return_value=miner.id,
    ):
        miner_admiral.adjust_ship_count_for_category("Tritanium", 1)
    miner.set_target.reset_mock()
    miner.set_state.reset_mock()
    miner.set_resource_to_mine.reset_mock()

    asteroids = [MockAsteroid(resources={ResourceType.PLASMA: 50})]  # Asteroid has wrong resource
    mock_find_nearest.return_value = None  # Mock finding nothing

    miner_admiral.assign_idle_miners(asteroids)

    mock_find_nearest.assert_called_once_with(miner.position, asteroids, "Tritanium")
    miner.set_target.assert_called_once_with(None)
    miner.set_state.assert_called_once_with(ShipState.IDLE)
    miner.set_resource_to_mine.assert_called_once_with(None)
    assert miner.state == ShipState.IDLE


# --- Tests for _find_target_for_category --- # Updated signature


# @patch('src.systems.admirals.miner_admiral.utils.find_nearest_with_resource') # Incorrect target
@patch(
    "src.systems.admirals.miner_admiral.MinerAdmiral._find_nearest_with_resource"
)  # Correct target
def test_find_target_specific_category_success(mock_find_nearest, miner_admiral):
    """Test _find_target_for_category successfully finds target for a specific resource."""
    miner_pos = (0, 0)
    miner = MockMiningShip(position=miner_pos)
    target_asteroid = MockAsteroid(resources={ResourceType.CREDITS: 100}, position=(10, 0))
    other_asteroid = MockAsteroid(resources={ResourceType.CREDITS: 100}, position=(20, 0))
    asteroids = [other_asteroid, target_asteroid]  # Target is closer
    mock_find_nearest.return_value = target_asteroid

    # Function returns a tuple: (target_asteroid, resource_to_mine)
    found_target, found_resource = miner_admiral._find_target_for_category(miner, "Credits", asteroids)

    mock_find_nearest.assert_called_once_with(miner_pos, asteroids, "Credits")
    assert found_target is target_asteroid
    assert found_resource == ResourceType.CREDITS # Check the returned resource type


@patch("src.systems.admirals.miner_admiral.random.choice")
def test_find_target_random_category_success(mock_random_choice, miner_admiral):
    """Test _find_target_for_category finds random for 'Random' category."""
    miner = MockMiningShip(position=(0, 0))
    asteroid_plasma = MockAsteroid(
        resources={ResourceType.PLASMA: 50},
        position=(10, 10),
        asteroid_id=1001,
        scanned=True,
    )
    asteroid_trit = MockAsteroid(
        resources={ResourceType.TRITANIUM: 50},
        position=(5, 5),
        asteroid_id=1002,
        scanned=True,
    )
    asteroids = [asteroid_plasma, asteroid_trit]

    # Mock the category choice ('Plasma') and then the asteroid choice
    mock_random_choice.side_effect = [ResourceType.PLASMA, asteroid_plasma]

    found_target, found_resource = miner_admiral._find_target_for_category(miner, "Random", asteroids)

    assert mock_random_choice.call_count == 2
    # First call chooses category
    assert mock_random_choice.call_args_list[0][0][0] == ResourceType.list()
    # Second call chooses from asteroids with that resource (only plasma one is valid)
    assert mock_random_choice.call_args_list[1][0][0] == [asteroid_plasma]

    assert found_target is asteroid_plasma
    assert found_resource == ResourceType.PLASMA


# @patch('src.systems.admirals.miner_admiral.utils.find_nearest_with_resource') # Incorrect target
@patch(
    "src.systems.admirals.miner_admiral.MinerAdmiral._find_nearest_with_resource"
)  # Correct target
def test_find_target_specific_category_not_found(mock_find_nearest, miner_admiral):
    """Test _find_target_for_category returns None when no asteroid has the resource."""
    miner_pos = (0, 0)
    # Pass miner object, not position, to the function being tested
    miner = MockMiningShip(position=miner_pos)
    asteroids = [MockAsteroid(resources={ResourceType.PLASMA: 50})]
    mock_find_nearest.return_value = None

    # Unpack the tuple return value
    found_target, found_resource = miner_admiral._find_target_for_category(miner, "Credits", asteroids)

    # Check that the *mocked* function was called with the correct position
    mock_find_nearest.assert_called_once_with(miner_pos, asteroids, "Credits")
    assert found_target is None # Check only the target part
    # Resource type should still be the requested one, even if no target found
    assert found_resource is None


def test_find_target_random_category_no_asteroids(miner_admiral):
    """Test _find_target_for_category for 'Random' when no asteroids exist."""
    miner = MockMiningShip(position=(0, 0))
    asteroids = []

    # Need to patch random.choice for category selection
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        return_value="Tritanium",
    ) as mock_cat_choice:
        # Unpack the tuple return value
        found_target, found_resource = miner_admiral._find_target_for_category(miner, "Random", asteroids)

    mock_cat_choice.assert_called_once()
    assert found_target is None # Check only the target part
    assert found_resource is None # Resource is also None here


def test_find_target_random_category_no_matching_asteroid(miner_admiral):
    """Test _find_target_for_category for 'Random' when no asteroid has the chosen resource."""
    miner = MockMiningShip(position=(0, 0))
    # Asteroid exists, but doesn't have the randomly chosen resource, and isn't scanned
    asteroids = [MockAsteroid(resources={ResourceType.PLASMA: 50}, scanned=True)]

    # Patch random.choice to return 'Tritanium', which isn't available
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        return_value="Tritanium",
    ) as mock_cat_choice:
        found_target, found_resource = miner_admiral._find_target_for_category(miner, "Random", asteroids)

    mock_cat_choice.assert_called_once()
    assert found_target is None # Check only the target part
    assert found_resource is None # Resource is also None here


def test_find_target_invalid_category(miner_admiral, capsys):
    """Test _find_target_for_category with an invalid category string."""
    miner = MockMiningShip()
    asteroids = [MockAsteroid()]

    found_target, found_resource = miner_admiral._find_target_for_category(miner, "InvalidCategory", asteroids)
    captured = capsys.readouterr()

    assert found_target is None # Check only the target part
    assert found_resource is None # Resource is also None here
    assert "WARN: Invalid category InvalidCategory" in captured.out


# --- More specific tests for assign_idle_miners Edge Cases ---


# @patch('src.systems.admirals.miner_admiral.utils.find_nearest_with_resource') # Incorrect target
@patch(
    "src.systems.admirals.miner_admiral.MinerAdmiral._find_nearest_with_resource"
)  # Correct target
def test_assign_idle_miner_ignores_unscanned_asteroid(
    mock_find_nearest, miner_admiral
):
    """Test that _find_nearest_with_resource (called by admiral) ignores unscanned asteroids."""
    miner = MockMiningShip(ship_id=1, state=ShipState.IDLE, position=(0, 0))
    miner_admiral.add_ship(miner)
    # Assign to Tritanium
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        return_value=miner.id,
    ):
        miner_admiral.adjust_ship_count_for_category("Tritanium", 1)
    miner.set_target.reset_mock()
    miner.set_state.reset_mock()
    miner.set_resource_to_mine.reset_mock()

    # utils.find_nearest_with_resource should handle filtering unscanned/zero resource
    # So we just need to ensure it returns None if only unsuitable asteroids exist
    unscanned_asteroid = MockAsteroid(resources={ResourceType.TRITANIUM: 100}, scanned=False)
    asteroids = [unscanned_asteroid]
    mock_find_nearest.return_value = None  # Mocking the expected outcome

    miner_admiral.assign_idle_miners(asteroids)

    mock_find_nearest.assert_called_once_with(miner.position, asteroids, "Tritanium")
    # set_target IS called with None when no suitable asteroid is found
    miner.set_target.assert_called_once_with(None)
    miner.set_state.assert_called_once_with(ShipState.IDLE)
    miner.set_resource_to_mine.assert_called_once_with(None)
    assert miner.state == ShipState.IDLE


# @patch('src.systems.admirals.miner_admiral.utils.find_nearest_with_resource') # Incorrect target
@patch(
    "src.systems.admirals.miner_admiral.MinerAdmiral._find_nearest_with_resource"
)  # Correct target
def test_assign_idle_miner_ignores_zero_resource_asteroid(
    mock_find_nearest, miner_admiral
):
    """Test that _find_nearest_with_resource (called by admiral) ignores asteroids with zero resources."""
    miner = MockMiningShip(ship_id=1, state=ShipState.IDLE, position=(0, 0))
    miner_admiral.add_ship(miner)
    # Assign to Tritanium
    with patch(
        "src.systems.admirals.miner_admiral.random.choice",
        return_value=miner.id,
    ):
        miner_admiral.adjust_ship_count_for_category("Tritanium", 1)
    miner.set_target.reset_mock()
    miner.set_state.reset_mock()
    miner.set_resource_to_mine.reset_mock()

    zero_resource_asteroid = MockAsteroid(resources={ResourceType.TRITANIUM: 0}, scanned=True)
    asteroids = [zero_resource_asteroid]
    mock_find_nearest.return_value = None  # Mocking the expected outcome

    miner_admiral.assign_idle_miners(asteroids)

    mock_find_nearest.assert_called_once_with(miner.position, asteroids, "Tritanium")
    # set_target IS called with None when no suitable asteroid is found
    miner.set_target.assert_called_once_with(None)
    miner.set_state.assert_called_once_with(ShipState.IDLE)
    miner.set_resource_to_mine.assert_called_once_with(None)
    assert miner.state == ShipState.IDLE


# Test the Random assignment path specifically regarding filtering
@patch("src.systems.admirals.miner_admiral.random.choice")
def test_assign_idle_miner_random_ignores_unsuitable(
    mock_random_choice, miner_admiral
):
    """Test Random miner assignment filters out unscanned/zero-resource asteroids."""
    miner = MockMiningShip(ship_id=1, state=ShipState.IDLE)
    miner_admiral.add_ship(miner)  # In Random category
    miner.set_target.reset_mock()
    miner.set_state.reset_mock()
    miner.set_resource_to_mine.reset_mock()

    unscanned_trit = MockAsteroid(resources={ResourceType.TRITANIUM: 100}, scanned=False, asteroid_id=1001)
    zero_trit = MockAsteroid(resources={ResourceType.TRITANIUM: 0}, scanned=True, asteroid_id=1002)
    good_plasma = MockAsteroid(resources={ResourceType.PLASMA: 50}, scanned=True, asteroid_id=1003)
    asteroids = [unscanned_trit, zero_trit, good_plasma]

    # Mock random choice: first selects 'Tritanium' category,
    # then should only be presented with valid asteroids for that category (none in this case)
    # Since Tritanium fails, it tries again or does nothing.
    # Current code only tries one category per cycle, so it should do nothing.
    mock_random_choice.side_effect = ["Tritanium"]  # Choose Tritanium

    miner_admiral.assign_idle_miners(asteroids)

    # random.choice called once to pick category
    mock_random_choice.assert_called_once_with(ResourceType.list())
    miner.set_target.assert_called_once_with(None)
    miner.set_state.assert_called_once_with(ShipState.IDLE)
    miner.set_resource_to_mine.assert_called_once_with(None)
    assert miner.state == ShipState.IDLE


@patch("src.systems.admirals.miner_admiral.random.choice")
def test_assign_idle_miner_random_selects_correct_asteroid(
    mock_random_choice, miner_admiral
):
    """Test Random miner assignment selects a valid asteroid when mixed options exist."""
    miner = MockMiningShip(ship_id=1, state=ShipState.IDLE)
    miner_admiral.add_ship(miner)  # In Random category
    miner.set_target.reset_mock()

    zero_trit = MockAsteroid(resources={ResourceType.TRITANIUM: 0}, scanned=True, asteroid_id=1002)
    good_plasma = MockAsteroid(resources={ResourceType.PLASMA: 50}, scanned=True, asteroid_id=1003)
    asteroids = [zero_trit, good_plasma]

    # Mock random choice: first selects 'Plasma' category,
    # then should choose the only valid Plasma asteroid.
    mock_random_choice.side_effect = [ResourceType.PLASMA, good_plasma]

    miner_admiral.assign_idle_miners(asteroids)

    # random.choice called twice (category, then asteroid)
    assert mock_random_choice.call_count == 2
    assert mock_random_choice.call_args_list[0][0][0] == ResourceType.list()
    assert mock_random_choice.call_args_list[1][0][0] == [
        good_plasma
    ]  # Only valid option presented
    # Target should be assigned to the good plasma asteroid
    miner.set_target.assert_called_once_with(good_plasma)
    # Assuming set_target implies state change (though mock doesn't enforce)
    # assert miner.state != ShipState.IDLE


# --- Tests for _find_nearest_with_resource ---


def test_find_nearest_with_resource_finds_closest(miner_admiral):
    source_pos = Vector2(0, 0)
    a_near = MockAsteroid(position=(10, 0), resources={ResourceType.TRITANIUM: 50})
    a_far = MockAsteroid(position=(100, 0), resources={ResourceType.TRITANIUM: 100})
    asteroids = [a_far, a_near]
    nearest = miner_admiral._find_nearest_with_resource(source_pos, asteroids, "Tritanium")
    assert nearest is a_near


def test_find_nearest_with_resource_ignores_wrong_resource(miner_admiral):
    source_pos = Vector2(0, 0)
    a_trit = MockAsteroid(position=(10, 0), resources={ResourceType.TRITANIUM: 50})
    a_cred = MockAsteroid(position=(5, 0), resources={ResourceType.CREDITS: 100})  # Closer but wrong resource
    asteroids = [a_trit, a_cred]
    # Look for Tritanium, should ignore the closer Credits asteroid
    nearest = miner_admiral._find_nearest_with_resource(source_pos, asteroids, "Tritanium")
    assert nearest is a_trit


def test_find_nearest_with_resource_ignores_unscanned(miner_admiral):
    source_pos = Vector2(0, 0)
    a_scanned = MockAsteroid(position=(100, 0), scanned=True, resources={ResourceType.PLASMA: 50})
    a_unscanned = MockAsteroid(
        position=(10, 0), scanned=False, resources={ResourceType.PLASMA: 100}
    )  # Closer but unscanned
    asteroids = [a_scanned, a_unscanned]
    nearest = miner_admiral._find_nearest_with_resource(source_pos, asteroids, "Plasma")
    assert nearest is a_scanned  # Should ignore the closer unscanned one


def test_find_nearest_with_resource_no_match(miner_admiral):
    source_pos = Vector2(0, 0)
    a_trit = MockAsteroid(position=(10, 0), resources={ResourceType.TRITANIUM: 50})
    a_cred = MockAsteroid(position=(5, 0), resources={ResourceType.CREDITS: 100})
    asteroids = [a_trit, a_cred]
    # Look for Plasma, none exists
    nearest = miner_admiral._find_nearest_with_resource(source_pos, asteroids, "Plasma")
    assert nearest is None


def test_find_nearest_with_resource_empty_list(miner_admiral):
    source_pos = Vector2(0, 0)
    asteroids = []
    nearest = miner_admiral._find_nearest_with_resource(source_pos, asteroids, "Tritanium")
    assert nearest is None

def test_issue_command_returning_to_planet_sets_returning_and_resets_timers(miner_admiral):
    # TODO: Implement this test and for other issue commands
    pass
