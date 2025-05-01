import sys
import os
import inspect
import pytest

# Add project root to sys.path so that 'src' modules can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.entities.ships.base_ship import Ship

@pytest.fixture(autouse=True)
def enforce_set_target_caller(monkeypatch):
    original = Ship.set_target
    def wrapper(self, target_entity):
        # Walk the call stack to find an allowed caller
        for frame_info in inspect.stack()[1:]:
            module = inspect.getmodule(frame_info.frame)
            # Allow calls from admiral modules
            if module and module.__name__.startswith("src.systems.admirals"):
                return original(self, target_entity)
            # Skip enforcement for test files
            if "tests/" in frame_info.filename or (module and module.__name__.startswith("tests")):
                return original(self, target_entity)
        # No allowed caller found: fail the test
        pytest.fail(
            f"Unauthorized call to set_target in {frame_info.filename}:{frame_info.lineno}"
        )
    monkeypatch.setattr(Ship, "set_target", wrapper)

@pytest.fixture(scope="session", autouse=True)
def check_no_set_target_override():
    # Ensure no subclass of Ship overrides the base set_target implementation
    # This is to ensure that the set_target method is not overridden by any subclass
    # See conftest.py/enforce_set_target_caller for this check
    from src.entities.ships.base_ship import Ship
    # Recursively gather all subclasses
    def all_subclasses(cls):
        for sub in cls.__subclasses__():
            yield sub
            yield from all_subclasses(sub)
    for subclass in all_subclasses(Ship):
        # If subclass defines its own set_target (not inherited)
        if getattr(subclass, 'set_target', None) is not Ship.set_target:
            pytest.fail(f"Class {subclass.__module__}.{subclass.__name__} overrides set_target, tests require using the base implementation.") 