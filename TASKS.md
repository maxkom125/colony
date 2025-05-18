# Project Tasks 

## Task ID: 1
- Status: DONE
- Description: Set up basic Pygame project structure (window, main loop, constants file) and implement camera controls (zoom, pan within fixed boundaries).
- Priority: High
- Dependencies: None

## Task ID: 2
- Status: DONE
- Description: Create a `Planet` class and display the central artificial planet.
- Priority: High
- Dependencies: 1

## Task ID: 3
- Status: DONE
- Description: Create an `Asteroid` class, generate multiple instances with random positions.
- Priority: High
- Dependencies: 1

## Task ID: 4
- Status: DONE
- Description: Create background elements (stars, distant planets - static initially).
- Priority: Medium
- Dependencies: 1

## Task ID: 5
- Status: DONE
- Description: Define resource types: Tritanium, Credits, Plasma. Link random amounts to asteroids.
- Priority: Medium
- Dependencies: 3

## Task ID: 6
- Status: DONE
- Description: Create a basic `Spaceship` class (e.g., Scanner ship) and display it.
- Priority: Medium
- Dependencies: 1

## Task ID: 7
- Status: DONE
- Description: Implement simple AI movement for ships (e.g., move towards target asteroid).
- Priority: Medium
- Dependencies: 6

## Task ID: 8
- Status: DONE
- Description: Implement "Scan" action: select asteroid, reveal its resources.
- Priority: Medium
- Dependencies: 5, 7

## Task ID: 9
- Status: DONE
- Description: Create a second `Spaceship` type (Mining ship).
- Priority: Low
- Dependencies: 6

## Task ID: 10
- Status: DONE
- Description: Implement "Mine" action for `MiningShip`: target nearest *scanned* asteroid with resources, move to it, mine for a duration (based on radius and multiplier), transfer resources to ship cargo (respecting capacity), return to central planet, dump resources into planet storage (fixed duration), deplete asteroid resources. Includes adding `storage` to `Planet` and `cargo`/`capacity` to ships.
- Priority: Medium # Increased priority as it's a core mechanic
- Dependencies: 9, 5, 7 # Depends on Mining Ship, Resources defined, Basic Movement

## Task ID: 11
- Status: DONE
- Description: Implement basic UI to display the resource amounts stored at the central `Planet`.
- Priority: Low
- Dependencies: 10 # Depends on resources being delivered to planet storage

## Task ID: 12
- Status: DONE
- Description: Create a `SpaceMarket` class to handle dynamic resource conversion. Implement logic for storing current/base rates, calculating transactions with fees, adjusting rates based on trades, and decaying rates towards base values over time. Define initial base rates and fee.
- Priority: Low
- Dependencies: 5

## Task ID: 13
- Status: DONE
- Description: Implement UI/mechanism for resource conversion.
- Priority: High
- Dependencies: 11, 12

## Task ID: 14
- Status: DONE
- Description: Define construction costs (Tritanium, Credits) for Scanner and Mining ships.
- Priority: Medium
- Dependencies: 5, 6, 9

## Task ID: 15
- Status: DONE
- Description: Implement ship construction mechanism (deduct resources, add ship instance).
- Priority: Medium
- Dependencies: 14

## Task ID: 16
- Status: TODO
- Description: Implement objective tracking (10 ships built, 1000 Credits accumulated).
- Priority: Low
- Dependencies: 11, 15 

## Task ID: 17
- Status: DONE
- Description: Implement ship collision avoidance (e.g., using steering behaviors or simple path adjustments) to prevent ships from flying through asteroids.
- Priority: Medium
- Dependencies: 7 # Depends on basic movement 

## Task ID: 18
- Status: DONE
- Description: Implement resource mining priorities. Add UI sliders (0 to 1, default 1) for Tritanium, Credits, and Plasma. Store these priority values. Modify Mining Ship AI (`find_nearest_asteroid` or a new planning logic) to select target asteroids based on a weighted distribution reflecting these priorities, aiming for a proportional mining intensity/frequency for each resource rather than a strict queue. (Reminder: Discuss implementation details of weighted selection/expedition planning when starting this task).
- Priority: Medium
- Dependencies: 10 # Depends on Mining Implementation 

## Task ID: 19
- Status: DONE
- Description: Implement unit tests for key components (e.g., Camera coordinate conversion, Planet storage updates, construction/conversion logic, AI target scoring).
- Priority: High
- Dependencies: None 

## Task ID: 20
- Status: DONE
- Description: Improve Scanner AI: Prevent multiple scanners from targeting the same unscanned asteroid simultaneously. Each scanner should check if an asteroid is already targeted by another scanner before selecting it.
- Priority: Medium
- Dependencies: 8 # Depends on basic Scan action/AI

## Task ID: 21
- Status: DONE
- Description: Add new conftest: check if admirals remove ship is called only from fleet class! ( to maintain consistency)
- Priority: High
- Dependencies: None

## Task ID: 22
- Status: DONE
- Description: Fix scanner ship rotation. Ensure it correctly faces its direction of movement.
- Priority: High
- Dependencies: 6

## Task ID: 23
- Status: DONE
- Description: Prevent scanners from scanning asteroids larger than their scan range. Modify `ScannerAdmiral` to check `asteroid.radius < scanner.scan_range` before assigning scan targets.
- Priority: High
- Dependencies: 8, 20

## Task ID: 24
- Status: DONE
- Description: Investigate and fix bug where `MiningShip` might get stuck or assigned incorrectly when returning to base and receiving new orders immediately.
- Priority: High
- Dependencies: 10, 18

## Task ID: 25
- Status: DONE
- Description: Create `ResearchSystem` class. This class will manage available research items, their costs, current research levels, and methods to apply their effects.
- Priority: High
- Dependencies: None

## Task ID: 26
- Status: DONE
- Description: Define specific researchable upgrades (ship speed, cargo size, mining speed, scan speed, scan radius), their incremental effects per level, and their costs (in Tritanium, Credits, Plasma). Store these definitions within or accessible by the `ResearchSystem`.
- Priority: High
- Dependencies: 25

## Task ID: 27
- Status: DONE
- Description: Integrate `ResearchSystem` with `HUDManager` to display available research options, their current levels, costs for the next level, and a button to purchase/research them in the "Research" tab.
- Priority: Medium
- Dependencies: 25, 26

## Task ID: 28
- Status: DONE
- Description: Implement the logic to purchase research. This includes: checking if the player has enough resources, deducting resources from the central planet's storage, and updating the research level in the `ResearchSystem`.
- Priority: Medium
- Dependencies: 25, 26, 11

## Task ID: 29
- Status: Done
- Description: Implement the application of research effects. Modify relevant ship classes (e.g., `Spaceship`, `MiningShip`, `ScannerShip`) or their admirals to query the `ResearchSystem` for current bonus levels and apply them to their stats (e.g., speed, cargo capacity, mining rate, scan speed, scan radius).
- Priority: Medium
- Dependencies: 25, 26, 6, 9

## Task ID: 30
- Status: TODO
- Description: Add unit tests for the `ResearchSystem`, covering aspects like initializing research items, checking costs, purchasing upgrades, and verifying that effects are correctly calculated/applied (even if indirectly through mock objects).
- Priority: Medium
- Dependencies: 25

## Task ID: 31
- Status: DONE
- Description: Refactor `ResourceType.list()` to return enum members instead of names. Update all usages and fix resulting test failures in `test_asteroid.py` and `test_miner_admiral.py`.
- Priority: High
- Dependencies: 19

# TODO: click on Random + button unassigns a ship from category with the most ships
# TODO: fix alignment in research tab
# TODO: ADD mining ship return to base to refill logic like in scanner