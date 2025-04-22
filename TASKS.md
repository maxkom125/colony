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
- Status: TODO
- Description: Define resource conversion rates (Tritanium <-> Credits, Plasma <-> Credits) including fees.
- Priority: Low
- Dependencies: 5

## Task ID: 13
- Status: TODO
- Description: Implement UI/mechanism for resource conversion.
- Priority: Low
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
- Status: TODO
- Description: Implement resource mining priorities. Add UI sliders (0 to 1, default 1) for Tritanium, Credits, and Plasma. Store these priority values. Modify Mining Ship AI (`find_nearest_asteroid` or a new planning logic) to select target asteroids based on a weighted distribution reflecting these priorities, aiming for a proportional mining intensity/frequency for each resource rather than a strict queue. (Reminder: Discuss implementation details of weighted selection/expedition planning when starting this task).
- Priority: Medium
- Dependencies: 10 # Depends on Mining Implementation 

## Task ID: 19
- Status: TODO
- Description: Implement unit tests for key components (e.g., Camera coordinate conversion, Planet storage updates, construction/conversion logic, AI target scoring).
- Priority: High
- Dependencies: None 

## Task ID: 20
- Status: TODO
- Description: Improve Scanner AI: Prevent multiple scanners from targeting the same unscanned asteroid simultaneously. Each scanner should check if an asteroid is already targeted by another scanner before selecting it.
- Priority: Medium
- Dependencies: 8 # Depends on basic Scan action/AI 