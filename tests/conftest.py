import sys
import os
import inspect
import logging # Required for the custom caplog
import pytest
from loguru import logger # Required for the custom caplog

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

# Custom caplog fixture for Loguru
# This allows Loguru logs to be captured by pytest's caplog fixture.
@pytest.fixture
def caplog(caplog):
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    # Ensure the Loguru logger instance is the one from our application
    # This might require importing it from src.logger if it's not globally available
    # For now, assuming 'logger' is the global Loguru instance or imported correctly.
    # If src.logger.logger is the instance, use that.
    # from src.logger import logger as loguru_logger_instance
    loguru_logger_instance = logger # Assuming global logger or already imported

    handler_id = loguru_logger_instance.add(PropagateHandler(), format="{message}", level="DEBUG")
    caplog.set_level(logging.DEBUG) # Ensure pytest's caplog captures DEBUG level
    yield caplog
    loguru_logger_instance.remove(handler_id)