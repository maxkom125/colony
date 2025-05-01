# This file makes Python treat the directory as a package. 

from .base_ship import Ship          # Import the base class
from .mining_ship import MiningShip
from .scanner_ship import ScannerShip
# Import other ship types here as they are created

__all__ = [
    "Ship",       # Export the base class
    "MiningShip",
    "ScannerShip",
    # Add other ship types to this list
] 