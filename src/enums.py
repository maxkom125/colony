from enum import Enum, auto


class ShipState(Enum):
    IDLE = auto()
    MOVING_TO_ASTEROID = auto()
    SCANNING = auto()
    MINING = auto()
    RETURNING_TO_BASE = auto()
    DUMPING = auto()
