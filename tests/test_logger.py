import pytest
import os
import json
import shutil
from datetime import datetime

# Ensure src modules can be imported (if conftest.py doesn't handle it sufficiently for all test runners)
# This might be redundant if conftest.py's sys.path manipulation is effective.
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.dirname(current_dir)
# if project_root not in sys.path:
#    sys.path.insert(0, project_root)

from src.logger import logger, setup_logging

# --- Fixtures ---

@pytest.fixture
def game_debug_env(monkeypatch):
    """Fixture to manage the GAME_DEBUG environment variable."""
    def _set_game_debug(value):
        if value is None:
            monkeypatch.delenv("GAME_DEBUG", raising=False)
        else:
            monkeypatch.setenv("GAME_DEBUG", str(value))
    return _set_game_debug

@pytest.fixture(scope="function")
def temp_log_file(tmp_path):
    """
    Fixture to set up a temporary log directory and file for testing file logging.
    It also ensures setup_logging is called to use this temp file.
    """
    original_stderr_handler_id = None
    original_file_handler_id = None

    # Find existing handlers to remove them before adding test-specific ones
    # This is a bit complex as Loguru doesn't easily expose all handlers by default.
    # We rely on the fact that setup_logging() in logger.py will remove and re-add.

    # Store current state of logger's handlers to restore later (if any were added outside setup_logging)
    # For this test, we assume setup_logging is the sole configurator.
    
    # Redirect logs to a temporary directory
    temp_log_dir = tmp_path / "temp_test_logs"
    temp_log_dir.mkdir()
    test_log_file = temp_log_dir / "test_game.log"

    # Temporarily modify setup_logging or logger's configuration for the test
    # For Loguru, this means removing existing handlers and adding new ones pointing to the temp file.
    
    logger.remove() # Remove all handlers

    # Add a minimal console handler for test visibility if needed (or rely on caplog)
    # logger.add(sys.stderr, level="DEBUG") # Or use caplog for console capture

    # Add the temporary file handler
    file_handler_id = logger.add(
        test_log_file,
        level="DEBUG",
        format="{message}", # Keep consistent with main setup for JSON
        serialize=True,
        rotation="1 day", # Not strictly needed for test, but matches config
        retention="1 day",
        compression=None # No compression for easier reading in tests
    )

    yield test_log_file # Provide the path to the test log file

    # Teardown: remove the temporary file handler and directory
    logger.remove(file_handler_id)
    # Re-run original setup_logging to restore normal logger behavior
    # This is crucial so other tests are not affected.
    # Need to ensure setup_logging() itself is idempotent or correctly re-initializes.
    # logger.py's setup_logging already calls logger.remove()
    setup_logging() 
    
    # shutil.rmtree(temp_log_dir) # tmp_path fixture handles cleanup of the directory

# --- Helper Functions ---

def parse_log_file(log_file_path):
    """Parses a JSON log file, returning a list of log records."""
    records = []
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    return records

# --- Console Logging Tests ---

def test_console_default_logging(caplog, game_debug_env):
    """Test that INFO messages are logged by default (GAME_DEBUG not set)."""
    game_debug_env(None)
    logger.remove() # Ensure clean slate for handlers
    setup_logging() # Initialize logger with current env var state
    
    logger.info("Info message for default test")
    logger.debug("Debug message for default test")

    assert "Info message for default test" in caplog.text
    assert "Debug message for default test" not in caplog.text
    # Check level in records
    info_record = next((r for r in caplog.records if r.message == "Info message for default test"), None)
    assert info_record is not None
    assert info_record.levelname == "INFO"

def test_console_game_debug_true(caplog, game_debug_env):
    """Test that DEBUG messages are logged when GAME_DEBUG is 'True'."""
    game_debug_env("True")
    logger.remove()
    setup_logging()

    logger.info("Info message for GAME_DEBUG=True test")
    logger.debug("Debug message for GAME_DEBUG=True test")

    assert "Info message for GAME_DEBUG=True test" in caplog.text
    assert "Debug message for GAME_DEBUG=True test" in caplog.text
    debug_record = next((r for r in caplog.records if r.message == "Debug message for GAME_DEBUG=True test"), None)
    assert debug_record is not None
    assert debug_record.levelname == "DEBUG"

def test_console_game_debug_one(caplog, game_debug_env):
    """Test that DEBUG messages are logged when GAME_DEBUG is '1'."""
    game_debug_env("1")
    logger.remove()
    setup_logging()

    logger.debug("Debug message for GAME_DEBUG=1 test")
    assert "Debug message for GAME_DEBUG=1 test" in caplog.text
    debug_record = next((r for r in caplog.records if r.message == "Debug message for GAME_DEBUG=1 test"), None)
    assert debug_record is not None
    assert debug_record.levelname == "DEBUG"

def test_console_game_debug_false(caplog, game_debug_env):
    """Test that DEBUG messages are NOT logged when GAME_DEBUG is 'False'."""
    game_debug_env("False")
    logger.remove()
    setup_logging()

    logger.info("Info message for GAME_DEBUG=False test")
    logger.debug("Debug message for GAME_DEBUG=False test")
    
    assert "Info message for GAME_DEBUG=False test" in caplog.text
    assert "Debug message for GAME_DEBUG=False test" not in caplog.text

def test_console_game_debug_unset(caplog, game_debug_env):
    """Test that DEBUG messages are NOT logged when GAME_DEBUG is unset."""
    game_debug_env(None) # Equivalent to not being set
    logger.remove()
    setup_logging()

    logger.info("Info message for GAME_DEBUG unset test")
    logger.debug("Debug message for GAME_DEBUG unset test")

    assert "Info message for GAME_DEBUG unset test" in caplog.text
    assert "Debug message for GAME_DEBUG unset test" not in caplog.text

def test_console_log_format(caplog, game_debug_env):
    """Test the console log message format."""
    game_debug_env("True") # Ensure a known level (DEBUG) for format check
    logger.remove()
    setup_logging()

    test_message = "Testing console format"
    logger.info(test_message)

    # Example: 2023-10-27 10:00:00.123 | INFO     | test_logger:test_console_log_format:123 - Testing console format
    # We can't match the exact time or line number easily.
    # Instead, check for key parts of the format.
    
    # Find the relevant log record from caplog.records
    # The custom conftest.py caplog for Loguru might not populate caplog.text in the same way
    # or might not have the fully formatted message there.
    # It's safer to check the record attributes if the PropagateHandler works as expected.
    
    found_record = None
    for record in caplog.records:
        if record.message == test_message and record.levelname == "INFO":
            found_record = record
            break
    
    assert found_record is not None, "Test message not found in caplog.records"
    
    # If using the PropagateHandler, the `record.msg` or `record.message` should be the raw message.
    # The formatted message would be in caplog.text if the handler setup works perfectly with pytest's caplog.
    # Let's assume the conftest caplog makes formatted text available via caplog.text for simplicity here.
    # If not, this part of the test would need adjustment to reconstruct/check format from record fields.

    # A less fragile check for the formatted message:
    # This relies on the conftest.py correctly piping formatted Loguru output to caplog.text
    formatted_log_entry = None
    for log_text_line in caplog.text.splitlines():
        if test_message in log_text_line and "INFO" in log_text_line:
            formatted_log_entry = log_text_line
            break
    
    assert formatted_log_entry is not None, "Formatted log entry not found in caplog.text"
    assert "INFO" in formatted_log_entry
    assert test_message in formatted_log_entry
    assert "|" in formatted_log_entry # Check for separators
    # A regex could be used for a more precise format match if needed:
    # import re
    # assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| INFO\s* \| .*:\d+ - Testing console format", formatted_log_entry)


# --- File Logging Tests ---

def test_file_logging_creates_file_and_directory(temp_log_file):
    """Test that the log file and directory are created."""
    assert os.path.exists(os.path.dirname(temp_log_file)), "Log directory was not created"
    # Log a message to ensure the file itself is created by Loguru
    logger.info("Test message to ensure file creation.")
    assert os.path.exists(temp_log_file), "Log file was not created"

def test_file_logging_json_format_and_content(temp_log_file):
    """Test that file logs are in JSON format and contain expected fields."""
    logger.info("File JSON test: Info message.")
    logger.debug({"structured": True, "message": "File JSON test: Debug message with data."})

    records = parse_log_file(temp_log_file)
    assert len(records) >= 2, "Not enough log records found in file."

    # Check first record (simple string message)
    record1 = next(r for r in records if r['record']['message'] == "File JSON test: Info message.")
    assert record1 is not None
    assert record1['record']['level']['name'] == "INFO"
    assert "time" in record1['record']
    assert "text" in record1 # Loguru adds 'text' field with the full formatted log string
    
    # Check second record (structured dict message)
    record2 = next(r for r in records if isinstance(r['record']['message'], dict) and r['record']['message']['message'] == "File JSON test: Debug message with data.")
    assert record2 is not None
    assert record2['record']['level']['name'] == "DEBUG"
    assert record2['record']['message']['structured'] is True
    assert "time" in record2['record']

def test_file_logging_all_levels(temp_log_file):
    """Test that messages of all levels are logged to the file (since file log level is DEBUG)."""
    logger.debug("File: Debug Level Test")
    logger.info("File: Info Level Test")
    logger.warning("File: Warning Level Test")
    logger.error("File: Error Level Test")

    records = parse_log_file(temp_log_file)
    
    messages = [r['record']['message'] for r in records]
    levels = [r['record']['level']['name'] for r in records]

    assert "File: Debug Level Test" in messages
    assert "DEBUG" in levels
    assert "File: Info Level Test" in messages
    assert "INFO" in levels
    assert "File: Warning Level Test" in messages
    assert "WARNING" in levels
    assert "File: Error Level Test" in messages
    assert "ERROR" in levels
    
    # Ensure order if necessary, or just presence
    assert len(records) >= 4

def test_file_logging_rotation_and_retention_manual_check_placeholder(temp_log_file):
    """
    Placeholder for testing rotation and retention.
    These are harder to test automatically in a short unit test.
    Manual verification or longer-running integration tests would be needed.
    For this test, we just acknowledge it by its presence.
    """
    logger.info("This log is for a test that would manually verify rotation/retention.")
    assert os.path.exists(temp_log_file) # Basic check that logging is happening

# --- Environment Variable Test (already covered by console tests but can be explicit) ---

def test_game_debug_env_ vaikutus_setup(caplog, game_debug_env):
    """Explicitly test GAME_DEBUG effect during setup_logging."""
    game_debug_env("True")
    logger.remove()
    setup_logging() # Loguru's setup_logging prints an INFO message about levels
    
    init_log_msg = "Loguru logging initialized. Console level: DEBUG."
    found_init_msg = False
    for record in caplog.records:
        if init_log_msg in record.message and record.levelname == "INFO":
            found_init_msg = True
            break
    assert found_init_msg, f"Expected setup log message not found or console level not DEBUG."

    caplog.clear()
    game_debug_env(None)
    logger.remove()
    setup_logging()
    init_log_msg_info = "Loguru logging initialized. Console level: INFO."
    found_init_msg_info = False
    for record in caplog.records:
        if init_log_msg_info in record.message and record.levelname == "INFO":
            found_init_msg_info = True
            break
    assert found_init_msg_info, f"Expected setup log message not found or console level not INFO."

# Ensure that the main logs directory is not polluted by tests
def test_main_log_directory_not_created_by_tests(tmp_path):
    # This test assumes that if file logging tests run, they use temp_log_file fixture
    # which redirects to tmp_path. We check if "logs/game.log" is NOT created.
    # This is a bit of a meta-test.
    
    # Run a simple console log to ensure logger is active but not necessarily file logging to default path
    logger.remove()
    setup_logging() # This will setup based on env vars, potentially to default file if not careful
    logger.info("A console log message during directory check test.")

    main_log_dir = os.path.join(os.getcwd(), "logs") # Default log dir
    main_log_file = os.path.join(main_log_dir, "game.log")

    # Crucial: If a test *before* this one failed to clean up or used default paths,
    # this test might fail. It's best effort.
    # The `temp_log_file` fixture is designed to prevent this for file-specific tests.
    
    # Check if the main log file was created in the project's "logs" directory
    # This test is more about ensuring test isolation provided by temp_log_file fixture.
    if "PYTEST_CURRENT_TEST" in os.environ: # Running within pytest
         assert not os.path.exists(main_log_file), \
             f"Main log file '{main_log_file}' should not be created during isolated tests. " \
             "Ensure file logging tests use the 'temp_log_file' fixture."
    else:
        # If not running in pytest, this check is less meaningful as setup_logging might run normally.
        pass

# Note: The `caplog` fixture in conftest.py might need adjustment if it doesn't
# correctly capture formatted Loguru messages in `caplog.text` or rich details in `caplog.records`.
# The tests above try to be robust by checking both `caplog.text` and `caplog.records`.
# The file logging tests are more direct as they parse the file content.
# Cleanup of the `logs` directory created by Loguru when `setup_logging` is called without
# the `temp_log_file` fixture (e.g. in console tests) is not explicitly handled here,
# assuming that for local dev it's acceptable, or CI handles workspace cleanup.
# The `test_main_log_directory_not_created_by_tests` is a safeguard.
# The `temp_log_file` fixture *does* handle its own temp directory cleanup via `tmp_path`.
