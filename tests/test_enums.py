import pytest
from src.enums import ShipType
from src.entities.ships.base_ship import Ship
from pygame.math import Vector2
from src.entities.planet import Planet


def test_shiptype_class_reachable_and_inheritance():
    for ship_type in ShipType:
        cls = ship_type.ship_class
        assert isinstance(cls, type), f"ShipType {ship_type} class not reachable: {cls}"
        # Always instantiate the class and check inheritance, including UNKNOWN
        dummy_args = [Vector2(0, 0), 10, (0, 0, 0), 1.0, Planet(Vector2(0, 0))]
        instance = cls(*dummy_args)
        assert isinstance(instance, Ship), f"Instance of {cls} is not a subclass of Ship"
