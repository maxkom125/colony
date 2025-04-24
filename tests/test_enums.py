import pytest
from src.enums import ShipState

def test_shipstate_members_exist():
    expected = {"IDLE", "MOVING_TO_ASTEROID", "SCANNING", "MINING", "RETURNING_TO_BASE", "DUMPING"}
    actual = {state.name for state in ShipState}
    assert actual == expected 