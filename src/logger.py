import os
import sys
from loguru import logger

# Remove default handler
logger.remove()

# Function to setup logging based on environment variable
def setup_logging():
    """
    Sets up the Loguru logging configuration.
    - Console logger: level DEBUG if GAME_DEBUG is 'True' or '1', else INFO.
      Format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    - File logger ("logs/game.log"): level DEBUG, JSON format, daily rotation, 7-day retention, zip compression.
    """
    game_debug_env = os.environ.get('GAME_DEBUG', '').lower()
    console_log_level = "INFO"
    if game_debug_env in ['true', '1']:
        console_log_level = "DEBUG"

    # Add console sink
    logger.add(
        sys.stderr,
        level=console_log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        colorize=True # Optional: make console logs colorful
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

    # Add file sink
    logger.add(
        os.path.join(logs_dir, "game.log"), # Use os.path.join for cross-platform compatibility
        level="DEBUG",
        format="{message}", # Default format is good for JSON when serialize=True
        serialize=True,
        rotation="1 day",  # New file every day
        retention="7 days",
        compression="zip"
    )

    logger.info(f"Loguru logging initialized. Console level: {console_log_level}. File logging to 'logs/game.log'")

# The Loguru logger instance is directly usable.
# For compatibility with existing code that might do `from src.logger import logger as game_logger`
# or `from src.logger import logger`, this is fine.
# If a specific name `game_logger` was imported, we can alias it:
# game_logger = logger # This line is optional if imports are `from src.logger import logger`

# The set_log_level function is no longer needed as Loguru's levels are set per-handler.
# If dynamic level changing for the console is required later, specific handler IDs would be needed.

if __name__ == '__main__':
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
