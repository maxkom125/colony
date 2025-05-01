import pygame
from collections import defaultdict  # Import defaultdict
from . import constants
import random  # Needed for random assignment logic later

# Import necessary types for hinting
from .entities.planet import Planet
from .entities.asteroid import Asteroid
from .entities.ships.base_ship import Ship
from .entities.ships.scanner_ship import ScannerShip
from .entities.ships.mining_ship import MiningShip
from .enums import ShipState
from .camera.camera import Camera  # Import Camera for type hinting
from .systems.admirals.miner_admiral import MinerAdmiral  # Import MinerAdmiral
from .fleet import Fleet

# Dictionary to store calculated button rects for interaction
assignment_button_rects = {
    "Tritanium": {"+": None, "-": None},
    "Credits": {"+": None, "-": None},
    "Plasma": {"+": None, "-": None},
    "Random": {"+": None, "-": None},
}


def get_assignment_button_rects():
    """Returns the dictionary containing assignment button Rects."""
    global assignment_button_rects
    return assignment_button_rects


def get_construction_button_rects(font):
    """Calculates and returns the Rects for the construction buttons, centered horizontally."""
    button_y = constants.SCREEN_HEIGHT - 40  # Position near bottom
    padding = 20  # Padding between buttons
    scanner_text = "[Build Scanner (50T, 100C)]"
    miner_text = "[Build Miner (100T, 50C)]"

    # Use the actual font passed in
    scanner_surf = font.render(scanner_text, True, (0, 0, 0))  # Color doesn't matter for size
    miner_surf = font.render(miner_text, True, (0, 0, 0))

    total_width = scanner_surf.get_width() + padding + miner_surf.get_width()
    start_x = (constants.SCREEN_WIDTH - total_width) // 2

    scanner_rect = scanner_surf.get_rect(bottomleft=(start_x, button_y))
    miner_rect = miner_surf.get_rect(bottomleft=(scanner_rect.right + padding, button_y))

    return scanner_rect, miner_rect


def draw_ship_statuses(screen, ships: list[Ship], font):
    """Draws ship status text in the bottom-left corner."""
    ship_ui_start_x = 10
    line_height = 20  # Approximate line height
    padding_bottom = 10
    total_ui_height = len(ships) * line_height
    ship_ui_start_y = constants.SCREEN_HEIGHT - total_ui_height - padding_bottom

    y_offset = ship_ui_start_y
    for i, ship in enumerate(ships):
        # Display state name from enum
        state_text = f"Ship {i} ({type(ship).__name__}): {ship.state.name}"
        if ship.target:
            if isinstance(ship.target, Asteroid):
                target = f"Target: Asteroid {ship.target.id}"
            elif isinstance(ship.target, Planet):
                target = f"Target: Planet {ship.target.id}"
            else:
                try:
                    target = f"Target: {type(ship.target)} {ship.target.id}"
                except:
                    target = f"Target: Something wrong with target"
            state_text += f" -> {target}"
        # Append timer/cargo info
        if isinstance(ship, ScannerShip) and ship.state == ShipState.SCANNING:
            state_text += f" (Scan: {ship.scan_timer:.1f}s)"
        elif isinstance(ship, MiningShip):
            if ship.state == ShipState.MINING:
                state_text += f" (Mine: {ship.mining_timer:.1f}s)"
            elif ship.state == ShipState.DUMPING:
                state_text += f" (Dump: {ship.dumping_timer:.1f}s)"
            state_text += f" Cargo: {int(ship.get_cargo_total())}"

        text_surface = font.render(state_text, True, constants.UI_TEXT_COLOR)
        screen.blit(text_surface, (ship_ui_start_x, y_offset))
        y_offset += line_height


def draw_planet_storage(screen, planet: Planet, font):
    """Draws planet resource storage text in the top-left corner."""
    storage_y_offset = 10
    storage_x_offset = 10
    for resource_type, amount in planet.storage.items():
        color = constants.WHITE
        if resource_type == "Tritanium":
            color = constants.TRITANIUM_COLOR
        elif resource_type == "Credits":
            color = constants.CREDITS_COLOR
        elif resource_type == "Plasma":
            color = constants.PLASMA_COLOR
        text = f"{resource_type}: {int(amount)}"
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(topleft=(storage_x_offset, storage_y_offset))
        screen.blit(text_surface, text_rect)
        storage_y_offset += 20


def draw_zoom_level(screen, camera: Camera, font):
    """Draws the current zoom level in the top-right corner."""
    # Use camera.zoom instead of passed zoom_level
    zoom_text = f"Zoom: {camera.zoom:.2f}x"
    zoom_surface = font.render(zoom_text, True, constants.UI_TEXT_COLOR)
    # Position top-right using constants.SCREEN_WIDTH directly
    text_rect = zoom_surface.get_rect(topright=(constants.SCREEN_WIDTH - 10, 10))
    screen.blit(zoom_surface, text_rect)


def draw_miner_assignments(screen, miner_admiral: MinerAdmiral, font):
    """Draws the miner assignment UI based on MinerAdmiral state."""
    global assignment_button_rects

    # --- Get Current State from Admiral ---
    total_mining_ships = miner_admiral.get_ship_count()  # Use correct base method
    idle_count = miner_admiral.get_idle_ship_count()  # Use new helper
    categories = miner_admiral.get_all_categories()  # Use new helper

    # --- Draw Title ---
    title_surf = font.render("Miner Assignments:", True, constants.UI_TEXT_COLOR)
    title_rect = title_surf.get_rect(
        topleft=(constants.ASSIGNMENT_AREA_X, constants.ASSIGNMENT_AREA_Y)
    )
    screen.blit(title_surf, title_rect)
    y_offset = title_rect.bottom + 10

    # --- Draw Each Category Assignment ---
    # Ensure consistent order if needed, e.g., sort categories
    # categories.sort() # Optional: sort if needed

    for category in categories:
        # Get count directly for the category list
        current_count = miner_admiral.get_ship_count_for_category(category)

        # Determine color based on category
        color = constants.WHITE
        if category == "Tritanium":
            color = constants.TRITANIUM_COLOR
        elif category == "Credits":
            color = constants.CREDITS_COLOR
        elif category == "Plasma":
            color = constants.PLASMA_COLOR
        # Add color for Random if desired, e.g., GREY
        elif category == "Random":
            color = constants.GRAY

        # Display just the current count for the category
        text = f"{category}: {current_count}"
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(topleft=(constants.ASSIGNMENT_AREA_X, y_offset))
        screen.blit(text_surf, text_rect)

        # Draw buttons (+/-) - Logic remains the same
        button_y = text_rect.centery - constants.ASSIGNMENT_BUTTON_HEIGHT // 2
        minus_rect = pygame.Rect(
            text_rect.right + constants.ASSIGNMENT_BUTTON_PADDING,
            button_y,
            constants.ASSIGNMENT_BUTTON_WIDTH,
            constants.ASSIGNMENT_BUTTON_HEIGHT,
        )
        pygame.draw.rect(screen, constants.SLIDER_BG_COLOR, minus_rect, border_radius=3)
        minus_surf = font.render("-", True, constants.WHITE)
        minus_surf_rect = minus_surf.get_rect(center=minus_rect.center)
        screen.blit(minus_surf, minus_surf_rect)
        assignment_button_rects[category]["-"] = minus_rect  # Store rect

        plus_rect = pygame.Rect(
            minus_rect.right + constants.ASSIGNMENT_BUTTON_PADDING,
            button_y,
            constants.ASSIGNMENT_BUTTON_WIDTH,
            constants.ASSIGNMENT_BUTTON_HEIGHT,
        )
        pygame.draw.rect(screen, constants.SLIDER_BG_COLOR, plus_rect, border_radius=3)
        plus_surf = font.render("+", True, constants.WHITE)
        plus_surf_rect = plus_surf.get_rect(center=plus_rect.center)
        screen.blit(plus_surf, plus_surf_rect)
        assignment_button_rects[category]["+"] = plus_rect  # Store rect

        y_offset += constants.ASSIGNMENT_LINE_HEIGHT

    # --- Draw Totals ---
    y_offset += 5  # Add a little space
    idle_text = f"Idle: {idle_count}"
    idle_surf = font.render(idle_text, True, constants.UI_TEXT_COLOR)
    idle_rect = idle_surf.get_rect(topleft=(constants.ASSIGNMENT_AREA_X, y_offset))
    screen.blit(idle_surf, idle_rect)
    y_offset += constants.ASSIGNMENT_LINE_HEIGHT

    # Display total ships managed by the admiral
    total_text = f"Total Miners: {total_mining_ships}"
    total_surf = font.render(total_text, True, constants.UI_TEXT_COLOR)
    total_rect = total_surf.get_rect(topleft=(constants.ASSIGNMENT_AREA_X, y_offset))
    screen.blit(total_surf, total_rect)


def draw_construction_buttons(screen, font):
    """Draws placeholder text/buttons for building ships (rects calculated elsewhere)."""
    # Recalculate rects using the font for accurate positioning
    scanner_rect, miner_rect = get_construction_button_rects(font)
    scanner_text = "[Build Scanner (50T, 100C)]"
    miner_text = "[Build Miner (100T, 50C)]"

    scanner_surf = font.render(scanner_text, True, constants.UI_TEXT_COLOR)
    miner_surf = font.render(miner_text, True, constants.UI_TEXT_COLOR)

    screen.blit(scanner_surf, scanner_rect)
    screen.blit(miner_surf, miner_rect)

    # No longer returns rects
    # return scanner_rect, miner_rect


# --- Main HUD Drawing Function ---
def draw_hud(screen, font, fleet: Fleet, planet: Planet, camera: Camera, all_ships: list[Ship]):
    """Draws all HUD elements by calling specific drawing functions."""
    draw_planet_storage(screen, planet, font)
    # Combine ships from admiral and potentially other sources (like scanners)
    # For now, just use all_ships passed from main
    draw_ship_statuses(screen, all_ships, font)
    draw_zoom_level(screen, camera, font)
    draw_construction_buttons(screen, font)
    # Use the newer assignment drawing function that takes the admiral
    draw_miner_assignments(screen, fleet.miner_admiral, font)
