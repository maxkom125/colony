import os
import sys
import time
from collections import defaultdict
from loguru import logger

# Remove default handler
logger.remove()


# Simple duplicate message filter using Loguru's built-in filter functionality
class MessageFilter:
    def __init__(self, max_interval=5.0):
        self.max_interval = max_interval
        self.last_seen = defaultdict(float)
        self.counts = defaultdict(int)

    def __call__(self, record):
        message = record["message"]
        current_time = time.time()

        # Always allow non-debug messages
        if record["level"].no > 10:  # Above DEBUG level
            return True

        # For debug messages, check if we've seen this recently
        if message in self.last_seen:
            time_diff = current_time - self.last_seen[message]
            if time_diff < self.max_interval:
                self.counts[message] += 1
                return False  # Filter out this duplicate
            else:
                # Show the message with count if it was repeated
                if self.counts[message] > 0:
                    record["message"] = f"{message} (repeated {self.counts[message] + 1} times)"
                    self.counts[message] = 0

        self.last_seen[message] = current_time
        return True


# Create filter instance
message_filter = MessageFilter(max_interval=3.0)


# Function to setup logging based on environment variable
def setup_logging():
    """
    Sets up the Loguru logging configuration.
    - Console logger: level DEBUG if GAME_DEBUG is 'True' or '1', else INFO.
      Format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    - File logger ("logs/game.log"): level DEBUG, JSON format, daily rotation, 7-day retention, zip compression.
    """
    game_debug_env = os.environ.get("GAME_DEBUG", "").lower()
    console_log_level = "INFO"
    if game_debug_env in ["true", "1"]:
        console_log_level = "DEBUG"

    # Add console sink with filter for debug messages
    logger.add(
        sys.stderr,
        level=console_log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        colorize=True,
        filter=message_filter if console_log_level == "DEBUG" else None,
    )

    # Ensure logs directory exists
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
        except OSError as e:
            logger.error(f"Could not create logs directory: {logs_dir}. Error: {e}")
            # Fallback or raise error if directory creation is critical
            # For now, loguru might still work if it can create it, or fail gracefully for the file logger.

    # Add file sink (no filter - keep all logs in file)
    logger.add(
        os.path.join(logs_dir, "game.log"),  # Use os.path.join for cross-platform compatibility
        level="DEBUG",
        format="{message}",  # Default format is good for JSON when serialize=True
        serialize=True,
        rotation="1 day",  # New file every day
        retention="7 days",
        compression="zip",
    )

    logger.info(
        f"Loguru logging initialized. Console level: {console_log_level}. File logging to 'logs/game.log'"
    )


# The Loguru logger instance is directly usable.
# For compatibility with existing code that might do `from src.logger import logger as game_logger`
# or `from src.logger import logger`, this is fine.
# If a specific name `game_logger` was imported, we can alias it:
# game_logger = logger # This line is optional if imports are `from src.logger import logger`

# The set_log_level function is no longer needed as Loguru's levels are set per-handler.
# If dynamic level changing for the console is required later, specific handler IDs would be needed.

if __name__ == "__main__":
    # Call setup_logging() to apply environment variable settings first
    setup_logging()

    logger.debug("This is a Loguru debug message.")
    logger.info("This is a Loguru info message.")
    logger.warning("This is a Loguru warning message.")
    logger.error("This is a Loguru error message.")
    logger.critical("This is a Loguru critical message.")

    logger.info("Testing with some context specific data.", data={"player_id": 123, "score": 1000})
    try:
        x = 1 / 0
    except ZeroDivisionError:
        logger.exception("Something went wrong (Loguru exception logging):")

    logger.info(f"GAME_DEBUG is: {os.environ.get('GAME_DEBUG')}")

    # Test the filter
    for i in range(10):
        logger.debug("This is a repeated debug message")
        time.sleep(0.1)
