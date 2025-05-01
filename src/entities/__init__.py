# This file makes Python treat the directory as a package. 

from .entity import Entity
from .asteroid import Asteroid
from .planet import Planet
# Import ship types indirectly via the ships subpackage
from .ships import MiningShip, ScannerShip, Ship # Import base Ship too?

__all__ = [
    "Entity",
    "Asteroid",
    "Planet",
    "Ship", # Export base Ship
    "MiningShip",
    "ScannerShip",
    # Add other specific ship types if needed directly
] 