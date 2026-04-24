# Naming Refactor Report (Step 1)

## Scope
- Updated: `main-copy.py`
- Updated: `terrain_builder-copy.py`
- Focus: naming consistency and English-first identifiers

## What Was Changed

### `main-copy.py`
- Renamed default/config constants to clearer `ALL_CAPS` names:
  - `DEFAULT_N_AGENTS` -> `DEFAULT_PREY_COUNT`
  - `DEFAULT_N_PRED` -> `DEFAULT_PREDATOR_COUNT`
  - `DEFAULT_N_FOOD` -> `DEFAULT_CLOVER_CAPACITY`
  - `DEFAULT_SPEED` -> `DEFAULT_INITIAL_SPEED`
  - `DEFAULT_SIZE` -> `DEFAULT_INITIAL_SIZE`
  - `DEFAULT_SENSE` -> `DEFAULT_INITIAL_SENSE`
  - `DEFAULT_MUT_PROB` -> `DEFAULT_MUTATION_PROBABILITY`
  - `DEFAULT_MUT_STR` -> `DEFAULT_MUTATION_STRENGTH`
  - `DEFAULT_SIM_SPEED` -> `DEFAULT_SIMULATION_DELAY_SECONDS`
  - `DEFAULT_UI_REFRESH_MS` -> `DEFAULT_UI_REFRESH_INTERVAL_MS`
- Renamed terrain access methods for readability:
  - `get_props_at(...)` -> `get_terrain_props_at(...)`
  - `get_water_dist_at(...)` -> `get_water_distance_at(...)`
- Standardized mutation parameter naming:
  - `mut_prob` / `mut_str` -> `mutation_probability` / `mutation_strength`
- Renamed UI helper class:
  - `ParamEntry` -> `ParameterEntry`
- Renamed key UI/state attributes:
  - `q` (App side) -> `data_queue`
  - `ent_speed` -> `entry_simulation_delay`
  - `ent_refresh` -> `entry_ui_refresh_ms`
  - `var_debug` -> `show_debug_overlay`
  - `var_terrain` -> `selected_terrain_name`
  - `opt_terrain` -> `terrain_option_menu`
  - `_agent_graphics` -> `_agent_canvas_items`
  - `_terrain_drawn` -> `_is_terrain_drawn`
- Updated UI labels/status text to English where touched.

### `terrain_builder-copy.py`
- Renamed `generate_terrain_grid(...)` threshold parameters:
  - `t_water`, `t_sand`, `t_grass`, `t_forest`, `t_mount`
  - -> `water_threshold`, `sand_threshold`, `grass_threshold`, `forest_threshold`, `mountain_threshold`
- Renamed terrain type local variable:
  - `ctype` -> `terrain_type`
- Renamed form/input widget fields to explicit snake_case names:
  - `ent_w`, `ent_h`, `ent_cell`, `ent_seed`
  - -> `entry_width`, `entry_height`, `entry_cell_size`, `entry_seed`
- Renamed scale widgets:
  - `scl_scale`, `scl_oct` -> `scale_noise_frequency`, `scale_octaves`
  - `scl_water`, `scl_sand`, `scl_grass`, `scl_forest`, `scl_mount`
  - -> `scale_water_threshold`, `scale_sand_threshold`, `scale_grass_threshold`, `scale_forest_threshold`, `scale_mountain_threshold`

## Enforced Naming Standard (for ongoing development)

- Classes: `PascalCase`
  - Example: `TerrainBuilder`, `SimThread`, `ParameterEntry`
- Functions/methods/variables/attributes: `snake_case`
  - Example: `generate_terrain_grid`, `get_terrain_props_at`, `entry_ui_refresh_ms`
- Constants: `ALL_CAPS`
  - Example: `DEFAULT_MUTATION_STRENGTH`, `SIM_WIDTH`
- Boolean names should read as true/false flags
  - Example: `_is_terrain_drawn`, `show_debug_overlay`
- Prefer descriptive names over abbreviations
  - Avoid: `ent_*`, `scl_*`, `mut_str`, `ctype`
  - Prefer: `entry_*`, `scale_*`, `mutation_strength`, `terrain_type`
- Keep identifiers and new user-facing labels in English.

## Notes
- JSON terrain cell keys (`"h"`, `"t"`) were kept as-is for compatibility with existing saved terrain files.
- This step focuses on naming only; behavior changes were intentionally avoided.

## Enum Migration (Step 2)

### `main-copy.py`
- Added enum classes:
  - `EntityType` (`AGENT`, `PREY`, `PREDATOR`, `CLOVER`)
  - `Priority` (`THIRST`, `HUNGER`, `REPRODUCTION`, `WANDER`)
  - `Action` (`WANDER`, `FLEE`, `MATE`, `THIRST`, `DRINK`, `HUNGER`, `EAT`, `HUNT`, `CONSUME`, `GROW`)
- Replaced string comparisons with enum checks in simulation logic.
- Replaced `cls_name` with `entity_type` in agents.
- Kept payload/UI compatibility by serializing enum values:
  - `ag.current_action.value`
  - `ag.entity_type.value`

### Enforced rule for future work
- Use enums in core simulation logic.
- Convert to strings only at boundaries (UI, queue payloads, persistence).

## No-Else Refactor (Step 3)

### Scope
- Updated: `main-copy.py`
- Updated: `terrain_builder-copy.py`

### What was changed
- Removed all `else:` blocks and replaced them with:
  - guard clauses / early returns,
  - sequential `if` checks,
  - explicit fallback branches without `else`.
- Refactored high-branch behavior methods (`Prey.act`, `Predator.act`) to return early per priority path.
- Refactored UI flow methods (`App._set_ui_running`, `App.toggle_pause`, `_draw_sim`) to avoid `else` blocks.
- Refactored terrain generation classification defaulting in `terrain_builder-copy.py` (default peak + guarded threshold checks).

### Enforced rule for future work
- Avoid block `else` branches.
- Prefer one-directional flow with early exits for readability and lower nesting.

## SRP and Primitive Encapsulation (Step 4)

### `main-copy.py`
- Added self-documenting interaction constants:
  - `REPRODUCTION_DISTANCE_PADDING`
  - `INTERACTION_DISTANCE_PADDING`
  - `WATER_SHORELINE_PADDING`
  - `THIRST_RESTORE_AMOUNT`
  - speed multipliers for flee/chase
- Encapsulated repeated primitive behavior in `Agent` helpers:
  - `is_in_interaction_range(...)`
  - `try_drink_from_nearest_water(...)`
- Reused helpers in `Prey.act` and `Predator.act` to reduce duplication and improve single-responsibility structure.

### `terrain_builder-copy.py`
- Added value object `TerrainThresholds` to encapsulate threshold normalization and biome classification behavior.
- Added helper `_build_noise_grid(...)` to separate noise generation from terrain classification.
- Updated `generate_terrain_grid(...)` and `TerrainBuilder.generate_terrain()` to use `TerrainThresholds` for clearer, self-documenting flow.

### Enforced rule for future work
- Encapsulate domain primitives that carry behavior (threshold sets, interaction rules) into dedicated objects.
- Keep methods focused on one responsibility and move reusable behavior to named helpers.

## SRP Decomposition and Comment Cleanup (Step 5)

### `main-copy.py`
- Split `Prey.act` into focused helpers:
  - `_categorize_visible_entities(...)`
  - `_flee_if_needed(...)`
  - `_handle_reproduction(...)`
  - `_handle_thirst(...)`
  - `_handle_hunger(...)`
- Split `Predator.act` into focused helpers:
  - `_handle_reproduction(...)`
  - `_handle_thirst(...)`
  - `_select_prey_target(...)`
  - `_handle_hunt(...)`
- Preserved original decision order and side effects while reducing method size and duplication.

### Comment policy applied
- Removed low-value structural comments.
- Kept concise comments only where behavior/math is non-obvious.
- Standardized touched comments to English.

