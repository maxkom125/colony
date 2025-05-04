# tests/systems/test_space_market.py
import pytest
from src.systems.space_market import SpaceMarket
from src.enums import ResourceType


@pytest.fixture
def space_market() -> SpaceMarket:
    """Provides a default SpaceMarket instance for testing."""
    return SpaceMarket()


def test_market_rates_contain_all_resource_types(space_market):
    """Verify that market rate dictionaries contain all non-credit ResourceTypes."""
    # Get all defined ResourceType members
    all_resources = set(ResourceType)
    # Define the resources that should be tradable (i.e., not Credits itself)
    tradable_resources = all_resources - {ResourceType.CREDITS}

    # Check current sell rates keys
    assert (
        set(space_market.current_sell_rates.keys()) == tradable_resources
    ), "current_sell_rates missing or has extra resource types"

    # Check current buy rates keys
    assert (
        set(space_market.current_buy_rates.keys()) == tradable_resources
    ), "current_buy_rates missing or has extra resource types"

    # Optionally, check base rates as well
    assert (
        set(space_market.base_sell_rates.keys()) == tradable_resources
    ), "base_sell_rates missing or has extra resource types"
    assert (
        set(space_market.base_buy_rates.keys()) == tradable_resources
    ), "base_buy_rates missing or has extra resource types"
