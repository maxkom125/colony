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
BACKGROUND_COLOR = (0, 0, 20)  # ADDED BACK

# Camera settings
MIN_ZOOM = 0.5  # Example minimum zoom
MAX_ZOOM = 3.0  # Example maximum zoom

# Planet Constants
PLANET_RADIUS = 150
PLANET_COLOR = BLUE  # Use the BLUE constant defined above

# Asteroid Constants
ASTEROID_COUNT = 50
ASTEROID_MIN_RADIUS = 10
ASTEROID_MAX_RADIUS = 40
ASTEROID_COLOR = GRAY
ASTEROID_SPAWN_RADIUS_MIN = 300  # Min distance from center (0,0)
ASTEROID_SPAWN_RADIUS_MAX = 1500  # Max distance from center (0,0)

# Background Star Constants
STAR_COUNT = 200
STAR_MIN_RADIUS = 1  # Min radius for stars
STAR_MAX_RADIUS = 3  # Max radius for stars
STAR_COLOR = WHITE
STAR_PARALLAX_FACTOR = 0.1  # How much stars move relative to camera (0=none, 1=same as foreground)

# Range for the single resource amount
ASTEROID_MIN_RESOURCE_AMOUNT = 100
ASTEROID_MAX_RESOURCE_AMOUNT = 300

# Spaceship Constants
SHIP_SIZE = 20  # Default size (used for Scanner)
SHIP_COLOR = (0, 200, 200)  # Cyan (for Scanner)
MINING_SHIP_SIZE = 25
MINING_SHIP_COLOR = (200, 200, 0)  # Yellow (for Miner)
SHIP_SPEED = 100.0  # Default speed
SCANNER_SPEED = 120.0  # Scanner specific speed - ADDED BACK
MINER_SPEED = 80.0  # Miner specific speed

# Visited Asteroid Color
VISITED_ASTEROID_COLOR = (100, 100, 100)  # Darker gray

# Resource Colors
TRITANIUM_COLOR = (0, 150, 255)  # Bluish
CREDITS_COLOR = (255, 215, 0)  # Goldish
PLASMA_COLOR = (255, 0, 150)  # Pinkish
DEPLETED_ASTEROID_COLOR = (255, 0, 0)  # Red

# --- Action Time Constants ---
BASE_ACTION_TIME_UNIT = 1.0  # Base seconds for actions like mining (before multipliers)

# Scan Time
# SCAN_TIME_PER_RADIUS_UNIT = 0.05 # Old way: Seconds per world unit of asteroid radius
SCAN_DURATION = 3.0  # Fixed time in seconds to scan an asteroid
SCANNER_SCAN_RANGE = 40.0

# --- Scanning Logic ---
SCANNER_SCAN_RATE = 20.0  # "Scan points" per second
SCAN_POINTS_PER_RADIUS = 5.0  # Scan points required per unit of asteroid radius
MINIMUM_SCAN_POINTS = 50  # Minimum scan points
# Mining and Dumping Times
# MINING_TIME_MULTIPLIER = 0.1 # Old way: Multiplied by radius and base time
MINING_DURATION = 5.0  # Fixed time in seconds to mine an asteroid patch
MINING_RATE = 10.0  # Resources mined per second
DUMPING_DURATION = 2.0  # Seconds to dump resources at the planet

# Cargo Capacity
MINING_SHIP_CARGO_CAPACITY = 50  # Max total resource units mining ship can hold

# Avoidance
AVOIDANCE_LOOKAHEAD_TIME = 0.5  # Seconds to look ahead for obstacles

# UI / Font
UI_FONT_SIZE = 16
UI_TEXT_COLOR = WHITE

# --- Slider Colors ---
SLIDER_BG_COLOR = (50, 50, 50)
SLIDER_KNOB_COLOR = (180, 180, 180)

# --- HUD Assignment UI Constants ---
ASSIGNMENT_AREA_X = None  # Calculated in calculate_dependent_constants()
ASSIGNMENT_AREA_Y = 80
ASSIGNMENT_LINE_HEIGHT = 25
ASSIGNMENT_BUTTON_WIDTH = 20
ASSIGNMENT_BUTTON_HEIGHT = 20
ASSIGNMENT_BUTTON_PADDING = 5

# --- Gameplay & Physics ---
ARRIVAL_DISTANCE_BUFFER = 5  # World units buffer for arrival checks
EPSILON = 1e-6  # Small value for float comparisons
EPSILON_SQ = EPSILON * EPSILON  # Epsilon squared for distance comparisons
TARGET_LINE_COLOR = (255, 255, 0)  # Yellow for target lines

# --- Bottom Panel UI ---
BOTTOM_PANEL_WIDTH = None  # Calculated in calculate_dependent_constants()
BOTTOM_PANEL_HEIGHT = None  # Calculated in calculate_dependent_constants()
BOTTOM_PANEL_COLOR = (30, 30, 30)  # Dark gray
BOTTOM_PANEL_TAB_WIDTH = 150
BOTTOM_PANEL_TAB_HEIGHT = 25
BOTTOM_PANEL_TAB_COLOR = (50, 50, 50)  # Slightly lighter gray
BOTTOM_PANEL_TAB_SELECTED_COLOR = (70, 70, 70)  # Even lighter gray
BOTTOM_PANEL_BORDER_COLOR = (90, 90, 90)  # Border color
BOTTOM_PANEL_BORDER_WIDTH = 2

# --- Panel Toggle Button ---
PANEL_TOGGLE_BUTTON_WIDTH = 40
PANEL_TOGGLE_BUTTON_HEIGHT = 15
PANEL_TOGGLE_BUTTON_COLOR = (80, 80, 80)  # Similar to selected tab
PANEL_TOGGLE_SYMBOL_COLLAPSE = "^"  # Symbol for collapse
PANEL_TOGGLE_SYMBOL_EXPAND = "v"  # Symbol for expand

# --- Construction Costs ---
SCANNER_COST_TRITANIUM = 50
SCANNER_COST_CREDITS = 100
MINING_SHIP_COST_TRITANIUM = 100
MINING_SHIP_COST_CREDITS = 50

# --- Market Constants ---
CONVERSION_FEE_PERCENT = 0.1
SELL_TRITANIUM_RATE = 0.5
SELL_PLASMA_RATE = 0.5
BUY_TRITANIUM_RATE = 1.0
BUY_PLASMA_RATE = 1.0

# Enums (Import necessary enums)
from .enums import ShipState

# --- Behavioral Constants ---
ARRIVAL_DISTANCE_BUFFER = 5  # How close ships need to be to radius sum to trigger arrival

# --- Game Speed Control ---
GAME_SPEED_MULTIPLIERS = [0.0, 1.0, 2.0, 4.0]  # 0=Pause, 1=Normal, 2=Fast, 4=SuperFast
GAME_SPEED_ICONS = ["||", ">", ">>", ">>>"]  # Text icons for buttons
GAME_SPEED_BUTTON_SIZE = 30
GAME_SPEED_BUTTON_PADDING = 5
GAME_SPEED_AREA_TOP_RIGHT = None  # Calculated in calculate_dependent_constants()

# Set of ship states considered "moving" states for update_movement logic
MOVING_SHIP_STATES = {
    ShipState.MOVING_TO_ASTEROID,
    ShipState.MOVING_TO_SCAN,
    ShipState.MOVING_TO_POSITION,
    ShipState.RETURNING_TO_BASE,
}


# --- Function to recalculate constants dependent on screen size ---
def calculate_dependent_constants():
    """Recalculates constants that depend on SCREEN_WIDTH and SCREEN_HEIGHT.
    This should be called after the display mode is set.
    """
    global ASSIGNMENT_AREA_X, BOTTOM_PANEL_WIDTH, BOTTOM_PANEL_HEIGHT, GAME_SPEED_AREA_TOP_RIGHT

    # Re-calculate based on the potentially updated SCREEN_WIDTH
    ASSIGNMENT_AREA_X = SCREEN_WIDTH - 140
    BOTTOM_PANEL_WIDTH = int(SCREEN_WIDTH * 0.6)
    BOTTOM_PANEL_HEIGHT = int(SCREEN_WIDTH * 0.05)
    GAME_SPEED_AREA_TOP_RIGHT = (SCREEN_WIDTH - 10, 10)  # X depends on SCREEN_WIDTH

    print(f"DEBUG: Recalculated constants based on SCREEN_WIDTH={SCREEN_WIDTH}")
    # ---- End of Screen-Dependent Constants recalculation  ----


calculate_dependent_constants()
