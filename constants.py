# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Frame rate
FPS = 60

# Game Title
GAME_TITLE = "Space Colony Sim"

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)

# Camera settings
MIN_ZOOM = 0.5  # Example minimum zoom
MAX_ZOOM = 3.0  # Example maximum zoom

# Planet Constants
PLANET_RADIUS = 150
PLANET_COLOR = BLUE # Use the BLUE constant defined above

# Asteroid Constants
ASTEROID_COUNT = 50
ASTEROID_MIN_RADIUS = 10
ASTEROID_MAX_RADIUS = 40
ASTEROID_COLOR = GRAY
ASTEROID_SPAWN_RADIUS_MIN = 300 # Min distance from center (0,0)
ASTEROID_SPAWN_RADIUS_MAX = 1500 # Max distance from center (0,0)

# Background Star Constants
STAR_COUNT = 200
STAR_RADIUS = 1
STAR_COLOR = WHITE
STAR_PARALLAX_FACTOR = 0.1 # How much stars move relative to camera (0=none, 1=same as foreground)

# Resource Constants
RESOURCE_TYPES = ["Tritanium", "Credits", "Plasma"]
# Remove old min/max per resource
# ASTEROID_MIN_TRITANIUM = 50
# ASTEROID_MAX_TRITANIUM = 150
# ASTEROID_MIN_CREDITS = 30
# ASTEROID_MAX_CREDITS = 180
# ASTEROID_MIN_PLASMA = 40
# ASTEROID_MAX_PLASMA = 160

# Probabilities for single resource type per asteroid
RESOURCE_WEIGHTS = [0.45, 0.15, 0.40] # Tritanium, Credits, Plasma

# Range for the single resource amount
ASTEROID_MIN_RESOURCE_AMOUNT = 100
ASTEROID_MAX_RESOURCE_AMOUNT = 300

# Spaceship Constants
SHIP_SIZE = 20
SHIP_COLOR = (255, 100, 0) # Orange - Scanner Ship

MINING_SHIP_SIZE = 25 # Slightly larger
MINING_SHIP_COLOR = (200, 200, 200) # Light Gray

SHIP_SPEED = 100 # Pixels per second (for both types for now)

# Visited Asteroid Color
VISITED_ASTEROID_COLOR = (100, 100, 100) # Darker gray

# Resource Colors
TRITANIUM_COLOR = (0, 150, 255) # Bluish
CREDITS_COLOR = (255, 215, 0)  # Goldish
PLASMA_COLOR = (255, 0, 150)    # Pinkish
DEPLETED_ASTEROID_COLOR = (255, 0, 0) # Red

# --- Action Time Constants ---
BASE_ACTION_TIME_UNIT = 0.05 # Base time unit in seconds (e.g., for scan/mine per radius)

# Scan Time (derived from base)
SCAN_TIME_PER_RADIUS_UNIT = BASE_ACTION_TIME_UNIT # seconds per radius unit

# Mining and Dumping Times
MINING_TIME_MULTIPLIER = 4.0 # Multiplier for mining time (based on radius * base unit)
DUMPING_DURATION = BASE_ACTION_TIME_UNIT * 100 # Fixed time in seconds to dump resources

# Cargo Capacity
MINING_SHIP_CARGO_CAPACITY = 250 # Max total resource units mining ship can hold

# Avoidance
AVOIDANCE_LOOKAHEAD_TIME = 0.2 # seconds - How far ahead to check for collisions

# UI / Font
UI_FONT_SIZE = 16
# UI_FONT = pygame.font.SysFont(None, UI_FONT_SIZE) # Use None for default font
