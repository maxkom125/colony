# src/ui/hud_manager.py
import pygame
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Need imports for type hinting (will be adjusted as methods are moved)
from .. import constants
from ..entities.planet import Planet
from ..entities.asteroid import Asteroid
from ..entities.ships.base_ship import Ship
from ..entities.ships.scanner_ship import ScannerShip
from ..entities.ships.mining_ship import MiningShip
from ..enums import ShipState, ResourceType, ShipType
from ..camera.camera import Camera
from ..systems.admirals.miner_admiral import MinerAdmiral
from ..fleet import Fleet
from ..systems.space_market import SpaceMarket
from ..systems.research_system import ResearchSystem


class HUDManager:
    """Manages the drawing and state of the Heads-Up Display elements."""

    def __init__(self, font: pygame.font.Font):
        self.font = font

        # --- Attributes to store calculated Rects for interaction ---
        self.bottom_tab_rects: Dict[int, pygame.Rect] = {}
        self.panel_toggle_button_rect: pygame.Rect | None = None
        self.assignment_button_rects: Dict[str, Dict[str, pygame.Rect | None]] = defaultdict(
            lambda: {"+": None, "-": None}
        )
        self.construction_button_rects: Dict[str, pygame.Rect | None] = {
            "scanner": None,
            "miner": None,
        }
        # --- NEW: Market Slider State ---
        self.market_slider_rects: Dict[ResourceType, pygame.Rect] = {}
        self.market_slider_handle_rects: Dict[ResourceType, pygame.Rect] = {}
        self.market_slider_values: Dict[ResourceType, float] = {  # -1.0 (sell max) to 1.0 (buy max)
            res: 0.0 for res in [ResourceType.TRITANIUM, ResourceType.PLASMA]
        }
        self.market_slider_plus_buttons: Dict[ResourceType, pygame.Rect] = {}
        self.market_slider_minus_buttons: Dict[ResourceType, pygame.Rect] = {}
        self.market_confirm_button_rects: Dict[ResourceType, pygame.Rect] = {}
        self.dragging_slider: Optional[ResourceType] = None
        self.current_trade_details: Dict[ResourceType, Tuple[str, int, float]] = (
            {  # Action ("Buy"/"Sell"), Amount, Cost/Gain
                res: ("Sell", 0, 0.0) for res in [ResourceType.TRITANIUM, ResourceType.PLASMA]
            }
        )
        # --- REMOVED: Old market UI state ---
        # self.market_ui_elements: ...
        # self.market_trade_amounts: ...

        # --- NEW: Speed Control State ---
        self.speed_control_button_rects: Dict[int, pygame.Rect] = {}

        # --- Internal UI State ---
        self.selected_bottom_tab_index: int = 0  # Default to first tab
        self.is_panel_collapsed: bool = False  # Default to expanded
        # --- NEW: Research Ship Type Selector State ---
        self.research_selected_ship_type = ShipType.MINER  # Default to MINER
        self.research_ship_type_tab_rects = {}
        self.research_modal_ship_type = None  # None, 'MINER', or 'SCANNER'

    # --- Main Draw Method ---
    def draw(
        self,
        screen: pygame.Surface,
        fleet: Fleet,
        planet: Planet,
        camera: Camera,
        space_market: SpaceMarket,  # Add space_market instance
        research_system: ResearchSystem,  # Add research_system instance
    ):
        """Draws all HUD elements using internal state."""
        all_ships = fleet.get_all_ships()
        miner_admiral = fleet.miner_admiral

        # --- Calculate positions ---
        # Use internal state now
        positions = self._calculate_panel_positions(self.is_panel_collapsed)

        # --- Draw standard HUD elements ---
        # Convert standalone functions to methods (prefix with _ and add self)
        self._draw_ship_statuses(screen, all_ships)
        self._draw_planet_storage(screen, planet)
        self._draw_miner_assignments(screen, miner_admiral)
        self._draw_speed_controls(screen)  # Draw speed controls

        # --- Draw Bottom Panel Elements ---
        self._draw_bottom_tabs(
            screen,
            self.selected_bottom_tab_index,
            positions["tab_start_x"],
            positions["current_tab_y"],
        )
        self._draw_panel_toggle_button(
            screen,
            positions["button_x_common"],
            positions["button_y_expanded"],
            positions["button_y_collapsed"],
        )

        # Only draw the main panel background and content if not collapsed
        if not self.is_panel_collapsed:
            self._draw_panel_background(screen)
            # --- Draw content specific to the selected tab ---
            if self.selected_bottom_tab_index == 0:  # Construction Tab
                self._draw_construction_buttons(screen)
            elif self.selected_bottom_tab_index == 1:  # Space Market Tab
                self._draw_space_market_ui(screen, space_market, planet)  # Pass market and planet
            elif self.selected_bottom_tab_index == 2:  # Research Tab
                self._draw_research_ui(screen, planet, research_system)
            # --- Draw research modal if open ---
            if self.research_modal_ship_type:
                self._draw_research_modal(screen, planet, research_system)

    # --- State Modification Methods ---
    def toggle_panel_collapsed(self):
        """Flips the collapsed state of the bottom panel."""
        self.is_panel_collapsed = not self.is_panel_collapsed

    def select_bottom_tab(self, index: int):
        """Sets the selected bottom tab index and ensures panel is expanded."""
        # Add check if index is valid? For now assume it is.
        self.selected_bottom_tab_index = index
        # Selecting a tab automatically expands the panel
        self.is_panel_collapsed = False

    # --- REMOVED: Old market amount methods ---
    # def increase_trade_amount(...)
    # def decrease_trade_amount(...)
    # def get_trade_amount(...)

    # --- NEW: Slider Interaction Methods ---
    def start_slider_drag(self, resource: ResourceType, mouse_pos: Tuple[int, int]) -> bool:
        """Checks if the mouse click is on a slider handle and starts dragging."""
        if resource in self.market_slider_handle_rects:
            handle_rect = self.market_slider_handle_rects[resource]
            if handle_rect and handle_rect.collidepoint(mouse_pos):
                self.dragging_slider = resource
                return True
        return False

    def stop_slider_drag(self):
        """Stops dragging any slider."""
        self.dragging_slider = None

    def update_slider_drag(
        self, mouse_pos: Tuple[int, int], planet: Planet, space_market: SpaceMarket
    ):
        """Updates the value of the slider being dragged based on mouse position."""
        if self.dragging_slider and self.dragging_slider in self.market_slider_rects:
            slider_rect = self.market_slider_rects[self.dragging_slider]
            if not slider_rect:
                return  # Should not happen if dragging

            # Calculate value based on horizontal position relative to slider rect
            relative_x = mouse_pos[0] - slider_rect.left
            slider_width = slider_rect.width
            # Clamp value between 0 and slider_width
            relative_x = max(0, min(relative_x, slider_width))
            # Normalize to -1.0 to 1.0 (0 = center)
            value = (relative_x / slider_width) * 2.0 - 1.0
            # Small deadzone near center? Optional, for now snap to 0 if very close
            if abs(value) < 0.05:
                value = 0.0

            self.market_slider_values[self.dragging_slider] = value
            # Update the trade details based on the new slider value
            self._update_trade_details(self.dragging_slider, planet, space_market)

    def adjust_slider(
        self, resource: ResourceType, delta: float, planet: Planet, space_market: SpaceMarket
    ):
        """Adjusts the slider value by a small delta (e.g., from +/- buttons)."""
        if resource in self.market_slider_values:
            current_value = self.market_slider_values[resource]
            new_value = max(-1.0, min(1.0, current_value + delta))
            # Small deadzone near center? Optional, for now snap to 0 if very close
            if (
                abs(new_value) < 0.05 and delta != 0
            ):  # Only snap if moving *through* zero via button
                new_value = 0.0
            self.market_slider_values[resource] = new_value
            # Update the trade details based on the new slider value
            self._update_trade_details(resource, planet, space_market)

    def _update_trade_details(
        self, resource: ResourceType, planet: Planet, space_market: SpaceMarket
    ):
        """Calculates the trade action, amount, and cost/gain based on the slider value."""
        value = self.market_slider_values[resource]
        # Fix: Use ResourceType enum objects as keys, not string values
        available_amount = planet.storage.get(resource, 0)
        available_credits = planet.storage.get(ResourceType.CREDITS, 0)

        if value < 0:  # Selling
            action = "Sell"
            # Scale amount from 0 (at center) to available_amount (at -1.0)
            amount = int(abs(value) * available_amount)
            cost_gain = space_market.get_sell_gain(resource, amount)
        elif value > 0:  # Buying
            action = "Buy"
            # Calculate cost of buying 1 unit
            cost_per_unit = space_market.get_buy_cost(resource, 1)
            # Calculate max buyable amount based on credits
            max_buyable_amount = 0
            if cost_per_unit > constants.EPSILON:  # Avoid division by zero/tiny numbers
                max_buyable_amount = int(available_credits // cost_per_unit)

            # Scale amount from 0 (at center) to MAX_BUY (at 1.0)
            amount = int(value * max_buyable_amount)
            cost_gain = -space_market.get_buy_cost(resource, amount)  # Cost is negative gain
        else:  # value == 0
            action = "Sell"  # Default action text when at 0
            amount = 0
            cost_gain = 0.0

        self.current_trade_details[resource] = (action, amount, cost_gain)

    def reset_market_sliders(self):
        """Resets all sliders to 0 and clears dragging state."""
        self.dragging_slider = None
        for resource in self.market_slider_values:
            self.market_slider_values[resource] = 0.0
            # Optionally re-update trade details if needed, but draw call will do it
            # self._update_trade_details(resource, planet, space_market) # Need planet/market refs here

    # --- Getter Methods ---
    def get_bottom_tab_rects(self) -> Dict[int, pygame.Rect]:
        return self.bottom_tab_rects

    def get_panel_toggle_button_rect(self) -> pygame.Rect | None:
        return self.panel_toggle_button_rect

    def get_assignment_button_rects(self) -> Dict[str, Dict[str, pygame.Rect | None]]:
        return self.assignment_button_rects

    def get_construction_button_rects(self) -> Dict[str, pygame.Rect | None]:
        return self.construction_button_rects

    # --- NEW: Slider/Market Getter Methods ---
    def get_market_slider_rects(self) -> Dict[ResourceType, pygame.Rect]:
        return self.market_slider_rects

    def get_market_slider_handle_rects(self) -> Dict[ResourceType, pygame.Rect]:
        return self.market_slider_handle_rects

    def get_market_slider_plus_buttons(self) -> Dict[ResourceType, pygame.Rect]:
        return self.market_slider_plus_buttons

    def get_market_slider_minus_buttons(self) -> Dict[ResourceType, pygame.Rect]:
        return self.market_slider_minus_buttons

    def get_market_confirm_button_rects(self) -> Dict[ResourceType, pygame.Rect]:
        return self.market_confirm_button_rects

    def get_current_trade_details(self, resource: ResourceType) -> Tuple[str, int, float]:
        """Returns the calculated (Action, Amount, Cost/Gain) for a resource."""
        return self.current_trade_details.get(resource, ("Sell", 0, 0.0))

    def get_speed_control_button_rects(self) -> Dict[int, pygame.Rect]:
        """Returns the calculated Rects for the speed control buttons."""
        return self.speed_control_button_rects

    def get_research_button_rects(self):
        return getattr(self, "research_button_rects", {})

    def get_research_scroll_up_rect(self):
        return getattr(self, "research_scroll_up_rect", None)

    def get_research_scroll_down_rect(self):
        return getattr(self, "research_scroll_down_rect", None)

    def get_research_scrollbar_track_rect(self):
        """Get the research modal scrollbar track rect for interaction."""
        return getattr(self, "research_scrollbar_track_rect", None)

    def get_research_scrollbar_handle_rect(self):
        """Get the research modal scrollbar handle rect for interaction."""
        return getattr(self, "research_scrollbar_handle_rect", None)

    def handle_research_scroll(self, scroll_delta):
        """Handle mouse wheel scrolling in the research modal."""
        if not hasattr(self, "research_scroll_offset"):
            self.research_scroll_offset = 0

        # Calculate scroll amount (negative delta means scroll up)
        scroll_amount = -scroll_delta * 30  # 30 pixels per scroll step

        # Apply scroll with bounds checking (will be clamped in _draw_research_modal)
        self.research_scroll_offset += scroll_amount

    def start_research_scrollbar_drag(self, mouse_pos):
        """Start dragging the research modal scrollbar."""
        if (
            not hasattr(self, "research_scrollbar_handle_rect")
            or not self.research_scrollbar_handle_rect
        ):
            return False

        if self.research_scrollbar_handle_rect.collidepoint(mouse_pos):
            self.research_scrollbar_dragging = True
            self.research_scrollbar_drag_offset = (
                mouse_pos[1] - self.research_scrollbar_handle_rect.y
            )
            return True
        return False

    def stop_research_scrollbar_drag(self):
        """Stop dragging the research modal scrollbar."""
        self.research_scrollbar_dragging = False

    def update_research_scrollbar_drag(self, mouse_pos):
        """Update research modal scrollbar position during drag."""
        if not getattr(self, "research_scrollbar_dragging", False):
            return

        if (
            not hasattr(self, "research_scrollbar_track_rect")
            or not self.research_scrollbar_track_rect
        ):
            return

        # Calculate new handle position
        new_handle_y = mouse_pos[1] - self.research_scrollbar_drag_offset
        track_top = self.research_scrollbar_track_rect.y
        track_bottom = self.research_scrollbar_track_rect.bottom
        handle_height = self.research_scrollbar_handle_rect.height

        # Clamp handle position within track
        new_handle_y = max(track_top, min(new_handle_y, track_bottom - handle_height))

        # Calculate scroll offset based on handle position
        track_height = self.research_scrollbar_track_rect.height
        handle_travel = track_height - handle_height
        if handle_travel > 0:
            scroll_ratio = (new_handle_y - track_top) / handle_travel

            # Calculate max scroll based on content (this will be recalculated in draw method)
            # For now, use a reasonable estimate
            if hasattr(self, "research_modal_ship_type"):
                from ..systems.research_system import ResearchSystem

                # This is a rough estimate - the exact value is calculated in _draw_research_modal
                estimated_max_scroll = max(
                    0,
                    len(ResearchSystem().research_defs.get(self.research_modal_ship_type, {})) * 100
                    - 400,
                )
                self.research_scroll_offset = scroll_ratio * estimated_max_scroll

    # --- Internal Helper & Drawing Methods ---

    def _calculate_panel_positions(self, is_collapsed: bool) -> dict:
        # (Copied from hud.py, uses self.font implicitly if needed, though font isn't used here)
        # ... (Implementation as before)
        panel_start_x = (constants.SCREEN_WIDTH - constants.BOTTOM_PANEL_WIDTH) / 2
        tabs = ["Construction", "Space Market", "Research"]
        num_tabs = len(tabs)
        total_tab_width = num_tabs * constants.BOTTOM_PANEL_TAB_WIDTH
        tab_start_x = panel_start_x + (constants.BOTTOM_PANEL_WIDTH - total_tab_width) / 2
        tab_y_expanded = (
            constants.SCREEN_HEIGHT
            - constants.BOTTOM_PANEL_HEIGHT
            - constants.BOTTOM_PANEL_TAB_HEIGHT
            + constants.BOTTOM_PANEL_BORDER_WIDTH
        )
        tab_y_collapsed = constants.SCREEN_HEIGHT - constants.BOTTOM_PANEL_TAB_HEIGHT
        current_tab_y = tab_y_collapsed if is_collapsed else tab_y_expanded
        button_x_common = tab_start_x - constants.PANEL_TOGGLE_BUTTON_WIDTH / 2 - 5
        button_y_expanded = tab_y_expanded + constants.BOTTOM_PANEL_TAB_HEIGHT / 2
        button_y_collapsed = tab_y_collapsed + constants.BOTTOM_PANEL_TAB_HEIGHT / 2
        return {
            "panel_start_x": panel_start_x,  # Added for background drawing
            "tab_start_x": tab_start_x,
            "current_tab_y": current_tab_y,
            "button_x_common": button_x_common,
            "button_y_expanded": button_y_expanded,
            "button_y_collapsed": button_y_collapsed,
        }

    def _draw_panel_background(self, screen: pygame.Surface):
        # (Copied from hud.py)
        panel_start_x = (constants.SCREEN_WIDTH - constants.BOTTOM_PANEL_WIDTH) / 2
        panel_rect = pygame.Rect(
            panel_start_x,
            constants.SCREEN_HEIGHT - constants.BOTTOM_PANEL_HEIGHT,
            constants.BOTTOM_PANEL_WIDTH,
            constants.BOTTOM_PANEL_HEIGHT,
        )
        pygame.draw.rect(screen, constants.BOTTOM_PANEL_COLOR, panel_rect)
        pygame.draw.rect(
            screen,
            constants.BOTTOM_PANEL_BORDER_COLOR,
            panel_rect,
            constants.BOTTOM_PANEL_BORDER_WIDTH,
        )

    def _draw_bottom_tabs(
        self, screen: pygame.Surface, selected_index: int, tab_start_x: float, tab_y: float
    ):
        # (Copied from hud.py, uses self.font)
        self.bottom_tab_rects.clear()  # Use self attribute
        tabs = ["Construction", "Space Market", "Research"]
        for i, tab_name in enumerate(tabs):
            tab_x = tab_start_x + i * constants.BOTTOM_PANEL_TAB_WIDTH
            tab_rect = pygame.Rect(
                tab_x, tab_y, constants.BOTTOM_PANEL_TAB_WIDTH, constants.BOTTOM_PANEL_TAB_HEIGHT
            )
            self.bottom_tab_rects[i] = tab_rect  # Store in self attribute
            is_selected = i == selected_index
            tab_color = (
                constants.BOTTOM_PANEL_TAB_SELECTED_COLOR
                if is_selected
                else constants.BOTTOM_PANEL_TAB_COLOR
            )
            pygame.draw.rect(
                screen, tab_color, tab_rect, border_top_left_radius=5, border_top_right_radius=5
            )
            pygame.draw.rect(
                screen,
                constants.BOTTOM_PANEL_BORDER_COLOR,
                tab_rect,
                constants.BOTTOM_PANEL_BORDER_WIDTH,
                border_top_left_radius=5,
                border_top_right_radius=5,
            )
            text_surf = self.font.render(tab_name, True, constants.UI_TEXT_COLOR)  # Use self.font
            text_rect = text_surf.get_rect(center=tab_rect.center)
            screen.blit(text_surf, text_rect)

    def _draw_panel_toggle_button(
        self,
        screen: pygame.Surface,
        button_x: float,
        button_y_expanded: float,
        button_y_collapsed: float,
    ):
        # (Copied from hud.py, uses self.font and self.is_panel_collapsed)
        rect = pygame.Rect(
            0, 0, constants.PANEL_TOGGLE_BUTTON_WIDTH, constants.PANEL_TOGGLE_BUTTON_HEIGHT
        )
        if self.is_panel_collapsed:  # Use self attribute
            button_y = button_y_collapsed
            symbol = constants.PANEL_TOGGLE_SYMBOL_EXPAND
        else:
            button_y = button_y_expanded
            symbol = constants.PANEL_TOGGLE_SYMBOL_COLLAPSE
        rect.center = (button_x, button_y)
        pygame.draw.rect(screen, constants.PANEL_TOGGLE_BUTTON_COLOR, rect, border_radius=3)
        pygame.draw.rect(screen, constants.BOTTOM_PANEL_BORDER_COLOR, rect, 1, border_radius=3)
        text_surf = self.font.render(symbol, True, constants.UI_TEXT_COLOR)  # Use self.font
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        self.panel_toggle_button_rect = rect  # Store in self attribute

    # --- Moved Drawing Methods ---
    def _draw_ship_statuses(self, screen: pygame.Surface, ships: List[Ship]):
        # (Copied from hud.py, uses self.font)
        ship_ui_start_x = 10
        line_height = 20
        # Adjust padding to account only for tab height, pushing logs lower
        padding_bottom = 5

        # Calculate start Y based on number of ships
        max_ships_shown = (constants.SCREEN_HEIGHT - padding_bottom) // line_height
        display_ships = ships[:max_ships_shown]
        total_ui_height = len(display_ships) * line_height
        ship_ui_start_y = constants.SCREEN_HEIGHT - total_ui_height - padding_bottom

        y_offset = ship_ui_start_y
        # Use enumerate for index if needed later, but using ship.id is clearer
        for ship in display_ships:
            state_text = f"Ship {ship.id} ({type(ship).__name__}): {ship.state.name}"
            # ... (rest of the ship status text generation)
            if ship.target:
                if isinstance(ship.target, Asteroid):
                    target = f"Target: Asteroid {ship.target.id}"
                elif isinstance(ship.target, Planet):
                    target = f"Target: Planet {ship.target.id}"
                else:
                    try:
                        target = f"Target: {type(ship.target).__name__} {ship.target.id}"
                    except AttributeError:
                        target = f"Target: Unknown Type"
                state_text += f" -> {target}"
            if isinstance(ship, ScannerShip) and ship.state == ShipState.SCANNING:
                state_text += f" (Scan: {ship.scan_timer:.1f}s)"
            elif isinstance(ship, MiningShip):
                if ship.state == ShipState.MINING:
                    state_text += f" (Mine: {ship.mining_timer:.1f}s)"
                elif ship.state == ShipState.DUMPING:
                    state_text += f" (Dump: {ship.dumping_timer:.1f}s)"
                state_text += f" Cargo: {int(ship.get_cargo_total())}"

            # Add Fuel status for all ships
            state_text += f" Fuel: {int(ship.fuel)}/{int(ship.fuel_max_capacity)}"

            text_surface = self.font.render(
                state_text, True, constants.UI_TEXT_COLOR
            )  # Use self.font
            screen.blit(text_surface, (ship_ui_start_x, y_offset))
            y_offset += line_height

    def _draw_planet_storage(self, screen: pygame.Surface, planet: Planet):
        # (Copied from hud.py, uses self.font)
        storage_y_offset = 10
        storage_x_offset = 10
        for resource_type_enum in ResourceType:  # Iterate through Enum
            resource_type = resource_type_enum.value  # Get string value for dict key
            amount = planet.storage.get(resource_type_enum, 0)  # Use .get for safety

            color = constants.WHITE
            if resource_type_enum == ResourceType.TRITANIUM:
                color = constants.TRITANIUM_COLOR
            elif resource_type_enum == ResourceType.CREDITS:
                color = constants.CREDITS_COLOR
            elif resource_type_enum == ResourceType.PLASMA:
                color = constants.PLASMA_COLOR

            text = f"{resource_type}: {int(amount)}"
            text_surface = self.font.render(text, True, color)  # Use self.font
            text_rect = text_surface.get_rect(topleft=(storage_x_offset, storage_y_offset))
            screen.blit(text_surface, text_rect)
            storage_y_offset += 20

    def _draw_miner_assignments(self, screen: pygame.Surface, miner_admiral: MinerAdmiral):
        # (Copied from hud.py, uses self.font and self.assignment_button_rects)
        # Clear previous rects stored in the instance
        self.assignment_button_rects.clear()
        # Add default dict entries back if needed after clear, or just rely on defaultdict behavior
        # for category in ResourceType.list() + ["Random"]:
        #     self.assignment_button_rects[category] = {"+": None, "-": None}

        total_mining_ships = miner_admiral.get_ship_count()
        idle_count = miner_admiral.get_idle_ship_count()
        categories = miner_admiral.get_all_categories()

        title_surf = self.font.render("Miner Assignments:", True, constants.UI_TEXT_COLOR)
        title_rect = title_surf.get_rect(
            topleft=(constants.ASSIGNMENT_AREA_X, constants.ASSIGNMENT_AREA_Y)
        )
        screen.blit(title_surf, title_rect)
        y_offset = title_rect.bottom + 10

        for category in categories:
            current_count = miner_admiral.get_ship_count_for_category(category)

            color = constants.WHITE
            # Check against Enum members for safety
            if category == ResourceType.TRITANIUM.value:
                color = constants.TRITANIUM_COLOR
            elif category == ResourceType.CREDITS.value:
                color = constants.CREDITS_COLOR  # This won't be assignable, but check anyway
            elif category == ResourceType.PLASMA.value:
                color = constants.PLASMA_COLOR
            elif category == "Random":  # Assuming "Random" is a special string key
                color = constants.GRAY

            text = f"{category}: {current_count}"
            text_surf = self.font.render(text, True, color)
            text_rect = text_surf.get_rect(topleft=(constants.ASSIGNMENT_AREA_X, y_offset))
            screen.blit(text_surf, text_rect)

            button_y = text_rect.centery - constants.ASSIGNMENT_BUTTON_HEIGHT // 2
            minus_rect = pygame.Rect(
                text_rect.right + constants.ASSIGNMENT_BUTTON_PADDING,
                button_y,
                constants.ASSIGNMENT_BUTTON_WIDTH,
                constants.ASSIGNMENT_BUTTON_HEIGHT,
            )
            pygame.draw.rect(screen, constants.SLIDER_BG_COLOR, minus_rect, border_radius=3)
            minus_surf = self.font.render("-", True, constants.WHITE)
            minus_surf_rect = minus_surf.get_rect(center=minus_rect.center)
            screen.blit(minus_surf, minus_surf_rect)
            self.assignment_button_rects[category]["-"] = minus_rect  # Store in self attribute

            plus_rect = pygame.Rect(
                minus_rect.right + constants.ASSIGNMENT_BUTTON_PADDING,
                button_y,
                constants.ASSIGNMENT_BUTTON_WIDTH,
                constants.ASSIGNMENT_BUTTON_HEIGHT,
            )
            pygame.draw.rect(screen, constants.SLIDER_BG_COLOR, plus_rect, border_radius=3)
            plus_surf = self.font.render("+", True, constants.WHITE)
            plus_surf_rect = plus_surf.get_rect(center=plus_rect.center)
            screen.blit(plus_surf, plus_surf_rect)
            self.assignment_button_rects[category]["+"] = plus_rect  # Store in self attribute

            y_offset += constants.ASSIGNMENT_LINE_HEIGHT

        y_offset += 5
        idle_text = f"Idle: {idle_count}"
        idle_surf = self.font.render(idle_text, True, constants.UI_TEXT_COLOR)
        idle_rect = idle_surf.get_rect(topleft=(constants.ASSIGNMENT_AREA_X, y_offset))
        screen.blit(idle_surf, idle_rect)
        y_offset += constants.ASSIGNMENT_LINE_HEIGHT

        total_text = f"Total Miners: {total_mining_ships}"
        total_surf = self.font.render(total_text, True, constants.UI_TEXT_COLOR)
        total_rect = total_surf.get_rect(topleft=(constants.ASSIGNMENT_AREA_X, y_offset))
        screen.blit(total_surf, total_rect)

    def _draw_construction_buttons(self, screen: pygame.Surface):
        # Position buttons inside the expanded panel
        panel_top_y = constants.SCREEN_HEIGHT - constants.BOTTOM_PANEL_HEIGHT
        button_y = panel_top_y + constants.BOTTOM_PANEL_HEIGHT / 2  # Center vertically in panel
        padding = 20
        scanner_text = "[Build Scanner (50T, 100C)]"
        miner_text = "[Build Miner (100T, 50C)]"

        scanner_surf = self.font.render(scanner_text, True, constants.UI_TEXT_COLOR)
        miner_surf = self.font.render(miner_text, True, constants.UI_TEXT_COLOR)

        total_width = scanner_surf.get_width() + padding + miner_surf.get_width()
        # Center horizontally within the panel width
        panel_start_x = (constants.SCREEN_WIDTH - constants.BOTTOM_PANEL_WIDTH) / 2
        start_x = panel_start_x + (constants.BOTTOM_PANEL_WIDTH - total_width) / 2

        # Use center alignment for positioning based on calculated y
        scanner_rect = scanner_surf.get_rect(
            center=(start_x + scanner_surf.get_width() / 2, button_y)
        )
        miner_rect = miner_surf.get_rect(
            center=(scanner_rect.right + padding + miner_surf.get_width() / 2, button_y)
        )

        self.construction_button_rects["scanner"] = scanner_rect
        self.construction_button_rects["miner"] = miner_rect

        screen.blit(scanner_surf, scanner_rect)
        screen.blit(miner_surf, miner_rect)

    def _draw_space_market_ui(
        self, screen: pygame.Surface, space_market: SpaceMarket, planet: Planet
    ):
        """Draws the interactive UI for the Space Market tab using a slider."""
        # Clear old rects - important!
        self.market_slider_rects.clear()
        self.market_slider_handle_rects.clear()
        self.market_slider_plus_buttons.clear()
        self.market_slider_minus_buttons.clear()
        self.market_confirm_button_rects.clear()

        panel_start_x = (constants.SCREEN_WIDTH - constants.BOTTOM_PANEL_WIDTH) / 2
        panel_top_y = constants.SCREEN_HEIGHT - constants.BOTTOM_PANEL_HEIGHT
        content_start_x = panel_start_x + 20
        content_start_y = panel_top_y + 10  # Start slightly lower
        line_height = 35  # Increased line height for slider + text
        button_size = 20
        slider_width = 200
        slider_height = 10
        handle_width = 8
        handle_height = 15
        button_padding = 10
        confirm_button_width = 80
        confirm_button_height = 25

        y_offset = content_start_y

        resources_to_trade = [ResourceType.TRITANIUM, ResourceType.PLASMA]

        for resource in resources_to_trade:
            # Update trade details for this resource based on current slider value
            self._update_trade_details(resource, planet, space_market)
            action, amount, cost_gain = self.current_trade_details[resource]

            resource_str = resource.value
            slider_value = self.market_slider_values[resource]

            # Resource Info (Name, Have)
            have_amount = int(planet.storage.get(resource, 0))
            info_text = f"{resource_str} (Have: {have_amount})"
            color = (
                constants.TRITANIUM_COLOR
                if resource == ResourceType.TRITANIUM
                else constants.PLASMA_COLOR
            )
            info_surf = self.font.render(info_text, True, color)
            info_rect = info_surf.get_rect(topleft=(content_start_x, y_offset))
            screen.blit(info_surf, info_rect)
            current_x = info_rect.right + 20  # Space after resource name

            # --- Slider ---
            # Minus Button
            minus_rect = pygame.Rect(
                current_x,
                y_offset + (info_surf.get_height() - button_size) // 2,
                button_size,
                button_size,
            )
            pygame.draw.rect(screen, constants.BOTTOM_PANEL_TAB_COLOR, minus_rect, border_radius=3)
            pygame.draw.rect(
                screen, constants.BOTTOM_PANEL_BORDER_COLOR, minus_rect, 1, border_radius=3
            )
            minus_surf = self.font.render("-", True, constants.UI_TEXT_COLOR)
            minus_text_rect = minus_surf.get_rect(center=minus_rect.center)
            screen.blit(minus_surf, minus_text_rect)
            self.market_slider_minus_buttons[resource] = minus_rect
            current_x += button_size + button_padding

            # Slider Track
            slider_track_rect = pygame.Rect(
                current_x,
                y_offset + (info_surf.get_height() - slider_height) // 2,
                slider_width,
                slider_height,
            )
            pygame.draw.rect(screen, constants.SLIDER_BG_COLOR, slider_track_rect, border_radius=5)
            self.market_slider_rects[resource] = slider_track_rect  # Store track rect
            # Draw center line
            center_x = slider_track_rect.centerx
            pygame.draw.line(
                screen,
                constants.GRAY,
                (center_x, slider_track_rect.top),
                (center_x, slider_track_rect.bottom),
                1,
            )
            current_x += slider_width + button_padding

            # Slider Handle
            handle_x_normalized = (slider_value + 1.0) / 2.0  # Convert -1..1 to 0..1
            handle_center_x = slider_track_rect.left + handle_x_normalized * slider_track_rect.width
            handle_rect = pygame.Rect(0, 0, handle_width, handle_height)
            handle_rect.center = (handle_center_x, slider_track_rect.centery)
            handle_color = constants.SLIDER_KNOB_COLOR
            if self.dragging_slider == resource:
                handle_color = constants.WHITE  # Highlight if dragging
            pygame.draw.rect(screen, handle_color, handle_rect, border_radius=3)
            self.market_slider_handle_rects[resource] = handle_rect  # Store handle rect

            # Plus Button
            plus_rect = pygame.Rect(
                current_x,
                y_offset + (info_surf.get_height() - button_size) // 2,
                button_size,
                button_size,
            )
            pygame.draw.rect(screen, constants.BOTTOM_PANEL_TAB_COLOR, plus_rect, border_radius=3)
            pygame.draw.rect(
                screen, constants.BOTTOM_PANEL_BORDER_COLOR, plus_rect, 1, border_radius=3
            )
            plus_surf = self.font.render("+", True, constants.UI_TEXT_COLOR)
            plus_text_rect = plus_surf.get_rect(center=plus_rect.center)
            screen.blit(plus_surf, plus_text_rect)
            self.market_slider_plus_buttons[resource] = plus_rect
            current_x += plus_rect.width + 20  # More space before trade details

            # --- Trade Details and Confirm Button ---
            # Trade Action Text (Buy/Sell Amount)
            trade_text = f"{action} {amount}"
            trade_surf = self.font.render(trade_text, True, constants.UI_TEXT_COLOR)
            trade_rect = trade_surf.get_rect(midleft=(current_x, plus_rect.centery))
            screen.blit(trade_surf, trade_rect)
            current_x = trade_rect.right + 15

            # Cost/Gain Text
            cost_gain_str = f"({cost_gain:+.1f} Cr)"
            cost_gain_surf = self.font.render(cost_gain_str, True, constants.CREDITS_COLOR)
            cost_gain_rect = cost_gain_surf.get_rect(midleft=(current_x, plus_rect.centery))
            screen.blit(cost_gain_surf, cost_gain_rect)
            current_x = cost_gain_rect.right + 25

            # Confirm Button
            confirm_rect = pygame.Rect(
                current_x,
                y_offset + (info_surf.get_height() - confirm_button_height) // 2,
                confirm_button_width,
                confirm_button_height,
            )
            # Only enable confirm if amount > 0
            button_color = (
                constants.BOTTOM_PANEL_TAB_COLOR if amount > 0 else constants.SLIDER_BG_COLOR
            )
            text_color = constants.UI_TEXT_COLOR if amount > 0 else constants.GRAY
            pygame.draw.rect(screen, button_color, confirm_rect, border_radius=5)
            pygame.draw.rect(
                screen, constants.BOTTOM_PANEL_BORDER_COLOR, confirm_rect, 1, border_radius=5
            )
            confirm_surf = self.font.render("Confirm", True, text_color)
            confirm_text_rect = confirm_surf.get_rect(center=confirm_rect.center)
            screen.blit(confirm_surf, confirm_text_rect)
            self.market_confirm_button_rects[resource] = confirm_rect  # Store confirm button rect

            y_offset += line_height

    def _draw_speed_controls(self, screen: pygame.Surface):
        """Draws the game speed control buttons (pause, play, ff) in the top-right corner."""
        self.speed_control_button_rects.clear()

        # Start drawing from the right edge of the screen, accounting for padding
        right_margin = 10  # Define the margin from the edge
        current_x = constants.SCREEN_WIDTH - right_margin
        start_y = right_margin  # Use the same margin for the top

        # Iterate backwards through icons and indices
        for i in range(len(constants.GAME_SPEED_ICONS) - 1, -1, -1):
            icon = constants.GAME_SPEED_ICONS[i]
            # Calculate the left edge of the button for this iteration
            button_x = current_x - constants.GAME_SPEED_BUTTON_SIZE

            # Determine color based on if this is the *active* speed? (Needs active speed index)
            # TODO: Highlight the active button later if needed.
            button_rect = pygame.Rect(
                button_x,
                start_y,
                constants.GAME_SPEED_BUTTON_SIZE,
                constants.GAME_SPEED_BUTTON_SIZE,
            )
            pygame.draw.rect(screen, constants.SLIDER_BG_COLOR, button_rect, border_radius=3)
            pygame.draw.rect(
                screen, constants.BOTTOM_PANEL_BORDER_COLOR, button_rect, 1, border_radius=3
            )

            icon_surf = self.font.render(icon, True, constants.UI_TEXT_COLOR)
            icon_rect = icon_surf.get_rect(center=button_rect.center)
            screen.blit(icon_surf, icon_rect)

            self.speed_control_button_rects[i] = button_rect
            # Move current_x to the left for the next button, including padding
            current_x = button_x - constants.GAME_SPEED_BUTTON_PADDING

    def _draw_research_ui(
        self, screen: pygame.Surface, planet: Planet, research_system: ResearchSystem
    ):
        """Draws only the ship type selection buttons in the Research tab. Buttons are dynamically sized and centered."""
        from ..enums import ShipType

        # Layout
        panel_start_x = (constants.SCREEN_WIDTH - constants.BOTTOM_PANEL_WIDTH) / 2
        panel_top_y = constants.SCREEN_HEIGHT - constants.BOTTOM_PANEL_HEIGHT
        panel_width = constants.BOTTOM_PANEL_WIDTH
        panel_height = constants.BOTTOM_PANEL_HEIGHT
        # Dynamic sizing
        num_buttons = 2
        button_width = int(panel_width * 0.32)
        button_height = int(panel_height * 0.32)
        button_padding = int(panel_width * 0.04)
        total_buttons_width = num_buttons * button_width + (num_buttons - 1) * button_padding
        # Center horizontally and vertically
        buttons_start_x = panel_start_x + (panel_width - total_buttons_width) / 2
        buttons_center_y = panel_top_y + panel_height / 2
        button_top = int(buttons_center_y - button_height / 2)
        # Font size scales with button height
        font_size = max(18, int(button_height * 0.45))
        ship_types = [ShipType.MINER, ShipType.SCANNER]
        self.research_ship_type_tab_rects = {}
        for i, stype in enumerate(ship_types):
            rect = pygame.Rect(
                int(buttons_start_x + i * (button_width + button_padding)),
                button_top,
                button_width,
                button_height,
            )
            color = constants.BOTTOM_PANEL_TAB_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=round(button_height * 0.18))
            pygame.draw.rect(
                screen,
                constants.BOTTOM_PANEL_BORDER_COLOR,
                rect,
                2,
                border_radius=round(button_height * 0.18),
            )
            font = pygame.font.SysFont(None, font_size, bold=True)
            label = stype.value
            surf = font.render(label, True, constants.UI_TEXT_COLOR)
            surf_rect = surf.get_rect(center=rect.center)
            screen.blit(surf, surf_rect)
            self.research_ship_type_tab_rects[stype] = rect
        # No research items are shown here. The actual research window/modal will be drawn elsewhere when a type is selected.

    def _draw_research_modal(self, screen: pygame.Surface, planet, research_system):
        """Draws a modal overlay with the research tree for the selected ship type, centered in the middle of the screen as a separate window."""
        ship_type = self.research_modal_ship_type

        # Initialize scroll offset if not exists
        if not hasattr(self, "research_scroll_offset"):
            self.research_scroll_offset = 0

        # Draw semi-transparent overlay over the whole screen
        overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # RGBA, alpha=160 for dimming
        screen.blit(overlay, (0, 0))

        # Modal window size and position (larger)
        modal_width = int(constants.SCREEN_WIDTH * 0.56)
        modal_height = int(constants.SCREEN_HEIGHT * 0.66)
        modal_x = (constants.SCREEN_WIDTH - modal_width) // 2
        modal_y = (constants.SCREEN_HEIGHT - modal_height) // 2
        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)

        # Modal background
        pygame.draw.rect(screen, constants.BOTTOM_PANEL_COLOR, modal_rect, border_radius=18)
        pygame.draw.rect(
            screen, constants.BOTTOM_PANEL_BORDER_COLOR, modal_rect, 4, border_radius=18
        )

        # Title
        font = pygame.font.SysFont(None, max(28, int(modal_height * 0.09)), bold=True)
        title = f"{ship_type} Research"
        title_surf = font.render(title, True, constants.UI_TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(modal_rect.centerx, modal_rect.top + 44))
        screen.blit(title_surf, title_rect)

        # Close button
        close_size = int(modal_height * 0.09)
        close_rect = pygame.Rect(
            modal_rect.right - close_size - 22, modal_rect.top + 22, close_size, close_size
        )
        pygame.draw.rect(
            screen, constants.SLIDER_BG_COLOR, close_rect, border_radius=close_size // 3
        )
        pygame.draw.rect(
            screen,
            constants.BOTTOM_PANEL_BORDER_COLOR,
            close_rect,
            2,
            border_radius=close_size // 3,
        )
        x_font = pygame.font.SysFont(None, close_size - 2, bold=True)
        x_surf = x_font.render("×", True, constants.UI_TEXT_COLOR)
        x_rect = x_surf.get_rect(center=close_rect.center)
        screen.blit(x_surf, x_rect)
        self.research_modal_close_rect = close_rect

        # Research items with scrolling
        research_defs = research_system.research_defs[ship_type]
        research_levels = research_system.research_levels[ship_type]

        # Calculate content area (excluding title and padding)
        content_start_y = title_rect.bottom + 36
        content_height = modal_rect.bottom - content_start_y - 20  # 20px bottom padding

        # Item dimensions
        item_font = pygame.font.SysFont(
            None, max(16, int(modal_height * 0.06)), bold=True
        )  # Reduced from 0.07
        body_font = pygame.font.SysFont(
            None, max(14, int(modal_height * 0.05))
        )  # Reduced from 0.055
        effect_font = pygame.font.SysFont(
            None, max(14, int(modal_height * 0.05)), bold=True
        )  # Reduced from 0.055

        item_width = modal_width * 0.42  # Slightly smaller to make more room on right
        item_height = modal_height * 0.29  # Keep original larger cards
        item_padding = modal_width * 0.03  # Reduced padding between columns (was 0.04)
        row_spacing = 15  # Reduced from 20

        # Calculate total content height needed
        num_items = len(research_defs)
        rows_needed = (num_items + 1) // 2  # 2 columns
        total_content_height = rows_needed * (item_height + row_spacing) - row_spacing

        # Scrollbar setup
        scrollbar_width = 20
        scrollbar_x = modal_rect.right - scrollbar_width - 10
        scrollbar_y = content_start_y
        scrollbar_height = content_height

        # Calculate scroll limits
        max_scroll = max(0, total_content_height - content_height)
        self.research_scroll_offset = max(0, min(self.research_scroll_offset, max_scroll))

        # Draw scrollbar if needed
        if max_scroll > 0:
            # Scrollbar track
            scrollbar_track = pygame.Rect(
                scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height
            )
            pygame.draw.rect(screen, constants.SLIDER_BG_COLOR, scrollbar_track, border_radius=10)
            pygame.draw.rect(
                screen, constants.BOTTOM_PANEL_BORDER_COLOR, scrollbar_track, 1, border_radius=10
            )

            # Scrollbar handle
            handle_height = max(20, int(scrollbar_height * (content_height / total_content_height)))
            handle_y = scrollbar_y + int(
                (self.research_scroll_offset / max_scroll) * (scrollbar_height - handle_height)
            )
            handle_rect = pygame.Rect(scrollbar_x + 2, handle_y, scrollbar_width - 4, handle_height)
            pygame.draw.rect(screen, constants.BOTTOM_PANEL_TAB_COLOR, handle_rect, border_radius=8)
            pygame.draw.rect(
                screen, constants.BOTTOM_PANEL_BORDER_COLOR, handle_rect, 1, border_radius=8
            )

            # Store scrollbar rects for interaction
            self.research_scrollbar_track_rect = scrollbar_track
            self.research_scrollbar_handle_rect = handle_rect
        else:
            self.research_scrollbar_track_rect = None
            self.research_scrollbar_handle_rect = None

        # Create clipping area for content - equal margins on both sides
        content_rect = pygame.Rect(
            modal_x + 10, content_start_y, modal_width - scrollbar_width - 20, content_height
        )

        # Create a surface for the scrollable content
        content_surface = pygame.Surface(
            (content_rect.width, max(content_height, total_content_height)), pygame.SRCALPHA
        )

        # Calculate item positions
        start_x = (content_rect.width - (2 * item_width + item_padding)) / 2
        start_y = -self.research_scroll_offset

        # Clear button rects
        if not hasattr(self, "research_modal_button_rects"):
            self.research_modal_button_rects = {}
        else:
            # Clear previous button rects for this ship type
            keys_to_remove = [
                key for key in self.research_modal_button_rects.keys() if key[0] == ship_type
            ]
            for key in keys_to_remove:
                del self.research_modal_button_rects[key]

        # Draw research items on content surface
        for i, (key, info) in enumerate(research_defs.items()):
            col = i % 2
            row = i // 2
            x = start_x + col * (item_width + item_padding)
            y = start_y + row * (item_height + row_spacing)

            # Skip items that are completely outside the visible area
            if y + item_height < 0 or y > content_height:
                continue

            item_rect = pygame.Rect(x, y, item_width, item_height)
            pygame.draw.rect(
                content_surface, constants.SLIDER_BG_COLOR, item_rect, border_radius=12
            )
            pygame.draw.rect(
                content_surface, constants.BOTTOM_PANEL_BORDER_COLOR, item_rect, 1, border_radius=12
            )

            # Name and level (left-aligned, top)
            name = info["display_name"]
            level = research_levels[key]
            max_level = info["max_level"]
            name_surf = item_font.render(
                f"{name} [{level}/{max_level}]", True, constants.UI_TEXT_COLOR
            )
            name_y = item_rect.top + 15  # Reduced from 18
            content_surface.blit(name_surf, (item_rect.left + 18, name_y))  # Reduced from 22

            # Cost (left-aligned, below name)
            next_cost = research_system.get_next_level_cost(key, ship_type)
            cost_y = name_y + name_surf.get_height() + 8  # Reduced from 10
            cost_x = item_rect.left + 18  # Reduced from 22
            if next_cost:
                for idx, (res, amount) in enumerate(next_cost.items()):
                    color = constants.UI_TEXT_COLOR
                    if res == ResourceType.CREDITS:
                        color = constants.CREDITS_COLOR
                    elif res == ResourceType.PLASMA:
                        color = constants.PLASMA_COLOR
                    elif res == ResourceType.TRITANIUM:
                        color = constants.TRITANIUM_COLOR
                    part_surf = body_font.render(f"{amount} {res.value}", True, color)
                    content_surface.blit(part_surf, (cost_x, cost_y))
                    cost_x += part_surf.get_width() + 16

            # Effect (left-aligned, above button)
            effect = info["effect_per_level"]
            effect_text = f"+{int(effect*100)}%/lvl" if effect >= 0 else f"{int(effect*100)}%/lvl"
            effect_surf = effect_font.render(effect_text, True, constants.WHITE)
            effect_y = item_rect.bottom - 32 - effect_surf.get_height()  # Reduced from 38
            content_surface.blit(effect_surf, (item_rect.left + 18, effect_y))  # Reduced from 22

            # Button (bottom right corner, dynamic size)
            btn_width = max(80, min(int(item_width * 0.32), 160))
            btn_height = max(28, min(int(item_height * 0.28), 48))
            btn_x = item_rect.right - btn_width - 18  # Reduced from 22
            btn_y = item_rect.bottom - btn_height - 15  # Reduced from 18
            can_buy = next_cost and research_system.can_research(key, ship_type, planet.storage)
            button_color = (
                constants.BOTTOM_PANEL_TAB_COLOR if can_buy else constants.SLIDER_BG_COLOR
            )
            text_color = constants.UI_TEXT_COLOR if can_buy else constants.GRAY
            pygame.draw.rect(
                content_surface,
                button_color,
                (btn_x, btn_y, btn_width, btn_height),
                border_radius=btn_height // 3,
            )
            pygame.draw.rect(
                content_surface,
                constants.BOTTOM_PANEL_BORDER_COLOR,
                (btn_x, btn_y, btn_width, btn_height),
                1,
                border_radius=btn_height // 3,
            )
            btn_text = "Research" if next_cost else "MAXED"
            btn_font_size = max(16, int(btn_height * 0.55))
            btn_font = pygame.font.SysFont(None, btn_font_size, bold=False)
            btn_surf = btn_font.render(btn_text, True, text_color)
            btn_rect = btn_surf.get_rect(center=(btn_x + btn_width / 2, btn_y + btn_height / 2))
            content_surface.blit(btn_surf, btn_rect)

            # Store button rect for click detection (adjusted for screen coordinates)
            screen_btn_rect = pygame.Rect(
                content_rect.x + btn_x,
                content_rect.y + btn_y,  # No additional scroll offset needed
                btn_width,
                btn_height,
            )
            # Only store if button is visible
            if (
                screen_btn_rect.bottom > content_rect.top
                and screen_btn_rect.top < content_rect.bottom
            ):
                self.research_modal_button_rects[(ship_type, key)] = screen_btn_rect

        # Blit the content surface to the screen with clipping
        screen.set_clip(content_rect)
        screen.blit(content_surface, content_rect.topleft)
        screen.set_clip(None)
