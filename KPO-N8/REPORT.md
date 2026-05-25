# Test Report (Unit Tests)

## Test list and intent

1. test_terrain_load_and_water_distance
   - Loads a tiny terrain from JSON and verifies:
     - Correct terrain type lookup by coordinates.
     - Correct BFS-derived water distance.
     - Correct nearest water coordinate.
   - Detects errors in terrain loading, BFS distance propagation, or coordinate mapping.

2. test_spatial_grid_skips_dead_agents
   - Inserts a dead agent into SpatialGrid and confirms it does not appear in queries.
   - Detects regressions where dead agents remain searchable.

3. test_agent_move_step_blocks_nonwalkable
   - Attempts to move a prey into a non-walkable cell.
   - Asserts the move is rejected and position is unchanged.
   - Detects incorrect walkable checks or movement side effects.

4. test_agent_priority_rules
   - Verifies that high thirst overrides hunger, and high hunger selects hunger priority.
   - Detects incorrect priority thresholds or priority ordering.

5. test_reproduction_costs_are_applied
   - Forces a valid reproduction pair and applies reproduction cost.
   - Asserts hunger/thirst cost and cooldown are set.
   - Detects missing or incorrect reproduction penalties.

6. test_prey_flee_interrupts_for_predator
   - Places a predator within sense range and checks prey switches to flee action.
   - Verifies the prey moves away.
   - Detects errors in predator detection or flee logic.

7. test_predator_consumes_close_prey
   - Places predator and prey on the same tile and triggers hunting.
   - Confirms prey is killed and predator consumes (hunger reset).
   - Detects interaction-range or consume logic issues.

8. test_clover_spawns_when_ready
   - Sets clover to a ready state, forces deterministic random spawn angle/distance.
   - Confirms a new clover is spawned and parent thirst increases.
   - Detects spawn failure or incorrect reproduction consequences.

9. test_terrain_clamps_cell_coords
   - Requests cell coordinates outside bounds.
   - Confirms coordinates are clamped to grid edges.
   - Detects clamping errors that could lead to IndexError or invalid indices.

10. test_agent_drinks_at_shoreline
    - Places prey adjacent to water, calls drink logic.
    - Confirms it drinks immediately and thirst decreases.
    - Detects incorrect shoreline distance logic or thirst updates.

11. test_predator_priority_prefers_hunger_over_thirst
    - Sets predator hunger and thirst both high.
    - Confirms predator chooses hunger priority per its custom rule order.
    - Detects changes to predator priority ordering.

12. test_reproduction_partner_requires_opposite_sex
    - Attempts reproduction between same-sex prey.
    - Confirms it is rejected.
    - Detects incorrect partner validation.

## Notes
- The tests use a tiny synthetic terrain JSON written to a temp folder to avoid reliance on external terrain files.
- Randomness is controlled via fixed values or monkeypatching to make the tests deterministic.
- If you change thresholds or action logic, update tests to reflect the intended behavior.


## How to run the tests

```powershell
pip install -r requirements.txt
pytest
```

## External tools (quality checks)

### flake8

Short summary:
- Findings focus on line length (E501), blank line spacing (E302/E305), multiple statements on one line (E701), trailing whitespace (W291/W293), inline comment spacing (E261), and missing final newline (W292).

Command:

```powershell
flake8 main.py terrain_builder.py
```

Exact output:

```
main.py:24:80: E501 line too long (80 > 79 characters)
main.py:31:80: E501 line too long (80 > 79 characters)
main.py:52:1: E302 expected 2 blank lines, found 1
main.py:78:1: E305 expected 2 blank lines after class or function definition, found 1
main.py:85:1: E302 expected 2 blank lines, found 1
main.py:88:80: E501 line too long (106 > 79 characters)
main.py:90:80: E501 line too long (105 > 79 characters)
main.py:92:80: E501 line too long (105 > 79 characters)
main.py:94:80: E501 line too long (105 > 79 characters)
main.py:96:80: E501 line too long (105 > 79 characters)
main.py:98:80: E501 line too long (106 > 79 characters)
main.py:143:80: E501 line too long (94 > 79 characters)
main.py:144:80: E501 line too long (89 > 79 characters)
main.py:171:80: E501 line too long (85 > 79 characters)
main.py:174:80: E501 line too long (83 > 79 characters)
main.py:178:80: E501 line too long (80 > 79 characters)
main.py:212:27: E701 multiple statements on one line (colon)
main.py:250:80: E501 line too long (84 > 79 characters)
main.py:287:80: E501 line too long (89 > 79 characters)
main.py:288:80: E501 line too long (87 > 79 characters)
main.py:327:80: E501 line too long (92 > 79 characters)
main.py:330:80: E501 line too long (91 > 79 characters)
main.py:333:80: E501 line too long (92 > 79 characters)
main.py:350:80: E501 line too long (83 > 79 characters)
main.py:431:80: E501 line too long (84 > 79 characters)
main.py:456:80: E501 line too long (103 > 79 characters)
main.py:475:80: E501 line too long (86 > 79 characters)
main.py:484:80: E501 line too long (83 > 79 characters)
main.py:519:80: E501 line too long (89 > 79 characters)
main.py:530:80: E501 line too long (117 > 79 characters)
main.py:533:80: E501 line too long (91 > 79 characters)
main.py:546:80: E501 line too long (82 > 79 characters)
main.py:550:80: E501 line too long (96 > 79 characters)
main.py:552:80: E501 line too long (93 > 79 characters)
main.py:553:80: E501 line too long (91 > 79 characters)
main.py:555:80: E501 line too long (94 > 79 characters)
main.py:613:80: E501 line too long (93 > 79 characters)
main.py:617:80: E501 line too long (95 > 79 characters)
main.py:673:80: E501 line too long (94 > 79 characters)
main.py:706:80: E501 line too long (83 > 79 characters)
main.py:736:80: E501 line too long (94 > 79 characters)
main.py:791:80: E501 line too long (84 > 79 characters)
main.py:813:80: E501 line too long (94 > 79 characters)
main.py:885:80: E501 line too long (105 > 79 characters)
main.py:886:80: E501 line too long (93 > 79 characters)
main.py:909:80: E501 line too long (102 > 79 characters)
main.py:968:80: E501 line too long (89 > 79 characters)
main.py:990:80: E501 line too long (86 > 79 characters)
main.py:993:80: E501 line too long (82 > 79 characters)
main.py:994:80: E501 line too long (80 > 79 characters)
main.py:995:80: E501 line too long (82 > 79 characters)
main.py:996:80: E501 line too long (90 > 79 characters)
main.py:1048:80: E501 line too long (100 > 79 characters)
main.py:1052:80: E501 line too long (88 > 79 characters)
main.py:1053:80: E501 line too long (92 > 79 characters)
main.py:1108:80: E501 line too long (91 > 79 characters)
main.py:1109:80: E501 line too long (91 > 79 characters)
main.py:1110:80: E501 line too long (89 > 79 characters)
main.py:1111:80: E501 line too long (87 > 79 characters)
main.py:1112:80: E501 line too long (89 > 79 characters)
main.py:1113:80: E501 line too long (85 > 79 characters)
main.py:1114:80: E501 line too long (91 > 79 characters)
main.py:1115:80: E501 line too long (91 > 79 characters)
main.py:1116:80: E501 line too long (89 > 79 characters)
main.py:1117:80: E501 line too long (87 > 79 characters)
main.py:1118:80: E501 line too long (89 > 79 characters)
main.py:1119:80: E501 line too long (85 > 79 characters)
main.py:1120:80: E501 line too long (97 > 79 characters)
main.py:1121:80: E501 line too long (91 > 79 characters)
main.py:1264:80: E501 line too long (88 > 79 characters)
main.py:1273:80: E501 line too long (89 > 79 characters)
main.py:1287:80: E501 line too long (100 > 79 characters)
main.py:1290:80: E501 line too long (112 > 79 characters)
main.py:1293:80: E501 line too long (103 > 79 characters)
main.py:1303:80: E501 line too long (82 > 79 characters)
main.py:1328:80: E501 line too long (85 > 79 characters)
main.py:1329:80: E501 line too long (97 > 79 characters)
main.py:1330:80: E501 line too long (98 > 79 characters)
main.py:1332:80: E501 line too long (94 > 79 characters)
main.py:1333:80: E501 line too long (91 > 79 characters)
main.py:1334:80: E501 line too long (94 > 79 characters)
main.py:1336:80: E501 line too long (91 > 79 characters)
main.py:1337:80: E501 line too long (95 > 79 characters)
main.py:1338:80: E501 line too long (118 > 79 characters)
main.py:1345:80: E501 line too long (81 > 79 characters)
main.py:1351:80: E501 line too long (96 > 79 characters)
main.py:1369:80: E501 line too long (80 > 79 characters)
main.py:1382:80: E501 line too long (89 > 79 characters)
main.py:1384:80: E501 line too long (85 > 79 characters)
main.py:1390:80: E501 line too long (84 > 79 characters)
main.py:1391:80: E501 line too long (93 > 79 characters)
main.py:1436:80: E501 line too long (89 > 79 characters)
main.py:1437:80: E501 line too long (88 > 79 characters)
main.py:1503:80: E501 line too long (85 > 79 characters)
main.py:1535:28: E701 multiple statements on one line (colon)
main.py:1569:80: E501 line too long (106 > 79 characters)
main.py:1650:80: E501 line too long (83 > 79 characters)
main.py:1658:80: E501 line too long (98 > 79 characters)
main.py:1679:80: E501 line too long (91 > 79 characters)
main.py:1682:80: E501 line too long (83 > 79 characters)
main.py:1689:80: E501 line too long (84 > 79 characters)
main.py:1696:80: E501 line too long (118 > 79 characters)
main.py:1697:80: E501 line too long (107 > 79 characters)
main.py:1698:80: E501 line too long (110 > 79 characters)
main.py:1699:80: E501 line too long (107 > 79 characters)
main.py:1700:80: E501 line too long (110 > 79 characters)
main.py:1701:80: E501 line too long (105 > 79 characters)
main.py:1703:80: E501 line too long (95 > 79 characters)
main.py:1712:80: E501 line too long (90 > 79 characters)
main.py:1715:80: E501 line too long (92 > 79 characters)
main.py:1716:80: E501 line too long (91 > 79 characters)
main.py:1731:80: E501 line too long (99 > 79 characters)
main.py:1742:80: E501 line too long (92 > 79 characters)
main.py:1760:80: E501 line too long (144 > 79 characters)
main.py:1765:19: W292 no newline at end of file
terrain_builder.py:23:80: E501 line too long (100 > 79 characters)
terrain_builder.py:61:1: E302 expected 2 blank lines, found 1
terrain_builder.py:85:80: E501 line too long (95 > 79 characters)
terrain_builder.py:87:80: E501 line too long (89 > 79 characters)
terrain_builder.py:98:1: W293 blank line contains whitespace
terrain_builder.py:100:1: W293 blank line contains whitespace
terrain_builder.py:103:1: E302 expected 2 blank lines, found 1
terrain_builder.py:119:1: W293 blank line contains whitespace
terrain_builder.py:120:80: E501 line too long (100 > 79 characters)
terrain_builder.py:128:1: W293 blank line contains whitespace
terrain_builder.py:134:80: E501 line too long (80 > 79 characters)
terrain_builder.py:139:80: E501 line too long (83 > 79 characters)
terrain_builder.py:144:80: E501 line too long (88 > 79 characters)
terrain_builder.py:151:1: W293 blank line contains whitespace
terrain_builder.py:153:80: E501 line too long (90 > 79 characters)
terrain_builder.py:158:80: E501 line too long (80 > 79 characters)
terrain_builder.py:164:1: W293 blank line contains whitespace
terrain_builder.py:166:80: E501 line too long (109 > 79 characters)
terrain_builder.py:171:80: E501 line too long (108 > 79 characters)
terrain_builder.py:177:1: W293 blank line contains whitespace
terrain_builder.py:179:80: E501 line too long (109 > 79 characters)
terrain_builder.py:184:80: E501 line too long (110 > 79 characters)
terrain_builder.py:190:1: W293 blank line contains whitespace
terrain_builder.py:192:80: E501 line too long (112 > 79 characters)
terrain_builder.py:198:1: W293 blank line contains whitespace
terrain_builder.py:199:80: E501 line too long (124 > 79 characters)
terrain_builder.py:200:80: E501 line too long (114 > 79 characters)
terrain_builder.py:201:80: E501 line too long (109 > 79 characters)
terrain_builder.py:234:80: E501 line too long (82 > 79 characters)
terrain_builder.py:243:26: E261 at least two spaces before inline comment
terrain_builder.py:244:26: E261 at least two spaces before inline comment
terrain_builder.py:245:26: E261 at least two spaces before inline comment
terrain_builder.py:246:26: E261 at least two spaces before inline comment
terrain_builder.py:247:26: E261 at least two spaces before inline comment
terrain_builder.py:260:80: E501 line too long (114 > 79 characters)
terrain_builder.py:266:1: W293 blank line contains whitespace
terrain_builder.py:269:50: W291 trailing whitespace
terrain_builder.py:282:80: E501 line too long (87 > 79 characters)
terrain_builder.py:284:1: E305 expected 2 blank lines after class or function definition, found 1

### pylint

Short summary:
- Main issues are line length (C0301), missing docstrings (C0114/C0115/C0116), too many arguments/attributes (R0913/R0902), and style warnings like multiple statements on one line (C0321) and missing final newline (C0304).
- Overall score: 8.75/10.

Command:

```powershell
pylint main.py terrain_builder.py
```

Exact output:

```
************* Module main
main.py:88:0: C0301: Line too long (106/100) (line-too-long)
main.py:90:0: C0301: Line too long (105/100) (line-too-long)
main.py:92:0: C0301: Line too long (105/100) (line-too-long)
main.py:94:0: C0301: Line too long (105/100) (line-too-long)
main.py:96:0: C0301: Line too long (105/100) (line-too-long)
main.py:98:0: C0301: Line too long (106/100) (line-too-long)
main.py:456:0: C0301: Line too long (103/100) (line-too-long)
main.py:530:0: C0301: Line too long (117/100) (line-too-long)
main.py:885:0: C0301: Line too long (105/100) (line-too-long)
main.py:909:0: C0301: Line too long (102/100) (line-too-long)
main.py:1290:0: C0301: Line too long (112/100) (line-too-long)
main.py:1293:0: C0301: Line too long (103/100) (line-too-long)
main.py:1338:0: C0301: Line too long (118/100) (line-too-long)
main.py:1569:0: C0301: Line too long (106/100) (line-too-long)
main.py:1687:0: C0325: Unnecessary parens after '=' keyword (superfluous-parens)
main.py:1696:0: C0301: Line too long (118/100) (line-too-long)
main.py:1697:0: C0301: Line too long (107/100) (line-too-long)
main.py:1698:0: C0301: Line too long (110/100) (line-too-long)
main.py:1699:0: C0301: Line too long (107/100) (line-too-long)
main.py:1700:0: C0301: Line too long (110/100) (line-too-long)
main.py:1701:0: C0301: Line too long (105/100) (line-too-long)
main.py:1760:0: C0301: Line too long (144/100) (line-too-long)
main.py:1765:0: C0304: Final newline missing (missing-final-newline)
main.py:1:0: C0302: Too many lines in module (1765/1000) (too-many-lines)
main.py:1:0: C0114: Missing module docstring (missing-module-docstring)
main.py:52:0: C0115: Missing class docstring (missing-class-docstring)
main.py:59:0: C0115: Missing class docstring (missing-class-docstring)
main.py:66:0: C0115: Missing class docstring (missing-class-docstring)
main.py:85:0: C0115: Missing class docstring (missing-class-docstring)
main.py:85:0: R0902: Too many instance attributes (8/7) (too-many-instance-attributes)
main.py:119:13: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
main.py:181:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:190:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:194:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:198:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:203:0: C0115: Missing class docstring (missing-class-docstring)
main.py:208:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:211:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:212:28: C0321: More than one statement on a single line (multiple-statements)
main.py:219:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:233:0: C0115: Missing class docstring (missing-class-docstring)
main.py:233:0: R0902: Too many instance attributes (17/7) (too-many-instance-attributes)
main.py:250:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:250:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:276:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:279:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:307:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:315:12: E1102: Agent.death_hook is not callable (not-callable)
main.py:317:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:343:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:382:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:428:8: W0212: Access to a protected member _apply_reproduction_cost of a client class (protected-access)
main.py:433:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:448:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:456:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:460:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:484:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:530:4: R0913: Too many arguments (7/5) (too-many-arguments)
main.py:530:4: R0917: Too many positional arguments (7/5) (too-many-positional-arguments)
main.py:555:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:555:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:555:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:589:33: W0613: Unused argument 'entities' (unused-argument)
main.py:589:43: W0613: Unused argument 'sense_sq' (unused-argument)
main.py:589:53: W0613: Unused argument 'terrain' (unused-argument)
main.py:596:0: C0115: Missing class docstring (missing-class-docstring)
main.py:608:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:608:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:682:0: C0115: Missing class docstring (missing-class-docstring)
main.py:694:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:694:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:750:0: C0115: Missing class docstring (missing-class-docstring)
main.py:750:0: R0902: Too many instance attributes (8/7) (too-many-instance-attributes)
main.py:782:4: W0221: Number of parameters was 2 in 'Agent.update_needs' and is now 1 in overriding 'Clover.update_needs' method (arguments-differ)
main.py:854:4: W0221: Number of parameters was 6 in 'Agent.act' and is now 5 in overriding 'Clover.act' method (arguments-differ)
main.py:884:0: C0115: Missing class docstring (missing-class-docstring)
main.py:884:0: R0902: Too many instance attributes (19/7) (too-many-instance-attributes)
main.py:885:4: R0913: Too many arguments (11/5) (too-many-arguments)
main.py:885:4: R0917: Too many positional arguments (11/5) (too-many-positional-arguments)
main.py:935:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:940:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:943:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:947:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:967:32: C0103: Argument name "AgentClass" doesn't conform to snake_case naming style (invalid-name)
main.py:1062:30: W0613: Unused argument 'agent' (unused-argument)
main.py:1205:0: C0115: Missing class docstring (missing-class-docstring)
main.py:1214:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1217:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1221:0: C0115: Missing class docstring (missing-class-docstring)
main.py:1221:0: R0902: Too many instance attributes (35/7) (too-many-instance-attributes)
main.py:1279:8: C0104: Disallowed name "bar" (disallowed-name)
main.py:1458:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1534:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1535:29: C0321: More than one statement on a single line (multiple-statements)
main.py:1544:4: C0116: Missing function or method docstring (missing-function-docstring)
main.py:1652:4: R0913: Too many arguments (6/5) (too-many-arguments)
main.py:1652:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
main.py:1707:4: R0913: Too many arguments (9/5) (too-many-arguments)
main.py:1707:4: R0917: Too many positional arguments (9/5) (too-many-positional-arguments)
main.py:1731:4: R0913: Too many arguments (10/5) (too-many-arguments)
main.py:1731:4: R0917: Too many positional arguments (10/5) (too-many-positional-arguments)
main.py:1256:8: W0201: Attribute 'sim_canvas' defined outside __init__ (attribute-defined-outside-init)
main.py:1264:8: W0201: Attribute 'ctrl' defined outside __init__ (attribute-defined-outside-init)
main.py:1271:8: W0201: Attribute 'lbl_info' defined outside __init__ (attribute-defined-outside-init)
main.py:1287:8: W0201: Attribute 'btn_start' defined outside __init__ (attribute-defined-outside-init)
main.py:1290:8: W0201: Attribute 'btn_pause' defined outside __init__ (attribute-defined-outside-init)
main.py:1293:8: W0201: Attribute 'btn_restart' defined outside __init__ (attribute-defined-outside-init)
main.py:1299:8: W0201: Attribute 'entry_simulation_delay' defined outside __init__ (attribute-defined-outside-init)
main.py:1304:8: W0201: Attribute 'entry_ui_refresh_ms' defined outside __init__ (attribute-defined-outside-init)
main.py:1309:8: W0201: Attribute 'show_debug_overlay' defined outside __init__ (attribute-defined-outside-init)
main.py:1328:8: W0201: Attribute 'input_prey_count' defined outside __init__ (attribute-defined-outside-init)
main.py:1329:8: W0201: Attribute 'input_predator_count' defined outside __init__ (attribute-defined-outside-init)
main.py:1330:8: W0201: Attribute 'input_clover_capacity' defined outside __init__ (attribute-defined-outside-init)
main.py:1332:8: W0201: Attribute 'input_initial_speed' defined outside __init__ (attribute-defined-outside-init)
main.py:1333:8: W0201: Attribute 'input_initial_size' defined outside __init__ (attribute-defined-outside-init)
main.py:1334:8: W0201: Attribute 'input_initial_sense' defined outside __init__ (attribute-defined-outside-init)
main.py:1336:8: W0201: Attribute 'input_mutation_probability' defined outside __init__ (attribute-defined-outside-init)
main.py:1338:8: W0201: Attribute 'input_mutation_strength' defined outside __init__ (attribute-defined-outside-init)
main.py:1350:8: W0201: Attribute 'selected_terrain_name' defined outside __init__ (attribute-defined-outside-init)
main.py:1351:8: W0201: Attribute 'terrain_option_menu' defined outside __init__ (attribute-defined-outside-init)
main.py:1358:8: W0201: Attribute 'chk_enable_logging' defined outside __init__ (attribute-defined-outside-init)
main.py:1366:8: W0201: Attribute 'logging_options_frame' defined outside __init__ (attribute-defined-outside-init)
main.py:1370:8: W0201: Attribute 'entry_log_dir' defined outside __init__ (attribute-defined-outside-init)
main.py:1374:8: W0201: Attribute 'btn_browse_log_dir' defined outside __init__ (attribute-defined-outside-init)
main.py:1383:8: W0201: Attribute 'entry_log_interval' defined outside __init__ (attribute-defined-outside-init)
************* Module terrain_builder
terrain_builder.py:98:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:100:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:119:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:128:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:151:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:164:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:166:0: C0301: Line too long (109/100) (line-too-long)
terrain_builder.py:171:0: C0301: Line too long (108/100) (line-too-long)
terrain_builder.py:177:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:179:0: C0301: Line too long (109/100) (line-too-long)
terrain_builder.py:184:0: C0301: Line too long (110/100) (line-too-long)
terrain_builder.py:190:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:192:0: C0301: Line too long (112/100) (line-too-long)
terrain_builder.py:198:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:199:0: C0301: Line too long (124/100) (line-too-long)
terrain_builder.py:200:0: C0301: Line too long (114/100) (line-too-long)
terrain_builder.py:201:0: C0301: Line too long (109/100) (line-too-long)
terrain_builder.py:260:0: C0301: Line too long (114/100) (line-too-long)
terrain_builder.py:266:0: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:269:49: C0303: Trailing whitespace (trailing-whitespace)
terrain_builder.py:1:0: C0114: Missing module docstring (missing-module-docstring)
terrain_builder.py:10:0: C0115: Missing class docstring (missing-class-docstring)
terrain_builder.py:18:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:18:4: R0913: Too many arguments (6/5) (too-many-arguments)
terrain_builder.py:18:4: R0917: Too many positional arguments (6/5) (too-many-positional-arguments)
terrain_builder.py:25:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:61:0: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:61:0: R0913: Too many arguments (11/5) (too-many-arguments)
terrain_builder.py:61:0: R0917: Too many positional arguments (11/5) (too-many-positional-arguments)
terrain_builder.py:61:0: R0914: Too many local variables (24/15) (too-many-locals)
terrain_builder.py:103:0: C0115: Missing class docstring (missing-class-docstring)
terrain_builder.py:103:0: R0902: Too many instance attributes (16/7) (too-many-instance-attributes)
terrain_builder.py:116:4: R0915: Too many statements (66/50) (too-many-statements)
terrain_builder.py:203:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:208:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:262:4: C0116: Missing function or method docstring (missing-function-docstring)
terrain_builder.py:280:17: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)

------------------------------------------------------------------
Your code has been rated at 8.75/10 (previous run: 7.92/10, +0.82)

