import pygame
import sys

# Adjust imports for new structure
from src import constants
from src.enums import ResourceType
import random  # Import random module
import math  # Import math for trigonometric functions
from pygame.math import Vector2  # Import Vector2

# Import specific entity classes
from src.entities.planet import Planet
from src.entities.asteroid import Asteroid
from src.entities.ships.scanner_ship import ScannerShip
from src.entities.ships.mining_ship import MiningShip

from src.systems import construction_system  # Import the new construction system
from src.rendering import renderer  # Import the new renderer module
from src.camera.camera import Camera  # Import the new Camera class

# Import Fleet
from src.fleet import Fleet

# Import HUDManager
from src.ui.hud_manager import HUDManager

# Import SpaceMarket
from src.systems.space_market import SpaceMarket


def main():
    # global camera_offset, zoom_level  # REMOVED Globals

    # Initialize Pygame
    pygame.init()
    # Initialize Font
    try:
        ui_font = pygame.font.SysFont(None, constants.UI_FONT_SIZE)
    except Exception as e:
        print(f"Error initializing font: {e}")
        ui_font = pygame.font.Font(None, 30)  # Fallback basic font

    # Screen setup
    try:
        # screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Try fullscreen
        # Update constants with actual screen size if fullscreen is used
        constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = screen.get_size()
        print(f"Screen size set to: {constants.SCREEN_WIDTH}x{constants.SCREEN_HEIGHT}")
        # Recalculate constants dependent on the new screen size
        constants.calculate_dependent_constants()
    except pygame.error as e:
        print(f"Error setting display mode: {e}. Falling back to windowed.")
        constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT = 1280, 720  # Default fallback
        screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        # Also recalculate if falling back to windowed mode
        constants.calculate_dependent_constants()

    pygame.display.set_caption(constants.GAME_TITLE)

    # Clock for controlling frame rate
    clock = pygame.time.Clock()

    # --- Create Systems & Managers ---
    fleet = Fleet()
    camera = Camera()
    space_market = SpaceMarket() # Instantiate SpaceMarket
    # Pass space_market to HUDManager if needed later (or interact directly)
    hud_manager = HUDManager(ui_font)

    # --- Create Game World Objects ---
    central_planet = Planet(position=Vector2(0, 0))  # Uses constants internally
    asteroids = []
    max_gen_attempts = (
        constants.ASTEROID_COUNT * 10
    )  # Prevent infinite loop if space is too crowded
    attempts = 0
    while len(asteroids) < constants.ASTEROID_COUNT and attempts < max_gen_attempts:
        attempts += 1
        angle = random.uniform(0, 2 * math.pi)
        spawn_dist = random.uniform(
            constants.ASTEROID_SPAWN_RADIUS_MIN, constants.ASTEROID_SPAWN_RADIUS_MAX
        )
        cand_pos = Vector2(spawn_dist, 0).rotate_rad(angle)
        cand_radius = random.uniform(constants.ASTEROID_MIN_RADIUS, constants.ASTEROID_MAX_RADIUS)
        overlap = False
        for existing_asteroid in asteroids:
            if (
                cand_pos.distance_squared_to(existing_asteroid.position)
                < (cand_radius + existing_asteroid.radius + 5) ** 2
            ):
                overlap = True
                break
        if cand_pos.length_squared() < (cand_radius + constants.PLANET_RADIUS + 20) ** 2:
            overlap = True
        if not overlap:
            asteroids.append(
                Asteroid(
                    position=cand_pos,
                    radius=cand_radius,
                    color=constants.ASTEROID_COLOR,
                )
            )
    if len(asteroids) < constants.ASTEROID_COUNT:
        print(f"WARNING: Generated {len(asteroids)} asteroids...")

    # Create background stars (Generate positions in world coordinates)
    stars = []
    star_gen_radius = constants.ASTEROID_SPAWN_RADIUS_MAX * 1.5  # Generate stars a bit further out
    for _ in range(constants.STAR_COUNT):
        star_pos = Vector2(
            random.uniform(-star_gen_radius, star_gen_radius),
            random.uniform(-star_gen_radius, star_gen_radius),
        )
        star_radius = random.uniform(constants.STAR_MIN_RADIUS, constants.STAR_MAX_RADIUS)
        stars.append((star_pos, star_radius))  # Store world Vector2 and radius

    # --- Create initial ships AND add to Fleet and Admirals ---
    scanner1 = ScannerShip(
        position=Vector2(0, -constants.PLANET_RADIUS - 50), home_planet=central_planet
    )
    miner1 = MiningShip(
        position=Vector2(50, -constants.PLANET_RADIUS - 50), home_planet=central_planet
    )

    fleet.add_ship(scanner1)
    fleet.add_ship(miner1)
    # Initial miner assignments are handled by admiral logic (defaults to Random)

    # Game loop flag
    running = True
    panning = False  # Initialize panning state
    pan_start_pos = None  # Also initialize pan_start_pos

    # --- Game Speed State ---
    current_speed_index = 1 # Index into GAME_SPEED_MULTIPLIERS/ICONS (1 = 1.0x speed)

    # --- Main Game Loop ---
    while running:
        dt_raw = clock.tick(constants.FPS) / 1000.0
        # Apply game speed multiplier
        game_speed_multiplier = constants.GAME_SPEED_MULTIPLIERS[current_speed_index]
        dt = dt_raw * game_speed_multiplier

        # Get current ships from fleet for rendering/global checks
        all_ships = fleet.get_all_ships()

        # --- Get UI element rects for interaction from HUDManager ---
        current_assignment_buttons = hud_manager.get_assignment_button_rects()
        current_bottom_tab_rects = hud_manager.get_bottom_tab_rects()
        current_toggle_button_rect = hud_manager.get_panel_toggle_button_rect()
        current_construction_buttons = hud_manager.get_construction_button_rects()
        # Get NEW market UI rects
        current_market_slider_handles = hud_manager.get_market_slider_handle_rects()
        current_market_minus_buttons = hud_manager.get_market_slider_minus_buttons()
        current_market_plus_buttons = hud_manager.get_market_slider_plus_buttons()
        current_market_confirm_buttons = hud_manager.get_market_confirm_button_rects()
        current_speed_buttons = hud_manager.get_speed_control_button_rects()
        scanner_button_rect = current_construction_buttons["scanner"]
        miner_button_rect = current_construction_buttons["miner"]

        # --- Event Handling ---
        mouse_pos_vec = Vector2(pygame.mouse.get_pos())  # Get mouse pos as Vector2
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False  # Allow exiting fullscreen with ESC
            elif event.type == pygame.MOUSEWHEEL:
                # Delegate zoom handling to camera object
                zoom_direction = event.y
                camera.handle_zoom(zoom_direction, mouse_pos_vec)
                # Remove old zoom logic

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    clicked_on_ui = False

                    # --- Check for Panel Toggle Button Click ---
                    if current_toggle_button_rect and current_toggle_button_rect.collidepoint(
                        event.pos
                    ):
                        hud_manager.toggle_panel_collapsed()
                        clicked_on_ui = True

                    # --- Check for Bottom Tab Clicks --- (Always check)
                    if not clicked_on_ui and current_bottom_tab_rects:
                        for i, rect in current_bottom_tab_rects.items():
                            if rect.collidepoint(event.pos):
                                hud_manager.select_bottom_tab(i)
                                # Reset sliders when switching to market tab
                                if i == 1: # Index of Market Tab
                                    hud_manager.reset_market_sliders()
                                clicked_on_ui = True
                                break

                    # --- Check UI Buttons based on current tab and panel state ---
                    if not clicked_on_ui and not hud_manager.is_panel_collapsed:
                        if hud_manager.selected_bottom_tab_index == 0: # Construction Tab
                            # Check Construction Buttons
                            if scanner_button_rect and scanner_button_rect.collidepoint(event.pos):
                                new_ship = construction_system.attempt_construction(
                                    central_planet, "scanner"
                                )
                                if new_ship:
                                    fleet.add_ship(new_ship)
                                    clicked_on_ui = True
                            elif miner_button_rect and miner_button_rect.collidepoint(event.pos):
                                new_ship = construction_system.attempt_construction(
                                    central_planet, "miner"
                                )
                                if new_ship:
                                    fleet.add_ship(new_ship)
                                    clicked_on_ui = True
                        elif hud_manager.selected_bottom_tab_index == 1: # Space Market Tab
                            # --- NEW: Handle Market Slider Interaction ---
                            # Check slider handles first (start drag)
                            for resource_type, handle_rect in current_market_slider_handles.items():
                                if handle_rect and handle_rect.collidepoint(event.pos):
                                    if hud_manager.start_slider_drag(resource_type, event.pos):
                                        clicked_on_ui = True
                                        break
                            # Check +/- buttons if not dragging
                            if not clicked_on_ui and not hud_manager.dragging_slider:
                                delta = 0.1 # Amount to adjust slider by per click
                                for resource_type, minus_rect in current_market_minus_buttons.items():
                                    if minus_rect and minus_rect.collidepoint(event.pos):
                                        hud_manager.adjust_slider(resource_type, -delta, central_planet, space_market)
                                        clicked_on_ui = True
                                        break
                                if not clicked_on_ui:
                                    for resource_type, plus_rect in current_market_plus_buttons.items():
                                        if plus_rect and plus_rect.collidepoint(event.pos):
                                            hud_manager.adjust_slider(resource_type, delta, central_planet, space_market)
                                            clicked_on_ui = True
                                            break
                            # Check Confirm buttons if not dragging
                            if not clicked_on_ui and not hud_manager.dragging_slider:
                                for resource_type, confirm_rect in current_market_confirm_buttons.items():
                                    if confirm_rect and confirm_rect.collidepoint(event.pos):
                                        action, amount, cost_gain = hud_manager.get_current_trade_details(resource_type)
                                        if amount > 0: # Only process if there's an amount
                                            if action == "Buy":
                                                success = space_market.buy_resource(central_planet.storage, resource_type, amount)
                                            elif action == "Sell":
                                                success = space_market.sell_resource(central_planet.storage, resource_type, amount)
                                            else: # Should not happen
                                                success = False

                                            if success:
                                                print(f"Market: {action} {amount} {resource_type.value} successful.")
                                                # Optionally reset slider after confirm?
                                                # hud_manager.market_slider_values[resource_type] = 0.0
                                                # hud_manager._update_trade_details(resource_type, central_planet, space_market)
                                            else:
                                                 print(f"Market: {action} {amount} {resource_type.value} FAILED.")

                                            clicked_on_ui = True # Mark UI clicked even if transaction failed
                                            break

                        # elif hud_manager.selected_bottom_tab_index == 2: # Research Tab
                            # TODO: Handle research button clicks
                            # pass

                    # --- Check for Assignment Button Clicks --- (Can happen regardless of panel)
                    if not clicked_on_ui and current_assignment_buttons:
                        for category, buttons in current_assignment_buttons.items():
                            delta = 0
                            if buttons["+"] and buttons["+"].collidepoint(event.pos):
                                delta = 1
                            elif buttons["-"] and buttons["-"].collidepoint(event.pos):
                                delta = -1

                            if delta != 0:
                                # Call admiral to update targets
                                fleet.miner_admiral.adjust_ship_count_for_category(category, delta)
                                clicked_on_ui = True  # Set flag
                                break  # Process only one button click per event

                    # --- Check Speed Control Buttons ---
                    if not clicked_on_ui and current_speed_buttons:
                        for i, rect in current_speed_buttons.items():
                            if rect.collidepoint(event.pos):
                                current_speed_index = i
                                print(f"Game speed set to {constants.GAME_SPEED_MULTIPLIERS[current_speed_index]}x")
                                clicked_on_ui = True
                                break

                elif event.button == 2:  # Panning
                    panning = True
                    pan_start_pos = mouse_pos_vec
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: # Left mouse button up
                    if hud_manager.dragging_slider: # Stop dragging slider
                        hud_manager.stop_slider_drag()
                elif event.button == 2:
                    panning = False
                    pan_start_pos = None
            elif event.type == pygame.MOUSEMOTION:
                if hud_manager.dragging_slider:
                    hud_manager.update_slider_drag(event.pos, central_planet, space_market)
                elif panning and pan_start_pos:
                    pan_delta_screen = mouse_pos_vec - pan_start_pos
                    camera.handle_pan(pan_delta_screen)
                    pan_start_pos = mouse_pos_vec

        # --- Update Systems --- (Skip if paused)
        if game_speed_multiplier > 0.0:
            # Call Miner Admiral update/assignment
            fleet.give_orders(asteroids, central_planet)

            # Update individual ship states (movement, mining, scanning timers)
            fleet.update_ships(dt, [*asteroids, central_planet])

        # --- Rendering ---
        screen.fill(constants.BACKGROUND_COLOR)  # Use constants
        # Call the consolidated draw_frame function instead of individual stubs
        renderer.draw_frame(
            screen,
            ui_font,  # Pass the font needed by asteroid drawing
            camera,
            central_planet,
            asteroids,
            all_ships,  # Pass all ships
            stars,
        )

        # --- Draw HUD (using HUDManager instance) ---
        hud_manager.draw(screen, fleet, central_planet, camera, space_market)

        # Update Display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
