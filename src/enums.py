from enum import Enum, auto
from typing import List


class ShipState(Enum):
    IDLE = auto()
    MOVING_TO_ASTEROID = auto()
    MOVING_TO_SCAN = auto()
    MOVING_TO_POSITION = auto()
    SCANNING = auto()
    MINING = auto()
    RETURNING_TO_BASE = auto()
    DUMPING = auto()

    def __str__(self):
        # so str(ShipState.IDLE) == "IDLE"
        return self.value

    @classmethod
    def list(cls) -> List[str]:
        # e.g. ["IDLE", "MOVING_TO_ASTEROID"]
        return [member.value for member in cls]

class ShipType(Enum):
    UNKNOWN = "Unknown"
    MINER = "Miner"
    SCANNER = "Scanner"
    # Add other types like COMBAT, TRANSPORT etc.

    def __str__(self):
        # so str(ShipType.MINER) == "Miner"
        return self.value

    @classmethod
    def list(cls) -> List[str]:
        # e.g. ["Miner", "Scanner"]
        return [member.value for member in cls]

class ResourceType(Enum):
    TRITANIUM = ("Tritanium", 0.45)
    CREDITS   = ("Credits",   0.15)
    PLASMA    = ("Plasma",    0.40)

    def __new__(cls, label: str, weight: float):
        obj = object.__new__(cls)
        obj._value_ = label
        obj.weight = weight
        return obj

    def __str__(self):
        # so str(ResourceType.TRITANIUM) == "Tritanium"
        return self.value

    @classmethod
    def list(cls) -> List[str]:
        # e.g. ["Tritanium", "Credits", "Plasma"]
        return [member.value for member in cls]

    @classmethod
    def weights(cls) -> List[float]:
        """Returns list of weights in the same order as list()."""
        return [member.weight for member in cls]
