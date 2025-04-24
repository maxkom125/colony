import pytest
import random
from pygame.math import Vector2
from src.entities.asteroid import Asteroid
from src import constants

@pytest.fixture(autouse=True)
def fixed_random(monkeypatch):
    # Always choose the first resource type and minimal amount
    monkeypatch.setattr(random, 'choices', lambda *args, **kwargs: [constants.RESOURCE_TYPES[0]])
    monkeypatch.setattr(random, 'randint', lambda a, b: a)

    yield


def test_resource_distribution_and_dominant_color():
    color = (123, 234, 56)
    ast = Asteroid(Vector2(0, 0), radius=5, color=color)
    # After init, only first resource type should have positive amount
    dominant = constants.RESOURCE_TYPES[0]
    for res_type, amount in ast.resources.items():
        if res_type == dominant:
            assert amount == constants.ASTEROID_MIN_RESOURCE_AMOUNT
        else:
            assert amount == 0
    # get_dominant_resource_color should map Tritanium -> TRITANIUM_COLOR
    expected_color = constants.TRITANIUM_COLOR
    assert ast.get_dominant_resource_color() == expected_color


def test_dominant_color_falls_back_to_initial_when_empty():
    ast = Asteroid(Vector2(0, 0), radius=5, color=(10, 20, 30))
    # Empty out resources
    ast.resources = {}
    assert ast.get_dominant_resource_color() == (10, 20, 30) 