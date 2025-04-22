import pygame
from . import constants

# Import necessary types for hinting
from .entities.planet import Planet
from .entities.ships.base_ship import Spaceship
from .entities.ships.scanner_ship import ScannerShip
from .entities.ships.mining_ship import MiningShip
from .enums import ShipState
from .camera.camera import Camera # Import Camera for type hinting

def get_construction_button_rects(font):
    """Calculates and returns the Rects for the construction buttons, centered horizontally."""
    button_y = constants.SCREEN_HEIGHT - 40 # Position near bottom
    padding = 20 # Padding between buttons
    scanner_text = "[Build Scanner (50T, 100C)]"
    miner_text = "[Build Miner (100T, 50C)]"

    # Use the actual font passed in
    scanner_surf = font.render(scanner_text, True, (0,0,0)) # Color doesn't matter for size
    miner_surf = font.render(miner_text, True, (0,0,0))

    total_width = scanner_surf.get_width() + padding + miner_surf.get_width()
    start_x = (constants.SCREEN_WIDTH - total_width) // 2

    scanner_rect = scanner_surf.get_rect(bottomleft=(start_x, button_y))
    miner_rect = miner_surf.get_rect(bottomleft=(scanner_rect.right + padding, button_y))

    return scanner_rect, miner_rect

def draw_ship_statuses(screen, ships: list[Spaceship], font):
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
            target_id = f"Target ID: {ship.target.id if hasattr(ship.target, 'id') else 'Planet'}"
            state_text += f" -> {target_id}"
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

def draw_mining_priorities(screen, priorities: dict, font):
    """Draws the current mining priorities.
       TODO: Replace with sliders or interactive elements later.
    """
    start_x = constants.SCREEN_WIDTH - 150 # Position near top-right, below zoom
    start_y = 40
    line_height = 20

    title_surf = font.render("Mining Priorities:", True, constants.UI_TEXT_COLOR)
    title_rect = title_surf.get_rect(topleft=(start_x, start_y))
    screen.blit(title_surf, title_rect)
    y_offset = title_rect.bottom + 5

    for resource_type, priority in priorities.items():
        color = constants.WHITE # Default color
        if resource_type == "Tritanium": color = constants.TRITANIUM_COLOR
        elif resource_type == "Credits": color = constants.CREDITS_COLOR
        elif resource_type == "Plasma": color = constants.PLASMA_COLOR

        text = f"{resource_type}: {priority:.1f}"
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(topleft=(start_x, y_offset))
        screen.blit(text_surf, text_rect)
        y_offset += line_height

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